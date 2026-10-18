import { useCallback, useEffect, useState } from "react";
import { getConversation, getConversations, getWebsites, sendChat } from "./api.js";
import WebsiteSelector from "./components/WebsiteSelector.jsx";
import ConversationSidebar from "./components/ConversationSidebar.jsx";
import ChatWindow from "./components/ChatWindow.jsx";
import Composer from "./components/Composer.jsx";

// Only the fields the UI shows are kept from a chat response; `requirements`
// and anything else internal are dropped here and never reach a component.
function assistantMessage(data) {
  return {
    role: "assistant",
    content: data.answer || "",
    products: Array.isArray(data.products) ? data.products : [],
    alternatives: Array.isArray(data.alternatives) ? data.alternatives : [],
    comparison: data.comparison || null,
    notices: Array.isArray(data.notices) ? data.notices : [],
  };
}

export default function App() {
  const [websites, setWebsites] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const scopeLocked = conversationId !== null || messages.length > 0;

  const refreshConversations = useCallback(async () => {
    try {
      setConversations(await getConversations());
    } catch {
      // The list is a convenience; the chat keeps working without it.
    }
  }, []);

  useEffect(() => {
    getWebsites()
      .then((list) => {
        setWebsites(list);
        if (list.length === 1) setSelectedIds([list[0].id]);
      })
      .catch((err) => setError(err.message));
    refreshConversations();
  }, [refreshConversations]);

  function startNewConversation() {
    setConversationId(null);
    setMessages([]);
    setError("");
    setSidebarOpen(false);
  }

  async function openConversation(id) {
    setError("");
    setLoading(true);
    setSidebarOpen(false);
    try {
      const data = await getConversation(id);
      setConversationId(data.id);
      setSelectedIds(data.website_scope);
      setMessages(data.messages.map((m) => ({ role: m.role, content: m.content })));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function send(text) {
    if (!selectedIds.length) {
      setError("Select at least one website first.");
      return false;
    }
    setError("");
    setLoading(true);
    setMessages((current) => [...current, { role: "user", content: text }]);
    try {
      const data = await sendChat({ message: text, websiteIds: selectedIds, conversationId });
      setConversationId(data.conversation_id);
      setMessages((current) => [...current, assistantMessage(data)]);
      refreshConversations();
      return true;
    } catch (err) {
      setMessages((current) => current.slice(0, -1));
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  }

  const unavailableScope = scopeLocked && selectedIds.some((id) => !websites.some((w) => w.id === id));

  return (
    <div className="app">
      <header className="topbar">
        <button
          type="button"
          className="menu-button"
          aria-expanded={sidebarOpen}
          aria-controls="sidebar"
          onClick={() => setSidebarOpen((open) => !open)}
        >
          Menu
        </button>
        <h1 className="brand">EcommerceAI</h1>
        <span className="tagline">Shopping assistant</span>
      </header>

      <div className="layout">
        <aside id="sidebar" className={`sidebar${sidebarOpen ? " open" : ""}`}>
          <ConversationSidebar
            conversations={conversations}
            activeId={conversationId}
            onNew={startNewConversation}
            onOpen={openConversation}
          />
          <WebsiteSelector
            websites={websites}
            selectedIds={selectedIds}
            onChange={setSelectedIds}
            locked={scopeLocked}
          />
        </aside>

        <main className="main">
          {unavailableScope && (
            <p className="banner warning">
              A website in this conversation is no longer available. Start a new conversation to keep shopping.
            </p>
          )}
          {error && (
            <div className="banner error" role="alert">
              {error}
            </div>
          )}
          <ChatWindow messages={messages} loading={loading} />
          <Composer onSend={send} disabled={loading || unavailableScope} />
        </main>
      </div>
    </div>
  );
}
