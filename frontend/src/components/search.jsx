import { useState } from "react";

function Search() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ query })
      });

      const data = await res.json();

      setResults(data.results || []);

    } catch (err) {
      console.error(err);
      setResults([]);
    }

    setLoading(false);
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Search Papers</h2>

      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search..."
        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        style={{ marginRight: 10 }}
      />

      <button onClick={handleSearch} disabled={loading}>
        {loading ? "Searching..." : "Search"}
      </button>

      <hr />

      {loading && <p>Loading...</p>}

      <ul>
        {results.map((r, i) => (
          <li key={i} style={{ marginBottom: 20 }}>
            <h3>{r.title}</h3>
            <p>{r.abstract}</p>

            {r.url && (
              <a href={r.url} target="_blank" rel="noreferrer">
                Link
              </a>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
export default Search;