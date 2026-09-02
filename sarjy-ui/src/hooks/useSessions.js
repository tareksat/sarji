import { useCallback, useEffect, useRef, useState } from 'react';
import {
  deleteSession,
  fetchMessages,
  fetchSessions,
  readStored,
  renameSession as renameSessionRequest,
  writeStored,
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

  // Read inside callbacks without making them depend on every state change.
  const sessionsRef = useRef(sessions);
  const activeIdRef = useRef(activeId);
  const messagesRef = useRef(messagesBySession);

  // Every write to the session list goes through here so the ref is current the
  // instant the call returns. A ref synced by an effect lags a render, which is
  // long enough for two quick deletes to resurrect the first one from a stale
  // snapshot, and a state updater's return value cannot be read back
  // synchronously (React runs it at render time, twice under StrictMode).
  const commitSessions = useCallback((updater) => {
    const next = typeof updater === 'function' ? updater(sessionsRef.current) : updater;
    sessionsRef.current = next;
    setSessions(next);
    return next;
  }, []);

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
        commitSessions([pending]);
        setActiveId(pending.id);
        setMessagesBySession({ [pending.id]: [] });
      } else {
        const stored = readStored(ACTIVE_KEY);
        const restored = loaded.some((s) => s.id === stored) ? stored : loaded[0].id;
        commitSessions(loaded);
        setActiveId(restored);
      }
      setLoadingSessions(false);
    })();

    return () => {
      cancelled = true;
    };
  }, [userId, commitSessions]);

  useEffect(() => {
    if (activeId) writeStored(ACTIVE_KEY, activeId);
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

    (async () => {
      let loaded = [];
      try {
        loaded = await fetchMessages(userId, activeId);
      } catch {
        loaded = [];
      } finally {
        if (!cancelled) {
          setMessagesBySession((prev) => ({ ...prev, [activeId]: loaded }));
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [activeId, userId]);

  const activeSession = sessions.find((s) => s.id === activeId);
  const messages = messagesBySession[activeId] ?? [];
  // Derived rather than stored: a flag set before the fetch and cleared only on
  // its non-cancelled completion latches on forever if the user switches to a
  // cached session mid-flight, leaving the chat replaced by a placeholder.
  const loadingMessages = !!activeId && messagesBySession[activeId] === undefined;

  const selectSession = useCallback((id) => setActiveId(id), []);

  const newSession = useCallback(() => {
    const pending = createPendingSession();
    commitSessions((prev) => [pending, ...prev]);
    setMessagesBySession((prev) => ({ ...prev, [pending.id]: [] }));
    setActiveId(pending.id);
  }, [commitSessions]);

  // Explicitly addressed. A turn resolves its target session once, when it is
  // sent: resolving it per delta writes a reply that is still streaming into
  // whichever conversation the user has since clicked on.
  const updateSessionMessages = useCallback((sessionId, updater) => {
    if (!sessionId) return;
    setMessagesBySession((prev) => ({
      ...prev,
      [sessionId]: updater(prev[sessionId] ?? []),
    }));
  }, []);

  const updateActiveMessages = useCallback(
    (updater) => updateSessionMessages(activeIdRef.current, updater),
    [updateSessionMessages]
  );

  // Called after a turn completes, for the session that turn was sent from. A
  // pending session has just been created server-side, so refetch to pick up its
  // derived title; otherwise just move it to the top of the list locally rather
  // than spending a request on ordering.
  const notePersisted = useCallback(async (sessionId) => {
    const id = sessionId ?? activeIdRef.current;
    const session = sessionsRef.current.find((s) => s.id === id);

    if (!session?.pending) {
      const now = new Date().toISOString();
      commitSessions((prev) =>
        prev.map((s) => (s.id === id ? { ...s, updatedAt: now } : s)).sort(byRecency)
      );
      return;
    }

    try {
      const loaded = await fetchSessions(userId);
      commitSessions((prev) => {
        const stillPending = prev.filter((s) => s.pending && !loaded.some((l) => l.id === s.id));
        return [...stillPending, ...loaded].sort(byRecency);
      });
    } catch {
      // Non-fatal: the title stays "New chat" until the next successful load.
    }
  }, [userId, commitSessions]);

  const renameActiveSession = useCallback(
    async (id, title) => {
      const trimmed = title.trim();
      if (!trimmed) return;
      const previous = sessionsRef.current.find((s) => s.id === id);
      commitSessions((prev) => prev.map((s) => (s.id === id ? { ...s, title: trimmed } : s)));

      if (previous?.pending) return; // no row to rename yet

      try {
        await renameSessionRequest(userId, id, trimmed);
      } catch {
        commitSessions((prev) =>
          prev.map((s) => (s.id === id ? { ...s, title: previous?.title ?? s.title } : s))
        );
      }
    },
    [userId, commitSessions]
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
      const next = commitSessions(replacement ? [replacement] : remaining);

      setMessagesBySession((prev) => {
        const copy = { ...prev };
        delete copy[id];
        if (replacement) copy[replacement.id] = [];
        return copy;
      });
      if (activeIdRef.current === id) setActiveId(next[0].id);
    },
    [userId, commitSessions]
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
    updateSessionMessages,
    notePersisted,
    renameActiveSession,
    removeSession,
  };
}
