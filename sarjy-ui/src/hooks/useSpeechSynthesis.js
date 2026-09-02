import { useCallback, useEffect, useRef, useState } from 'react';

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
  // Bumped by `cancel`. A cancelled utterance still fires `onend`, and Chrome
  // can still report `speechSynthesis.speaking` as true for a tick afterwards,
  // which flips `speaking` back on right after a barge-in. Handlers from an
  // older generation are ignored.
  const generationRef = useRef(0);

  // Whole-reply speech: cancels whatever is in flight first. Unused while the UI
  // streams every reply through `speakChunk`; kept as the non-streamed path's
  // counterpart, alongside `sendMessage` in api.js.
  const speak = useCallback((text, { onStart } = {}) => {
    if (!supported || !text) return;
    window.speechSynthesis.cancel();
    const generation = generationRef.current;
    const utterance = utteranceFor(text);
    utterance.onstart = () => {
      if (generation !== generationRef.current) return;
      setSpeaking(true);
      onStart?.();
    };
    utterance.onend = () => {
      if (generation !== generationRef.current) return;
      setSpeaking(false);
    };
    window.speechSynthesis.speak(utterance);
  }, []);

  // Streamed speech: each sentence is appended to the queue the browser
  // already holds, so playback is continuous while tokens are still arriving.
  const speakChunk = useCallback((text, { onStart } = {}) => {
    if (!supported || !text.trim()) return;
    const generation = generationRef.current;
    const utterance = utteranceFor(text);
    utterance.onstart = () => {
      if (generation !== generationRef.current) return;
      setSpeaking(true);
      if (!startedRef.current) {
        startedRef.current = true;
        onStart?.();
      }
    };
    utterance.onend = () => {
      if (generation !== generationRef.current) return;
      setSpeaking(window.speechSynthesis.speaking);
    };
    window.speechSynthesis.speak(utterance);
  }, []);

  const beginTurn = useCallback(() => {
    startedRef.current = false;
  }, []);

  const warmedRef = useRef(false);

  // Chrome populates the voice list asynchronously, and the first utterance
  // pays for it. Called at page load and again on the first user gesture,
  // since autoplay policy blocks synthesis before one.
  const warm = useCallback(() => {
    if (!supported || warmedRef.current) return;
    window.speechSynthesis.getVoices();
    const silent = new SpeechSynthesisUtterance(' ');
    silent.volume = 0;
    silent.onend = () => {
      warmedRef.current = true;
    };
    window.speechSynthesis.speak(silent);
  }, []);

  const cancel = useCallback(() => {
    if (!supported) return;
    generationRef.current += 1;
    window.speechSynthesis.cancel();
    setSpeaking(false);
  }, []);

  // Synthesis is a browser-level queue, not a component-level one: without this
  // the browser keeps talking after the app is gone.
  useEffect(
    () => () => {
      if (supported) window.speechSynthesis.cancel();
    },
    []
  );

  return { speak, speakChunk, beginTurn, warm, cancel, speaking, supported };
}
