import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const topics = ['AI', 'Cloud', 'Data', 'Agile', 'Interviews', 'Emails'];

function ProfilePage() {
  const navigate = useNavigate();
  const [selectedTopics, setSelectedTopics] = useState(['AI', 'Cloud', 'Emails']);
  const [streakDays] = useState(7);
  const completedSessions = 3;
  const totalSessions = 5;

  const progressValue = useMemo(() => Math.min(100, Math.round((completedSessions / totalSessions) * 100)), [completedSessions, totalSessions]);

  const toggleTopic = (topic) => {
    setSelectedTopics((current) =>
      current.includes(topic) ? current.filter((item) => item !== topic) : [...current, topic]
    );
  };

  return (
    <div className="mx-auto min-h-screen max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="rounded-3xl border border-slate-700 bg-slate-900/90 p-8 shadow-xl shadow-slate-950/20">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-sky-300/90">FluentTech</p>
            <h1 className="mt-3 text-3xl font-semibold text-white sm:text-4xl">Your Profile</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-400">Track your progress, manage your focus topics, and retake the assessment anytime.</p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/onboarding')}
            className="inline-flex items-center justify-center rounded-3xl bg-sky-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-sky-400"
          >
            Retake Assessment
          </button>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
          <div className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6 text-center">
            <p className="text-sm uppercase tracking-[0.3em] text-slate-400">Current level</p>
            <div className="mx-auto mt-6 flex h-28 w-28 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-sky-500 text-4xl font-bold text-white shadow-lg shadow-violet-500/20">
              B2
            </div>
            <p className="mt-4 text-sm text-slate-300">CEFR proficiency estimated from your last diagnostic assessment.</p>
          </div>

          <div className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm text-slate-400">Weekly goal progress</p>
                <p className="mt-1 text-2xl font-semibold text-white">{completedSessions}/{totalSessions} sessions</p>
              </div>
              <div className="relative h-28 w-28">
                <svg className="rotate-[-90deg]" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="44" className="stroke-slate-800 fill-transparent stroke-[10]" />
                  <circle
                    cx="50"
                    cy="50"
                    r="44"
                    className="stroke-sky-500 fill-transparent stroke-[10]"
                    strokeDasharray="276.46"
                    strokeDashoffset={`${276.46 - (276.46 * progressValue) / 100}`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center text-sm font-semibold text-white">
                  {progressValue}%
                </div>
              </div>
            </div>
            <div className="mt-6 rounded-3xl bg-slate-900/90 p-4 text-sm text-slate-300">
              Keep your learning streak going to reach your weekly goal.
            </div>
          </div>
        </div>

        <div className="mt-6 rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-white">Editable learning topics</h2>
              <p className="mt-2 text-sm text-slate-400">Select the topics you want to focus on this week.</p>
            </div>
            <div className="rounded-full bg-slate-900 px-4 py-2 text-xs uppercase tracking-[0.24em] text-slate-400">
              {selectedTopics.length} selected
            </div>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {topics.map((topic) => (
              <button
                key={topic}
                type="button"
                onClick={() => toggleTopic(topic)}
                className={`rounded-3xl border px-4 py-4 text-left transition ${
                  selectedTopics.includes(topic)
                    ? 'border-sky-500 bg-sky-500/15 text-white'
                    : 'border-slate-700 bg-slate-900/80 text-slate-300 hover:border-slate-500 hover:bg-slate-900'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-base font-semibold">{topic}</span>
                  <span className="text-sm text-slate-400">{selectedTopics.includes(topic) ? 'Selected' : 'Select'}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 grid gap-6 sm:grid-cols-[1fr_1fr]">
          <div className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6 text-center">
            <p className="text-sm uppercase tracking-[0.3em] text-slate-400">Learning streak</p>
            <p className="mt-4 text-5xl font-bold text-white">{streakDays}</p>
            <p className="mt-2 text-sm text-slate-300">days in a row</p>
          </div>
          <div className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
            <h3 className="text-lg font-semibold text-white">Weekly status</h3>
            <p className="mt-3 text-sm text-slate-400">Keep going with your selected topics and complete the sessions to improve your fluency.</p>
            <div className="mt-6 space-y-3 text-sm text-slate-300">
              <p>• Focus on practical AI vocabulary.</p>
              <p>• Practice email writing with polite phrasing.</p>
              <p>• Review cloud and DevOps conversation examples.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProfilePage;
