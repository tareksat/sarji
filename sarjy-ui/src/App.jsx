import { useCallback, useEffect, useState } from 'react';
import ChatWindow from './components/ChatWindow';
import { HamburgerIcon } from './components/icons';
import MessageInput from './components/MessageInput';
import SessionList from './components/SessionList';
import { useSpeechRecognition } from './hooks/useSpeechRecognition';
import { useSpeechSynthesis } from './hooks/useSpeechSynthesis';
import { useSessions } from './hooks/useSessions';
import { getUserId, sendMessage } from './api';
import './App.css';

const userId = getUserId();

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
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const { speak, cancel: cancelSpeech, supported: ttsSupported } = useSpeechSynthesis();

  const runSend = useCallback(
    async (userMessageId, text) => {
      setLoading(true);
      try {
        const { reply } = await sendMessage(userId, activeId, text);
        updateActiveMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            text: reply,
            createdAt: new Date().toISOString(),
          },
        ]);
        notePersisted();
        if (!muted && ttsSupported) speak(reply);
      } catch {
        updateActiveMessages((prev) =>
          prev.map((m) => (m.id === userMessageId ? { ...m, status: 'error' } : m))
        );
      } finally {
        setLoading(false);
      }
    },
    [activeId, muted, ttsSupported, speak, updateActiveMessages, notePersisted]
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

  const { supported: micSupported, listening, start, stop } = useSpeechRecognition(handleSend);

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

        <MessageInput
          onSend={handleSend}
          disabled={loading || !activeId}
          micSupported={micSupported}
          micState={micState}
          onMicToggle={handleMicToggle}
          muted={muted}
          onMuteToggle={handleMuteToggle}
        />
      </div>
    </div>
  );
}
