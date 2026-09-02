import { useState } from 'react';
import { MicIcon, SendIcon, SpeakerOffIcon, SpeakerOnIcon } from './icons';

// Hands-free (the infinity toggle) keeps the microphone open between turns and
// arms barge-in. Turned off for now: flip this back to true to restore it —
// nothing else about the feature was removed, and with the toggle gone
// `handsFree` in App.jsx stays false, so the hot mic never opens.
const HANDS_FREE_ENABLED = false;

export default function MessageInput({
  onSend,
  disabled,
  micSupported,
  micState,
  onMicToggle,
  handsFree,
  onHandsFreeToggle,
  muted,
  onMuteToggle,
}) {
  const [text, setText] = useState('');

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="message-input">
      <button
        className="icon-btn mute-btn"
        onClick={onMuteToggle}
        title={muted ? 'Unmute assistant voice' : 'Mute assistant voice'}
      >
        {muted ? <SpeakerOffIcon /> : <SpeakerOnIcon />}
      </button>

      {micSupported && (
        <button
          className={`icon-btn mic-btn mic-${micState}`}
          onClick={onMicToggle}
          title="Toggle voice input"
        >
          <span className="mic-ring" />
          <MicIcon className="mic-icon" />
        </button>
      )}

      {micSupported && HANDS_FREE_ENABLED && (
        <button
          className={`icon-btn hands-free-btn ${handsFree ? 'active' : ''}`}
          onClick={onHandsFreeToggle}
          title={handsFree ? 'Hands-free on — speak any time to interrupt' : 'Hands-free off'}
          aria-pressed={handsFree}
        >
          ∞
        </button>
      )}

      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type a message..."
        disabled={disabled}
      />

      <button className="send-btn" onClick={handleSend} disabled={disabled || !text.trim()}>
        <SendIcon width={16} height={16} />
        Send
      </button>
    </div>
  );
}
