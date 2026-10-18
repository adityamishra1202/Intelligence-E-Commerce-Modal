export default function WebsiteSelector({ websites, selectedIds, onChange, locked }) {
  function toggle(id) {
    onChange(selectedIds.includes(id) ? selectedIds.filter((x) => x !== id) : [...selectedIds, id].sort((a, b) => a - b));
  }

  return (
    <fieldset className="panel websites" disabled={locked}>
      <legend>Websites to search</legend>
      {locked && <p className="hint">The websites are fixed for this conversation. Start a new conversation to change them.</p>}
      {websites.length === 0 && <p className="hint">No websites are available yet.</p>}
      <ul className="plain-list">
        {websites.map((site) => (
          <li key={site.id}>
            <label className="check">
              <input type="checkbox" checked={selectedIds.includes(site.id)} onChange={() => toggle(site.id)} />
              <span className="site-name">{site.name}</span>
              {site.stale && (
                <span className="badge muted" title={site.last_synced_at ? "Data may be out of date" : "Never synced"}>
                  {site.last_synced_at ? "Stale data" : "Not synced"}
                </span>
              )}
            </label>
          </li>
        ))}
      </ul>
    </fieldset>
  );
}
