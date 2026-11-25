/**
 * Safe Markdown Renderer using marked + DOMPurify
 */
(function (global) {
  global.renderMarkdown = function renderMarkdown(text) {
    if (!text) return "";
    if (global.marked && global.DOMPurify) {
      const html = global.marked.parse(text, { breaks: true, gfm: true });
      return global.DOMPurify.sanitize(html);
    }
    // Fallback: escape HTML and preserve line breaks
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\n/g, "<br/>");
  };
})(window);
