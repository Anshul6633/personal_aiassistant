/**
 * Comprehensive Browser Voice Input Hook for JARVIS.
 * 
 * Supports:
 * 1. Web Speech API (instant real-time continuous dictation on Chromium / Edge).
 * 2. MediaRecorder fallback -> local faster-whisper STT endpoint (/api/voice/transcribe).
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { api } from './api';

interface UseVoiceInputOptions {
  onFinalTranscript?: (text: string) => void;
  lang?: string;
}

export function useVoiceInput({ onFinalTranscript, lang = 'en-US' }: UseVoiceInputOptions = {}) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Check Web Speech API availability
  const hasWebSpeech = typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window);

  const startWebSpeech = useCallback(() => {
    try {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = lang;

      recognition.onstart = () => {
        setIsListening(true);
        setError(null);
        setInterimTranscript('');
      };

      recognition.onresult = (event: any) => {
        let currentInterim = '';
        let finalStr = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalStr += event.results[i][0].transcript;
          } else {
            currentInterim += event.results[i][0].transcript;
          }
        }

        if (finalStr) {
          setTranscript(finalStr);
          if (onFinalTranscript) onFinalTranscript(finalStr);
        }
        setInterimTranscript(currentInterim);
      };

      recognition.onerror = (e: any) => {
        console.warn('SpeechRecognition error:', e.error);
        if (e.error !== 'no-speech') {
          setError(`Voice input notice: ${e.error}`);
        }
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
        setInterimTranscript('');
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (e: any) {
      console.warn('Could not start Web Speech, falling back to MediaRecorder:', e);
      startMediaRecorder();
    }
  }, [lang, onFinalTranscript]);

  const startMediaRecorder = useCallback(async () => {
    try {
      audioChunksRef.current = [];
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        setIsListening(false);
        setIsProcessing(true);
        try {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const res = await api.transcribeAudio(audioBlob, 'browser_mic.webm');
          if (res.text) {
            setTranscript(res.text);
            if (onFinalTranscript) onFinalTranscript(res.text);
          }
        } catch (err: any) {
          setError('Whisper STT transcription failed');
        } finally {
          setIsProcessing(false);
          stream.getTracks().forEach((track) => track.stop());
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsListening(true);
      setError(null);
    } catch (err: any) {
      setError('Microphone permission denied or device not found.');
      setIsListening(false);
    }
  }, [onFinalTranscript]);

  const startListening = useCallback(() => {
    if (hasWebSpeech) {
      startWebSpeech();
    } else {
      startMediaRecorder();
    }
  }, [hasWebSpeech, startWebSpeech, startMediaRecorder]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {}
    }
    setIsListening(false);
  }, []);

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  return {
    isListening,
    isProcessing,
    transcript,
    interimTranscript,
    error,
    startListening,
    stopListening,
    toggleListening,
    hasWebSpeech,
  };
}

