import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const mcqQuestions = [
  { text: "Q1: 'I ____ a software engineer.'", options: ["am", "is", "are", "be"], correctIndex: 0 },
  { text: "Q2: '____ you work in an office?'", options: ["Does", "Are", "Do", "Is"], correctIndex: 2 },
  { text: "Q3: 'We ____ a new project last week.'", options: ["start", "started", "starting", "starts"], correctIndex: 1 },
  { text: "Q4: 'Please send the report ____ Friday.'", options: ["in", "on", "at", "by"], correctIndex: 3 },
  { text: "Q5: 'I look forward ____ you soon.'", options: ["to meet", "meeting", "to meeting", "meet"], correctIndex: 2 },
  { text: "Q6: 'If the server ____ down, we will lose data.'", options: ["goes", "will go", "go", "went"], correctIndex: 0 },
  { text: "Q7: 'Despite ____ a tight deadline, the team delivered the feature.'", options: ["have", "to have", "had", "having"], correctIndex: 3 },
  { text: "Q8: 'The new software is ____ faster than the previous version.'", options: ["significantly", "significant", "significance", "signify"], correctIndex: 0 },
  { text: "Q9: 'It is imperative that the system ____ updated immediately.'", options: ["is", "be", "was", "has been"], correctIndex: 1 },
  { text: "Q10: 'Had I known about the bug earlier, I ____ the release.'", options: ["would delay", "delayed", "will have delayed", "would have delayed"], correctIndex: 3 }
];

const levelProfiles = {
  A1: {
    description: 'You are at the beginner stage. Focus on basic vocabulary and simple sentences.',
    goals: ['Learn basic tech vocabulary', 'Introduce yourself clearly', 'Understand simple instructions']
  },
  A2: {
    description: 'You can form simple sentences but need more practice with grammar and flow.',
    goals: ['Describe daily tasks', 'Write simple emails', 'Participate in basic conversations']
  },
  B1: {
    description: 'You can communicate on familiar topics. The goal is to reduce grammar errors.',
    goals: ['Explain projects clearly', 'Write structured emails', 'Understand meeting discussions']
  },
  B2: {
    description: 'You interact with fluency! We will polish complex structures and professional tone.',
    goals: ['Lead meetings confidently', 'Present technical concepts', 'Write professional reports']
  },
  C1: {
    description: 'Advanced proficiency. You express ideas fluently with rare errors.',
    goals: ['Master persuasive speaking', 'Handle complex negotiations', 'Write executive summaries']
  },
  C2: {
    description: 'Near-native proficiency. Focus on sophisticated vocabulary and nuance.',
    goals: ['Publish technical papers', 'Deliver keynote speeches', 'Master cultural nuances']
  }
};

