interface Props {
  memory: Record<string, unknown>;
}

export default function MemoryPanel({ memory }: Props) {
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
    </div>
  );
}
