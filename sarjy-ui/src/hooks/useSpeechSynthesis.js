const supported = typeof window !== 'undefined' && 'speechSynthesis' in window;

const ARABIC_SCRIPT = /[؀-ۿ]/;

export function useSpeechSynthesis() {
  const speak = (text) => {
    if (!supported || !text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = ARABIC_SCRIPT.test(text) ? 'ar-SA' : 'en-US';
    window.speechSynthesis.speak(utterance);
  };

  const cancel = () => {
    if (!supported) return;
    window.speechSynthesis.cancel();
  };

  return { speak, cancel, supported };
}
