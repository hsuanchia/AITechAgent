import { useState, useRef, useEffect } from "react";

function Thinking() {
  const [dots, setDots] = useState("");

  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 500);

    return () => clearInterval(interval);
  }, []);

  return <span>Thinking{dots}</span>;
}

function Chat() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);

  const bottomRef = useRef(null);

  // 自動 scroll 到最底
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async () => {
  if (!query.trim()) return;

  const userMessage = query;

  setMessages((prev) => [
    ...prev,
    { role: "user", text: userMessage },
    { role: "assistant", text: "" } // 先放一個空的
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

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");

    let done = false;
    let fullText = "";

    while (!done) {
      const { value, done: doneReading } = await reader.read();
      done = doneReading;

      const chunk = decoder.decode(value);
      fullText += chunk;

      // 🔥 第一次收到資料 → 關掉 Thinking
      if (!streaming) {
        setStreaming(true);
        setLoading(false);
      }

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          text: fullText
        };
        return updated;
      });
    }

  } catch (err) {
    setMessages((prev) => [
      ...prev,
      { role: "assistant", text: "Error: API failed" }
    ]);
  }

  setStreaming(false);
  setLoading(false);
};

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>AI Chat</h2>

      {/* Chat 區域 */}
      <div style={styles.chatBox}>
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              ...styles.message,
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              background: m.role === "user" ? "#4CAF50" : "#333",
              color: "white"
            }}
          >
            {m.text}
          </div>
        ))}

        {loading && (
          <div style={{ ...styles.message, background: "#555" }}>
            <Thinking />
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input 區 */}
      <div style={styles.inputArea}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          style={styles.input}
          placeholder="Ask something..."
        />

        <button
          onClick={sendMessage}
          disabled={loading}
          style={styles.button}
        >
          Send
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    maxWidth: "1600px",
    margin: "0 auto",
    padding: "20px",
    fontFamily: "Arial"
  },
  title: {
    textAlign: "center"
  },
  chatBox: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    height: "600px",
    overflowY: "auto",
    border: "1px solid #ccc",
    padding: "10px",
    marginBottom: "10px",
    background: "#111"
  },
  message: {
    padding: "10px 15px",
    borderRadius: "10px",
    maxWidth: "70%"
  },
  inputArea: {
    display: "flex",
    gap: "10px"
  },
  input: {
    flex: 1,
    padding: "10px",
    fontSize: "16px"
  },
  button: {
    padding: "10px 20px",
    fontSize: "16px",
    cursor: "pointer"
  }
};

export default Chat;