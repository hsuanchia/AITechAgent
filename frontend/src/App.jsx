import { useState } from "react";
import Chat from "./components/chat";
import Search from "./components/search";

function App() {
  const [mode, setMode] = useState("chat");

  return (
    <div>
      <h1>AI Tech Assistant</h1>

      <button onClick={() => setMode("chat")}>Chat</button>
      <button onClick={() => setMode("search")}>Search</button>

      {mode === "chat" ? <Chat /> : <Search />}
    </div>
  );
}

export default App;