const USER_ID_KEY = 'sarjy_user_id';

// Reading `localStorage` throws outright under Safari private browsing, a
// blocked-cookies policy, or a third-party frame. `getUserId` runs at module
// scope, outside any error boundary, so an unguarded throw here is a white
// screen rather than a degraded session.
export function readStored(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function writeStored(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Non-fatal: the value simply does not survive a reload.
  }
}

export function getUserId() {
  let id = readStored(USER_ID_KEY);
  if (!id) {
    id = crypto.randomUUID();
    writeStored(USER_ID_KEY, id);
  }
  return id;
}

async function request(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  if (res.status === 204) return null;
  return res.json();
}

// No caller in the UI, which always streams. Kept because it is the client for
// the non-streaming route that the latency study's "before" column measures --
// `sarjy-backend/scripts/measure.py` exercises the same endpoint -- and because
// deleting it would leave that endpoint with no reference implementation here.
export async function sendMessage(userId, sessionId, message) {
  return request('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, session_id: sessionId, message }),
  }); // { reply: string, timings: object | null }
}

export class StreamTruncatedError extends Error {
  constructor() {
    super('The connection closed before Sarjy finished replying.');
    this.name = 'StreamTruncatedError';
  }
}

// One SSE frame to its payload, or null if the frame carries none. Fields other
// than `data:` -- comments, `event:`, `id:`, `retry:` -- are skipped rather than
// treated as a payload, and a `data:` value may span several lines. A frame that
// does not parse is dropped: one bad frame should not end the stream.
function parseFrame(frame) {
  const data = [];
  for (const raw of frame.split('\n')) {
    const line = raw.replace(/\r$/, '');
    if (line === '' || line.startsWith(':')) continue;
    const colon = line.indexOf(':');
    const field = colon === -1 ? line : line.slice(0, colon);
    if (field !== 'data') continue;
    const value = colon === -1 ? '' : line.slice(colon + 1);
    data.push(value.startsWith(' ') ? value.slice(1) : value);
  }
  if (data.length === 0) return null;
  try {
    return JSON.parse(data.join('\n'));
  } catch {
    return null;
  }
}

// SSE over POST, so `fetch` rather than `EventSource` (which is GET-only).
export async function sendMessageStream(userId, sessionId, message, handlers = {}) {
  const { onDelta, onDone, onError, signal } = handlers;
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, session_id: sessionId, message }),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(`Request failed: ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  // Whether a terminal frame arrived. Without this a stream cut short -- a
  // backend crash, a proxy read timeout, a sleeping laptop -- resolves as a
  // success and the half-written reply is presented as the whole answer.
  let terminated = false;

  const drain = () => {
    // Frames are separated by a blank line; a partial frame stays in `buffer`.
    let split;
    while ((split = buffer.indexOf('\n\n')) !== -1) {
      const frame = buffer.slice(0, split);
      buffer = buffer.slice(split + 2);
      const event = parseFrame(frame);
      if (!event) continue;
      if (event.type === 'delta') onDelta?.(event.text);
      else if (event.type === 'done') {
        terminated = true;
        onDone?.(event);
      } else if (event.type === 'error') {
        terminated = true;
        onError?.(new Error(event.detail));
      }
    }
  };

  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      drain();
    }
    // Flush any partial multi-byte sequence, then drain what is left in case
    // the last frame arrived without its trailing blank line.
    buffer += decoder.decode();
    if (buffer && !buffer.endsWith('\n\n')) buffer += '\n\n';
    drain();
    if (!terminated) throw new StreamTruncatedError();
  } finally {
    // Releases the socket. Without it the error-frame path and every aborted
    // send leave the backend generating tokens nobody will read.
    try {
      await reader.cancel();
    } catch {
      // Already closed or aborted.
    }
  }
}

export async function fetchSessions(userId) {
  const rows = await request(`/api/sessions?user_id=${encodeURIComponent(userId)}`);
  return rows.map((s) => ({
    id: s.id,
    title: s.title,
    createdAt: s.created_at,
    updatedAt: s.updated_at,
    pending: false,
  }));
}

export async function fetchMessages(userId, sessionId) {
  const rows = await request(
    `/api/sessions/${sessionId}/messages?user_id=${encodeURIComponent(userId)}`
  );
  // The UI renders `text`; the API returns `content`. Map here so ChatWindow
  // stays unaware of the wire shape.
  return rows.map((m) => ({ id: m.id, role: m.role, text: m.content, createdAt: m.created_at }));
}

export async function renameSession(userId, sessionId, title) {
  return request(`/api/sessions/${sessionId}?user_id=${encodeURIComponent(userId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
}

export async function deleteSession(userId, sessionId) {
  return request(`/api/sessions/${sessionId}?user_id=${encodeURIComponent(userId)}`, {
    method: 'DELETE',
  });
}
