import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';

export default function ChatWindow({ messages, loading, onRetry }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div className="chat-window">
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
