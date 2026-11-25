const { useState, useEffect } = React;

function getHashRoute() {
  return window.location.hash.replace(/^#/, "") || "";
}

function App() {
  const [token, setToken] = useState(localStorage.getItem("complyadi_token") || "");
  const [user, setUser] = useState(
    JSON.parse(localStorage.getItem("complyadi_user") || "null")
  );
  const [route, setRoute] = useState(getHashRoute());

  useEffect(() => {
    const onHashChange = () => setRoute(getHashRoute());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  // Enforce Auth / Chat routing cleanly
  useEffect(() => {
    if (!token && route !== "/login" && route !== "/register") {
      window.location.hash = "#/login";
    } else if (token && (route === "/login" || route === "/register" || route === "")) {
      window.location.hash = "#/chat";
    }
  }, [token, route]);

  const handleAuthSuccess = (data) => {
    const profile = { email: data.email, full_name: data.full_name };
    setToken(data.access_token);
    setUser(profile);
    localStorage.setItem("complyadi_token", data.access_token);
    localStorage.setItem("complyadi_user", JSON.stringify(profile));
    window.location.hash = "#/chat";
  };

  const handleLogout = () => {
    setToken("");
    setUser(null);
    localStorage.removeItem("complyadi_token");
    localStorage.removeItem("complyadi_user");
    localStorage.removeItem("complyadi_conv_id");
    window.location.hash = "#/login";
  };

  const AuthPage = window.AuthPage;
  const ChatPage = window.ChatPage;

  if (!token) {
    const mode = route === "/register" ? "register" : "login";
    return (
      <AuthPage
        initialMode={mode}
        onAuthSuccess={handleAuthSuccess}
        onNavigateMode={(next) => {
          window.location.hash = next === "register" ? "#/register" : "#/login";
        }}
      />
    );
  }

  return <ChatPage token={token} user={user} onLogout={handleLogout} />;
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
