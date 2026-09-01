import { useEffect, useRef, useState } from 'react';

const SpeechRecognitionImpl =
  typeof window !== 'undefined'
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null;

// How long to wait after speech ends for the engine's own final result before
// falling back to the last interim transcript.
const INTERIM_FALLBACK_MS = 400;

export function useSpeechRecognition(onResult, { onSpeechEnd } = {}) {
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);
  const interimTimeoutRef = useRef(null);
  const onResultRef = useRef(onResult);
  const onSpeechEndRef = useRef(onSpeechEnd);
  onResultRef.current = onResult;
  onSpeechEndRef.current = onSpeechEnd;

  useEffect(() => {
    if (!SpeechRecognitionImpl) return;

    const recognition = new SpeechRecognitionImpl();
    recognition.continuous = false;
    // Interim results give a transcript to fall back on the moment speech ends,
    // instead of waiting out the engine's silence timeout.
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    let interim = '';
    let sent = false;

    const send = (transcript) => {
      const text = transcript.trim();
      if (sent || !text) return;
      sent = true;
      onResultRef.current(text);
    };

    recognition.onresult = (event) => {
      let final = '';
      interim = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        if (result.isFinal) final += result[0].transcript;
        else interim += result[0].transcript;
      }
      if (final) send(final);
    };

    recognition.onspeechend = () => {
      onSpeechEndRef.current?.();
      // Forces the engine to finalize now rather than after its own silence
      // timeout. The final result usually still arrives and wins the race; the
      // interim is the floor, not the plan.
      recognition.stop();
      interimTimeoutRef.current = window.setTimeout(() => send(interim), INTERIM_FALLBACK_MS);
    };

    recognition.onend = () => {
      window.clearTimeout(interimTimeoutRef.current);
      if (!sent) send(interim);
      sent = false;
      interim = '';
      setListening(false);
    };
    recognition.onerror = () => setListening(false);

    recognitionRef.current = recognition;
    return () => {
      window.clearTimeout(interimTimeoutRef.current);
      recognition.abort();
    };
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
