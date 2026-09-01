import { useCallback, useRef, useState } from 'react';

const supported = typeof window !== 'undefined' && 'speechSynthesis' in window;

const ARABIC_SCRIPT = /[؀-ۿ]/;

function utteranceFor(text) {
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = ARABIC_SCRIPT.test(text) ? 'ar-SA' : 'en-US';
  return utterance;
}

export function useSpeechSynthesis() {
  const [speaking, setSpeaking] = useState(false);
  const startedRef = useRef(false);

  // Whole-reply speech: cancels whatever is in flight first.
  const speak = useCallback((text, { onStart } = {}) => {
    if (!supported || !text) return;
    window.speechSynthesis.cancel();
    const utterance = utteranceFor(text);
    utterance.onstart = () => {
      setSpeaking(true);
      onStart?.();
    };
    utterance.onend = () => setSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }, []);

  // Streamed speech: each sentence is appended to the queue the browser
  // already holds, so playback is continuous while tokens are still arriving.
  const speakChunk = useCallback((text, { onStart } = {}) => {
    if (!supported || !text.trim()) return;
    const utterance = utteranceFor(text);
    utterance.onstart = () => {
      setSpeaking(true);
      if (!startedRef.current) {
        startedRef.current = true;
        onStart?.();
      }
    };
    utterance.onend = () => setSpeaking(window.speechSynthesis.speaking);
    window.speechSynthesis.speak(utterance);
  }, []);

  const beginTurn = useCallback(() => {
    startedRef.current = false;
  }, []);

  const cancel = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    setSpeaking(false);
  }, []);

  return { speak, speakChunk, beginTurn, cancel, speaking, supported };
}
