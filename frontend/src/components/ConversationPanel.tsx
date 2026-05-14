import LanguageBadge from "./LanguageBadge";
import { speakText } from "../api/client";

interface Turn {
  role: "user" | "assistant";
  text: string;
  detected_language?: string;
  language_label?: string;
  language_switched?: boolean;
  previous_language?: string;
  latency_ms?: number;
  turn_number?: number;
}

interface Props {
  turns: Turn[];
  voiceGender?: "male" | "female";
}

export default function ConversationPanel({ turns, voiceGender = "male" }: Props) {
  if (turns.length === 0) {
    return (
      <div className="glass p-8 text-center text-white/30 text-sm">
        No conversation yet. Send a message or record your voice.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {turns.map((turn, i) => (
        <div key={i}>
          {/* Language switch notice */}
          {turn.language_switched && turn.previous_language && turn.detected_language && (
            <div className="flex items-center gap-2 justify-center my-2">
              <div className="h-px flex-1 bg-white/5" />
              <span className="text-[10px] text-white/30 px-2 flex items-center gap-1.5">
                <LanguageBadge language={turn.previous_language} size="sm" />
                <span>→</span>
                <LanguageBadge language={turn.detected_language} size="sm" />
                <span className="text-white/20">language switch</span>
              </span>
              <div className="h-px flex-1 bg-white/5" />
            </div>
          )}

          <div className={`flex ${turn.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 space-y-1.5 ${
                turn.role === "user"
                  ? "bg-violet-500/15 border border-violet-500/20"
                  : "glass-sm"
              }`}
            >
              {/* Header */}
              <div className="flex items-center gap-2 text-xs text-white/40">
                <span className="font-medium">{turn.role === "user" ? "You" : "Polyglot"}</span>
                {turn.turn_number !== undefined && (
                  <span className="text-white/20">#{turn.turn_number}</span>
                )}
                {turn.detected_language && (
                  <LanguageBadge language={turn.detected_language} size="sm" />
                )}
                {turn.latency_ms !== undefined && (
                  <span className="ml-auto text-white/20 font-mono">
                    {turn.latency_ms.toFixed(0)}ms
                  </span>
                )}
              </div>

              {/* Message */}
              <p className="text-sm text-white/90 leading-relaxed">{turn.text}</p>

              {/* Speak button for assistant */}
              {turn.role === "assistant" && turn.detected_language && (
                <button
                  onClick={() => speakText(turn.text, turn.detected_language!, voiceGender)}
                  className="text-[10px] text-violet-400/60 hover:text-violet-400 transition-colors"
                >
                  🔊 Replay
                </button>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
