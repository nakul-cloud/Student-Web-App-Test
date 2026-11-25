/**
 * Auth API — maps to backend `app/routes/auth_routes.py` (/api/v1/auth/*)
 */
(function (global) {
  global.AuthApi = {
    login(email, password) {
      return global.HttpClient.request("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
    },

    register(email, password, fullName) {
      return global.HttpClient.request("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName || "Compliance Officer",
        }),
      });
    },

    demoLogin() {
      return global.HttpClient.request("/api/v1/auth/demo-login", {
        method: "POST",
      });
    },
  };
})(window);
