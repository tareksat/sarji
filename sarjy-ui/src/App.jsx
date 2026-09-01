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
const SENTENCE_END = /([.!?…]+["')\]]*)(\s+)/;

// How long to wait for speech to start before publishing the turn without a
// time-to-first-audio.
const TTFA_PUBLISH_GRACE_MS = 2000;

function takeSentences(buffer) {
  const sentences = [];
  let rest = buffer;
  for (;;) {
    const match = SENTENCE_END.exec(rest);
    if (!match) break;
    const cut = match.index + match[1].length + match[2].length;
    sentences.push(rest.slice(0, cut).trim());
    rest = rest.slice(cut);
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
    updateActiveMessages,
    notePersisted,
    renameActiveSession,
    removeSession,
  } = useSessions(userId);

  const [loading, setLoading] = useState(false);
  const [muted, setMuted] = useState(false);
  const [timings, setTimings] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [handsFree, setHandsFree] = useState(false);
  // The timer for the turn currently in flight. Created at speech end for a
  // spoken turn, so it can measure the transcription tail.
  const timerRef = useRef(null);

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
    async (userMessageId, text) => {
      setLoading(true);
      const timer = timerRef.current ?? createTurnTimer();
      timerRef.current = timer;
      timer.mark('requestSent');
      beginTurn();

      const assistantId = crypto.randomUUID();
      let full = '';
      let spoken = '';
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
        setTimings(timer.publish());
      };
      const markAudio = () => {
        timer.mark('firstAudio');
        if (replyDone) publishOnce();
      };

      try {
        await sendMessageStream(userId, activeId, text, {
          onDelta: (delta) => {
            timer.mark('firstByte');
            full += delta;
            unspoken += delta;

            if (!opened) {
              opened = true;
              updateActiveMessages((prev) => [
                ...prev,
                {
                  id: assistantId,
                  role: 'assistant',
                  text: full,
                  createdAt: new Date().toISOString(),
                },
              ]);
            } else {
              updateActiveMessages((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, text: full } : m))
              );
            }

            const [sentences, rest] = takeSentences(unspoken);
            unspoken = rest;
            if (!muted && ttsSupported) {
              sentences.forEach((sentence) => {
                spoken += sentence;
                speakChunk(sentence, { onStart: markAudio });
              });
            }
          },
          onDone: (event) => {
            timer.mark('replyComplete');
            timer.setServer(event.timings);
            const tail = event.reply.slice(spoken.length).trim();
            if (!muted && ttsSupported && tail) speakChunk(tail, { onStart: markAudio });
            updateActiveMessages((prev) =>
              prev.map((m) => (m.id === assistantId ? { ...m, text: event.reply } : m))
            );
            replyDone = true;
            if (muted || !ttsSupported) publishOnce();
            // Backstop: if synthesis never reports a start — blocked by
            // autoplay policy, or no voice available — the turn is still
            // published, with a null ttfa_ms rather than nothing at all.
            else window.setTimeout(publishOnce, TTFA_PUBLISH_GRACE_MS);
            notePersisted();
          },
          onError: (error) => {
            throw error;
          },
        });
      } catch {
        updateActiveMessages((prev) =>
          prev
            .filter((m) => m.id !== assistantId)
            .map((m) => (m.id === userMessageId ? { ...m, status: 'error' } : m))
        );
      } finally {
        setLoading(false);
        // Marks are write-once, so a timer carried into the next turn would
        // report this turn's numbers forever. A spoken turn creates its own at
        // speech end; a typed one creates it here on the next send.
        timerRef.current = null;
      }
    },
    [activeId, muted, ttsSupported, speakChunk, beginTurn, updateActiveMessages, notePersisted]
  );

  const handleSend = useCallback(
    (text) => {
      if (!activeId) return;
      const id = crypto.randomUUID();
      updateActiveMessages((prev) => [
        ...prev,
        { id, role: 'user', text, createdAt: new Date().toISOString() },
      ]);
      cancelSpeech();
      runSend(id, text);
    },
    [activeId, cancelSpeech, updateActiveMessages, runSend]
  );

  const handleRetry = useCallback(
    (id) => {
      const message = messages.find((m) => m.id === id);
      if (!message) return;
      updateActiveMessages((prev) =>
        prev.map((m) => (m.id === id ? { ...m, status: undefined } : m))
      );
      cancelSpeech();
      runSend(id, message.text);
    },
    [messages, cancelSpeech, updateActiveMessages, runSend]
  );

  const handleSpeechEnd = useCallback(() => {
    const timer = createTurnTimer();
    timer.mark('speechEnd');
    timerRef.current = timer;
  }, []);

  // Barge-in: the moment the user starts speaking, Sarjy stops. Only armed in
  // hands-free mode — with a hot mic during playback, the microphone can hear
  // the speakers and interrupt Sarjy with her own voice.
  const handleSpeechStart = useCallback(() => {
    if (speaking) cancelSpeech();
  }, [speaking, cancelSpeech]);

  const { supported: micSupported, listening, start, stop } = useSpeechRecognition(handleSend, {
    onSpeechEnd: handleSpeechEnd,
    onSpeechStart: handleSpeechStart,
  });

  // Hands-free keeps the microphone open between turns, which is what makes
  // barge-in reachable without pressing anything.
  useEffect(() => {
    if (!handsFree || !micSupported || listening || loading) return;
    start();
  }, [handsFree, micSupported, listening, loading, start]);

  const micState = listening ? 'listening' : loading ? 'processing' : 'idle';

  const handleMicToggle = () => {
    if (listening) stop();
    else start();
  };

  const handleMuteToggle = () => {
    setMuted((prev) => {
      if (!prev) cancelSpeech();
      return !prev;
    });
  };

  const stopVoice = () => {
    cancelSpeech();
    if (listening) stop();
  };

  const handleSelectSession = (id) => {
    setSidebarOpen(false);
    if (id === activeId) return;
    stopVoice();
    selectSession(id);
  };

  const handleNewSession = () => {
    setSidebarOpen(false);
    stopVoice();
    newSession();
  };

  const handleDeleteSession = (id) => {
    if (id === activeId) stopVoice();
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
