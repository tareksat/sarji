import { useEffect, useRef, useState } from 'react';

const SpeechRecognitionImpl =
  typeof window !== 'undefined'
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null;

export function useSpeechRecognition(onResult, { onSpeechEnd } = {}) {
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);
  const onResultRef = useRef(onResult);
  const onSpeechEndRef = useRef(onSpeechEnd);
  onResultRef.current = onResult;
  onSpeechEndRef.current = onSpeechEnd;

  useEffect(() => {
    if (!SpeechRecognitionImpl) return;

    const recognition = new SpeechRecognitionImpl();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      const transcript = event.results[event.results.length - 1][0].transcript.trim();
      if (transcript) onResultRef.current(transcript);
    };
    // The mark that exposes the STT tail: the dead air between the user
    // stopping and the transcript arriving.
    recognition.onspeechend = () => onSpeechEndRef.current?.();
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);

    recognitionRef.current = recognition;
    return () => recognition.abort();
  }, []);

  const start = () => {
    if (!recognitionRef.current || listening) return;
    setListening(true);
    recognitionRef.current.start();
  };

  const stop = () => {
    if (!recognitionRef.current) return;
    recognitionRef.current.stop();
    setListening(false);
  };

  return {
    supported: !!SpeechRecognitionImpl,
    listening,
    start,
    stop,
  };
}
