import type { LatencyBreakdown } from "../api/client";

interface Props {
  latency: LatencyBreakdown;
  lmAvailable: boolean;
  fallback: boolean;
}

const stages = [
  { key: "audio_upload_ms" as const, label: "Audio Upload" },
  { key: "asr_ms" as const, label: "Transcription (ASR)" },
  { key: "language_detection_ms" as const, label: "Language Detection" },
  { key: "memory_update_ms" as const, label: "Memory Update" },
  { key: "tool_ms" as const, label: "Tool Lookup" },
  { key: "llm_ms" as const, label: "LLM Inference" },
  { key: "tts_start_ms" as const, label: "TTS Start" },
];

function Bar({ value, max }: { value: number; max: number }) {
  const pct = Math.min((value / max) * 100, 100);
  const color = pct < 40 ? "bg-violet-500" : pct < 70 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
      <div className={`${color} h-full rounded-full transition-all`} style={{ width: `${pct}%` }} />
    </div>
  );
}

export default function LatencyPanel({ latency, lmAvailable, fallback }: Props) {
  const max = Math.max(latency.total_ms, 100);

  return (
    <div className="glass p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-white/60 uppercase tracking-wider">Latency</span>
        <div className="flex items-center gap-2">
          <span
            className={`text-xs font-mono font-bold ${latency.total_ms < 800 ? "text-violet-400" : latency.total_ms < 1200 ? "text-yellow-400" : "text-red-400"}`}
          >
            {latency.total_ms.toFixed(0)} ms total
          </span>
          {fallback && (
            <span className="text-[10px] bg-yellow-500/15 text-yellow-400 border border-yellow-500/25 px-1.5 py-0.5 rounded">
              fallback
            </span>
          )}
          {!lmAvailable && (
            <span className="text-[10px] bg-red-500/15 text-red-400 border border-red-500/25 px-1.5 py-0.5 rounded">
              LM offline
            </span>
          )}
        </div>
      </div>

      <div className="space-y-1.5">
        {stages.map(({ key, label }) => {
          const val = latency[key];
          if (val == null) return null;
          return (
            <div key={key} className="flex items-center gap-3">
              <span className="text-xs text-white/40 w-36 shrink-0">{label}</span>
              <Bar value={val} max={max} />
              <span className="text-xs font-mono text-white/60 w-14 text-right shrink-0">
                {val.toFixed(0)} ms
              </span>
            </div>
          );
        })}
      </div>

      <div className="pt-2 border-t border-white/5 flex items-center justify-between">
        <span className="text-xs text-white/40">Target: &lt;1200ms</span>
        <span className="text-xs text-white/40">Stretch: &lt;800ms</span>
      </div>
    </div>
  );
}
