// App.js
import React, { useState } from "react";
import "./App.css";
import { sendMessageToBackend } from "./api";

function App() {
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Hi! I'm your Lecture Assistant Chatbot. Ask me anything from your lectures.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };

    // Build what the conversation will look like AFTER this message
    const allMessages = [...messages, userMessage];

    // Take the last N messages as "history"
    const N_HISTORY = 6; // you can tweak this (4–8 is typical)
    const recentMessages = allMessages.slice(-N_HISTORY);

    // Convert to { role, text } format for the backend
    const history = recentMessages.map((msg) => ({
      role: msg.sender === "user" ? "user" : "assistant",
      text: msg.text,
    }));

    // Update UI immediately with user message
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      // Call your FastAPI backend, sending both query and history
      const botReply = await sendMessageToBackend(input, history);

      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: botReply || "Sorry, I couldn't generate a response." },
      ]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Oops, something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="chat-window">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.sender}`}>
            <p>{msg.text}</p>
          </div>
        ))}
        {loading && (
          <div className="message bot">
            <p>Thinking...</p>
          </div>
        )}
      </div>

      <div className="input-area">
        <input
          type="text"
          placeholder="Ask a question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !loading && handleSend()}
        />
        <button onClick={handleSend} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}

export default App;
