interface Props {
  memory: Record<string, unknown>;
}

function renderValue(val: unknown): string {
  if (val === null || val === undefined) return "—";
  if (typeof val === "object") return JSON.stringify(val, null, 2);
  return String(val);
}

export default function MemoryPanel({ memory }: Props) {
  const entities = (memory.entities as Record<string, unknown>) ?? {};
  const entityEntries = Object.entries(entities).filter(
    ([, v]) => {
      if (v === null || v === undefined) return false;
      if (Array.isArray(v)) return v.length > 0;
      if (typeof v === "object") return Object.keys(v as object).length > 0;
      return true;
    }
  );

  return (
    <div className="glass p-4 space-y-3">
      <span className="text-xs font-semibold text-white/60 uppercase tracking-wider">Memory</span>

      {/* Session meta */}
      <div className="grid grid-cols-2 gap-2">
        {[
          { label: "Turn", value: memory.turn_count as number ?? 0 },
          { label: "Scenario", value: (memory.active_scenario as string) ?? "none" },
          { label: "Language", value: (memory.current_language as string) ?? "—" },
          { label: "Prev Lang", value: (memory.previous_language as string) ?? "—" },
        ].map((item) => (
          <div key={item.label} className="glass-sm p-2">
            <p className="text-[10px] text-white/40 mb-0.5">{item.label}</p>
            <p className="text-xs font-medium text-white/80">{String(item.value)}</p>
          </div>
        ))}
      </div>

      {/* Entities */}
      {entityEntries.length > 0 && (
        <div>
          <p className="text-[10px] text-white/40 mb-2 uppercase tracking-wider">Extracted Entities</p>
          <div className="space-y-1.5">
            {entityEntries.map(([key, val]) => (
              <div key={key} className="flex items-start gap-2">
                <span className="text-xs text-violet-400/70 font-mono w-28 shrink-0 pt-0.5">
                  {key}
                </span>
                <span className="text-xs text-white/70 font-mono break-all">
                  {renderValue(val)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {entityEntries.length === 0 && (
        <p className="text-xs text-white/20 text-center py-2">No entities extracted yet</p>
      )}
    </div>
  );
}
