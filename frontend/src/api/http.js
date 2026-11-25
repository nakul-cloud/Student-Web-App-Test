/**
 * Base HTTP Client — handles backend URL resolution, auth headers, and safe JSON parsing.
 */
(function (global) {
  const API_BASE =
    window.location.protocol === "file:" ||
    ((window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") &&
      window.location.port !== "8000" &&
      window.location.port !== "")
      ? "http://localhost:8000"
      : "";

  async function request(path, options = {}) {
    const url = `${API_BASE}${path}`;
    const res = await fetch(url, options);
    const rawText = await res.text();

    let data = {};
    try {
      data = rawText ? JSON.parse(rawText) : {};
    } catch {
      throw new Error(
        `HTTP ${res.status} (${url}): ${rawText ? rawText.slice(0, 120) : "Empty server response"}`
      );
    }

    if (!res.ok) {
      if (res.status === 401) {
        localStorage.removeItem("complyadi_token");
        localStorage.removeItem("complyadi_user");
        if (window.location.hash !== "#/login" && window.location.hash !== "#/register") {
          window.location.hash = "#/login";
        }
      }
      throw new Error(data.message || data.detail || `Request failed (${res.status})`);
    }

    return data;
  }

  global.HttpClient = { request, API_BASE };
})(window);
