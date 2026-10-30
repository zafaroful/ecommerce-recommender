import { useState, type FormEvent } from 'react';
import { useAuth } from '../auth/AuthContext';

function friendlyMessage(message: string): string {
  const text = message.toLowerCase();
  if (text.includes('email not confirmed')) {
    return 'Please confirm your email first, then sign in.';
  }
  if (text.includes('rate limit')) {
    return 'Too many sign-up emails were sent. Please wait a while and try again.';
  }
  if (text.includes('invalid login')) {
    return 'Wrong email or password. New here? Press "Create account" below.';
  }
  if (text.includes('already registered')) {
    return 'This email is already registered. Switch to "Sign in" below.';
  }
  return message;
}

export function AuthPanel() {
  const { session, signIn, signUp, signOut } = useAuth();
  const [mode, setMode] = useState<'signIn' | 'signUp'>('signIn');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (session) {
    return (
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span className="text-slate-600">{session.user.email}</span>
        <button
          type="button"
          onClick={() => void signOut()}
          className="min-h-11 rounded-xl border border-slate-300 bg-white px-4 font-semibold text-slate-800 transition hover:bg-slate-50"
        >
          Sign out
        </button>
      </div>
    );
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === 'signIn') {
        await signIn(email, password);
      } else {
        await signUp(email, password);
      }
    } catch (err) {
      setError(err instanceof Error ? friendlyMessage(err.message) : 'Authentication failed.');
    } finally {
      setBusy(false);
    }
  }

  function toggleMode() {
    setMode((m) => (m === 'signIn' ? 'signUp' : 'signIn'));
    setError(null);
  }

  const inputClass =
    'min-h-11 rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-900 placeholder:text-slate-500';

  return (
    <form className="flex flex-wrap items-center gap-2 text-sm" onSubmit={(e) => void handleSubmit(e)}>
      <label htmlFor="auth-email" className="sr-only">
        Email
      </label>
      <input
        id="auth-email"
        type="email"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="you@example.com"
        className={inputClass}
      />
      <label htmlFor="auth-password" className="sr-only">
        Password
      </label>
      <input
        id="auth-password"
        type="password"
        required
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        className={inputClass}
      />
      <button
        type="submit"
        disabled={busy}
        className="min-h-11 rounded-xl bg-indigo-600 px-4 font-semibold text-white transition hover:bg-indigo-700 disabled:opacity-50"
      >
        {busy ? 'Please wait…' : mode === 'signIn' ? 'Sign in' : 'Create account'}
      </button>
      <button
        type="button"
        onClick={toggleMode}
        className="text-sm font-medium text-indigo-700 hover:underline"
      >
        {mode === 'signIn' ? 'New here? Create account' : 'Already have an account? Sign in'}
      </button>
      {error && (
        <p role="alert" className="w-full text-sm text-rose-700">
          {error}
        </p>
      )}
    </form>
  );
}