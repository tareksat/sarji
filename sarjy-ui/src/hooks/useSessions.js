import { useCallback, useEffect, useRef, useState } from 'react';
import {
  deleteSession,
  fetchMessages,
  fetchSessions,
  renameSession as renameSessionRequest,
} from '../api';

const ACTIVE_KEY = 'sarjy_active_session';

// A session the user has opened but not yet sent a message in. It exists only
// in the browser until the first message creates the row server-side, which
// keeps empty sessions out of the database.
function createPendingSession() {
  return {
    id: crypto.randomUUID(),
    title: 'New chat',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    pending: true,
  };
}

function byRecency(a, b) {
  return new Date(b.updatedAt) - new Date(a.updatedAt);
}

export function useSessions(userId) {
  const [sessions, setSessions] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messagesBySession, setMessagesBySession] = useState({});
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);

  // Read inside callbacks without making them depend on every state change.
  const sessionsRef = useRef(sessions);
  const activeIdRef = useRef(activeId);
  const messagesRef = useRef(messagesBySession);

  useEffect(() => {
    sessionsRef.current = sessions;
  }, [sessions]);

  useEffect(() => {
    activeIdRef.current = activeId;
  }, [activeId]);

  useEffect(() => {
    messagesRef.current = messagesBySession;
  }, [messagesBySession]);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      let loaded = [];
      try {
        loaded = await fetchSessions(userId);
      } catch {
        loaded = [];
      }
      if (cancelled) return;

      if (loaded.length === 0) {
        const pending = createPendingSession();
        setSessions([pending]);
        setActiveId(pending.id);
        setMessagesBySession({ [pending.id]: [] });
      } else {
        const stored = localStorage.getItem(ACTIVE_KEY);
        const restored = loaded.some((s) => s.id === stored) ? stored : loaded[0].id;
        setSessions(loaded);
        setActiveId(restored);
      }
      setLoadingSessions(false);
    })();

    return () => {
      cancelled = true;
    };
  }, [userId]);

  useEffect(() => {
    if (activeId) localStorage.setItem(ACTIVE_KEY, activeId);
  }, [activeId]);

  // Messages load on demand and stay cached, so re-selecting a session is
  // instant. The cache is read through a ref so that appending a message does
  // not re-run -- and therefore cancel -- an in-flight history fetch.
  useEffect(() => {
    if (!activeId) return;
    if (messagesRef.current[activeId] !== undefined) return;

    const session = sessionsRef.current.find((s) => s.id === activeId);
    if (session?.pending) {
      setMessagesBySession((prev) => ({ ...prev, [activeId]: [] }));
      return;
    }

    let cancelled = false;
    setLoadingMessages(true);

    (async () => {
      let loaded = [];
      try {
        loaded = await fetchMessages(userId, activeId);
      } catch {
        loaded = [];
      } finally {
        if (!cancelled) {
          setMessagesBySession((prev) => ({ ...prev, [activeId]: loaded }));
          setLoadingMessages(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [activeId, userId]);

  const activeSession = sessions.find((s) => s.id === activeId);
  const messages = messagesBySession[activeId] ?? [];

  const selectSession = useCallback((id) => setActiveId(id), []);

  const newSession = useCallback(() => {
    const pending = createPendingSession();
    setSessions((prev) => [pending, ...prev]);
    setMessagesBySession((prev) => ({ ...prev, [pending.id]: [] }));
    setActiveId(pending.id);
  }, []);

  const updateActiveMessages = useCallback((updater) => {
    const id = activeIdRef.current;
    if (!id) return;
    setMessagesBySession((prev) => ({ ...prev, [id]: updater(prev[id] ?? []) }));
  }, []);

  // Called after a turn completes. A pending session has just been created
  // server-side, so refetch to pick up its derived title; otherwise just move it
  // to the top of the list locally rather than spending a request on ordering.
  const notePersisted = useCallback(async () => {
    const id = activeIdRef.current;
    const session = sessionsRef.current.find((s) => s.id === id);

    if (!session?.pending) {
      const now = new Date().toISOString();
      setSessions((prev) =>
        prev.map((s) => (s.id === id ? { ...s, updatedAt: now } : s)).sort(byRecency)
      );
      return;
    }

    try {
      const loaded = await fetchSessions(userId);
      setSessions((prev) => {
        const stillPending = prev.filter((s) => s.pending && !loaded.some((l) => l.id === s.id));
        return [...stillPending, ...loaded].sort(byRecency);
      });
    } catch {
      // Non-fatal: the title stays "New chat" until the next successful load.
    }
  }, [userId]);

  const renameActiveSession = useCallback(
    async (id, title) => {
      const trimmed = title.trim();
      if (!trimmed) return;
      const previous = sessionsRef.current.find((s) => s.id === id);
      setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, title: trimmed } : s)));

      if (previous?.pending) return; // no row to rename yet

      try {
        await renameSessionRequest(userId, id, trimmed);
      } catch {
        setSessions((prev) =>
          prev.map((s) => (s.id === id ? { ...s, title: previous?.title ?? s.title } : s))
        );
      }
    },
    [userId]
  );

  const removeSession = useCallback(
    async (id) => {
      const session = sessionsRef.current.find((s) => s.id === id);
      if (session && !session.pending) {
        try {
          await deleteSession(userId, id);
        } catch {
          return;
        }
      }

      const remaining = sessionsRef.current.filter((s) => s.id !== id);
      const replacement = remaining.length === 0 ? createPendingSession() : null;
      const next = replacement ? [replacement] : remaining;

      setSessions(next);
      setMessagesBySession((prev) => {
        const copy = { ...prev };
        delete copy[id];
        if (replacement) copy[replacement.id] = [];
        return copy;
      });
      if (activeIdRef.current === id) setActiveId(next[0].id);
    },
    [userId]
  );

  return {
    sessions,
    activeId,
    activeSession,
    messages,
    loadingSessions,
    loadingMessages,
    selectSession,
    newSession,
    updateActiveMessages,
    notePersisted,
    renameActiveSession,
    removeSession,
  };
}
