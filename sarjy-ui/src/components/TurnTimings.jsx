// Segments in the order they happen, so the bar reads left to right as the
// turn actually unfolded.
const SEGMENTS = [
  { key: 'stt_tail_ms', label: 'speech → send', className: 'seg-stt' },
  { key: 'server_read_ms', label: 'db', className: 'seg-db' },
  { key: 'server_ttft_ms', label: 'model', className: 'seg-model' },
  { key: 'audio_ms', label: 'audio start', className: 'seg-audio' },
];

function derive(timings) {
  if (!timings) return null;
  const server = timings.server ?? {};
  const dbMs = server.db_read_ms ?? 0;
  // llm_ttft_ms is marked from the start of the turn, so the db read has to
  // come back out of it to leave the model's own share.
  const ttftMs = Math.max(0, (server.llm_ttft_ms ?? 0) - dbMs);
  const sttMs = timings.stt_tail_ms ?? 0;
  const audioMs = Math.max(0, (timings.ttfa_ms ?? 0) - sttMs - dbMs - ttftMs);
  return {
    stt_tail_ms: sttMs,
    server_read_ms: dbMs,
    server_ttft_ms: ttftMs,
    audio_ms: audioMs,
    total: timings.ttfa_ms ?? 0,
  };
}

export default function TurnTimings({ timings }) {
  const parts = derive(timings);
  if (!parts || !parts.total) return null;

  return (
    <div className="turn-timings" title="Time to first audio, by segment">
      <div className="ttfa-readout">
        <strong>{Math.round(parts.total)}</strong> ms to first audio
      </div>
      <div className="waterfall">
        {SEGMENTS.map(({ key, label, className }) => {
          const width = (parts[key] / parts.total) * 100;
          if (width <= 0) return null;
          return (
            <div
              key={key}
              className={`waterfall-seg ${className}`}
              style={{ width: `${width}%` }}
              title={`${label}: ${Math.round(parts[key])} ms`}
            />
          );
        })}
      </div>
    </div>
  );
}
