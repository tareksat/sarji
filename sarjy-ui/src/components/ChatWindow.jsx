import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';

// How far from the bottom still counts as "following along". Past this, the
// user has scrolled back to read something and must not be yanked forward.
const FOLLOW_THRESHOLD_PX = 120;

export default function ChatWindow({ messages, loading, onRetry }) {
  const bottomRef = useRef(null);
  const windowRef = useRef(null);

  useEffect(() => {
    const el = windowRef.current;
    if (!el) return;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    if (distance > FOLLOW_THRESHOLD_PX) return;
    // `auto`, not `smooth`: `messages` changes identity once per token, and a
    // smooth animation queued per token never catches up with the stream.
    bottomRef.current?.scrollIntoView({ behavior: loading ? 'auto' : 'smooth' });
  }, [messages, loading]);

  return (
    <div className="chat-window" ref={windowRef}>
      {messages.map((m) => (
        <MessageBubble key={m.id} {...m} onRetry={onRetry} />
      ))}
      {loading && (
        <div className="bubble-row assistant">
          <div className="bubble assistant typing-indicator">
            <span></span>
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
