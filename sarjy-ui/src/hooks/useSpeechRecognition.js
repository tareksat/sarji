import { useEffect, useRef, useState } from 'react';

const SpeechRecognitionImpl =
  typeof window !== 'undefined'
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null;

// How long silence has to last before the turn is treated as finished. Chrome
// fires `speechend` at any gap its VAD reads as silence — a breath, a comma, a
// "uhh" — so finalizing there cuts the speaker off mid-sentence. This window is
// what separates a pause from an ending, and it is the latency/robustness dial.
const SILENCE_GRACE_MS = 1000;

// Once recognition has been stopped, how long to wait for the engine's own
// final result before falling back to the last interim transcript.
const INTERIM_FALLBACK_MS = 600;

export function useSpeechRecognition(onResult, { onSpeechEnd, onSpeechStart } = {}) {
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);
  const interimTimeoutRef = useRef(null);
  const endpointTimeoutRef = useRef(null);
  const onResultRef = useRef(onResult);
  const onSpeechEndRef = useRef(onSpeechEnd);
  const onSpeechStartRef = useRef(onSpeechStart);
  onResultRef.current = onResult;
  onSpeechEndRef.current = onSpeechEnd;
  onSpeechStartRef.current = onSpeechStart;

  useEffect(() => {
    if (!SpeechRecognitionImpl) return;

    const recognition = new SpeechRecognitionImpl();
    // Continuous, because the engine's own endpointing ends the session at the
    // first pause. The silence window below is the endpointing instead.
    recognition.continuous = true;
    // Interim results give a transcript to fall back on, and are the signal
    // that speech is still in flight.
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    // Continuous recognition emits one final result per segment, so the turn is
    // the segments so far plus whatever is still interim.
    let finals = '';
    let interim = '';
    let sent = false;

    const send = (transcript) => {
      const text = transcript.trim();
      if (sent || !text) return;
      sent = true;
      onResultRef.current(text);
    };

    const cancelEndpoint = () => {
      window.clearTimeout(endpointTimeoutRef.current);
      endpointTimeoutRef.current = null;
    };

    // `pauseStartedAt` is when the silence began, not when it was judged to be
    // an ending, so the turn timer measures what the user actually waited.
    const finalize = (pauseStartedAt) => {
      endpointTimeoutRef.current = null;
      onSpeechEndRef.current?.(pauseStartedAt);
      // Forces the engine to flush its final result now rather than after its
      // own timeout. The final usually still wins the race below; the interim
      // is the floor, not the plan.
      recognition.stop();
      interimTimeoutRef.current = window.setTimeout(
        () => send(finals + interim),
        INTERIM_FALLBACK_MS
      );
    };

    recognition.onresult = (event) => {
      interim = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        if (result.isFinal) finals += result[0].transcript;
        else interim += result[0].transcript;
      }
      // Live interim text means speech is still in flight. A result carrying
      // only finals is the engine flushing an already-finished segment, which
      // must not reset a pause that is already being timed.
      if (interim) cancelEndpoint();
    };

    recognition.onspeechstart = () => {
      cancelEndpoint();
      onSpeechStartRef.current?.();
    };

    recognition.onspeechend = () => {
      const pauseStartedAt = performance.now();
      cancelEndpoint();
      endpointTimeoutRef.current = window.setTimeout(
        () => finalize(pauseStartedAt),
        SILENCE_GRACE_MS
      );
    };

    recognition.onend = () => {
      cancelEndpoint();
      window.clearTimeout(interimTimeoutRef.current);
      if (!sent) send(finals + interim);
      sent = false;
      finals = '';
      interim = '';
      setListening(false);
    };
    recognition.onerror = () => setListening(false);

    recognitionRef.current = recognition;
    return () => {
      window.clearTimeout(interimTimeoutRef.current);
      window.clearTimeout(endpointTimeoutRef.current);
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
    window.clearTimeout(endpointTimeoutRef.current);
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
