import React, { useState } from "react";
import "./App.css";
import { sendMessageToBackend } from "./api";

function App() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hi! I'm your Lecture Assistant Chatbot. Ask me anything from your lectures." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    // Call your FastAPI backend
    const botReply = await sendMessageToBackend(input);

    setMessages((prev) => [...prev, { sender: "bot", text: botReply }]);
    setLoading(false);
  };

  return (
    <div className="app-container">
      <div className="chat-window">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.sender}`}>
            <p>{msg.text}</p>
          </div>
        ))}
        {loading && <div className="message bot"><p>Thinking...</p></div>}
      </div>

      <div className="input-area">
        <input
          type="text"
          placeholder="Ask a question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button onClick={handleSend} disabled={loading}>Send</button>
      </div>
    </div>
  );
}

export default App;
