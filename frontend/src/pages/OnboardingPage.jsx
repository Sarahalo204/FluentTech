import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../api/apiService';
const questions = [
  'Describe your last project in 2-3 sentences.',
  'What is one challenge you face when writing English emails?',
  'Explain your favorite technical topic in simple English.',
  'How do you prepare for a work presentation or meeting?',
];

const levelProfiles = {
  Beginner: {
    level: 'A2',
    description: 'You are building a foundation in English and can handle simple, everyday communication. A structured plan will help you grow confidence in professional scenarios.',
    goals: [
      'Practice short business conversations daily.',
      'Learn key workplace vocabulary and email phrases.',
      'Complete grammar drills for sentence structure.',
      'Build confidence with short spoken responses.',
    ],
  },
  Intermediate: {
    level: 'B1',
    description: 'You can communicate in many common workplace situations but still need polish and fluency. The next stage focuses on accuracy and clearer presentation skills.',
    goals: [
      'Develop stronger email and report writing skills.',
      'Practice structured story-telling for meetings.',
      'Review complex grammar and transition phrases.',
      'Take one mock presentation every week.',
    ],
  },
  Advanced: {
    level: 'B2',
    description: 'You already handle advanced communication well and can improve precision and confidence. This learning path accelerates your professional fluency.',
    goals: [
      'Refine persuasive language for proposals.',
      'Practice advanced listening and feedback skills.',
      'Write concise executive summaries and emails.',
      'Simulate leadership conversation scenarios.',
    ],
  },
};

function OnboardingPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [step, setStep] = useState(1);
  const [name, setName] = useState('');
  const [jobTitle, setJobTitle] = useState('Software Engineer');
  const [englishLevel, setEnglishLevel] = useState('Beginner');
  const [answers, setAnswers] = useState(['', '', '', '']);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const profile = useMemo(() => levelProfiles[englishLevel], [englishLevel]);

  useEffect(() => {
    if (step === 2 && currentQuestion >= questions.length) {
      setIsAnalyzing(true);
      const timer = setTimeout(() => {
        setIsAnalyzing(false);
        setStep(3);
      }, 2000);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [currentQuestion, step]);

  const progress = ((step - 1) / 2) * 100;

  const handleQuestionSubmit = (event) => {
    event.preventDefault();
    if (currentQuestion < questions.length) {
      setCurrentQuestion((current) => current + 1);
    }
  };

  const handleNextStep1 = async () => {
    if (!name.trim()) {
      alert("Please enter your name.");
      return;
    }
    const cefr = englishLevel === 'Beginner' ? 'A2' : englishLevel === 'Intermediate' ? 'B1' : 'B2';
    try {
      const data = await apiService.register({
        name,
        job_role: jobTitle,
        cefr_level: cefr,
      });
      login(data.token, { learner_id: data.learner_id, name: data.name, role: 'learner', cefr_level: cefr });
      setStep(2);
    } catch (error) {
      console.error('Registration failed:', error);
      alert('Registration failed. Please try again.');
    }
  };

  const handleGoalStart = async () => {
    try {
      await apiService.updateLevel(profile.level);
    } catch (e) {
      console.error("Failed to update level", e);
    }
    navigate('/chat');
  };

  return (
    <div className="mx-auto min-h-screen max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="rounded-3xl border border-slate-700 bg-slate-900/90 p-8 shadow-xl shadow-slate-950/20">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-sky-300/90">FluentTech</p>
            <h1 className="mt-3 text-3xl font-semibold text-white sm:text-4xl">Onboarding Assessment</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-400">
              Complete the quick wizard to personalize your learning path and begin practicing English professionally.
            </p>
          </div>
          <div className="rounded-3xl bg-slate-950/80 px-5 py-3 text-sm text-slate-300">
            Step {step} of 3
          </div>
        </div>

        <div className="mb-8 rounded-full bg-slate-800/80 p-1">
          <div className="h-2 rounded-full bg-sky-500 transition-all" style={{ width: `${progress}%` }} />
        </div>

        {step === 1 && (
          <div className="space-y-6">
            <div className="rounded-3xl bg-slate-950/70 p-6">
              <h2 className="text-xl font-semibold text-white">Step 1 — Basic Info</h2>
              <p className="mt-2 text-sm text-slate-400">Fill in the fields below to help FluentTech personalize your experience.</p>

              <div className="mt-6 grid gap-6 sm:grid-cols-2">
                <label className="space-y-2 text-sm text-slate-200">
                  الاسم
                  <input
                    type="text"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    placeholder="Your name"
                    className="w-full rounded-3xl border border-slate-700 bg-slate-950/90 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20"
                  />
                </label>

                <label className="space-y-2 text-sm text-slate-200">
                  المسمى الوظيفي
                  <select
                    value={jobTitle}
                    onChange={(event) => setJobTitle(event.target.value)}
                    className="w-full rounded-3xl border border-slate-700 bg-slate-950/90 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20"
                  >
                    <option>Software Engineer</option>
                    <option>Data Scientist</option>
                    <option>DevOps</option>
                    <option>Product Manager</option>
                    <option>Other</option>
                  </select>
                </label>

                <label className="space-y-2 text-sm text-slate-200 sm:col-span-2">
                  مستوى اللغة الإنجليزية الحالي
                  <div className="grid gap-2 sm:grid-cols-3">
                    {['Beginner', 'Intermediate', 'Advanced'].map((level) => (
                      <button
                        key={level}
                        type="button"
                        onClick={() => setEnglishLevel(level)}
                        className={`rounded-3xl border px-4 py-3 text-sm font-medium transition ${
                          englishLevel === level ? 'border-sky-400 bg-sky-500 text-white' : 'border-slate-700 bg-slate-950/90 text-slate-200 hover:border-slate-500 hover:bg-slate-800'
                        }`}
                      >
                        {level}
                      </button>
                    ))}
                  </div>
                </label>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleNextStep1}
                className="inline-flex items-center justify-center rounded-3xl bg-sky-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-sky-400"
              >
                التالي
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <div className="rounded-3xl bg-slate-950/70 p-6">
              <h2 className="text-xl font-semibold text-white">Step 2 — Diagnostic Chat</h2>
              <p className="mt-2 text-sm text-slate-400">Answer the English practice prompts to help us evaluate your current level.</p>

              {currentQuestion < questions.length ? (
                <form onSubmit={handleQuestionSubmit} className="mt-6 space-y-4">
                  <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
                    <p className="text-sm font-semibold text-slate-100">Question {currentQuestion + 1}</p>
                    <p className="mt-3 text-base leading-7 text-slate-200">{questions[currentQuestion]}</p>
                  </div>

                  <label className="space-y-2 text-sm text-slate-200">
                    Your answer
                    <textarea
                      rows="4"
                      value={answers[currentQuestion]}
                      onChange={(event) => {
                        const next = [...answers];
                        next[currentQuestion] = event.target.value;
                        setAnswers(next);
                      }}
                      className="w-full rounded-3xl border border-slate-700 bg-slate-950/90 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20"
                      placeholder="Type your response here…"
                    />
                  </label>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={!answers[currentQuestion].trim()}
                      className="inline-flex items-center justify-center rounded-3xl bg-sky-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-700"
                    >
                      {currentQuestion + 1 === questions.length ? 'Submit answers' : 'Next question'}
                    </button>
                  </div>
                </form>
              ) : (
                <div className="mt-6 rounded-3xl border border-slate-800 bg-slate-900/80 p-8 text-center text-slate-200">
                  {isAnalyzing ? (
                    <>
                      <p className="text-lg font-semibold text-white">Analyzing your level...</p>
                      <p className="mt-3 text-sm text-slate-400">This should only take a moment.</p>
                    </>
                  ) : (
                    <p className="text-lg font-semibold text-white">Ready to continue.</p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <div className="rounded-3xl bg-slate-950/70 p-8 text-center">
              <div className="mx-auto inline-flex h-32 w-32 items-center justify-center rounded-full bg-sky-500 text-4xl font-bold text-white shadow-lg shadow-sky-500/30">
                {profile.level}
              </div>
              <h2 className="mt-6 text-2xl font-semibold text-white">Your estimated CEFR level</h2>
              <p className="mt-3 max-w-2xl mx-auto text-sm leading-7 text-slate-300">{profile.description}</p>
            </div>

            <div className="rounded-3xl bg-slate-950/70 p-6">
              <h3 className="text-lg font-semibold text-white">4-week learning path</h3>
              <ul className="mt-4 space-y-3 text-slate-200">
                {profile.goals.map((goal) => (
                  <li key={goal} className="rounded-3xl border border-slate-800 bg-slate-900/80 px-4 py-4 text-sm">
                    {goal}
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-slate-400">Job title: <span className="text-slate-100">{jobTitle}</span></p>
                <p className="text-sm text-slate-400">English level: <span className="text-slate-100">{englishLevel}</span></p>
              </div>
              <button
                type="button"
                onClick={handleGoalStart}
                className="inline-flex items-center justify-center rounded-3xl bg-emerald-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-emerald-400"
              >
                ابدأ التعلم
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default OnboardingPage;
