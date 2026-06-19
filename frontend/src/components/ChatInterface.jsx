import { useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiService } from '../api/apiService';
import { useAuth } from '../context/AuthContext';
const formatTime = () => new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

const scoreColorClass = (value) => {
  if (value > 80) return 'bg-emerald-500';
  if (value >= 60) return 'bg-amber-400';
  return 'bg-rose-500';
};

function ChatInterface() {
  const { user } = useAuth();
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

  const mutation = useMutation(
    async (question) => {
      const response = await apiService.sendMessage(
        user?.learner_id || 'anonymous',
        'session_default',
        question,
        null // Removed forced session type, let Supervisor decide
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

        if (data.context_summary) {
           setSources([{ title: 'Context Summary', snippet: data.context_summary }]);
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

    setInput('');
    mutation.mutate(question);
  };

  const handleClear = () => {
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
      <header className="rounded-3xl border border-slate-700 p-6 shadow-xl shadow-slate-950/20 backdrop-blur bg-gradient-to-br from-sky-800 via-sky-900 to-slate-950">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-200/80">FluentTech</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white sm:text-4xl">Interactive Curriculum Chat</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-300 sm:text-base">
              Ask questions about the EdTech curriculum, language learning modules, and lesson content. The assistant retrieves answers from your knowledge base and shows source citations.
            </p>
          </div>
          <button
            onClick={handleClear}
            className="inline-flex items-center justify-center rounded-2xl border border-white/10 bg-white/10 px-4 py-2 text-sm font-medium text-white transition hover:border-white/20 hover:bg-white/15"
            type="button"
          >
            Clear chat
          </button>
        </div>
      </header>

      <main className="grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
        <section className="rounded-3xl border border-slate-700 bg-slate-900/90 p-6 shadow-xl shadow-slate-950/20">
          <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-white">Conversation</h2>
              <p className="mt-1 text-sm text-slate-400">The assistant will intelligently adapt to your learning needs.</p>
            </div>
            <div className="inline-flex items-center gap-2 rounded-2xl bg-slate-800 px-3 py-2 text-xs text-slate-300">
              <span className="h-2.5 w-2.5 rounded-full bg-sky-500"></span>
              {mutation.isLoading ? 'Typing...' : 'Ready to ask'}
            </div>
          </div>

          <div className="mb-4 max-h-[60vh] overflow-y-auto rounded-3xl border border-slate-800 bg-slate-950/70 p-4 text-sm shadow-inner shadow-slate-950/40 message-scroll">
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex flex-col gap-3 rounded-3xl p-4 shadow-sm ${
                    message.role === 'assistant'
                      ? 'items-start bg-slate-800 text-slate-100'
                      : 'items-end self-end bg-[#7C3AED] text-white'
                  }`}
                >
                  <div className="flex w-full flex-col gap-2">
                    <span className="text-xs uppercase tracking-[0.24em] text-slate-400">
                      {message.role === 'assistant' ? 'FluentTech Assistant' : 'You'}
                    </span>
                    <p className="whitespace-pre-wrap text-sm leading-6">{message.text}</p>
                  </div>
                  <div className="flex w-full items-center justify-between gap-4 text-[11px] text-slate-400">
                    <span>{message.role === 'assistant' ? 'Assistant' : 'User'}</span>
                    <span>{message.timestamp}</span>
                  </div>

                  {message.role === 'assistant' && message.scores && (
                    <div className="space-y-3 rounded-3xl border border-slate-700 bg-slate-950/80 p-4">
                      <p className="text-sm font-semibold text-slate-100">Feedback scores</p>
                      {Object.entries(message.scores).map(([label, value]) => (
                        <div key={label} className="space-y-2">
                          <div className="flex items-center justify-between text-xs text-slate-400">
                            <span>{label.charAt(0).toUpperCase() + label.slice(1)}</span>
                            <span>{value}%</span>
                          </div>
                          <div className="h-2.5 overflow-hidden rounded-full bg-slate-800">
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
              <div className="mt-4 flex items-center justify-center rounded-3xl bg-slate-800 px-4 py-3 text-sm text-slate-200">
                <div className="flex items-center gap-2">
                  <span>FluentTech is typing</span>
                  <span className="flex items-center gap-1">
                    <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-white/80"></span>
                    <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-white/60 delay-150"></span>
                    <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-white/40 delay-300"></span>
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
              className="w-full resize-none rounded-3xl border border-slate-700 bg-slate-950/90 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20"
            />
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-xs text-slate-500 sm:text-sm">Press Enter to submit or use the button below.</p>
              <button
                type="submit"
                disabled={mutation.isLoading || !input.trim()}
                className="inline-flex items-center justify-center rounded-3xl bg-sky-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-600"
              >
                {mutation.isLoading ? 'Sending…' : 'Send question'}
              </button>
            </div>
          </form>
        </section>

        <aside className="rounded-3xl border border-slate-700 bg-slate-900/90 p-6 shadow-xl shadow-slate-950/20">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-white">Sources</h2>
              <p className="mt-1 text-sm text-slate-400">Review the documents referenced for the most recent answer.</p>
            </div>
            <button
              onClick={() => setIsSourceOpen((open) => !open)}
              className="rounded-full border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-slate-300 transition hover:border-slate-500 hover:bg-slate-700"
              type="button"
            >
              {isSourceOpen ? 'Hide' : 'Show'}
            </button>
          </div>

          {isSourceOpen && (
            <div className="mt-5 space-y-4">
              {sources.length === 0 ? (
                <div className="rounded-3xl border border-slate-800 bg-slate-950/80 p-4 text-sm text-slate-400">
                  No source citations yet. Ask a question to see referenced curriculum documents.
                </div>
              ) : (
                <ul className="space-y-3">
                  {sources.map((source) => (
                    <li key={source.id ?? source.title ?? source.url} className="rounded-3xl border border-slate-800 bg-slate-950/80 p-4">
                      <p className="text-sm font-semibold text-slate-100">{source.title || 'Source document'}</p>
                      {source.snippet && <p className="mt-2 text-sm text-slate-300">{source.snippet}</p>}
                      {source.url && (
                        <a href={source.url} target="_blank" rel="noreferrer" className="mt-3 inline-flex text-sm text-sky-300 hover:text-sky-200">
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
