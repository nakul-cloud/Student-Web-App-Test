function ChatInput({ input, setInput, loading, onSend }) {
  return (
    <footer className="input-dock">
      <textarea
        className="input-box"
        rows="1"
        placeholder="Ask any compliance question (e.g. Tax holiday, Doing Business in IFSC, IBU, FME)..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSend();
          }
        }}
      />
      <button
        className="send-btn"
        onClick={() => onSend()}
        disabled={!input.trim() || loading}
        aria-label="Send message"
      >
        ➤
      </button>
    </footer>
  );
}

window.ChatInput = ChatInput;
