const supported = typeof window !== 'undefined' && 'speechSynthesis' in window;

const ARABIC_SCRIPT = /[؀-ۿ]/;

export function useSpeechSynthesis() {
  const speak = (text, { onStart } = {}) => {
    if (!supported || !text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = ARABIC_SCRIPT.test(text) ? 'ar-SA' : 'en-US';
    // `onstart` fires when the utterance begins, which is the client-side
    // definition of time-to-first-audio.
    utterance.onstart = () => onStart?.();
    window.speechSynthesis.speak(utterance);
  };

  const cancel = () => {
    if (!supported) return;
    window.speechSynthesis.cancel();
  };

  return { speak, cancel, supported };
}
