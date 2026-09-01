const USER_ID_KEY = 'sarjy_user_id';

export function getUserId() {
  let id = localStorage.getItem(USER_ID_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(USER_ID_KEY, id);
  }
  return id;
}

async function request(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  if (res.status === 204) return null;
  return res.json();
}

export async function sendMessage(userId, sessionId, message) {
  return request('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, session_id: sessionId, message }),
  }); // { reply: string, timings: object | null }
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
