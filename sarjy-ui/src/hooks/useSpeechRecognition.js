import { useCallback, useEffect, useRef, useState } from 'react';

const SpeechRecognitionImpl =
  typeof window !== 'undefined'
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null;

// How long transcript activity has to be quiet before the turn is treated as
// finished. Measured from the last `result` event, not from `speechend`: in
// continuous mode Chrome does not fire `speechend` at pauses, only once, right
// before `end`, when the engine itself gives up tens of seconds later. Results
// (interim or final) are the one signal that arrives while the user is talking,
// so their absence is the pause. This window is what separates a pause from an
// ending, and it is the latency/robustness dial.
const SILENCE_GRACE_MS = 1000;

// Once recognition has been stopped, how long to wait for the engine's own
// final result before falling back to the last interim transcript.
const INTERIM_FALLBACK_MS = 600;

// How long an open microphone waits for the first result before giving up. A
// mic pressed by mistake, or a room that stays quiet, must not stay hot until
// Chrome's own timeout. The turn is discarded, not sent: there is nothing in it.
const NO_SPEECH_MS = 8000;

export function useSpeechRecognition(onResult, { onSpeechEnd, onSpeechStart } = {}) {
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);
  const interimTimeoutRef = useRef(null);
  const endpointTimeoutRef = useRef(null);
  const noSpeechTimeoutRef = useRef(null);
  // Set by `cancel`, read by `onend`: the difference between stopping the
  // microphone and stopping it while throwing the utterance away.
  const discardRef = useRef(false);
  // The last error the engine reported, so hands-free does not re-arm into a
  // permission failure forever.
  const [lastError, setLastError] = useState(null);
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
    // Set once `finalize` has asked the engine to stop. The engine flushes a
    // last final result on the way out, and that flush must not restart the
    // silence window and schedule a second finalize.
    let stopping = false;

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

    const cancelNoSpeech = () => {
      window.clearTimeout(noSpeechTimeoutRef.current);
      noSpeechTimeoutRef.current = null;
    };

    const clearTimers = () => {
      cancelEndpoint();
      cancelNoSpeech();
      window.clearTimeout(interimTimeoutRef.current);
      interimTimeoutRef.current = null;
    };

    // `pauseStartedAt` is when the silence began, not when it was judged to be
    // an ending, so the turn timer measures what the user actually waited.
    const finalize = (pauseStartedAt) => {
      endpointTimeoutRef.current = null;
      stopping = true;
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

    // Restarts the silence window from `at`, the last moment speech was known
    // to be in flight.
    const armEndpoint = (at) => {
      if (stopping) return;
      cancelEndpoint();
      endpointTimeoutRef.current = window.setTimeout(() => finalize(at), SILENCE_GRACE_MS);
    };

    recognition.onstart = () => {
      cancelNoSpeech();
      noSpeechTimeoutRef.current = window.setTimeout(() => {
        noSpeechTimeoutRef.current = null;
        discardRef.current = true;
        recognition.abort();
      }, NO_SPEECH_MS);
    };

    recognition.onresult = (event) => {
      cancelNoSpeech();
      interim = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        if (result.isFinal) finals += result[0].transcript;
        else interim += result[0].transcript;
      }
      // Any result, interim or final, is the engine still hearing something.
      // The pause is measured from the last one.
      armEndpoint(performance.now());
    };

    recognition.onspeechstart = () => {
      cancelEndpoint();
      onSpeechStartRef.current?.();
    };

    // Rarely fires in continuous mode, but when it does it is the same fact as
    // a result going quiet, and it is the only signal in an engine that does
    // not deliver interim results.
    recognition.onspeechend = () => {
      armEndpoint(performance.now());
    };

    recognition.onend = () => {
      clearTimers();
      if (!sent && !discardRef.current) send(finals + interim);
      discardRef.current = false;
      sent = false;
      stopping = false;
      finals = '';
      interim = '';
      setListening(false);
    };
    recognition.onerror = (event) => {
      // A queued `finalize` would otherwise still fire and announce a speech
      // end for a turn that is not happening.
      clearTimers();
      stopping = false;
      setLastError(event?.error ?? 'unknown');
      setListening(false);
    };

    recognitionRef.current = recognition;
    return () => {
      clearTimers();
      recognition.abort();
    };
  }, []);

  // Memoized: the hands-free effect depends on `start`, and a new identity every
  // render re-runs it every render.
  const start = useCallback(() => {
    if (!recognitionRef.current || listening) return;
    setLastError(null);
    setListening(true);
    try {
      recognitionRef.current.start();
    } catch {
      // `InvalidStateError` when the engine has not finished stopping. The
      // optimistic state has to be given back, or the UI shows a live
      // microphone with nothing behind it.
      setListening(false);
    }
  }, [listening]);

  // Stops and delivers whatever has been transcribed.
  const stop = useCallback(() => {
    if (!recognitionRef.current) return;
    window.clearTimeout(endpointTimeoutRef.current);
    window.clearTimeout(noSpeechTimeoutRef.current);
    recognitionRef.current.stop();
    setListening(false);
  }, []);

  // Stops and throws it away.
  const cancel = useCallback(() => {
    if (!recognitionRef.current) return;
    window.clearTimeout(endpointTimeoutRef.current);
    window.clearTimeout(noSpeechTimeoutRef.current);
    window.clearTimeout(interimTimeoutRef.current);
    discardRef.current = true;
    recognitionRef.current.abort();
    setListening(false);
  }, []);

  return {
    supported: !!SpeechRecognitionImpl,
    listening,
    lastError,
    start,
    stop,
    cancel,
  };
}
