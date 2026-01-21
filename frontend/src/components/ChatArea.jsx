export default function ChatArea({ activeThreadId }) {
  if (!activeThreadId) {
    return (
      <div className="chat-area empty">
        Select or create a chat
      </div>
    );
  }

  return (
    <div className="chat-area">
      <h2>{activeThreadId}</h2>
      <div className="chat-placeholder">
        Chat messages will appear here
      </div>
    </div>
  );
}
