import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Volume2, VolumeX, Sparkles, Languages, Mic, MicOff, Square, Radio, ThumbsUp, ThumbsDown, CheckCircle2, MessageSquarePlus } from 'lucide-react';
import { api } from '../services/api';
import { useVoiceInput } from '../services/voice';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  audioUrl?: string;
  timestamp: string;
}

export const TalkToJarvis: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'init-1',
      role: 'assistant',
      text: "Good day, Boss! I'm online and standing by. What are we creating or automating today?",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [autoPlayAudio, setAutoPlayAudio] = useState(true);
  const [selectedLanguage, setSelectedLanguage] = useState<'en-US' | 'hi-IN'>('en-US');
  const [feedbackState, setFeedbackState] = useState<Record<string, { type: 'positive' | 'negative' | 'correction'; text?: string }>>({});
  const [correctionTargetId, setCorrectionTargetId] = useState<string | null>(null);
  const [correctionInput, setCorrectionInput] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  const handleThumbsUp = async (msgId: string, replyText: string) => {
    setFeedbackState(prev => ({ ...prev, [msgId]: { type: 'positive' } }));
    try {
      await api.submitRLHFFeedback({
        context_type: 'chat_response',
        prompt_or_input: 'Conversation dialogue',
        action_or_output: replyText,
        feedback_type: 'positive',
        category: 'persona'
      });
    } catch (e) {
      console.error('Failed to submit RLHF feedback:', e);
    }
  };

  const handleStartCorrection = (msgId: string) => {
    setCorrectionTargetId(msgId);
    setCorrectionInput('');
  };

  const handleSubmitCorrection = async (msgId: string, replyText: string) => {
    if (!correctionInput.trim()) {
      setCorrectionTargetId(null);
      return;
    }
    const corr = correctionInput.trim();
    setFeedbackState(prev => ({ ...prev, [msgId]: { type: 'correction', text: corr } }));
    setCorrectionTargetId(null);
    try {
      await api.submitRLHFFeedback({
        context_type: 'chat_response',
        prompt_or_input: 'Conversation dialogue',
        action_or_output: replyText,
        feedback_type: 'correction',
        user_correction: corr,
        category: 'persona'
      });
    } catch (e) {
      console.error('Failed to submit RLHF correction:', e);
    }
  };

  // Setup Voice Input (Web Speech API + local faster-whisper fallback)
  const {
    isListening,
    isProcessing: isTranscribing,
    interimTranscript,
    toggleListening,
    stopListening
  } = useVoiceInput({
    lang: selectedLanguage,
    onFinalTranscript: (finalText) => {
      if (finalText && finalText.trim()) {
        setInput(finalText);
        handleSendMessage(finalText);
      }
    }
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleInterrupt = () => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current.currentTime = 0;
    }
    setIsPlayingAudio(false);
    api.stopVoice();
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim() || isSending) return;

    if (isListening) {
      stopListening();
    }

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setIsSending(true);

    try {
      let res;
      try {
        res = await api.sendChat(text);
      } catch (firstErr) {
        console.warn('Initial chat attempt failed, retrying in 1s...', firstErr);
        await new Promise((resolve) => setTimeout(resolve, 1000));
        res = await api.sendChat(text);
      }

      const assistantMsg: Message = {
        id: `a-${Date.now()}`,
        role: 'assistant',
        text: res.reply,
        audioUrl: res.audio_url,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Play audio response automatically if enabled
      if (autoPlayAudio && res.audio_url) {
        if (audioPlayerRef.current) {
          audioPlayerRef.current.src = res.audio_url;
          audioPlayerRef.current.onplay = () => setIsPlayingAudio(true);
          audioPlayerRef.current.onended = () => setIsPlayingAudio(false);
          audioPlayerRef.current.onerror = () => setIsPlayingAudio(false);
          audioPlayerRef.current.play().catch((err) => {
            console.log('Audio autoplay prevented by browser policy (audio also played on PC speakers):', err);
            setIsPlayingAudio(false);
          });
        }
      }
    } catch (err: any) {
      console.error('Chat error:', err);
      const errorMsg: Message = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        text: `I'm here, Boss! The neural core is syncing (${err?.message || 'Connecting to port 8000'}). Please give me another command and I will execute it right away!`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
    }
  };

  const playAudio = (url: string) => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.src = url;
      audioPlayerRef.current.onplay = () => setIsPlayingAudio(true);
      audioPlayerRef.current.onended = () => setIsPlayingAudio(false);
      audioPlayerRef.current.play();
    }
  };

  const suggestions = [
    "Hey Jarvis! Let's make some reels.",
    "Jarvis, scan my videos and find podcast clips.",
    "What are some viral tech hook ideas today?",
    "Check my CPU, RAM and GPU status.",
    "Kaise ho Jarvis? Aaj kuch interesting banate hain!"
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] max-w-4xl mx-auto rounded-2xl bg-slate-950/70 border border-cyan-500/20 backdrop-blur-xl overflow-hidden shadow-cyan-glow">
      {/* Hidden audio element for speech playback */}
      <audio ref={audioPlayerRef} className="hidden" />

      {/* Header */}
      <div className="px-6 py-4 border-b border-cyan-500/20 flex items-center justify-between bg-slate-900/60">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-cyan-500/20 border border-cyan-400 flex items-center justify-center shadow-cyan-sm">
            <Bot className="w-4 h-4 text-cyan-300" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">JARVIS Neural Voice Interface</h2>
            <p className="text-[11px] font-mono text-cyan-400/80">
              Voice-In (Whisper/Speech) • Voice-Out (Christopher / Madhur Neural)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Interrupt Speech Button if JARVIS is talking */}
          {isPlayingAudio && (
            <button
              onClick={handleInterrupt}
              className="px-2.5 py-1 rounded bg-red-600/30 hover:bg-red-600/50 border border-red-500 text-[11px] font-mono text-red-300 flex items-center gap-1.5 cursor-pointer animate-pulse"
              title="Interrupt speech (Barge-in)"
            >
              <Square className="w-3 h-3 fill-current" />
              <span>INTERRUPT</span>
            </button>
          )}

          {/* Language Switcher */}
          <button
            onClick={() => setSelectedLanguage(selectedLanguage === 'en-US' ? 'hi-IN' : 'en-US')}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-950 border border-cyan-500/30 hover:border-cyan-400 text-[11px] font-mono text-cyan-300 cursor-pointer transition-colors"
            title="Click to toggle English / Hindi voice recognition"
          >
            <Languages className="w-3.5 h-3.5" />
            <span>{selectedLanguage === 'en-US' ? 'English (US)' : 'Hindi / Hinglish'}</span>
          </button>

          {/* Autoplay Audio Toggle */}
          <button
            onClick={() => setAutoPlayAudio(!autoPlayAudio)}
            className={`p-2 rounded-lg border text-xs cursor-pointer transition-all ${
              autoPlayAudio
                ? 'bg-cyan-500/20 border-cyan-500 text-cyan-300 shadow-cyan-sm'
                : 'bg-slate-900 border-slate-700 text-slate-400'
            }`}
            title={autoPlayAudio ? 'Speech Audio Enabled (Voice Out Active)' : 'Speech Audio Muted'}
          >
            {autoPlayAudio ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Message Feed */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((m) => {
          const isUser = m.role === 'user';
          return (
            <div
              key={m.id}
              className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                  isUser
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-900 border border-cyan-500/40 text-cyan-400 shadow-cyan-sm'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  isUser
                    ? 'bg-blue-600/90 text-white rounded-tr-none'
                    : 'bg-slate-900/90 border border-cyan-500/25 text-slate-200 rounded-tl-none font-sans shadow-lg'
                }`}
              >
                <div className="whitespace-pre-wrap">{m.text}</div>

                {/* RLHF Inline Correction Box */}
                {!isUser && correctionTargetId === m.id && (
                  <div className="mt-2 p-2.5 rounded-xl bg-slate-950 border border-cyan-500/40 text-xs font-mono space-y-2">
                    <div className="text-[10px] text-cyan-400 font-bold flex items-center gap-1">
                      <Sparkles className="w-3 h-3" />
                      <span>TEACH JARVIS (RLHF +2.0 REWARD):</span>
                    </div>
                    <input
                      type="text"
                      value={correctionInput}
                      onChange={(e) => setCorrectionInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSubmitCorrection(m.id, m.text)}
                      placeholder="e.g. Always set visibility to Public, or keep replies under 15 words"
                      className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-400"
                      autoFocus
                    />
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setCorrectionTargetId(null)}
                        className="px-2 py-1 rounded text-[10px] text-slate-400 hover:text-slate-200"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleSubmitCorrection(m.id, m.text)}
                        className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-[10px]"
                      >
                        Save Policy Rule
                      </button>
                    </div>
                  </div>
                )}

                <div className="mt-2 pt-1 border-t border-slate-800/60 flex items-center justify-between gap-4 text-[10px] text-slate-400 font-mono">
                  <div className="flex items-center gap-2">
                    <span>{m.timestamp}</span>
                    {/* RLHF Feedback Buttons for Assistant */}
                    {!isUser && (
                      <div className="flex items-center gap-1.5 ml-2 border-l border-slate-700/60 pl-2">
                        {feedbackState[m.id]?.type === 'positive' ? (
                          <span className="text-emerald-400 font-bold flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>RLHF +1.0</span>
                          </span>
                        ) : feedbackState[m.id]?.type === 'correction' ? (
                          <span className="text-cyan-400 font-bold flex items-center gap-1">
                            <Sparkles className="w-3 h-3" />
                            <span>Rule Learned</span>
                          </span>
                        ) : (
                          <>
                            <button
                              onClick={() => handleThumbsUp(m.id, m.text)}
                              className="p-1 rounded hover:bg-emerald-950/60 text-slate-400 hover:text-emerald-400 transition-colors"
                              title="Reinforce good answer (+1.0 reward)"
                            >
                              <ThumbsUp className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => handleStartCorrection(m.id)}
                              className="p-1 rounded hover:bg-rose-950/60 text-slate-400 hover:text-rose-400 transition-colors flex items-center gap-1"
                              title="Correct JARVIS (Learns a new policy rule with +2.0 reward)"
                            >
                              <ThumbsDown className="w-3 h-3" />
                              <span className="text-[9px]">Correct</span>
                            </button>
                          </>
                        )}
                      </div>
                    )}
                  </div>

                  {m.audioUrl && (
                    <button
                      onClick={() => playAudio(m.audioUrl!)}
                      className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
                    >
                      <Volume2 className="w-3 h-3" />
                      <span>Replay</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {isSending && (
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 animate-pulse">
            <Sparkles className="w-3.5 h-3.5" />
            <span>JARVIS is formulating vocal response...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Live Voice Dictation Status Banner */}
      {(isListening || interimTranscript || isTranscribing) && (
        <div className="px-6 py-2.5 bg-gradient-to-r from-cyan-950/80 to-blue-950/80 border-t border-cyan-500/30 flex items-center justify-between text-xs font-mono text-cyan-300">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500" />
            </span>
            <span className="font-bold">
              {isTranscribing ? 'Processing Whisper audio...' : 'Listening to your voice...'}
            </span>
            {interimTranscript && (
              <span className="text-slate-300 italic truncate max-w-md">"{interimTranscript}"</span>
            )}
          </div>
          <button
            onClick={stopListening}
            className="px-2 py-0.5 rounded bg-cyan-500/20 hover:bg-cyan-500/40 text-[10px] text-cyan-200 border border-cyan-400 cursor-pointer"
          >
            Finish Speaking
          </button>
        </div>
      )}

      {/* Suggested Quick Directives */}
      <div className="px-6 py-2 border-t border-cyan-500/10 flex gap-2 overflow-x-auto text-xs font-mono no-scrollbar">
        {suggestions.map((s, idx) => (
          <button
            key={idx}
            onClick={() => handleSendMessage(s)}
            className="px-3 py-1 rounded-full bg-slate-900 border border-cyan-500/20 text-slate-300 hover:text-cyan-300 hover:border-cyan-400 whitespace-nowrap transition-colors cursor-pointer"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Input Field with Microphone Button */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
        className="p-4 border-t border-cyan-500/20 bg-slate-900/80 flex items-center gap-3"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            isListening
              ? "Listening to you speak (or click mic to cancel)..."
              : "Speak or type to JARVIS in English or Hindi..."
          }
          className="flex-1 bg-slate-950 border border-cyan-500/30 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 font-mono"
        />

        {/* Microphone Voice-In Trigger Button */}
        <button
          type="button"
          onClick={toggleListening}
          className={`p-2.5 rounded-xl border transition-all cursor-pointer shadow-cyan-sm flex items-center justify-center ${
            isListening
              ? 'bg-red-500/20 border-red-500 text-red-400 animate-pulse shadow-red-500/30'
              : 'bg-slate-950 hover:bg-cyan-500/20 border-cyan-500/40 text-cyan-300 hover:border-cyan-400'
          }`}
          title={isListening ? 'Listening (Click to stop)' : 'Click to Speak (Voice Input)'}
        >
          {isListening ? <Mic className="w-5 h-5 text-red-400" /> : <Mic className="w-5 h-5 text-cyan-400" />}
        </button>

        {/* Send Button */}
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          className="p-2.5 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold disabled:opacity-50 transition-all shadow-cyan-sm cursor-pointer"
          title="Send message"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  );
};

