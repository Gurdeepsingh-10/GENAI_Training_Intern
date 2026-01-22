import { useState } from "react";
import "./App.css";
import About from "./pages/About";
import userAvatar from "./assets/user.png";
import botAvatar from "./assets/bot.png";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function App() {
  const [page, setPage] = useState("chat");

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [isLocked, setIsLocked] = useState(false);

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [threads, setThreads] = useState([{ id: "room1", title: "Chat 1" }]);
  const [activeThreadId, setActiveThreadId] = useState("room1");

  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedThreads, setSelectedThreads] = useState(new Set());

  const createNewChat = () => {
    const id = crypto.randomUUID();
    setThreads(prev => [...prev, { id, title: "New Chat" }]);
    setActiveThreadId(id);
    setMessages([]);
    setIsSidebarOpen(false);
  };

  const toggleSelect = (id) => {
    setSelectedThreads(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const deleteSelected = () => {
    setThreads(prev => prev.filter(t => !selectedThreads.has(t.id)));
    setSelectedThreads(new Set());
    setSelectionMode(false);
    setMessages([]);
  };
  const sendFeedback = async (messageId, approved) => {
    await fetch("http://127.0.0.1:8000/chat/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message_id: messageId,
        approved
      })
    });
  };


  const sendMessage = async () => {
    if (!input.trim() || isLocked || !activeThreadId) return;

    const userMessage = input;
    setInput("");
    setIsLocked(true);
    setIsThinking(true);

    setMessages(prev => [...prev, { sender: "user", text: userMessage }]);

    const url = `http://127.0.0.1:8000/chat/stream/${activeThreadId}?message=${encodeURIComponent(userMessage)}`;

    try {
      const response = await fetch(url, { method: "POST" });
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let streamedText = "";
      let botAdded = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        streamedText += chunk;

        if (!botAdded) {
          setIsThinking(false);
          setMessages(prev => [...prev, { sender: "bot", text: streamedText }]);
          botAdded = true;
        } else {
          setMessages(prev => {
            const copy = [...prev];
            copy[copy.length - 1].text = streamedText;
            return copy;
          });
        }
      }
    } catch {
      setMessages(prev => [...prev, { sender: "bot", text: "Backend error." }]);
    }

    setIsLocked(false);
    setIsThinking(false);
  };

  return (
    <div className="app-container">

      {/* SIDEBAR */}
      <div className={`sidebar ${isSidebarOpen ? "open" : ""}`}>
        <div className="sidebar-header">
          <button onClick={() => setIsSidebarOpen(false)}>☰</button>
          <button onClick={createNewChat}>New +</button>
        </div>

        <div className="thread-list">
          {threads.map(t => (
            <div
              key={t.id}
              className={`thread-item 
                ${activeThreadId === t.id ? "active" : ""} 
                ${selectedThreads.has(t.id) ? "selected" : ""}`}
              onClick={() => {
                if (selectionMode) toggleSelect(t.id);
                else {
                  setActiveThreadId(t.id);
                  setMessages([]);
                  setIsSidebarOpen(false);
                }
              }}
            >
              <div className="thread-title">{t.title}</div>

              <div className="thread-actions">
                <span onClick={(e) => {
                  e.stopPropagation();
                  setSelectionMode(true);
                  toggleSelect(t.id);
                }}>
                  ⋮
                </span>
              </div>
            </div>
          ))}
        </div>

        {selectionMode && (
          <div className="sidebar-footer">
            <button onClick={deleteSelected}>🗑 Delete Selected</button>
          </div>
        )}
      </div>

      {/* NAVBAR */}
      <div className="navbar">
        <div className="nav-title">
          <span style={{ cursor: "pointer", marginRight: 12 }} onClick={() => setIsSidebarOpen(true)}>
            ☰
          </span>
          GenAI Chat
        </div>
        <div className="nav-links">
          <a onClick={() => setPage("chat")}>Home</a>
          <a onClick={() => setPage("about")}>About</a>
        </div>
      </div>

      {/* CHAT */}
      {page === "chat" && (
        <div className="chat-wrapper">

          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className="message-row">
                {m.sender === "bot" && <img src={botAvatar} className="avatar" />}
                <div className={`message-bubble ${m.sender === "user" ? "user-bubble" : "bot-bubble"}`}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
                  {m.sender === "bot" && i === messages.length - 1 && (
                    <div style={{ display: "flex", gap: "10px", marginTop: "6px" }}>
                      <button onClick={() => sendFeedback(m.id, true)}>✅</button>
                      <button onClick={() => sendFeedback(m.id, false)}>❌</button>
                    </div>
                  )}
                </div>
                {m.sender === "user" && <img src={userAvatar} className="avatar" />}
              </div>
            ))}

            {isThinking && (
              <div className="message-row">
                <img src={botAvatar} className="avatar" />
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
          </div>

          <div className="input-bar">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && sendMessage()}
              disabled={isLocked}
              placeholder={isLocked ? "AI is thinking..." : "Type your message..."}
            />
            <button onClick={sendMessage} disabled={isLocked}>
              {isLocked ? "Thinking..." : "Send"}
            </button>
          </div>

        </div>
      )}

      {page === "about" && <About />}
    </div>
  );
}

export default App;
