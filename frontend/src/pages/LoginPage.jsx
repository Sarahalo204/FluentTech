import { useState } from 'react';
import { useNavigate, NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!email.trim() || !password.trim()) {
      setError("Please enter your email and password.");
      return;
    }

    setIsLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      console.error('Login failed:', err);
      setError('Invalid email or password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-[calc(100vh-80px)] items-center justify-center px-4 py-8 sm:px-6 lg:px-8">
      <div className="w-full max-w-md rounded-3xl border border-slate-200/60 bg-white dark:border-slate-700 dark:bg-slate-900/90 p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-xl dark:shadow-slate-950/20">
        <div className="mb-8 text-center">
          <h1 className="mt-3 text-3xl font-semibold text-slate-900 dark:text-white">Welcome Back</h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Log in to continue your English learning journey.</p>
        </div>

        {error && (
          <div className="mt-6 rounded-2xl bg-red-500/10 p-4 border border-red-500/20 text-sm text-red-400 text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <label className="block space-y-2 text-sm text-slate-700 dark:text-slate-200">
            البريد الإلكتروني (Email)
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full rounded-3xl border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-950/90 px-4 py-3 text-sm text-slate-900 dark:text-slate-100 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
            />
          </label>

          <label className="block space-y-2 text-sm text-slate-700 dark:text-slate-200">
            كلمة المرور (Password)
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-3xl border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-950/90 px-4 py-3 text-sm text-slate-900 dark:text-slate-100 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
            />
          </label>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center rounded-3xl bg-sky-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-600"
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-600 dark:text-slate-400">
          Don't have an account?{' '}
          <NavLink to="/onboarding" className="text-sky-600 dark:text-sky-400 hover:underline">
            Register here
          </NavLink>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
