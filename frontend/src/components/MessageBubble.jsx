function MessageBubble({ message }) {
  const isUser = message.role === "user";
  const citation = message.source_citation;

  // Extract page number if present in citation.page_number or reference string
  let pageLabel = citation?.page_number || null;
  if (!pageLabel && citation?.reference) {
    const match = citation.reference.match(/\((Page\s*\d+)\)/i);
    if (match) pageLabel = match[1];
  }

  return (
    <div className={`message-row ${message.role}`}>
      <div className="avatar">{isUser ? "👤" : "🏛️"}</div>
      <div className="bubble-wrapper">
        {isUser ? (
          <div className="bubble">{message.content}</div>
        ) : (
          <div
            className="bubble markdown-body"
            dangerouslySetInnerHTML={{
              __html: window.renderMarkdown(message.content),
            }}
          />
        )}

        {citation && (
          <div className="citation-card">
            <div className="citation-header">
              <span className="citation-title">📌 Regulatory Source</span>
              {pageLabel && <span className="page-badge">📄 {pageLabel}</span>}
            </div>
            <div className="citation-ref">{citation.reference}</div>
            <div className="citation-body">
              <strong>Ref #{citation.faq_id}:</strong> {citation.question}
            </div>
          </div>
        )}

        {message.is_direct_hit && (
          <span className="direct-tag">⚡ Direct Regulatory Rule Match (0 Tokens)</span>
        )}
      </div>
    </div>
  );
}

window.MessageBubble = MessageBubble;
