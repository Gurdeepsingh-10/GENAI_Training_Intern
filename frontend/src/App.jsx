import { useState } from "react";
import "./App.css";
import About from "./pages/About";
import userAvatar from "./assets/user.png";
import botAvatar from "./assets/bot.png";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";


const THREAD_ID = "room1";




function App() {
  const [page, setPage] = useState("chat");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [isLocked, setIsLocked] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || isLocked) return;

    const userMessage = input;
    setInput("");

    // lock UI + show dots
    setIsLocked(true);
    setIsThinking(true);

    // show user message
    setMessages((prev) => [
      ...prev,
      { sender: "user", text: userMessage }
    ]);

    const url = `http://127.0.0.1:8000/chat/stream/${THREAD_ID}?message=${encodeURIComponent(
      userMessage
    )}`;

    try {
      const response = await fetch(url, { method: "POST" });
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let streamedText = "";
      let botMessageAdded = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        streamedText += chunk;

        // first word arrives → create bubble + remove dots
        if (!botMessageAdded) {
          setIsThinking(false);

          setMessages((prev) => [
            ...prev,
            { sender: "bot", text: streamedText }
          ]);

          botMessageAdded = true;
        }
        // update same bubble after that
        else {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1].text = streamedText;
            return updated;
          });
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Backend connection error." }
      ]);
    }

    // unlock UI after streaming finishes
    setIsLocked(false);
    setIsThinking(false);
  };

  return (
    <div className="app-container">

      {/* NAVBAR */}
      <div className="navbar">
        <div className="nav-title">GenAI Chat</div>
        <div className="nav-links">
          <a onClick={() => setPage("chat")}>Home</a>
          <a onClick={() => setPage("about")}>About</a>
        </div>
      </div>

      {page === "chat" && (
        <div className="chat-wrapper">

          <div className="chat-messages">

            {messages.map((m, i) => (
              <div key={i} className="message-row">

                {m.sender === "bot" && (
                  <img src={botAvatar} className="avatar" alt="bot" />
                )}

                <div
                  className={`message-bubble ${m.sender === "user" ? "user-bubble" : "bot-bubble"
                    }`}
                >
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {m.text}
                  </ReactMarkdown>
                </div>


                {m.sender === "user" && (
                  <img src={userAvatar} className="avatar" alt="user" />
                )}
              </div>
            ))}

            {isThinking && (
              <div className="message-row">
                <img src={botAvatar} className="avatar" alt="bot" />
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}

          </div>

          <div className="input-bar">
            <input
              placeholder={isLocked ? "AI is thinking..." : "Type your message..."}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              disabled={isLocked}
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