function OnboardingPage() {
  const navigate = useNavigate();
  const { user, register, updateLevel } = useAuth();
  const [isNewUser, setIsNewUser] = useState(false);

  const [step, setStep] = useState(1);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [jobTitle, setJobTitle] = useState('Software Engineer');
  const [error, setError] = useState('');

  const [answers, setAnswers] = useState(Array(mcqQuestions.length).fill(null));
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [calculatedLevel, setCalculatedLevel] = useState('A1');

  useEffect(() => {
    // If they were already logged in when they visited the page, redirect them.
    // If isNewUser is true, it means they JUST registered on this page, so let them continue to Step 2.
    if (user && !isNewUser) {
      navigate('/chat');
    }
  }, [user, isNewUser, navigate]);


  useEffect(() => {
    if (step === 2 && currentQuestion >= mcqQuestions.length) {
      setIsAnalyzing(true);

      // Calculate level based on correct answers
      let correctCount = 0;
      for (let i = 0; i < mcqQuestions.length; i++) {
        if (answers[i] === mcqQuestions[i].correctIndex) {
          correctCount++;
        }
      }

      let level = "A1";
      if (correctCount >= 9) level = "C2";
      else if (correctCount >= 8) level = "C1";
      else if (correctCount >= 6) level = "B2";
      else if (correctCount >= 4) level = "B1";
      else if (correctCount >= 2) level = "A2";

      setCalculatedLevel(level);

      const completeAssessment = async () => {
        try {
          await updateLevel(level);
        } catch (e) {
          console.error("Failed to update level", e);
        }
        setIsAnalyzing(false);
        setStep(3);
      };

      const timer = setTimeout(completeAssessment, 2500);
      return () => clearTimeout(timer);
    }
  }, [currentQuestion, step, answers, updateLevel]);

  const progress = ((step - 1) / 2) * 100;

  const handleOptionSelect = (optionIndex) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestion] = optionIndex;
    setAnswers(newAnswers);

    // Auto proceed to next question after a tiny delay for better UX
    setTimeout(() => {
      setCurrentQuestion((current) => current + 1);
    }, 300);
  };

  const handleNextStep1 = async () => {
    setError('');
    if (!name.trim() || !email.trim() || !password.trim()) {
      setError("Please enter your name, email, and password.");
      return;
    }
    try {
      setIsNewUser(true); // Flag that this user was just created here
      await register({
        name,
        email,
        password,
        target_level: "B2", // Default target, user can change in profile
        learning_goals: ["Career Growth", "Interview Prep"],
        preferred_topics: [jobTitle],
      });
      setStep(2);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Registration failed. Email might already exist.");
    }
  };

  const handleGoalStart = () => {
    navigate('/');
  };

  return (
    <div className="mx-auto min-h-screen max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="rounded-3xl border border-slate-200/60 bg-white dark:border-slate-700 dark:bg-slate-900/90 p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-xl dark:shadow-slate-950/20">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-sky-600 dark:text-sky-300/90">FluentTech</p>
            <h1 className="mt-3 text-3xl font-semibold text-slate-900 dark:text-white sm:text-4xl">Onboarding Assessment</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-400">
              Complete the quick wizard to personalize your learning path and begin practicing English professionally.
            </p>
          </div>
          <div className="rounded-3xl bg-slate-100 dark:bg-slate-950/80 px-5 py-3 text-sm text-slate-600 dark:text-slate-300">
            Step {step} of 3
          </div>
        </div>

        <div className="mb-8 rounded-full bg-slate-200 dark:bg-slate-800/80 p-1">
          <div className="h-2 rounded-full bg-sky-500 transition-all" style={{ width: `${progress}%` }} />
        </div>

        {step === 1 && (
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="mt-4 text-3xl font-semibold text-slate-900 dark:text-white">Let's personalize your experience</h1>
              <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">Tell us a bit about your role so we can tailor your practice.</p>
            </div>

            {error && (
              <div className="rounded-2xl bg-red-500/10 p-4 border border-red-500/20 text-sm text-red-400 text-center">
                {error}
              </div>
            )}

            <div className="rounded-3xl bg-slate-50 dark:bg-slate-950/70 p-6 border border-slate-100 dark:border-transparent">
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Step 1 — Basic Info & Registration</h2>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Please provide your details to register.</p>

              <div className="mt-6 grid gap-6 sm:grid-cols-2">
                <label className="space-y-2 text-sm text-slate-700 dark:text-slate-200">
                  الاسم (Name)
                  <input
                    type="text"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    placeholder="Your name"
                    className="w-full rounded-3xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-950/90 px-4 py-3 text-sm text-slate-900 dark:text-slate-100 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
                  />
                </label>

                <label className="space-y-2 text-sm text-slate-700 dark:text-slate-200">
                  البريد الإلكتروني (Email)
                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.com"
                    className="w-full rounded-3xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-950/90 px-4 py-3 text-sm text-slate-900 dark:text-slate-100 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
                  />
                </label>

                <label className="space-y-2 text-sm text-slate-700 dark:text-slate-200">
                  كلمة المرور (Password)
                  <input
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="••••••••"
                    className="w-full rounded-3xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-950/90 px-4 py-3 text-sm text-slate-900 dark:text-slate-100 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
                  />
                </label>

                <label className="space-y-2 text-sm text-slate-700 dark:text-slate-200">
                  المجال المهني (Job Field)
                  <select
                    value={jobTitle}
                    onChange={(event) => setJobTitle(event.target.value)}
                    className="w-full rounded-3xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-950/90 px-4 py-3 text-sm text-slate-900 dark:text-slate-100 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20"
                  >
                    <option>Software Engineer</option>
                    <option>AI Engineer</option>
                    <option>Frontend Developer</option>
                    <option>Backend Developer</option>
                    <option>Data Scientist / Analyst</option>
                    <option>DevOps Engineer</option>
                    <option>Cybersecurity Specialist</option>
                    <option>UI/UX Designer</option>
                    <option>Product Manager</option>
                    <option>QA Engineer</option>
                    <option>IT Support</option>
                    <option>Other</option>
                  </select>
                </label>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleNextStep1}
                className="inline-flex items-center justify-center rounded-3xl bg-sky-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-sky-400"
              >
                Register & Start Test
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <div className="rounded-3xl bg-slate-50 border border-slate-100 dark:border-transparent dark:bg-slate-950/70 p-6">
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Step 2 — English Level Assessment</h2>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Answer these {mcqQuestions.length} questions to evaluate your level (A1-C2).</p>

              {currentQuestion < mcqQuestions.length ? (
                <div className="mt-6 space-y-4">
                  <div className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-6">
                    <p className="text-sm font-semibold text-slate-600 dark:text-slate-100">Question {currentQuestion + 1} of {mcqQuestions.length}</p>
                    <p className="mt-3 text-lg leading-7 text-slate-900 dark:text-white font-medium">{mcqQuestions[currentQuestion].text}</p>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2 mt-6">
                    {mcqQuestions[currentQuestion].options.map((option, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleOptionSelect(idx)}
                        className={`rounded-2xl border p-4 text-left text-sm font-medium transition ${answers[currentQuestion] === idx
                            ? 'border-sky-500 bg-sky-50 text-sky-700 dark:border-sky-400 dark:bg-sky-500/20 dark:text-white'
                            : 'border-slate-200 bg-white text-slate-700 hover:border-slate-400 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-slate-500 dark:hover:bg-slate-800'
                          }`}
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="mt-6 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-8 text-center text-slate-700 dark:text-slate-200">
                  {isAnalyzing ? (
                    <>
                      <p className="text-lg font-semibold text-slate-900 dark:text-white">Analyzing your level...</p>
                      <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">Mapping your answers to CEFR guidelines.</p>
                    </>
                  ) : (
                    <p className="text-lg font-semibold text-slate-900 dark:text-white">Assessment Complete.</p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <div className="rounded-3xl bg-slate-50 border border-slate-100 dark:border-transparent dark:bg-slate-950/70 p-8 text-center">
              <div className="mx-auto inline-flex h-32 w-32 items-center justify-center rounded-full bg-sky-500 text-4xl font-bold text-white shadow-lg shadow-sky-500/30">
                {calculatedLevel}
              </div>
              <h2 className="mt-6 text-2xl font-semibold text-slate-900 dark:text-white">Your Assessed CEFR Level</h2>
              <p className="mt-3 max-w-2xl mx-auto text-sm leading-7 text-slate-600 dark:text-slate-300">
                {levelProfiles[calculatedLevel]?.description}
              </p>
            </div>

            <div className="rounded-3xl bg-slate-50 border border-slate-100 dark:border-transparent dark:bg-slate-950/70 p-6">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Suggested Focus Areas</h3>
              <ul className="mt-4 space-y-3 text-slate-700 dark:text-slate-200">
                {levelProfiles[calculatedLevel]?.goals.map((goal, idx) => (
                  <li key={idx} className="rounded-3xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/80 px-4 py-4 text-sm">
                    {goal}
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Name: <span className="text-slate-900 dark:text-slate-100">{name}</span></p>
                <p className="text-sm text-slate-600 dark:text-slate-400">Level: <span className="text-slate-900 dark:text-slate-100">{calculatedLevel}</span></p>
              </div>
              <button
                type="button"
                onClick={handleGoalStart}
                className="inline-flex items-center justify-center rounded-3xl bg-emerald-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-emerald-400"
              >
                Go to Home Page
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default OnboardingPage;

