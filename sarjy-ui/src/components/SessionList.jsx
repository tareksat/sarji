import { useEffect, useRef, useState } from 'react';
import { PencilIcon } from './icons';

function SessionRow({ session, active, onSelect, onRename, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(session.title);
  const [armed, setArmed] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    if (editing) inputRef.current?.select();
  }, [editing]);

  // Disarm the delete confirmation whenever the row stops being the focus.
  useEffect(() => {
    if (!armed) return;
    const timer = setTimeout(() => setArmed(false), 4000);
    return () => clearTimeout(timer);
  }, [armed]);

  const startEditing = () => {
    setDraft(session.title);
    setEditing(true);
  };

  const commit = () => {
    setEditing(false);
    if (draft.trim() && draft.trim() !== session.title) onRename(session.id, draft);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') commit();
    if (e.key === 'Escape') setEditing(false);
  };

  if (editing) {
    return (
      <div className={`session-row ${active ? 'active' : ''}`}>
        <input
          ref={inputRef}
          className="session-rename-input"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={handleKeyDown}
        />
      </div>
    );
  }

  return (
    <div className={`session-row ${active ? 'active' : ''}`}>
      <button
        className="session-item"
        onClick={() => onSelect(session.id)}
        onDoubleClick={startEditing}
        title={`${session.title} — double-click to rename`}
      >
        {session.title}
      </button>
      <div className="session-actions">
      <button
        className="session-rename"
        onClick={startEditing}
        title="Rename chat"
        aria-label="Rename chat"
      >
        <PencilIcon width={14} height={14} />
      </button>
      <button
        className={`session-delete ${armed ? 'armed' : ''}`}
        onClick={() => (armed ? onDelete(session.id) : setArmed(true))}
        title={armed ? 'Click again to delete' : 'Delete chat'}
        aria-label={armed ? 'Confirm delete' : 'Delete chat'}
      >
        {armed ? 'Sure?' : '\u00d7'}
      </button>
      </div>
    </div>
  );
}

export default function SessionList({
  sessions,
  activeId,
  loading,
  open,
  onSelect,
  onNew,
  onRename,
  onDelete,
}) {
  return (
    <div className={`session-list ${open ? 'open' : ''}`}>
      <div className="brand">
        <span className="brand-dot" />
        <span className="brand-name">Sarjy</span>
      </div>

      <button className="new-session-btn" onClick={onNew}>
        + New chat
      </button>

      <div className="session-items">
        {loading ? (
          <div className="session-placeholder">Loading chats…</div>
        ) : (
          sessions.map((s) => (
            <SessionRow
              key={s.id}
              session={s}
              active={s.id === activeId}
              onSelect={onSelect}
              onRename={onRename}
              onDelete={onDelete}
            />
          ))
        )}
      </div>
    </div>
  );
}
