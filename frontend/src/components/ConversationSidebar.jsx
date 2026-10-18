function formatWhen(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function ConversationSidebar({ conversations, activeId, onNew, onOpen }) {
  return (
    <nav className="panel conversations" aria-label="Conversations">
      <button type="button" className="primary full" onClick={onNew}>
        New conversation
      </button>
      {conversations.length === 0 ? (
        <p className="hint">Your conversations will appear here.</p>
      ) : (
        <ul className="plain-list conversation-list">
          {conversations.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                className={`conversation${c.id === activeId ? " active" : ""}`}
                aria-current={c.id === activeId ? "true" : undefined}
                onClick={() => onOpen(c.id)}
              >
                <span className="conversation-title">{c.title}</span>
                <span className="conversation-date">{formatWhen(c.updated_at)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </nav>
  );
}
