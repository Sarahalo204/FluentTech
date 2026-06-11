import { NavLink, Navigate, Route, Routes } from 'react-router-dom';
import ChatInterface from './components/ChatInterface';
import LandingPage from './pages/LandingPage';
import OnboardingPage from './pages/OnboardingPage';
import ProfilePage from './pages/ProfilePage';

function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/90 px-4 py-4 shadow-sm shadow-slate-950/10 sm:px-6">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4">
          <NavLink to="/" className="flex items-center gap-0 text-white no-underline transition hover:opacity-80">
            <span style={{ fontSize: '1.2rem', fontWeight: 600, letterSpacing: '-0.03em' }}>Fluent</span>
            <span style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '-0.03em', color: '#6366F1', fontStyle: 'italic' }}>Tech</span>
          </NavLink>
          <nav className="flex flex-wrap gap-3">
            {[
              { path: '/', label: 'Home' },
              { path: '/onboarding', label: 'Onboarding' },
              { path: '/profile', label: 'Profile' },
              { path: '/chat', label: 'Chat' },
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
          </nav>
        </div>
      </header>

      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/chat" element={<ChatInterface />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

export default App;
