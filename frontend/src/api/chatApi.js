/**
 * Chat API — maps to backend `app/chatbot/router.py` (/api/v1/chatbot/*)
 */
(function (global) {
  global.ChatApi = {
    getSessions(token) {
      return global.HttpClient.request("/api/v1/chatbot/sessions", {
        headers: { Authorization: `Bearer ${token}` },
      });
    },

    getSessionMessages(conversationId, token) {
      return global.HttpClient.request(`/api/v1/chatbot/sessions/${conversationId}/messages`, {
        headers: { Authorization: `Bearer ${token}` },
      });
    },

    sendMessage(message, conversationId, token) {
      return global.HttpClient.request("/api/v1/chatbot/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message,
          conversation_id: conversationId || null,
        }),
      });
    },

    health() {
      return global.HttpClient.request("/api/v1/chatbot/health");
    },
  };
})(window);
