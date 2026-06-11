import React, { useState, useRef, useEffect } from "react";

const MOCK_MESSAGES = [
  {
    id: 1,
    role: "user",
    content: "Tell me about yourself and your experience in software engineering.",
    timestamp: new Date(Date.now() - 5 * 60000),
  },
  {
    id: 2,
    role: "agent",
    content:
      "I am a software engineer with 5 years of experience in full-stack development. I have worked on cloud-based applications, microservices, and frontend frameworks like React. My main focus has been building scalable systems and improving user experience.",
    timestamp: new Date(Date.now() - 4.5 * 60000),
    scores: {
      grammar: 92,
      vocabulary: 85,
      fluency: 88,
      tone: 90,
    },
  },
  {
    id: 3,
    role: "user",
    content: "What is your biggest professional achievement?",
    timestamp: new Date(Date.now() - 4 * 60000),
  },
  {
    id: 4,
    role: "agent",
    content:
      "One achievement I am proud of is leading the migration of a legacy system to a modern microservices architecture. This reduced system downtime by 60% and improved deployment speed significantly. The project required strong communication with stakeholders and cross-functional teams.",
    timestamp: new Date(Date.now() - 3 * 60000),
  },
  {
    id: 5,
    role: "user",
    content: "Tell me about a challenge you overcame.",
    timestamp: new Date(Date.now() - 2.5 * 60000),
  },
  {
    id: 6,
    role: "agent",
    content:
      "I faced a major challenge when debugging a production issue that affected thousands of users. The problem was not obvious from the logs. I worked systematically through the code, collaborated with team members, and implemented a solution within 4 hours. This experience reinforced the importance of careful analysis and teamwork.",
    timestamp: new Date(Date.now() - 2 * 60000),
    scores: {
      grammar: 88,
      vocabulary: 82,
      fluency: 85,
      tone: 87,
    },
  },
  {
    id: 7,
    role: "user",
    content: "Why do you want to join our company?",
    timestamp: new Date(Date.now() - 1 * 60000),
  },
  {
    id: 8,
    role: "agent",
    content:
      "I am interested in joining your company because of your innovative approach to cloud infrastructure and commitment to engineering excellence. I have followed your recent projects and I believe my experience aligns well with your team's goals. I am excited about the opportunity to contribute to impactful work.",
    timestamp: new Date(Date.now() - 30000),
  },
];

const SESSION_TYPES = [
  { key: "conversation", label: "Conversation", color: "bg-blue-500" },
  { key: "roleplay", label: "Roleplay", color: "bg-purple-500" },
  { key: "feedback", label: "Feedback", color: "bg-green-500" },
];

const ScoreBadge = ({ label, score }) => {
  let bgColor = "bg-red-100";
  let textColor = "text-red-700";
  let fillColor = "bg-red-500";

  if (score >= 80) {
    bgColor = "bg-green-100";
    textColor = "text-green-700";
    fillColor = "bg-green-500";
  } else if (score >= 60) {
    bgColor = "bg-yellow-100";
    textColor = "text-yellow-700";
    fillColor = "bg-yellow-500";
  }

  return (
    <div className="mb-2">
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className={`text-xs font-semibold ${textColor}`}>{score}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all ${fillColor}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
};

const TypingIndicator = () => (
  <style>{`
    @keyframes dot-pulse {
      0%, 60%, 100% { opacity: 0.3; }
      30% { opacity: 1; }
    }
    .dot-pulse-1 { animation: dot-pulse 1.4s infinite; }
    .dot-pulse-2 { animation: dot-pulse 1.4s infinite 0.2s; }
    .dot-pulse-3 { animation: dot-pulse 1.4s infinite 0.4s; }
  `}</style>
);

export default function ChatInterface({
  onSendMessage = () => {},
  messages = MOCK_MESSAGES,
  isLoading = false,
  sessionType = "roleplay",
  onSessionTypeChange = () => {},
}) {
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = () => {
    if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  const currentSession = SESSION_TYPES.find((s) => s.key === sessionType);
  const headerColor = currentSession?.color || "bg-blue-500";

  return (
    <div className="flex flex-col h-screen bg-white">
      <TypingIndicator />

      {/* Header */}
      <div className={`${headerColor} text-white p-4 shadow-md`}>
        <h1 className="text-2xl font-bold">FluentTech AI Coach</h1>
        <p className="text-sm opacity-90">
          {sessionType === "conversation" && "Improve your English conversational skills"}
          {sessionType === "roleplay" && "Practice interview scenarios and real-world dialogues"}
          {sessionType === "feedback" && "Receive detailed feedback on your English proficiency"}
        </p>
      </div>

      {/* Session Type Tabs */}
      <div className="flex border-b border-gray-200 bg-gray-50">
        {SESSION_TYPES.map((type) => (
          <button
            key={type.key}
            onClick={() => onSessionTypeChange(type.key)}
            className={`flex-1 py-3 px-4 text-center font-medium transition-colors ${
              sessionType === type.key
                ? `${type.color} text-white`
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            }`}
          >
            {type.label}
          </button>
        ))}
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-md lg:max-w-lg ${
                msg.role === "user"
                  ? "bg-purple-600 text-white rounded-lg rounded-tr-none"
                  : "bg-gray-200 text-gray-900 rounded-lg rounded-tl-none"
              } p-4 shadow-sm`}
            >
              <p className="text-sm leading-relaxed">{msg.content}</p>
              <div className={`text-xs mt-2 ${msg.role === "user" ? "text-purple-100" : "text-gray-500"}`}>
                {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </div>

              {/* Feedback Scores */}
              {msg.scores && (
                <div className={`mt-3 pt-3 border-t ${msg.role === "user" ? "border-purple-500" : "border-gray-300"}`}>
                  <ScoreBadge label="Grammar" score={msg.scores.grammar} />
                  <ScoreBadge label="Vocabulary" score={msg.scores.vocabulary} />
                  <ScoreBadge label="Fluency" score={msg.scores.fluency} />
                  <ScoreBadge label="Tone" score={msg.scores.tone} />
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Typing Indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 text-gray-900 rounded-lg rounded-tl-none p-4 shadow-sm">
              <div className="flex space-x-1">
                <span className="w-2 h-2 bg-gray-500 rounded-full dot-pulse-1" />
                <span className="w-2 h-2 bg-gray-500 rounded-full dot-pulse-2" />
                <span className="w-2 h-2 bg-gray-500 rounded-full dot-pulse-3" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white p-4">
        <div className="flex gap-3">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message here... (Shift+Enter for newline)"
            className="flex-1 border border-gray-300 rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent max-h-32"
            rows="1"
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !inputValue.trim()}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-semibold py-2 px-6 rounded-lg transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
