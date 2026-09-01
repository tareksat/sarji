import CopyButton from './CopyButton';
import { RetryIcon } from './icons';

function formatTime(createdAt) {
  if (!createdAt) return null;
  const date = new Date(createdAt);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function MessageBubble({ id, role, text, createdAt, status, onRetry }) {
  const isError = status === 'error';
  const time = formatTime(createdAt);

  return (
    <div className={`bubble-row ${role}`}>
      <div className={`bubble ${role}${isError ? ' error' : ''}`}>{text}</div>
      <div className="bubble-meta">
        {time && (
          <time dateTime={createdAt} title={new Date(createdAt).toLocaleString()}>
            {time}
          </time>
        )}
        <CopyButton text={text} />
        {isError && (
          <button
            className="meta-btn retry-btn"
            onClick={() => onRetry(id)}
            title="Retry send"
            aria-label="Retry send"
          >
            <RetryIcon width={13} height={13} />
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
