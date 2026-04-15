import { useState } from "react";

function Chat() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!query.trim()) return;

    const userMessage = query;

    // 先更新 user message
    setMessages((prev) => [
      ...prev,
      { role: "user", text: userMessage }
    ]);

    setQuery("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ query: userMessage })
      });

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.answer || "No response" }
      ]);

    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Error: API failed" }
      ]);
    }

    setLoading(false);
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Chat</h2>

      <div style={{ marginBottom: 20 }}>
        {messages.map((m, i) => (
          <div key={i}>
            <b>{m.role}:</b> {m.text}
          </div>
        ))}

        {loading && <div>Thinking...</div>}
      </div>

      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        style={{ marginRight: 10, fontSize: "20px", padding: "10px 20px" }}
      />

      <button onClick={sendMessage} disabled={loading}
        style={{ fontSize: "20px", padding: "10px 20px" }}
      >
        Send
      </button>
    </div>
  );
}

export default Chat;