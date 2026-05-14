/** Animated "LLM is thinking" bubble shown in the conversation while waiting. */
export default function ThinkingBubble() {
  return (
    <div className="flex justify-start">
      <div className="glass-sm rounded-2xl px-4 py-3 flex items-center gap-3 max-w-[160px]">
        {/* Label */}
        <span className="text-xs text-white/40 font-medium">Thinking</span>

        {/* Three bouncing dots */}
        <div className="flex items-end gap-1">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="block w-1.5 h-1.5 rounded-full bg-violet-400/70"
              style={{
                animation: "thinkingBounce 1.2s ease-in-out infinite",
                animationDelay: `${i * 0.2}s`,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
