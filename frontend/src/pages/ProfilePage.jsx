import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../api/apiService';

const allTopics = ['Software Engineering', 'Data Science', 'DevOps', 'Product Management', 'Cloud Computing', 'AI', 'Presentations', 'Email Writing'];

function ProfilePage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [name, setName] = useState('');
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [learningGoals, setLearningGoals] = useState([]);
  const [targetLevel, setTargetLevel] = useState('B2');
  
  const [streakDays, setStreakDays] = useState(0);
  const [completedSessions, setCompletedSessions] = useState(0);
  const totalSessions = 5;

  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (user?.learner_id) {
      // Fetch Profile Data
      apiService.getProfile(user.learner_id)
        .then(profile => {
          setName(profile.name || '');
          setTargetLevel(profile.target_level || 'B2');
          setSelectedTopics(profile.preferred_topics || []);
          setLearningGoals(profile.learning_goals || []);
        })
        .catch(err => console.error('Error fetching profile:', err));

      // Fetch Progress Data
      apiService.getProgress(user.learner_id)
        .then(data => {
          setCompletedSessions(data.sessionsCompleted || 0);
          setStreakDays(data.streak_days || 0);
        })
        .catch(err => console.error('Error fetching progress:', err));
    }
  }, [user]);

  const progressValue = useMemo(() => Math.min(100, Math.round((completedSessions / totalSessions) * 100)) || 0, [completedSessions, totalSessions]);

  const toggleTopic = (topic) => {
    setSelectedTopics((current) =>
      current.includes(topic) ? current.filter((item) => item !== topic) : [...current, topic]
    );
  };

  const handleSave = async () => {
    if (!user?.learner_id) return;
    setIsSaving(true);
    try {
      await apiService.updateProfile(user.learner_id, {
        name,
        target_level: targetLevel,
        preferred_topics: selectedTopics,
        learning_goals: learningGoals,
      });
      alert('Profile updated successfully!');
    } catch (e) {
      console.error(e);
      alert('Failed to update profile.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="mx-auto min-h-screen max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="rounded-3xl border border-slate-200/60 bg-white dark:border-slate-700 dark:bg-slate-900/90 p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-xl dark:shadow-slate-950/20">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-sky-600 dark:text-sky-300/90">FluentTech</p>
            <h1 className="mt-3 text-3xl font-semibold text-slate-900 dark:text-white sm:text-4xl">Your Profile</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-400">Track your progress, edit your personal details, and manage your focus topics.</p>
          </div>
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            className="inline-flex items-center justify-center rounded-3xl bg-emerald-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-emerald-400 disabled:opacity-50"
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
          <div className="rounded-3xl border border-slate-200/80 bg-slate-50/50 dark:border-slate-800 dark:bg-slate-950/80 p-6 shadow-sm shadow-slate-200/20 dark:shadow-none">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Personal Details</h2>
            <div className="space-y-4">
              <label className="block space-y-2 text-sm text-slate-700 dark:text-slate-200">
                Name
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-3xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900/80 px-4 py-3 text-sm text-slate-900 dark:text-slate-100 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-500/10 shadow-[0_2px_10px_rgb(0,0,0,0.02)] dark:shadow-none"
                />
              </label>
              
              <div className="block space-y-2 text-sm text-slate-700 dark:text-slate-200">
                Current Assessed Level
                <div className="w-full rounded-3xl border border-slate-200/80 bg-slate-100/50 dark:border-slate-700 dark:bg-slate-900/40 px-4 py-3 text-sm font-semibold text-sky-600 dark:text-sky-400 outline-none cursor-not-allowed shadow-[0_2px_10px_rgb(0,0,0,0.02)] dark:shadow-none">
                  {user?.cefr_level || 'A1'}
                </div>
              </div>

              <label className="block space-y-2 text-sm text-slate-700 dark:text-slate-200">
                Learning Goals (comma separated)
                <input
                  type="text"
                  value={learningGoals.join(', ')}
                  onChange={(e) => setLearningGoals(e.target.value.split(',').map(v => v.trim()).filter(Boolean))}
                  placeholder="e.g. Interview Prep, Presentation Skills"
                  className="w-full rounded-3xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900/80 px-4 py-3 text-sm text-slate-900 dark:text-slate-100 outline-none transition focus:border-sky-500 focus:ring-4 focus:ring-sky-500/10 shadow-[0_2px_10px_rgb(0,0,0,0.02)] dark:shadow-none"
                />
              </label>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200/80 bg-slate-50/50 dark:border-slate-800 dark:bg-slate-950/80 p-6 shadow-sm shadow-slate-200/20 dark:shadow-none">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Weekly goal progress</p>
                <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">{completedSessions}/{totalSessions} sessions</p>
              </div>
              <div className="relative h-28 w-28">
                <svg className="rotate-[-90deg]" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="44" className="stroke-slate-200 dark:stroke-slate-800 fill-transparent stroke-[10]" />
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
                <div className="absolute inset-0 flex items-center justify-center text-sm font-semibold text-slate-900 dark:text-white">
                  {progressValue}%
                </div>
              </div>
            </div>
            <div className="mt-6 rounded-3xl bg-white dark:bg-slate-900/90 border border-slate-200/80 dark:border-transparent p-4 text-sm text-slate-600 dark:text-slate-300 shadow-[0_2px_10px_rgb(0,0,0,0.02)] dark:shadow-none">
              Keep your learning streak going to reach your weekly goal.
            </div>
          </div>
        </div>

        <div className="mt-6 rounded-3xl border border-slate-200/80 bg-slate-50/50 dark:border-slate-800 dark:bg-slate-950/80 p-6 shadow-sm shadow-slate-200/20 dark:shadow-none">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Preferred Topics</h2>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Select the topics you want to focus on this week.</p>
            </div>
            <div className="rounded-full bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-transparent px-4 py-2 text-xs uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400 shadow-[0_2px_10px_rgb(0,0,0,0.02)] dark:shadow-none">
              {selectedTopics.length} selected
            </div>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {allTopics.map((topic) => (
              <button
                key={topic}
                type="button"
                onClick={() => toggleTopic(topic)}
                className={`rounded-3xl border px-4 py-4 text-left transition ${
                  selectedTopics.includes(topic)
                    ? 'border-sky-500 bg-sky-50 dark:bg-sky-500/15 text-sky-700 dark:text-white shadow-[0_2px_15px_rgb(2,132,199,0.12)] dark:shadow-none'
                    : 'border-slate-200/80 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-300 dark:hover:border-slate-500 dark:hover:bg-slate-900 shadow-[0_2px_10px_rgb(0,0,0,0.02)] hover:shadow-[0_4px_15px_rgb(0,0,0,0.04)] dark:shadow-none'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-base font-semibold">{topic}</span>
                  <span className="text-sm text-slate-500 dark:text-slate-400">{selectedTopics.includes(topic) ? 'Selected' : 'Select'}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProfilePage;
