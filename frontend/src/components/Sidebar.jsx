function Sidebar({
  user,
  conversations,
  currentConvId,
  sidebarOpen,
  onClose,
  onNewChat,
  onSelectSession,
  onLogout,
}) {
  return (
    <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
      <div className="sidebar-header">
        <span className="sidebar-title">📑 Case History</span>
        <button
          onClick={onClose}
          className="toggle-sidebar-btn"
          aria-label="Close sidebar"
        >
          ✕
        </button>
      </div>

      {user && (
        <div className="user-profile-badge">
          <div className="user-name" title={user.email}>
            {user.full_name || user.email}
          </div>
          <button className="logout-btn" onClick={onLogout}>
            Log out
          </button>
        </div>
      )}

      <div className="new-chat-wrap">
        <button className="new-chat-btn" onClick={onNewChat}>
          <span>+</span> New Inquiry
        </button>
      </div>

      <div className="session-list">
        {conversations.length === 0 ? (
          <p className="empty-sessions">No previous sessions</p>
        ) : (
          conversations.map((c) => (
            <div
              key={c.id}
              className={`session-item ${c.id === currentConvId ? "active" : ""}`}
              onClick={() => onSelectSession(c.id)}
            >
              <div className="session-title">{c.title}</div>
              <div className="session-meta">
                <span>{c.category}</span>
                <span>{c.updated_at ? c.updated_at.split(" ")[0] : ""}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}

window.Sidebar = Sidebar;
