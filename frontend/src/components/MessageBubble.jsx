import SimpleMarkdown from "./SimpleMarkdown.jsx";
import ProductCard from "./ProductCard.jsx";

function ComparisonTable({ comparison }) {
  const rows = comparison.products || [];
  if (rows.length < 2) return null;
  return (
    <div className="table-wrap">
      <table className="comparison">
        <caption>Comparison</caption>
        <thead>
          <tr>
            <th scope="col">Product</th>
            <th scope="col">Price</th>
            <th scope="col">Rating</th>
            <th scope="col">Reviews</th>
            <th scope="col">Stock</th>
            <th scope="col">Website</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <th scope="row">{row.title}</th>
              <td>
                {row.price} {row.currency}
              </td>
              <td>{row.rating ?? "–"}</td>
              <td>{row.review_count ?? "–"}</td>
              <td>{row.is_available ? "In stock" : "Out of stock"}</td>
              <td>{row.website_name}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";
  // Notices already written into the answer are not repeated underneath it.
  const notices = (message.notices || []).filter((n) => !message.content.includes(n));

  return (
    <li className={`message ${isUser ? "user" : "assistant"}`}>
      <span className="visually-hidden">{isUser ? "You said:" : "Assistant:"}</span>
      <div className="bubble">{isUser ? <p className="user-text">{message.content}</p> : <SimpleMarkdown text={message.content} />}</div>

      {notices.length > 0 && (
        <ul className="notices">
          {notices.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      )}

      {message.comparison && <ComparisonTable comparison={message.comparison} />}

      {message.products?.length > 0 && (
        <div className="cards" aria-label="Matching products">
          {message.products.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      )}

      {message.alternatives?.length > 0 && (
        <section className="alternatives" aria-label="Near matches">
          <h3>These do not fully match your request</h3>
          <div className="cards">
            {message.alternatives.map((p) => (
              <ProductCard key={p.id} product={p} unmet={p.unmet} />
            ))}
          </div>
        </section>
      )}
    </li>
  );
}
