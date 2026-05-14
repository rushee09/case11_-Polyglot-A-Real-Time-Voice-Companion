import { useNavigate } from "react-router-dom";

export default function LandingPage() {
  const nav = useNavigate();
  return (
    <div className="min-h-[calc(100vh-52px)] flex flex-col items-center justify-center px-6 text-center">
      {/* Hero */}
      <div className="mb-6">
        <div className="w-16 h-16 rounded-2xl bg-violet-500/15 border border-violet-500/20 flex items-center justify-center mx-auto mb-6 text-3xl">
          🌐
        </div>
        <h1 className="text-4xl font-bold tracking-tight mb-3">
          Polyglot{" "}
          <span className="text-violet-400">Voice Companion</span>
        </h1>
        <p className="text-white/50 text-lg max-w-xl mx-auto leading-relaxed">
          A local multilingual voice agent that switches between English, Hindi, and Spanish
          without forgetting context.
        </p>
      </div>

      {/* Language flags */}
      <div className="flex gap-3 mb-10">
        {["🇺🇸 English", "🇮🇳 Hindi", "🇪🇸 Spanish", "🔀 Mixed"].map((l) => (
          <span
            key={l}
            className="glass-sm px-3 py-1.5 text-sm text-white/60 rounded-full"
          >
            {l}
          </span>
        ))}
      </div>

      {/* CTA buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button onClick={() => nav("/agent")} className="btn-primary text-base px-8 py-3">
          🎙 Start Voice Demo
        </button>
        <button onClick={() => nav("/scenarios")} className="btn-secondary text-base px-8 py-3">
          📋 Run Scenario Tests
        </button>
        <button onClick={() => nav("/logs")} className="btn-secondary text-base px-8 py-3">
          📊 View Logs
        </button>
      </div>

      {/* Architecture summary */}
      <div className="mt-14 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl w-full">
        {[
          { icon: "🎙", title: "ASR", desc: "faster-whisper\nlocal transcription" },
          { icon: "🧠", title: "LLM", desc: "LM Studio\nlocal OpenAI API" },
          { icon: "💾", title: "Memory", desc: "Structured entities\nacross lang switches" },
          { icon: "🔊", title: "TTS", desc: "Browser speechSynthesis\ninstant playback" },
        ].map((item) => (
          <div key={item.title} className="glass p-4 text-center">
            <div className="text-2xl mb-2">{item.icon}</div>
            <p className="text-sm font-semibold text-white/80">{item.title}</p>
            <p className="text-xs text-white/35 mt-1 whitespace-pre-line leading-relaxed">
              {item.desc}
            </p>
          </div>
        ))}
      </div>

      <p className="mt-10 text-xs text-white/20 max-w-sm">
        Runs entirely locally. No data sent to OpenAI, Anthropic, or any cloud inference API.
        Requires LM Studio running at localhost:1234.
      </p>
    </div>
  );
}
