// Renders the small subset of Markdown the assistant uses: paragraphs,
// "- " list lines and **bold**. http(s) URLs become links. Everything is built
// from React elements, so model text can never inject HTML.

const URL_PATTERN = /(https?:\/\/[^\s<>"')\]]+)/g;

function linkify(text, keyPrefix) {
  return text.split(URL_PATTERN).map((part, i) => {
    if (i % 2 === 1) {
      const href = part.replace(/[.,;:!?]+$/, "");
      const tail = part.slice(href.length);
      return (
        <span key={`${keyPrefix}-u${i}`}>
          <a href={href} target="_blank" rel="noopener noreferrer">
            {href}
          </a>
          {tail}
        </span>
      );
    }
    return part;
  });
}

function inline(text, keyPrefix) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) => {
    const key = `${keyPrefix}-${i}`;
    if (part.length > 4 && part.startsWith("**") && part.endsWith("**")) {
      return <strong key={key}>{linkify(part.slice(2, -2), key)}</strong>;
    }
    return <span key={key}>{linkify(part, key)}</span>;
  });
}

export default function SimpleMarkdown({ text }) {
  const blocks = [];
  let paragraph = [];
  let list = [];

  const flushParagraph = () => {
    if (paragraph.length) blocks.push({ type: "p", lines: paragraph });
    paragraph = [];
  };
  const flushList = () => {
    if (list.length) blocks.push({ type: "ul", lines: list });
    list = [];
  };

  for (const raw of String(text || "").split(/\r?\n/)) {
    const line = raw.trimEnd();
    const item = line.match(/^\s*[-*]\s+(.*)$/);
    if (item) {
      flushParagraph();
      list.push(item[1]);
    } else if (!line.trim()) {
      flushParagraph();
      flushList();
    } else {
      flushList();
      paragraph.push(line.replace(/^#{1,6}\s+/, ""));
    }
  }
  flushParagraph();
  flushList();

  return (
    <div className="markdown">
      {blocks.map((block, b) =>
        block.type === "ul" ? (
          <ul key={b}>
            {block.lines.map((l, i) => (
              <li key={i}>{inline(l, `${b}-${i}`)}</li>
            ))}
          </ul>
        ) : (
          <p key={b}>
            {block.lines.map((l, i) => (
              <span key={i}>
                {i > 0 && <br />}
                {inline(l, `${b}-${i}`)}
              </span>
            ))}
          </p>
        )
      )}
    </div>
  );
}
