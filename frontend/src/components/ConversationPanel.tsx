import LanguageBadge from "./LanguageBadge";
import ThinkingBubble from "./ThinkingBubble";
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
  thinking?: boolean;
  userName?: string;
}

/** Robot/agent SVG icon for the Polyglot avatar */
function AgentAvatar() {
  return (
    <div className="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center
      bg-gradient-to-br from-violet-600/50 to-fuchsia-600/40
      border border-violet-400/35
      shadow-[0_0_14px_rgba(139,92,246,0.35)]">
      <svg className="w-[18px] h-[18px] text-violet-200" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7H3a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2zM7 14v2a5 5 0 0 0 10 0v-2H7zm3 5h4l-.8 3H10.8L10 19z"/>
      </svg>
    </div>
  );
}

export default function ConversationPanel({
  turns,
  voiceGender = "male",
  thinking = false,
  userName,
}: Props) {
  if (turns.length === 0 && !thinking) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4 text-center select-none">
        <div className="w-14 h-14 rounded-full bg-violet-500/10 border border-violet-500/20
          flex items-center justify-center shadow-[0_0_24px_rgba(139,92,246,0.2)]">
          <svg className="w-6 h-6 text-violet-400/70" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7H3a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2zM7 14v2a5 5 0 0 0 10 0v-2H7zm3 5h4l-.8 3H10.8L10 19z"/>
          </svg>
        </div>
        <div className="space-y-1">
          <p className="text-white/50 text-sm font-medium">Polyglot is ready</p>
          <p className="text-white/25 text-xs">Speak or type — I understand English, Hindi &amp; Spanish</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5 py-2 px-1">
      {turns.map((turn, i) => (
        <div key={i}>
          {/* ── Language switch banner ── */}
          {turn.language_switched && turn.previous_language && turn.detected_language && (
            <div className="flex items-center gap-2 justify-center my-3">
              <div className="h-px flex-1 bg-white/[0.05]" />
              <span className="text-[10px] text-white/30 px-3 py-0.5 rounded-full
                bg-white/[0.03] border border-white/[0.06] flex items-center gap-1.5">
                <LanguageBadge language={turn.previous_language} size="sm" />
                <span className="text-white/20">→</span>
                <LanguageBadge language={turn.detected_language} size="sm" />
                <span className="text-white/20 ml-0.5">switched language</span>
              </span>
              <div className="h-px flex-1 bg-white/[0.05]" />
            </div>
          )}

          {turn.role === "user" ? (
            /* ── User message ── */
            <div className="flex items-end justify-end gap-2.5">
              <div className="flex flex-col items-end gap-1 max-w-[76%]">
                <span className="text-[10px] text-white/30 mr-1">You</span>
                <div className="bg-violet-500/[0.18] border border-violet-400/20
                  rounded-2xl rounded-br-[4px] px-4 py-2.5
                  shadow-[0_2px_12px_rgba(139,92,246,0.12)]">
                  <p className="text-[14px] text-white/90 leading-relaxed">{turn.text}</p>
                </div>
                {/* Meta row */}
                <div className="flex items-center gap-2 mr-1">
                  {turn.detected_language && <LanguageBadge language={turn.detected_language} size="sm" />}
                  {turn.latency_ms !== undefined && (
                    <span className="text-[10px] text-white/20 font-mono">{turn.latency_ms.toFixed(0)}ms</span>
                  )}
                </div>
              </div>
              {/* User avatar */}
              <div className="w-9 h-9 rounded-full flex-shrink-0 mb-6
                bg-violet-500/20 border border-violet-400/25
                flex items-center justify-center
                text-xs font-semibold text-violet-300 uppercase">
                {userName?.[0] ?? "U"}
              </div>
            </div>
          ) : (
            /* ── Assistant message ── */
            <div className="flex items-end gap-2.5">
              <div className="mb-6">
                <AgentAvatar />
              </div>
              <div className="flex flex-col items-start gap-1 max-w-[76%]">
                <span className="text-[10px] text-violet-400/50 ml-1">Polyglot</span>
                <div className="bg-white/[0.055] border border-white/[0.09]
                  rounded-2xl rounded-bl-[4px] px-4 py-2.5
                  shadow-[0_2px_8px_rgba(0,0,0,0.2)]">
                  <p className="text-[14px] text-white/90 leading-relaxed whitespace-pre-wrap">{turn.text}</p>
                </div>
                {/* Meta row */}
                <div className="flex items-center gap-2 ml-1">
                  {turn.detected_language && <LanguageBadge language={turn.detected_language} size="sm" />}
                  {turn.latency_ms !== undefined && (
                    <span className="text-[10px] text-white/20 font-mono">{turn.latency_ms.toFixed(0)}ms</span>
                  )}
                  {turn.detected_language && (
                    <button
                      onClick={() => speakText(turn.text, turn.detected_language!, voiceGender)}
                      className="text-[10px] text-violet-400/40 hover:text-violet-400 transition-colors flex items-center gap-0.5"
                    >
                      🔊 replay
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      ))}

      {/* ── Thinking state ── */}
      {thinking && (
        <div className="flex items-end gap-2.5">
          <AgentAvatar />
          <div className="flex flex-col items-start gap-1">
            <span className="text-[10px] text-violet-400/50 ml-1">Polyglot</span>
            <ThinkingBubble />
          </div>
        </div>
      )}
    </div>
  );
}

