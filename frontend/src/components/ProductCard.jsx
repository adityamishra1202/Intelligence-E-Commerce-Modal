import { useState } from "react";

function safeHttpUrl(value) {
  if (typeof value !== "string" || !value) return "";
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:" ? url.href : "";
  } catch {
    return "";
  }
}

export default function ProductCard({ product, unmet }) {
  const [imageFailed, setImageFailed] = useState(false);
  const image = safeHttpUrl(product.image_url);
  const link = safeHttpUrl(product.product_url);

  return (
    <article className="card">
      <div className="card-image">
        {image && !imageFailed ? (
          <img src={image} alt="" loading="lazy" onError={() => setImageFailed(true)} />
        ) : (
          <div className="placeholder" aria-hidden="true">
            No image
          </div>
        )}
      </div>
      <div className="card-body">
        <div className="badges">
          <span className="badge site">{product.website_name}</span>
          <span className={`badge ${product.is_available ? "ok" : "muted"}`}>
            {product.is_available ? "In stock" : "Out of stock"}
          </span>
        </div>
        <h3 className="card-title">{product.title}</h3>
        {product.brand && <p className="card-brand">{product.brand}</p>}
        <p className="card-price">
          {product.price} {product.currency}
          {product.original_price && product.original_price !== product.price && (
            <span className="original-price">
              {" "}
              <s>
                {product.original_price} {product.currency}
              </s>
            </span>
          )}
        </p>
        {product.rating !== null && product.rating !== undefined && (
          <p className="card-rating">
            Rating {product.rating}
            {product.review_count !== null && product.review_count !== undefined && ` · ${product.review_count.toLocaleString()} reviews`}
          </p>
        )}
        {unmet?.length > 0 && (
          <ul className="unmet">
            {unmet.map((u) => (
              <li key={u}>{u}</li>
            ))}
          </ul>
        )}
        {link && (
          <a className="card-link" href={link} target="_blank" rel="noopener noreferrer">
            View on {product.website_name}
          </a>
        )}
      </div>
    </article>
  );
}
