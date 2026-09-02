import { useCallback, useEffect, useRef, useState } from 'react';
import ChatWindow from './components/ChatWindow';
import { HamburgerIcon } from './components/icons';
import MessageInput from './components/MessageInput';
import SessionList from './components/SessionList';
import TurnTimings from './components/TurnTimings';
import { useSpeechRecognition } from './hooks/useSpeechRecognition';
import { useSpeechSynthesis } from './hooks/useSpeechSynthesis';
import { useSessions } from './hooks/useSessions';
import { getUserId, sendMessageStream } from './api';
import { createTurnTimer } from './timing';
import './App.css';

const userId = getUserId();

// Returns [complete sentences, remainder]. Speaking whole sentences keeps the
// prosody natural; speaking token-by-token does not.
const SENTENCE_END = /([.!?…]+["')\]]*)(\s+)/g;

// How long to wait for speech to start before publishing the turn without a
// time-to-first-audio.
const TTFA_PUBLISH_GRACE_MS = 2000;

// Speak anyway once a fragment reaches this length. A reply with no terminal
// punctuation -- a list, a code-ish answer -- would otherwise stay silent until
// the stream ends, losing the whole point of streaming the audio.
const MAX_SPOKEN_CHUNK = 240;

// Errors no amount of retrying fixes.
const FATAL_MIC_ERRORS = new Set(['not-allowed', 'service-not-allowed', 'audio-capture']);

// Backoff before re-arming the microphone after a transient error.
const MIC_RETRY_MS = 1500;

const ABBREVIATIONS = new Set([
  'mr', 'mrs', 'ms', 'dr', 'prof', 'sr', 'jr', 'st', 'vs', 'etc',
  'eg', 'ie', 'approx', 'no', 'fig', 'al', 'inc', 'ltd', 'co',
]);

// A period after one of these is punctuation inside a phrase, not the end of
// one: "Dr. Smith", "e.g. this", "U.S. policy", "1. First item".
function isAbbreviation(token) {
  if (/^[A-Za-z]$/.test(token)) return true; // an initial, "A."
  if (/^\d+$/.test(token)) return true; // a list marker, "1."
  if (/^(?:[A-Za-z]\.)+[A-Za-z]?$/.test(token)) return true; // "U.S", "e.g"
  return ABBREVIATIONS.has(token.toLowerCase().replace(/\./g, ''));
}

function takeSentences(buffer) {
  const sentences = [];
  let rest = buffer;

  for (;;) {
    let match = null;
    SENTENCE_END.lastIndex = 0;
    for (;;) {
      const candidate = SENTENCE_END.exec(rest);
      if (!candidate) break;
      const lastToken = /\S+$/.exec(rest.slice(0, candidate.index))?.[0] ?? '';
      if (candidate[1] === '.' && isAbbreviation(lastToken)) continue;
      match = candidate;
      break;
    }
    if (!match) break;

    const cut = match.index + match[1].length + match[2].length;
    const sentence = rest.slice(0, cut).trim();
    if (sentence) sentences.push(sentence);
    rest = rest.slice(cut);
  }

  if (rest.length >= MAX_SPOKEN_CHUNK) {
    // Break at a word boundary so an utterance never splits a word.
    const space = rest.lastIndexOf(' ');
    const cut = space > 0 ? space + 1 : rest.length;
    const chunk = rest.slice(0, cut).trim();
    if (chunk) {
      sentences.push(chunk);
      rest = rest.slice(cut);
    }
  }

  return [sentences, rest];
}

export default function App() {
  const {
    sessions,
    activeId,
    activeSession,
    messages,
    loadingSessions,
    loadingMessages,
    selectSession,
    newSession,
    updateSessionMessages,
    notePersisted,
    renameActiveSession,
    removeSession,
  } = useSessions(userId);

  const [loading, setLoading] = useState(false);
  const [muted, setMuted] = useState(false);
  const [timings, setTimings] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [handsFree, setHandsFree] = useState(false);
  // A timer created at speech end, so a spoken turn can measure the
  // transcription tail. The turn in flight owns its own copy: marks are
  // write-once, so a timer shared between overlapping turns reports the first
  // turn's numbers for both.
  const timerRef = useRef(null);
  // Aborts the stream in flight when the user leaves the conversation it
  // belongs to, so the backend stops generating tokens nobody will read.
  const abortRef = useRef(null);
  const publishTimeoutRef = useRef(null);
  // Read inside a running turn, which captured its props one render ago:
  // muting mid-reply has to stop the reply, not the next one.
  const mutedRef = useRef(muted);
  const loadingRef = useRef(false);

  useEffect(() => {
    mutedRef.current = muted;
  }, [muted]);

  const abortInFlight = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  useEffect(
    () => () => {
      abortRef.current?.abort();
      if (publishTimeoutRef.current) window.clearTimeout(publishTimeoutRef.current);
    },
    []
  );

  const {
    speakChunk,
    beginTurn,
    warm,
    cancel: cancelSpeech,
    speaking,
    supported: ttsSupported,
  } = useSpeechSynthesis();

  useEffect(() => {
    warm();
    const onFirstGesture = () => warm();
    window.addEventListener('pointerdown', onFirstGesture, { once: true });
    window.addEventListener('keydown', onFirstGesture, { once: true });
    return () => {
      window.removeEventListener('pointerdown', onFirstGesture);
      window.removeEventListener('keydown', onFirstGesture);
    };
  }, [warm]);

  const runSend = useCallback(
    async (sessionId, userMessageId, text) => {
      if (loadingRef.current) return;
      loadingRef.current = true;
      setLoading(true);

      // Taken, not shared: the next turn must not inherit this turn's marks.
      const timer = timerRef.current ?? createTurnTimer();
      timerRef.current = null;
      timer.mark('requestSent');
      beginTurn();

      const controller = new AbortController();
      abortRef.current = controller;
      // The turn writes into the session it was sent from, whatever the user
      // has clicked on since.
      const update = (updater) => updateSessionMessages(sessionId, updater);

      const assistantId = crypto.randomUUID();
      let full = '';
      // Characters of the reply already handed to speech synthesis, counted
      // raw. Summing the trimmed sentences instead loses the separator
      // whitespace and the tail then re-speaks the end of the last sentence.
      let spokenChars = 0;
      let unspoken = '';
      let opened = false;

      // The turn is published once, at the later of the last token and the
      // first audio — either can come second. A short reply can finish
      // streaming before speech starts; a long one starts speaking mid-stream.
      let replyDone = false;
      let published = false;
      const publishOnce = () => {
        if (published) return;
        published = true;
        if (publishTimeoutRef.current) {
          window.clearTimeout(publishTimeoutRef.current);
          publishTimeoutRef.current = null;
        }
        setTimings(timer.publish());
      };
      const markAudio = () => {
        timer.mark('firstAudio');
        if (replyDone) publishOnce();
      };

      const showReply = (text_) => {
        if (!opened) {
          opened = true;
          update((prev) => [
            ...prev,
            {
              id: assistantId,
              role: 'assistant',
              text: text_,
              createdAt: new Date().toISOString(),
            },
          ]);
        } else {
          update((prev) => prev.map((m) => (m.id === assistantId ? { ...m, text: text_ } : m)));
        }
      };

      try {
        await sendMessageStream(userId, sessionId, text, {
          signal: controller.signal,
          onDelta: (delta) => {
            timer.mark('firstByte');
            full += delta;
            unspoken += delta;
            showReply(full);

            const [sentences, rest] = takeSentences(unspoken);
            spokenChars += unspoken.length - rest.length;
            unspoken = rest;
            if (!mutedRef.current && ttsSupported) {
              sentences.forEach((sentence) => speakChunk(sentence, { onStart: markAudio }));
            }
          },
          onDone: (event) => {
            timer.mark('replyComplete');
            timer.setServer(event.timings);
            const tail = event.reply.slice(spokenChars).trim();
            if (!mutedRef.current && ttsSupported && tail) {
              speakChunk(tail, { onStart: markAudio });
            }
            showReply(event.reply);
            replyDone = true;
            if (mutedRef.current || !ttsSupported) publishOnce();
            // Backstop: if synthesis never reports a start — blocked by
            // autoplay policy, or no voice available — the turn is still
            // published, with a null ttfa_ms rather than nothing at all.
            else {
              publishTimeoutRef.current = window.setTimeout(publishOnce, TTFA_PUBLISH_GRACE_MS);
            }
            notePersisted(sessionId);
          },
          onError: (error) => {
            throw error;
          },
        });
      } catch {
        // An abort is the user leaving this conversation, not a failure: the
        // backend persists whatever it streamed, so leave the partial reply
        // where it is rather than marking the turn failed.
        if (!controller.signal.aborted) {
          update((prev) =>
            prev
              .filter((m) => m.id !== assistantId)
              .map((m) => (m.id === userMessageId ? { ...m, status: 'error' } : m))
          );
        }
      } finally {
        if (abortRef.current === controller) abortRef.current = null;
        loadingRef.current = false;
        setLoading(false);
      }
    },
    [ttsSupported, speakChunk, beginTurn, updateSessionMessages, notePersisted]
  );

  const handleSend = useCallback(
    (text) => {
      const sessionId = activeId;
      const trimmed = text.trim();
      if (!sessionId || !trimmed || loadingRef.current) {
        // The timer was created for an utterance that is not becoming a turn;
        // leaving it would date the next turn from this abandoned one.
        timerRef.current = null;
        return;
      }
      const id = crypto.randomUUID();
      updateSessionMessages(sessionId, (prev) => [
        ...prev,
        { id, role: 'user', text: trimmed, createdAt: new Date().toISOString() },
      ]);
      cancelSpeech();
      runSend(sessionId, id, trimmed);
    },
    [activeId, cancelSpeech, updateSessionMessages, runSend]
  );

  const handleRetry = useCallback(
    (id) => {
      const sessionId = activeId;
      if (!sessionId || loadingRef.current) return;
      const message = messages.find((m) => m.id === id);
      if (!message) return;
      updateSessionMessages(sessionId, (prev) =>
        prev.map((m) => (m.id === id ? { ...m, status: undefined } : m))
      );
      cancelSpeech();
      runSend(sessionId, id, message.text);
    },
    [activeId, messages, cancelSpeech, updateSessionMessages, runSend]
  );

  const handleSpeechEnd = useCallback((at) => {
    const timer = createTurnTimer();
    timer.mark('speechEnd', at);
    timerRef.current = timer;
  }, []);

  // Barge-in: the moment the user starts speaking, Sarjy stops. Only armed in
  // hands-free mode — with a hot mic during playback, the microphone can hear
  // the speakers and interrupt Sarjy with her own voice.
  const handleSpeechStart = useCallback(() => {
    if (speaking) cancelSpeech();
  }, [speaking, cancelSpeech]);

  const {
    supported: micSupported,
    listening,
    start,
    cancel: cancelListening,
    lastError: micError,
  } = useSpeechRecognition(handleSend, {
    onSpeechEnd: handleSpeechEnd,
    onSpeechStart: handleSpeechStart,
  });

  // Hands-free keeps the microphone open between turns, which is what makes
  // barge-in reachable without pressing anything.
  useEffect(() => {
    if (!handsFree || !micSupported || listening || loading) return;
    // Re-arming into a denied permission or a missing device is an unthrottled
    // loop that pegs the main thread, so a fatal error ends hands-free rather
    // than being retried; anything transient waits first.
    if (micError && FATAL_MIC_ERRORS.has(micError)) {
      setHandsFree(false);
      return;
    }
    if (!micError) {
      start();
      return;
    }
    const retry = window.setTimeout(start, MIC_RETRY_MS);
    return () => window.clearTimeout(retry);
  }, [handsFree, micSupported, listening, loading, micError, start]);

  const micState = listening ? 'listening' : loading ? 'processing' : 'idle';

  // Tapping the microphone off discards the utterance. `stop()` sends it, which
  // is the wrong answer when the user is aborting something they misspoke.
  const handleMicToggle = () => {
    if (listening) cancelListening();
    else start();
  };

  const handleMuteToggle = () => {
    setMuted((prev) => {
      if (!prev) cancelSpeech();
      return !prev;
    });
  };

  // Leaving a conversation abandons the turn in flight. `cancelListening`
  // rather than `stop`, because `stop` would deliver the pending transcript --
  // asynchronously, and therefore into whichever session is open by then.
  const leaveConversation = () => {
    cancelSpeech();
    if (listening) cancelListening();
    abortInFlight();
  };

  const handleSelectSession = (id) => {
    setSidebarOpen(false);
    if (id === activeId) return;
    leaveConversation();
    selectSession(id);
  };

  const handleNewSession = () => {
    setSidebarOpen(false);
    leaveConversation();
    newSession();
  };

  const handleDeleteSession = (id) => {
    if (id === activeId) leaveConversation();
    removeSession(id);
  };

  useEffect(() => {
    if (!sidebarOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') setSidebarOpen(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [sidebarOpen]);

  return (
    <div className="layout">
      <SessionList
        sessions={sessions}
        activeId={activeId}
        loading={loadingSessions}
        open={sidebarOpen}
        onSelect={handleSelectSession}
        onNew={handleNewSession}
        onRename={renameActiveSession}
        onDelete={handleDeleteSession}
      />
      <div
        className={`sidebar-scrim ${sidebarOpen ? 'open' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      <div className="app">
        <header className="app-header">
          <button
            className="icon-btn sidebar-toggle"
            onClick={() => setSidebarOpen((prev) => !prev)}
            title="Toggle chat list"
            aria-label="Toggle chat list"
          >
            <HamburgerIcon />
          </button>
          <h2 className="session-title">{activeSession?.title ?? 'Sarjy'}</h2>
          <div className="header-right">
            {!micSupported && (
              <span className="hint">Voice input isn't supported in this browser.</span>
            )}
            <span className={`status-badge status-${micState}`}>
              <span className="status-dot" />
              {micState}
            </span>
          </div>
        </header>

        {loadingMessages ? (
          <div className="chat-placeholder">Loading conversation…</div>
        ) : (
          <ChatWindow messages={messages} loading={loading} onRetry={handleRetry} />
        )}

        <TurnTimings timings={timings} />

        <MessageInput
          onSend={handleSend}
          disabled={loading || !activeId}
          micSupported={micSupported}
          micState={micState}
          onMicToggle={handleMicToggle}
          handsFree={handsFree}
          onHandsFreeToggle={() => setHandsFree((prev) => !prev)}
          muted={muted}
          onMuteToggle={handleMuteToggle}
        />
      </div>
    </div>
  );
}
