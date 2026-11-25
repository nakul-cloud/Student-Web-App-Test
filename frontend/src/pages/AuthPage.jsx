function AuthPage({ initialMode = "login", onAuthSuccess, onNavigateMode }) {
  const [authMode, setAuthMode] = React.useState(initialMode);
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [fullName, setFullName] = React.useState("");
  const [error, setError] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);

  React.useEffect(() => {
    setAuthMode(initialMode);
    setError("");
  }, [initialMode]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const data =
        authMode === "login"
          ? await window.AuthApi.login(email, password)
          : await window.AuthApi.register(email, password, fullName);
      onAuthSuccess(data);
    } catch (err) {
      setError(err.message || "Authentication failed.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDemo = async () => {
    setError("");
    setSubmitting(true);
    try {
      const data = await window.AuthApi.demoLogin();
      onAuthSuccess(data);
    } catch (err) {
      setError(err.message || "Demo login failed.");
    } finally {
      setSubmitting(false);
    }
  };

  const toggleMode = () => {
    const next = authMode === "login" ? "register" : "login";
    setAuthMode(next);
    setError("");
    if (onNavigateMode) onNavigateMode(next);
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <div className="brand-logo">C</div>
          <div>
            <h1 className="auth-title">ComplyADI</h1>
            <span className="auth-subtitle">GIFT City IFSC · Regulatory Portal</span>
          </div>
        </div>

        <p className="auth-desc">
          {authMode === "login"
            ? "Sign in to access your GIFT City IFSC compliance records & regulatory assistant."
            : "Create an account for official IFSC compliance consulting."}
        </p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          {authMode === "register" && (
            <div className="auth-field">
              <label>Full Name</label>
              <input
                type="text"
                placeholder="e.g. Riya Patel"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
          )}
          <div className="auth-field">
            <label>Corporate / Official Email</label>
            <input
              type="email"
              placeholder="compliance@entity.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="auth-field">
            <label>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="auth-btn-primary" disabled={submitting}>
            {submitting
              ? "Please wait..."
              : authMode === "login"
              ? "Sign In"
              : "Create Account"}
          </button>
        </form>

        <div className="auth-divider">— OR FOR EVALUATOR —</div>
        <button
          type="button"
          className="auth-btn-demo"
          onClick={handleDemo}
          disabled={submitting}
        >
          <span>⚡</span> 1-Click Examiner Demo Login
        </button>

        <div className="auth-toggle-link" onClick={toggleMode}>
          {authMode === "login"
            ? "New entity? Register for an account"
            : "Already registered? Sign in"}
        </div>
      </div>
    </div>
  );
}

window.AuthPage = AuthPage;
