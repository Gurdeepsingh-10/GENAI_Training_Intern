export default function Sidebar({
  isOpen,
  toggleSidebar,
  threads,
  activeThreadId,
  setActiveThreadId,
  selectedThreadIds,
  toggleSelectThread,
  createNewChat,
  deleteSelectedChats,
}) {
  return (
    <div className={`sidebar ${isOpen ? "open" : ""}`}>
      <div className="sidebar-header">
        <button onClick={toggleSidebar}>☰</button>
        <button onClick={createNewChat}>＋ New Chat</button>
      </div>

      <div className="thread-list">
        {threads.map(thread => (
          <div
            key={thread.id}
            className={`thread-item ${
              activeThreadId === thread.id ? "active" : ""
            }`}
          >
            <input
              type="checkbox"
              checked={selectedThreadIds.has(thread.id)}
              onChange={() => toggleSelectThread(thread.id)}
            />
            <span onClick={() => setActiveThreadId(thread.id)}>
              {thread.title}
            </span>
          </div>
        ))}
      </div>

      {selectedThreadIds.size > 0 && (
        <button className="delete-btn" onClick={deleteSelectedChats}>
          🗑 Delete Selected
        </button>
      )}
    </div>
  );
}
