import { useState } from "react";

const MAX_LENGTH = 2000;

export default function Composer({ onSend, disabled }) {
  const [text, setText] = useState("");

  async function submit() {
    const message = text.trim();
    if (!message || disabled) return;
    setText("");
    const sent = await onSend(message);
    if (!sent) setText(message); // keep the text so it can be sent again
  }

  function onKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <form
      className="composer"
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <label htmlFor="composer-input" className="visually-hidden">
        Message
      </label>
      <textarea
        id="composer-input"
        rows={2}
        maxLength={MAX_LENGTH}
        value={text}
        placeholder="Ask about products… (Enter to send, Shift+Enter for a new line)"
        onChange={(event) => setText(event.target.value)}
        onKeyDown={onKeyDown}
        disabled={disabled}
      />
      <div className="composer-actions">
        <span className="counter" aria-live="off">
          {text.length}/{MAX_LENGTH}
        </span>
        <button type="submit" className="primary" disabled={disabled || !text.trim()}>
          Send
        </button>
      </div>
    </form>
  );
}
