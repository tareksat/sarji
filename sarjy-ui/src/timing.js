// One timer per conversational turn. Marks are wall-clock ms from
// `performance.now()`; segments are the differences the deep dive reports.
export function createTurnTimer() {
  const marks = {};
  let server = null;

  const diff = (from, to) =>
    marks[from] !== undefined && marks[to] !== undefined
      ? Math.round(marks[to] - marks[from])
      : null;

  return {
    mark(name) {
      if (marks[name] === undefined) marks[name] = performance.now();
    },
    setServer(timings) {
      server = timings ?? null;
    },
    segments() {
      // The origin is speech end for a spoken turn and the send for a typed
      // one, so the two are never averaged together in a results table.
      const origin = marks.speechEnd !== undefined ? 'speechEnd' : 'requestSent';
      return {
        source: marks.speechEnd !== undefined ? 'voice' : 'typed',
        stt_tail_ms: diff('speechEnd', 'requestSent'),
        first_byte_ms: diff('requestSent', 'firstByte'),
        reply_complete_ms: diff('requestSent', 'replyComplete'),
        ttfa_ms: diff(origin, 'firstAudio'),
        server,
      };
    },
    publish() {
      const line = this.segments();
      // One JSON line per turn. `summarize_client_timings.py` reads these.
      console.log(`[sarjy-timing] ${JSON.stringify(line)}`);
      return line;
    },
  };
}
