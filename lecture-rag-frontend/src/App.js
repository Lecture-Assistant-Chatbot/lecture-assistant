import React, { useState } from "react";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hi! I'm your Lecture Assistant Chatbot. Ask me anything from your lecture." }
  ]);
  const [input, setInput] = useState("");
  const [lastBotMessage, setLastBotMessage] = useState(null);
  const [showSimplify, setShowSimplify] = useState(false);

  const handleSend = () => {
    if (!input.trim()) return;

    const newMessage = { sender: "user", text: input };
    setMessages([...messages, newMessage]);
    setShowSimplify(false); // hide simplify when sending new question

    // For now, fake chatbot reply
    setTimeout(() => {
      const botReply = "Cloud computing is like renting a computer over the internet instead of owning one.";
      setMessages((prev) => [...prev, { sender: "bot", text: botReply }]);
      setLastBotMessage(botReply);
      setShowSimplify(true); // show simplify button after bot responds
    }, 800);

    setInput("");
  };

  const handleSimplify = () => {
    setShowSimplify(false);

    // Simulate a simpler explanation
    const simplified = "It means you use someone else's computer online to store files or run programs.";
    setMessages((prev) => [...prev, { sender: "bot", text: simplified }]);
  };

  return (
    <div className="app-container">
      <div className="chat-window">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.sender}`}>
            <p>{msg.text}</p>
          </div>
        ))}
      </div>

      {/* Simplify button (only visible after bot reply) */}
      {showSimplify && (
        <button className="simplify-btn" onClick={handleSimplify}>
          Simplify this explanation
        </button>
      )}

      <div className="input-area">
        <input
          type="text"
          placeholder="Ask a question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </div>
  );
}

export default App;

