import { useState } from "react";
import Chat from "./components/chat";
import Search from "./components/search";

function App() {
  const [mode, setMode] = useState("chat");

  return (
    <div>
      <h1>AI Tech Assistant</h1>

      <button onClick={() => setMode("chat")}
        style={{ fontSize: "20px", padding: "10px 20px" }}>
        Chat
      </button>
      <button onClick={() => setMode("search")}
        style={{ fontSize: "20px", padding: "10px 20px" }}>
        Search
      </button>

      {mode === "chat" ? <Chat /> : <Search />}
    </div>
  );
}

export default App;