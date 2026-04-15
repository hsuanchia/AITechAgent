import { useState } from "react";

function Search() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (inputQuery) => {
    const q = inputQuery ?? query;

    if (!q.trim()) return;

    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ query : q })
      });

      const data = await res.json();

      setResults([]); // 🔥 先清掉
      setTimeout(() => {
        setResults(data.results || []);
        setLoading(false);
      }, 0);

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
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            handleSearch(e.target.value);
          }
        }}
        style={{ marginRight: 10, fontSize: "20px", padding: "10px 20px" }}
      />

      <button onClick={() => handleSearch(query)} disabled={loading}
        style={{ fontSize: "20px", padding: "10px 20px" }}
      >
        {loading ? "Searching..." : "Search"}
      </button>

      <hr />

      {loading && <p>Loading...</p>}

      <ul>
        {results.map((r, i) => (
          <li key={r.id || r.title || i} style={{ marginBottom: 20 }}>
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