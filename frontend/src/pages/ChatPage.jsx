const { useState, useEffect, useRef } = React;

const QUICK_QUESTIONS = [
  "What are the benefits of setting up an entity in GIFT City IFSC from the guide?",
  "What is the income tax holiday available for units in GIFT City IFSC?",
  "What are the registration requirements for a Fund Management Entity (FME)?",
  "What are the Suspicious Transaction Report (STR) deadlines under IFSCA AML rules?",
];

function ChatPage({ token, user, onLogout }) {
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(
    localStorage.getItem("complyadi_conv_id") || ""
  );
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const chatEndRef = useRef(null);

  const loadSessions = async () => {
    if (!token) return;
    try {
      const data = await window.ChatApi.getSessions(token);
      if (Array.isArray(data)) setConversations(data);
    } catch (err) {
      console.error("Sessions load error:", err);
    }
  };

  useEffect(() => {
    loadSessions();
  }, [token]);

  useEffect(() => {
    if (!currentConvId || !token) return;
    window.ChatApi.getSessionMessages(currentConvId, token)
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) setMessages(data);
      })
      .catch((err) => console.error("Messages load error:", err));
  }, [currentConvId, token]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (textToSend) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    setInput("");
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), role: "user", content: query },
    ]);
    setLoading(true);

    try {
      const data = await window.ChatApi.sendMessage(query, currentConvId, token);

      if (data.conversation_id && data.conversation_id !== currentConvId) {
        setCurrentConvId(data.conversation_id);
        localStorage.setItem("complyadi_conv_id", data.conversation_id);
        loadSessions();
      }

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: data.reply,
          source_citation: data.source_citation,
          is_direct_hit: data.is_direct_hit,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "⚠️ **Connection Issue:** " + (err.message || "Please retry in a moment."),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const startNewChat = () => {
    setCurrentConvId("");
    localStorage.removeItem("complyadi_conv_id");
    setMessages([]);
    setSidebarOpen(false);
  };

  const Sidebar = window.Sidebar;
  const MessageBubble = window.MessageBubble;
  const ChatInput = window.ChatInput;

  return (
    <div className="app-container">
      <Sidebar
        user={user}
        conversations={conversations}
        currentConvId={currentConvId}
        sidebarOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewChat={startNewChat}
        onSelectSession={(id) => {
          setCurrentConvId(id);
          localStorage.setItem("complyadi_conv_id", id);
          setSidebarOpen(false);
        }}
        onLogout={onLogout}
      />

      <main className="main-chat">
        <header className="top-nav">
          <div className="brand-group">
            <button
              className="toggle-sidebar-btn"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label="Open menu"
            >
              ☰
            </button>
            <div className="brand-logo">C</div>
            <div className="brand-info">
              <h1>ComplyADI</h1>
              <span>GIFT City IFSC Regulatory Assistant</span>
            </div>
          </div>
          <div className="nav-actions">
            <span className="model-badge">Groq: gpt-oss-120b</span>
            <span className="demo-pill">🟢 IFSC Online</span>
          </div>
        </header>

        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="welcome-container">
              <div className="welcome-icon">🏛️</div>
              <h2 className="welcome-title">GIFT City IFSC Compliance Assistant</h2>
              <p className="welcome-desc">
                Ask questions regarding tax holidays, banking units (IBUs), fund management,
                AML/KYC guidelines, and Doing Business at IFSC regulations.
              </p>
              <div className="chips-grid">
                {QUICK_QUESTIONS.map((q, idx) => (
                  <button key={idx} className="chip-btn" onClick={() => handleSend(q)}>
                    <span>🔍</span>
                    <span>{q}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m) => <MessageBubble key={m.id} message={m} />)
          )}

          {loading && (
            <div className="message-row assistant">
              <div className="avatar">🏛️</div>
              <div className="typing-box">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <ChatInput
          input={input}
          setInput={setInput}
          loading={loading}
          onSend={handleSend}
        />
      </main>
    </div>
  );
}

window.ChatPage = ChatPage;
