import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, Send, Brain, Shield, RefreshCw, MessageSquare, ArrowRight, ExternalLink } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { api } from '../services/api';

interface Message {
  id: string;
  role: 'user' | 'model';
  text: string;
  timestamp: Date;
  sources?: { title: string; uri: string }[];
}

export default function AIChatbot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome-msg',
      role: 'model',
      text: `Hello! I am **ArogyaMitra**, your intelligent Agentic Clinical Assistant. 

I am securely synced with your local clinical data repository. I can help you with:
- **Biomarker Explanations**: Ask me about HbA1c, lipids, blood pressure, and what they mean.
- **Risk Analysis**: I can analyze your latest computed health risk score and suggest targeted lifestyle changes.
- **Medication Schedulers**: Check on your active reminder regimens and safety guides.
- **General Wellness Grounding**: Ask general medical questions to retrieve verified literature using real-time Google search grounding.

How can I assist you with your health logs today?`,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedPrompts = [
    { text: 'Analyze my cardiovascular risks', query: 'What is my current clinical risk score status and what factors are contributing to it?' },
    { text: 'Summarize my latest lab parameters', query: 'Can you summarize all my latest extracted bio-marker parameters and their status?' },
    { text: 'Check my medication reminders', query: 'Do I have any medication or scheduling reminders? Give me active guidelines.' },
    { text: 'Explain HbA1c and normal ranges', query: 'What is HbA1c, what are the normal reference ranges, and how is it managed?' }
  ];

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend: string) => {
    if (!textToSend.trim() || isLoading) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      text: textToSend,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      // Map conversation history to the format server expects
      const historyToSend = messages.map(m => ({
        role: m.role,
        text: m.text
      }));

      const response = await api.sendChatMessage(textToSend, historyToSend);

      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: 'model',
        text: response.text,
        timestamp: new Date(),
        sources: response.sources
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        id: crypto.randomUUID(),
        role: 'model',
        text: `I'm sorry, I encountered an issue connecting with the clinical reasoning server. Please verify your connection or refresh. \n\n*(Error detail: ${err.message || 'Network Timeout'})*`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetChat = () => {
    if (confirm('Are you sure you want to clear this active clinical chat session history?')) {
      setMessages([
        {
          id: 'welcome-reset',
          role: 'model',
          text: `Session reset successfully. I am ready for new inquiries. How can I assist you with your health logs today?`,
          timestamp: new Date()
        }
      ]);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)] min-h-[500px] bg-white rounded-2xl border border-gray-150 overflow-hidden shadow-sm" id="ai-companion-root">
      
      {/* Companion Header */}
      <div className="px-6 py-4 border-b border-gray-150 bg-gray-50/50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-teal-50 flex items-center justify-center text-teal-700">
            <Brain className="w-5 h-5 text-teal-600" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-gray-800 flex items-center gap-2 font-serif">
              ArogyaMitra AI Companion
              <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-teal-100 text-teal-800 uppercase tracking-wider">
                Agentic
              </span>
            </h3>
            <p className="text-[10px] text-gray-500 font-medium">Secured, context-aware physician-patient dialogue partner</p>
          </div>
        </div>

        <button
          onClick={handleResetChat}
          className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition"
          title="Reset conversation"
          id="btn-reset-chat"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Main Conversation Log & Helper Panels */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Messages Stage */}
        <div className="flex-1 flex flex-col justify-between overflow-y-auto p-6 bg-gray-50/20">
          
          <div className="space-y-6 flex-1">
            {messages.map((msg) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={msg.id}
                  className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
                  id={`chat-msg-${msg.id}`}
                >
                  <div className={`max-w-[85%] rounded-2xl px-5 py-4 ${
                    isUser 
                      ? 'bg-teal-700 text-white rounded-tr-none shadow-sm' 
                      : 'bg-white text-gray-800 border border-gray-150 rounded-tl-none shadow-sm'
                  }`}>
                    
                    {/* Role header */}
                    <div className="flex items-center gap-2 mb-2 text-[10px] font-bold uppercase tracking-wider opacity-75">
                      {isUser ? (
                        <span>You (Patient)</span>
                      ) : (
                        <span className="text-teal-700 flex items-center gap-1">
                          <Sparkles className="w-3 h-3 text-teal-600" /> ArogyaMitra AI
                        </span>
                      )}
                      <span>•</span>
                      <span>{msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>

                    {/* Markdown Text Body */}
                    <div className={`text-xs leading-relaxed font-sans ${isUser ? 'prose-invert text-white' : 'prose text-gray-800'} break-words markdown-body`}>
                      <ReactMarkdown>{msg.text}</ReactMarkdown>
                    </div>

                    {/* Citations/Grounding Sources */}
                    {!isUser && msg.sources && msg.sources.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-gray-100">
                        <span className="text-[9px] font-bold text-gray-400 uppercase tracking-wider block mb-1.5">
                          Verified Medical Citations
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {msg.sources.map((src, idx) => (
                            <a
                              key={idx}
                              href={src.uri}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-teal-50 hover:bg-teal-100 text-teal-800 text-[10px] font-bold transition border border-teal-100 shadow-sm"
                            >
                              <ExternalLink className="w-3 h-3 shrink-0 text-teal-600" />
                              <span className="truncate max-w-[150px]">{src.title}</span>
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                  </div>
                </div>
              );
            })}

            {isLoading && (
              <div className="flex justify-start" id="chat-loading-indicator">
                <div className="bg-white border border-gray-150 rounded-2xl rounded-tl-none px-5 py-4 shadow-sm flex items-center gap-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-teal-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-teal-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-teal-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <span className="text-[11px] font-bold text-gray-500 font-sans">ArogyaMitra is synthesizing health telemetry...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick-Action Panel at Bottom */}
          {messages.length <= 2 && (
            <div className="mt-6 border-t border-gray-150 pt-5">
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-3">
                Suggested Agentic Inquiries
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {suggestedPrompts.map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(p.query)}
                    className="flex items-center justify-between text-left px-4 py-3 bg-white hover:bg-teal-50/30 border border-gray-150 hover:border-teal-200 rounded-xl transition text-xs font-semibold text-gray-700 shadow-xs"
                    id={`suggested-prompt-${idx}`}
                  >
                    <span className="truncate pr-2">{p.text}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          )}

        </div>

      </div>

      {/* Input Stage */}
      <div className="px-6 py-4 border-t border-gray-150 bg-white">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage(input);
          }}
          className="flex gap-3"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            placeholder="Ask ArogyaMitra about your biometric parameters, reminders, or health risk trends..."
            className="flex-1 px-4 py-3 bg-gray-50 hover:bg-gray-50/50 border border-gray-200 rounded-xl text-xs font-semibold text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 transition disabled:opacity-50"
            id="chat-input-field"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-5 py-3 bg-teal-700 hover:bg-teal-800 disabled:bg-gray-100 disabled:text-gray-400 text-white rounded-xl text-xs font-bold transition flex items-center gap-2 shadow-sm"
            id="chat-send-button"
          >
            <Send className="w-3.5 h-3.5" />
            Send Inquiry
          </button>
        </form>

        <div className="flex items-center justify-between mt-3 px-1">
          <span className="text-[9px] text-gray-400 font-medium flex items-center gap-1.5">
            <Shield className="w-3 h-3 text-teal-600" /> Local database encrypted. Advice is informational only.
          </span>
          <span className="text-[9px] text-gray-400 font-medium font-mono">
            Model: gemini-3.6-flash
          </span>
        </div>
      </div>

    </div>
  );
}
