import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble.jsx";

const EXAMPLES = ["Suggest headphones under $350", "Which laptop has the best rating?", "Is noise cancelling worth it for flights?"];

export default function ChatWindow({ messages, loading }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [messages, loading]);

  return (
    <section className="chat" aria-label="Chat">
      {messages.length === 0 && !loading && (
        <div className="empty">
          <h2>What are you shopping for?</h2>
          <p>Choose one or more websites (under Menu on small screens), then ask in your own words. For example:</p>
          <ul>
            {EXAMPLES.map((e) => (
              <li key={e}>{e}</li>
            ))}
          </ul>
        </div>
      )}
      <ol className="messages" aria-live="polite" aria-relevant="additions">
        {messages.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))}
      </ol>
      {loading && (
        <p className="loading" role="status">
          <span className="dot" aria-hidden="true" />
          <span className="dot" aria-hidden="true" />
          <span className="dot" aria-hidden="true" />
          <span className="visually-hidden">The assistant is searching</span>
        </p>
      )}
      <div ref={endRef} />
    </section>
  );
}
