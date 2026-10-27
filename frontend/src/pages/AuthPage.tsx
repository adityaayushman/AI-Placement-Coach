import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { ErrorNote, Field } from "../components/ui";

export default function AuthPage({ mode }: { mode: "login" | "register" }) {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password, name);
      navigate(mode === "register" ? "/welcome" : "/");
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="grid min-h-screen place-items-center px-4 py-12">
      <div className="grid w-full max-w-5xl items-center gap-10 lg:grid-cols-[1.1fr_1fr]">
        <section className="hidden lg:block">
          <p className="eyebrow">AI Placement Coach</p>
          <h1 className="mt-4 font-serif text-5xl leading-[1.08] tracking-tight">
            Know where you stand.
            <br />
            <span className="bg-gradient-to-r from-rose via-amber to-sage bg-clip-text text-transparent">
              Know what to do next.
            </span>
          </h1>
          <p className="mt-6 max-w-md text-muted">
            Bring your marks, resume, practice and mock interviews together. You get one readiness
            score, the reasons behind it, and a short list of what to work on this week.
          </p>
        </section>

        <form onSubmit={submit} className="glass-strong mx-auto w-full max-w-md p-7 sm:p-9" noValidate>
          <h2 className="font-serif text-2xl">{mode === "login" ? "Sign in" : "Create your account"}</h2>
          <p className="mt-1 text-sm text-muted">
            {mode === "login" ? "Welcome back." : "Students sign up here. Staff accounts come from your admin."}
          </p>
          <div className="mt-6 space-y-4">
            {mode === "register" && (
              <Field label="Full name">
                <input className="input" value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />
              </Field>
            )}
            <Field label="Email">
              <input className="input" type="email" required value={email}
                onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
            </Field>
            <Field label="Password" hint={mode === "register" ? "At least 8 characters." : undefined}>
              <input className="input" type="password" required minLength={8} value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={mode === "login" ? "current-password" : "new-password"} />
            </Field>
            <ErrorNote error={error} />
            <button type="submit" className="btn-primary w-full" disabled={busy}>
              {busy ? "Please wait" : mode === "login" ? "Sign in" : "Create account"}
            </button>
          </div>
          <p className="mt-6 text-center text-sm text-muted">
            {mode === "login" ? (
              <>New here? <Link className="text-amber underline-offset-4 hover:underline" to="/register">Create an account</Link></>
            ) : (
              <>Have an account? <Link className="text-amber underline-offset-4 hover:underline" to="/login">Sign in</Link></>
            )}
          </p>
        </form>
      </div>
    </main>
  );
}
