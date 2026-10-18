import { useState, type FormEvent } from 'react';
import { useAuth } from '../auth/AuthContext';

export function AuthPanel() {
  const { session, signIn, signUp, signOut } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (session) {
    return (
      <div className="flex items-center gap-3 text-sm">
        <span className="text-slate-400">{session.user.email}</span>
        <button
          type="button"
          onClick={() => void signOut()}
          className="rounded-lg border border-slate-700 px-3 py-1.5 text-slate-200 transition hover:border-cyan-400 hover:text-cyan-300"
        >
          Sign out
        </button>
      </div>
    );
  }

  async function handleSubmit(event: FormEvent, mode: 'signIn' | 'signUp') {
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
      setError(err instanceof Error ? err.message : 'Authentication failed.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="flex flex-wrap items-center gap-2 text-sm" onSubmit={(e) => void handleSubmit(e, 'signIn')}>
      <input
        type="email"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="you@example.com"
        className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-slate-100 outline-none focus:border-cyan-400"
      />
      <input
        type="password"
        required
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-slate-100 outline-none focus:border-cyan-400"
      />
      <button
        type="submit"
        disabled={busy}
        className="rounded-lg bg-cyan-500 px-3 py-1.5 font-medium text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50"
      >
        Sign in
      </button>
      <button
        type="button"
        disabled={busy}
        onClick={(e) => void handleSubmit(e, 'signUp')}
        className="rounded-lg border border-slate-700 px-3 py-1.5 text-slate-200 transition hover:border-cyan-400 hover:text-cyan-300 disabled:opacity-50"
      >
        Sign up
      </button>
      {error && <span className="text-rose-400">{error}</span>}
    </form>
  );
}