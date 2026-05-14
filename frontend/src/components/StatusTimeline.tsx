interface Stage {
  id: string;
  label: string;
  active: boolean;
  done: boolean;
  ms?: number;
}

interface Props {
  stages: Stage[];
}

export default function StatusTimeline({ stages }: Props) {
  return (
    <div className="flex items-center gap-1 flex-wrap">
      {stages.map((s, i) => (
        <div key={s.id} className="flex items-center gap-1">
          <div
            className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-medium transition-all ${
              s.active
                ? "bg-violet-500/20 text-violet-400 border border-violet-500/30"
                : s.done
                ? "bg-white/5 text-white/40 border border-white/5"
                : "bg-transparent text-white/20"
            }`}
          >
            {s.active && (
              <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
            )}
            {s.done && (
              <span className="w-1.5 h-1.5 rounded-full bg-white/20" />
            )}
            <span>{s.label}</span>
            {s.ms !== undefined && s.done && (
              <span className="font-mono text-white/30">{s.ms.toFixed(0)}ms</span>
            )}
          </div>
          {i < stages.length - 1 && (
            <span className="text-white/10 text-[10px]">→</span>
          )}
        </div>
      ))}
    </div>
  );
}
