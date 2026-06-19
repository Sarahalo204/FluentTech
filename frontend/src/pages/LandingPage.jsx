import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const messages = [
  'Let’s refine your update for the product review meeting.',
  'Use clear headlines and explain benefits in simple phrases.',
  'Try saying: “The new feature reduces response time by 40%.”',
];

function LandingPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const worksRef = useRef(null);
  const [coachMessage, setCoachMessage] = useState('');
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    let typingTimer;
    let charIndex = 0;

    const typeText = (text) => {
      setCoachMessage('');
      charIndex = 0;
      typingTimer = setInterval(() => {
        setCoachMessage((current) => current + text[charIndex]);
        charIndex += 1;
        if (charIndex >= text.length) {
          clearInterval(typingTimer);
          setTimeout(() => {
            setMessageIndex((current) => (current + 1) % messages.length);
          }, 1800);
        }
      }, 45);
    };

    typeText(messages[messageIndex]);
    return () => clearInterval(typingTimer);
  }, [messageIndex]);

  const handleStartFree = () => navigate(user ? '/chat' : '/onboarding');
  const handleSeeHow = () => worksRef.current?.scrollIntoView({ behavior: 'smooth' });

  return (
    <div className="landing-page">
      <style>{`
        :root {
          color-scheme: dark;
          --bg: #0a0a0f;
          --surface: #10121c;
          --surface-strong: #141728;
          --text: #e5e7eb;
          --muted: #94a3b8;
          --accent: #6366f1;
          --accent-soft: rgba(99, 102, 241, 0.18);
          --gold: #f59e0b;
          --gold-soft: rgba(245, 158, 11, 0.16);
          --radius: 28px;
          font-family: "Inter", "Plus Jakarta Sans", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        * { box-sizing: border-box; }
        html, body { margin: 0; min-height: 100%; background: var(--bg); }
        body { overflow-x: hidden; }
        .page-wrapper { max-width: 1300px; margin: 0 auto; padding: 32px 24px 64px; }
        .topbar { display: flex; align-items: center; justify-content: space-between; gap: 24px; margin-bottom: 2rem; }
        .brand { display: inline-flex; align-items: center; gap: 12px; font-size: 1.05rem; font-weight: 700; letter-spacing: 0.04em; }
        .brand-icon { display: inline-flex; align-items: center; justify-content: center; width: 42px; height: 42px; border-radius: 16px; background: linear-gradient(135deg, rgba(99, 102, 241, 0.14), rgba(245, 158, 11, 0.12)); color: var(--gold); font-size: 1.3rem; }
        .brand span { color: var(--accent); }
        .topbar-links { display: flex; flex-wrap: wrap; gap: 18px; align-items: center; }
        .topbar-link { color: var(--muted); text-decoration: none; font-size: 0.96rem; transition: color 0.2s ease; }
        .topbar-link:hover { color: var(--text); }
        .hero { min-height: calc(100vh - 136px); display: grid; grid-template-columns: 1.15fr 0.95fr; gap: 3rem; align-items: center; padding-top: 32px; background: radial-gradient(circle at top, rgba(99, 102, 241, 0.18), transparent 28%), radial-gradient(circle at 80% 10%, rgba(245, 158, 11, 0.12), transparent 24%), var(--bg); }
        .hero-copy { max-width: 640px; }
        .eyebrow { display: inline-flex; align-items: center; gap: 10px; padding: 10px 16px; border-radius: 999px; background: rgba(99, 102, 241, 0.14); color: var(--gold); text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.2em; font-weight: 700; }
        h1 { margin: 24px 0 18px; font-size: clamp(3rem, 5vw, 4.8rem); line-height: 0.95; letter-spacing: -0.04em; font-weight: 800; max-width: 12ch; }
        h1 strong { color: var(--accent); }
        .hero-text { margin-bottom: 28px; max-width: 600px; font-size: 1.05rem; line-height: 1.85; color: var(--muted); }
        .hero-actions { display: flex; flex-wrap: wrap; gap: 16px; }
        .btn-primary, .btn-secondary { border-radius: 999px; font-weight: 700; padding: 18px 30px; border: 1px solid transparent; transition: transform 0.25s ease, box-shadow 0.25s ease, background-color 0.25s ease, color 0.25s ease; cursor: pointer; }
        .btn-primary { background: linear-gradient(135deg, var(--accent), #818cf8); color: #fff; box-shadow: 0 18px 40px rgba(99, 102, 241, 0.18); }
        .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 22px 44px rgba(99, 102, 241, 0.26); }
        .btn-secondary { background: transparent; color: var(--text); border-color: rgba(255,255,255,0.16); }
        .btn-secondary:hover { background: rgba(255,255,255,0.06); }
        .hero-panel { position: relative; padding: 2rem; border-radius: 40px; background: radial-gradient(circle at top left, rgba(99, 102, 241, 0.18), transparent 38%), radial-gradient(circle at bottom right, rgba(245, 158, 11, 0.14), transparent 34%), linear-gradient(180deg, rgba(15, 23, 42, 0.9), rgba(10, 10, 15, 0.98)); border: 1px solid rgba(255,255,255,0.06); overflow: hidden; }
        .panel-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 26px; }
        .panel-tag { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 10px 14px; border-radius: 999px; background: rgba(99, 102, 241, 0.14); color: var(--accent); font-size: 0.9rem; font-weight: 700; }
        .panel-status { color: var(--muted); font-size: 0.92rem; }
        .chat-card { border-radius: 32px; background: rgba(15, 23, 42, 0.92); border: 1px solid rgba(255,255,255,0.07); padding: 26px 26px 28px; min-height: 420px; display: grid; gap: 22px; }
        .chat-message { position: relative; padding: 18px 22px; border-radius: 28px; line-height: 1.7; font-size: 0.95rem; }
        .chat-message.learner { background: rgba(255,255,255,0.06); align-self: start; color: #e2e8f0; }
        .chat-message.coach { background: linear-gradient(135deg, rgba(99, 102, 241, 0.16), rgba(245, 158, 11, 0.12)); color: #f8fafc; }
        .chat-message::before { content: ''; position: absolute; width: 10px; height: 10px; border-radius: 50%; top: 18px; left: -4px; background: rgba(255,255,255,0.08); }
        .chat-message.coach::before { left: unset; right: -4px; background: rgba(99, 102, 241, 0.55); }
        .chat-meta { display: flex; justify-content: space-between; gap: 12px; color: var(--muted); font-size: 0.82rem; }
        .typing-dots { display: inline-flex; align-items: center; gap: 8px; }
        .dot { width: 10px; height: 10px; background: #fff; border-radius: 999px; opacity: 0.25; animation: blink 1.2s infinite ease-in-out; }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink { 0%, 80%, 100% { opacity: 0.25; transform: translateY(0); } 40% { opacity: 1; transform: translateY(-3px); } }
        .section { padding: 72px 0; }
        .section-title { font-size: clamp(1.75rem, 2.2vw, 2.6rem); line-height: 1.05; margin: 0 0 0.75rem; }
        .section-copy { max-width: 620px; color: var(--muted); line-height: 1.8; margin-bottom: 2rem; }
        .stat-grid, .how-grid, .agent-grid { display: grid; gap: 18px; }
        .stat-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        .stat-card { padding: 28px; border-radius: 28px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); }
        .stat-number { font-size: 2.5rem; font-weight: 800; letter-spacing: -0.04em; margin-bottom: 0.65rem; color: var(--accent); }
        .stat-copy { color: var(--muted); line-height: 1.7; }
        .how-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        .how-card { padding: 28px; border-radius: 28px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); }
        .how-step { font-size: 0.96rem; font-weight: 700; color: var(--gold); margin-bottom: 14px; }
        .how-title { font-size: 1.35rem; margin-bottom: 0.8rem; }
        .how-text { color: var(--muted); line-height: 1.85; }
        .agent-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        .agent-card { padding: 32px; border-radius: 32px; background: rgba(15, 23, 42, 0.94); border: 1px solid rgba(255,255,255,0.05); transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease; }
        .agent-card:hover { transform: translateY(-6px); border-color: rgba(99, 102, 241, 0.35); box-shadow: 0 24px 70px rgba(99, 102, 241, 0.14); }
        .agent-label { display: inline-flex; align-items: center; gap: 10px; margin-bottom: 1rem; font-size: 0.95rem; color: var(--gold); }
        .agent-title { margin: 0; font-size: 1.45rem; font-weight: 700; }
        .agent-copy { margin-top: 0.85rem; color: var(--muted); line-height: 1.75; }
        .footer { padding: 48px 0 24px; border-top: 1px solid rgba(255,255,255,0.06); }
        .footer-grid { display: grid; grid-template-columns: 1fr 0.9fr; gap: 36px; align-items: start; }
        .footer-links { display: inline-flex; flex-wrap: wrap; gap: 16px; margin-top: 12px; }
        .footer-link { color: var(--muted); text-decoration: none; font-size: 0.95rem; }
        .footer-link:hover { color: var(--text); }
        .footer-copy { margin-top: 18px; max-width: 520px; color: var(--muted); line-height: 1.9; }
        .footer-brand { display: inline-flex; align-items: center; gap: 12px; margin-bottom: 12px; font-weight: 700; }
        .footer-brand span { color: var(--accent); }
        @media (max-width: 1024px) { .hero { grid-template-columns: 1fr; min-height: auto; } .hero-panel { order: -1; } }
        @media (max-width: 780px) { .page-wrapper { padding: 24px 18px 48px; } .topbar { flex-direction: column; align-items: flex-start; } .hero { gap: 1.75rem; } .section { padding: 54px 0; } .stat-grid, .how-grid, .agent-grid, .footer-grid { grid-template-columns: 1fr; } }
      `}</style>
      <div className="page-wrapper">
        <main className="hero">
          <section className="hero-copy">
            <span className="eyebrow">AI English Coaching</span>
            <h1>Speak Like You <strong>Belong in the Room</strong>.</h1>
            <p className="hero-text">AI-powered English coaching built for Saudi tech professionals — designed to give your language confidence, cultural poise, and career momentum.</p>
            <div className="hero-actions">
              <button type="button" className="btn-primary" onClick={handleStartFree}>
                {user ? 'Go to Chat' : 'Start Free'}
              </button>
              {!user && (
                <button type="button" className="btn-secondary" onClick={() => navigate('/login')}>
                  Login
                </button>
              )}
            </div>
          </section>

          <aside className="hero-panel" aria-label="Live demo chat card">
            <div className="panel-header">
              <span className="panel-tag">Live Demo</span>
              <span className="panel-status">AI coach interaction</span>
            </div>
            <div className="chat-card">
              <div className="chat-message learner">
                <p>Hello, I need to improve my technical English for product updates.</p>
                <div className="chat-meta"><span>Razan</span><span>09:12</span></div>
              </div>
              <div className="chat-message coach">
                <p>{coachMessage}</p>
                <div className="chat-meta"><span>FluentTech Coach</span><span>{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></div>
              </div>
              <div className="typing-dots">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
                <span style={{ color: 'var(--muted)', fontSize: '0.88rem' }}>Typing...</span>
              </div>
            </div>
          </aside>
        </main>

        <section id="problem" className="section">
          <div className="section-title">The barrier Saudi tech talent is solving today.</div>
          <p className="section-copy">When English is the gatekeeper to global engineering roles, confidence in communication becomes a strategic advantage. FluentTech is built to close that gap with coaching, roleplay, and instant feedback.</p>
          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-number">73%</div>
              <p className="stat-copy">of Saudi tech grads cite English as their #1 career barrier.</p>
            </div>
            <div className="stat-card">
              <div className="stat-number">82%</div>
              <p className="stat-copy">say they need stronger spoken English for leadership meetings.</p>
            </div>
            <div className="stat-card">
              <div className="stat-number">94%</div>
              <p className="stat-copy">believe AI coaching can accelerate language progress faster than traditional courses.</p>
            </div>
          </div>
        </section>

        <section id="works" ref={worksRef} className="section">
          <div className="section-title">How it works</div>
          <p className="section-copy">A simple three-step flow lets engineers move from assessment to real-world speaking practice and measurable improvement.</p>
          <div className="how-grid">
            <div className="how-card">
              <div className="how-step">Assess</div>
              <h3 className="how-title">Understand your current level</h3>
              <p className="how-text">Complete a tailored diagnostic and get an instant proficiency snapshot based on real Saudi tech scenarios.</p>
            </div>
            <div className="how-card">
              <div className="how-step">Practice</div>
              <h3 className="how-title">Roleplay real work conversations</h3>
              <p className="how-text">Simulate standups, product reviews, and interview responses with an AI partner that corrects tone and clarity.</p>
            </div>
            <div className="how-card">
              <div className="how-step">Improve</div>
              <h3 className="how-title">Receive precise feedback</h3>
              <p className="how-text">Get actionable writing and speaking guidance so your next presentation sounds polished and professional.</p>
            </div>
          </div>
        </section>

        <section id="agents" className="section">
          <div className="section-title">Three coaching agents, one distinctive edge</div>
          <p className="section-copy">FluentTech combines assessment, roleplay, and feedback agents into a single workflow that scales with your ambitions.</p>
          <div className="agent-grid">
            <article className="agent-card">
              <div className="agent-label">Learning Agent</div>
              <h3 className="agent-title">Build vocabulary & confidence</h3>
              <p className="agent-copy">Tailored practice sessions that reinforce the language needed for engineering, product, and leadership roles.</p>
            </article>
            <article className="agent-card">
              <div className="agent-label">Roleplay Agent</div>
              <h3 className="agent-title">Simulate workplace conversations</h3>
              <p className="agent-copy">Practice meetings, standups, and stakeholder updates with an AI partner that mirrors real Saudi tech environments.</p>
            </article>
            <article className="agent-card">
              <div className="agent-label">Feedback Agent</div>
              <h3 className="agent-title">Get real-time improvement cues</h3>
              <p className="agent-copy">Instant analysis on grammar, clarity, tone, and structure so every response becomes stronger.</p>
            </article>
          </div>
        </section>

        <footer id="footer" className="footer">
          <div className="footer-grid">
            <div>
              <div className="footer-brand"><span>🎓</span> Fluent<span>Tech</span></div>
              <p className="footer-copy">AI-powered English coaching for Saudi tech professionals, designed to elevate communication and unlock leadership roles.</p>
            </div>
            <div>
              <div className="footer-links">
                <a className="footer-link" href="#works">How it works</a>
                <a className="footer-link" href="#agents">Agents</a>
                <a className="footer-link" href="#footer">Contact</a>
              </div>
              <p className="footer-copy">Built with motion, clarity, and design for investor-ready storytelling.</p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default LandingPage;
