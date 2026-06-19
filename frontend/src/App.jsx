import { NavLink, Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import ChatInterface from './components/ChatInterface';
import LandingPage from './pages/LandingPage';
import OnboardingPage from './pages/OnboardingPage';
import LoginPage from './pages/LoginPage';
import ProfilePage from './pages/ProfilePage';

const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/onboarding" replace />;
  }
  return children;
};

function App() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/90 px-4 py-4 shadow-sm shadow-slate-950/10 sm:px-6">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4">
          <NavLink to="/" className="flex items-center gap-0 text-white no-underline transition hover:opacity-80">
            <span style={{ fontSize: '1.2rem', fontWeight: 600, letterSpacing: '-0.03em' }}>Fluent</span>
            <span style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '-0.03em', color: '#6366F1', fontStyle: 'italic' }}>Tech</span>
          </NavLink>
          <nav className="flex flex-wrap items-center gap-3">
            {[
              { path: '/', label: 'Home' },
              ...(user ? [
                { path: '/profile', label: 'Profile' },
                { path: '/chat', label: 'Chat' },
              ] : [
                { path: '/onboarding', label: 'Start Free' },
                { path: '/login', label: 'Login' },
              ])
            ].map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `rounded-3xl px-4 py-2 text-sm font-medium transition ${
                    isActive ? 'bg-slate-700 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
            
            {user && (
              <button
                onClick={handleLogout}
                className="rounded-3xl border border-slate-700 bg-transparent px-4 py-2 text-sm font-medium text-slate-300 transition hover:bg-slate-800 hover:text-white"
              >
                Logout
              </button>
            )}
          </nav>
        </div>
      </header>

      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/profile" element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        } />
        <Route path="/chat" element={
          <ProtectedRoute>
            <ChatInterface />
          </ProtectedRoute>
        } />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

export default App;
