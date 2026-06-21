import React, { useRef, useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiService } from '../api/apiService';
import { useAuth } from '../context/AuthContext';
import 'regenerator-runtime/runtime';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import { Mic, MicOff, Volume2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
const formatTime = () => new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

const scoreColorClass = (value) => {
  if (value > 80) return 'bg-emerald-500';
  if (value >= 60) return 'bg-amber-400';
  return 'bg-rose-500';
};

function ChatInterface() {
  const { user } = useAuth();
  const [sessionId, setSessionId] = useState(`sess_${Date.now()}`);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      text: 'Hi there! I am your AI language coach. Ask me anything or let us practice!',
      timestamp: formatTime(),
    }
  ]);
  const [sources, setSources] = useState([]);
  const [isSourceOpen, setIsSourceOpen] = useState(true);
  const chatEndRef = useRef(null);

  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition
  } = useSpeechRecognition();

  useEffect(() => {
    if (listening && transcript) {
      setInput(transcript);
    }
  }, [transcript, listening]);

  const toggleListening = () => {
    if (listening) {
      SpeechRecognition.stopListening();
    } else {
      resetTranscript();
      setInput('');
      SpeechRecognition.startListening({ continuous: true });
    }
  };

  const playTTS = (text) => {
    try {
      const userStr = localStorage.getItem('edulingo_user');
      const token = userStr ? JSON.parse(userStr).access_token : '';
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const url = `${baseUrl}/api/tts?text=${encodeURIComponent(text)}&token=${encodeURIComponent(token)}`;
      const audio = new Audio(url);
      audio.play();
    } catch (err) {
      console.error("Failed to play audio:", err);
    }
  };

  const mutation = useMutation(
    async (question) => {
      const response = await apiService.sendMessage(
        user?.learner_id || 'anonymous',
        sessionId,
        question,
        null // let Supervisor decide
      );
      return response;
    },
    {
      onSuccess: (data, question) => {
        const assistantMessage = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          text: data.response || 'I could not generate an answer right now. Please try again.',
          timestamp: formatTime(),
          scores: data.feedback?.scores || null,
        };

        setMessages((current) => [
          ...current,
          assistantMessage,
        ]);

        let newSources = [];
        if (data.context_summary) {
           newSources.push({ title: 'Context Summary', snippet: data.context_summary });
        }
        if (data.feedback && data.feedback.rag_sources) {
           data.feedback.rag_sources.forEach(src => {
               newSources.push({ title: 'Grammar Reference', snippet: src });
           });
        }
        if (newSources.length > 0) {
            setSources(newSources);
        }

        setInput('');
        scrollToBottom();
      },
      onError: (error) => {
        setMessages((current) => [
          ...current,
          {
            id: `assistant-error-${Date.now()}`,
            role: 'assistant',
            text: error?.response?.data?.message || error.message || 'There was an error fetching the answer.',
            timestamp: formatTime(),
          },
        ]);
        setInput('');
        scrollToBottom();
      },
    }
  );

  const scrollToBottom = () => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();

    const question = input.trim();
    if (!question || mutation.isLoading) {
      return;
    }

    setMessages((current) => [
      ...current,
      { id: `user-${Date.now()}`, role: 'user', text: question, timestamp: formatTime() },
    ]);

    if (listening) {
      SpeechRecognition.stopListening();
      resetTranscript();
    }

    setInput('');
    mutation.mutate(question);
  };

  const handleClear = () => {
    setSessionId(`sess_${Date.now()}`); // Create a fresh session in the backend
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        text: 'Chat history cleared. Ask me anything about the FluentTech curriculum or language learning path.',
        timestamp: formatTime(),
      },
    ]);
    setSources([]);
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
      <header className="rounded-3xl border border-slate-200 dark:border-slate-700 p-6 shadow-xl shadow-slate-200 dark:shadow-slate-950/20 backdrop-blur bg-gradient-to-br from-sky-100 via-sky-50 to-white dark:from-sky-800 dark:via-sky-900 dark:to-slate-950 transition-colors">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-500 dark:text-slate-200/80">FluentTech</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900 dark:text-white sm:text-4xl">FluentTech AI Language Coach</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-300 sm:text-base">
              Ask me anything, practice job interviews, or improve your grammar and vocabulary. I will track your progress and provide personalized feedback to help you succeed!
            </p>
          </div>
          <button
            onClick={handleClear}
            className="inline-flex items-center justify-center rounded-2xl border border-slate-300 bg-white dark:border-white/10 dark:bg-white/10 px-4 py-2 text-sm font-medium text-slate-700 dark:text-white transition hover:bg-slate-50 dark:hover:border-white/20 dark:hover:bg-white/15"
            type="button"
          >
            Clear chat
          </button>
        </div>
      </header>

      <main className="grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
        <section className="rounded-3xl border border-slate-200/60 bg-white dark:border-slate-700 dark:bg-slate-900/90 p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-xl dark:shadow-slate-950/20">
          <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Conversation</h2>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">The assistant will intelligently adapt to your learning needs.</p>
            </div>
            <div className="inline-flex items-center gap-2 rounded-2xl bg-slate-100 dark:bg-slate-800 px-3 py-2 text-xs text-slate-600 dark:text-slate-300">
              <span className="h-2.5 w-2.5 rounded-full bg-sky-500"></span>
              {mutation.isLoading ? 'Typing...' : 'Ready to ask'}
            </div>
          </div>

          <div className="mb-4 max-h-[60vh] overflow-y-auto rounded-3xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/70 p-4 text-sm shadow-inner shadow-slate-200/50 dark:shadow-slate-950/40 message-scroll">
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex flex-col gap-3 rounded-3xl p-4 shadow-sm ${
                    message.role === 'assistant'
                      ? 'items-start bg-white border border-slate-200 dark:border-transparent dark:bg-slate-800 text-slate-800 dark:text-slate-100 shadow-[0_2px_10px_rgb(0,0,0,0.02)]'
                      : 'items-end self-end bg-sky-600 dark:bg-[#7C3AED] text-white shadow-[0_2px_10px_rgb(2,132,199,0.2)]'
                  }`}
                >
                  <div className="flex w-full flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
                        {message.role === 'assistant' ? 'FluentTech Assistant' : 'You'}
                      </span>
                      {message.role === 'assistant' && (
                        <button onClick={() => playTTS(message.text)} className="text-slate-400 hover:text-sky-500 dark:hover:text-sky-400 transition" title="Play audio">
                          <Volume2 size={16} />
                        </button>
                      )}
                    </div>
                    <div className="text-sm leading-6">
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                          strong: ({node, ...props}) => <strong className="font-bold text-slate-900 dark:text-white" {...props} />,
                          ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-2 space-y-1" {...props} />,
                          ol: ({node, ...props}) => <ol className="list-decimal pl-5 mb-2 space-y-1" {...props} />,
                          li: ({node, ...props}) => <li className="marker:text-sky-500" {...props} />
                        }}
                      >
                        {message.text}
                      </ReactMarkdown>
                    </div>
                  </div>
                  <div className="flex w-full items-center justify-between gap-4 text-[11px] text-slate-500 dark:text-slate-400">
                    <span>{message.role === 'assistant' ? 'Assistant' : 'User'}</span>
                    <span>{message.timestamp}</span>
                  </div>

                  {message.role === 'assistant' && message.scores && (
                    <div className="space-y-3 rounded-3xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950/80 p-4">
                      <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">Feedback scores</p>
                      {Object.entries(message.scores).map(([label, value]) => (
                        <div key={label} className="space-y-2">
                          <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                            <span>{label.charAt(0).toUpperCase() + label.slice(1)}</span>
                            <span>{value}%</span>
                          </div>
                          <div className="h-2.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                            <div className={`h-full rounded-full ${scoreColorClass(value)}`} style={{ width: `${value}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
            {mutation.isLoading && (
              <div className="mt-4 flex items-center justify-center rounded-3xl bg-slate-100 dark:bg-slate-800 px-4 py-3 text-sm text-slate-600 dark:text-slate-200">
                <div className="flex items-center gap-2">
                  <span>FluentTech is typing</span>
                  <span className="flex items-center gap-1">
                    <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-slate-400 dark:bg-white/80"></span>
                    <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-slate-400/60 dark:bg-white/60 delay-150"></span>
                    <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-slate-400/40 dark:bg-white/40 delay-300"></span>
                  </span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <label htmlFor="user-question" className="sr-only">
              Ask a question
            </label>
            <textarea
              id="user-question"
              rows="3"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Type your question about the curriculum, lessons, or pedagogy…"
              className="w-full resize-none rounded-3xl border border-slate-200/80 bg-slate-50/50 dark:border-slate-700 dark:bg-slate-950/90 px-4 py-3 text-sm text-slate-900 dark:text-slate-100 outline-none transition focus:border-sky-500 focus:bg-white dark:focus:bg-slate-900/90 focus:ring-4 focus:ring-sky-500/10"
            />
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-xs text-slate-500 sm:text-sm">Press Enter to submit or use the microphone.</p>
              <div className="flex items-center gap-3">
                {browserSupportsSpeechRecognition && (
                  <button
                    type="button"
                    onClick={toggleListening}
                    className={`inline-flex items-center justify-center rounded-full p-3 transition ${listening ? 'bg-rose-500 text-white animate-pulse' : 'bg-slate-100 text-slate-500 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'}`}
                    title={listening ? "Stop listening" : "Start listening"}
                  >
                    {listening ? <MicOff size={20} /> : <Mic size={20} />}
                  </button>
                )}
                <button
                  type="submit"
                  disabled={mutation.isLoading || !input.trim()}
                  className="inline-flex items-center justify-center rounded-3xl bg-sky-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-300 dark:disabled:bg-slate-600"
                >
                  {mutation.isLoading ? 'Sending…' : 'Send'}
                </button>
              </div>
            </div>
          </form>
        </section>

        <aside className="rounded-3xl border border-slate-200/60 bg-white dark:border-slate-700 dark:bg-slate-900/90 p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-xl dark:shadow-slate-950/20 h-fit">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Sources</h2>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">Review the documents referenced for the most recent answer.</p>
            </div>
            <button
              onClick={() => setIsSourceOpen((open) => !open)}
              className="rounded-full border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800 px-3 py-2 text-xs text-slate-600 dark:text-slate-300 transition hover:bg-slate-100 dark:hover:border-slate-500 dark:hover:bg-slate-700"
              type="button"
            >
              {isSourceOpen ? 'Hide' : 'Show'}
            </button>
          </div>

          {isSourceOpen && (
            <div className="mt-5 space-y-4">
              {sources.length === 0 ? (
                <div className="rounded-3xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/80 p-4 text-sm text-slate-500 dark:text-slate-400">
                  No source citations yet. Ask a question to see referenced curriculum documents.
                </div>
              ) : (
                <ul className="space-y-3">
                  {sources.map((source) => (
                    <li key={source.id ?? source.title ?? source.url} className="rounded-3xl border border-slate-200/80 bg-slate-50/50 dark:border-slate-800 dark:bg-slate-950/80 p-4 shadow-sm shadow-slate-200/20 dark:shadow-none">
                      <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{source.title || 'Source document'}</p>
                      {source.snippet && <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{source.snippet}</p>}
                      {source.url && (
                        <a href={source.url} target="_blank" rel="noreferrer" className="mt-3 inline-flex text-sm text-sky-600 dark:text-sky-300 hover:text-sky-500 dark:hover:text-sky-200">
                          View document
                        </a>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}

export default ChatInterface;
