// All calls go to the same origin; in development Vite proxies /api to Django.

const FRIENDLY = {
  invalid_request: "That message could not be sent. Please check it and try again.",
  website_unavailable: "One of the selected websites is no longer available. Start a new conversation.",
  conversation_not_found: "This conversation is not available any more. Start a new conversation.",
  rate_limited: "You are sending messages too quickly. Please wait a moment and try again.",
  model_unavailable: "The assistant's language model is not reachable right now. Please try again shortly.",
  internal_error: "Something went wrong on the server. Please try again.",
  network: "Cannot reach the server. Check that the backend is running.",
};

export class ApiError extends Error {
  constructor(code, status) {
    super(FRIENDLY[code] || FRIENDLY.internal_error);
    this.code = code;
    this.status = status;
  }
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      credentials: "same-origin",
      headers: { Accept: "application/json", ...(options.body ? { "Content-Type": "application/json" } : {}) },
      ...options,
    });
  } catch {
    throw new ApiError("network", 0);
  }
  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }
  if (!response.ok) {
    const code = data && typeof data.code === "string" ? data.code : response.status === 404 ? "conversation_not_found" : "internal_error";
    throw new ApiError(code, response.status);
  }
  return data;
}

export function getWebsites() {
  return request("/api/websites/");
}

export function getConversations() {
  return request("/api/conversations/");
}

export function getConversation(id) {
  return request(`/api/conversations/${encodeURIComponent(id)}/`);
}

export function sendChat({ message, websiteIds, conversationId }) {
  const body = { message, website_ids: websiteIds };
  if (conversationId) body.conversation_id = conversationId;
  return request("/api/chat/", { method: "POST", body: JSON.stringify(body) });
}
