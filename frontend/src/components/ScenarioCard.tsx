import type { Scenario, ScenarioTurn } from "../data/scenarios";
import LanguageBadge from "./LanguageBadge";
import { speakText } from "../api/client";

interface Props {
  scenario: Scenario;
  onSendTurn: (turn: ScenarioTurn) => void;
  results: Record<number, { response?: string; loading?: boolean; error?: string }>;
  sessionId: string;
}

export default function ScenarioCard({ scenario, onSendTurn, results, sessionId }: Props) {
  return (
    <div className="glass p-5 space-y-4">
      <div>
        <h3 className="font-semibold text-white text-sm">{scenario.title}</h3>
        <p className="text-xs text-white/40 mt-0.5">{scenario.description}</p>
        <p className="text-[10px] text-white/20 mt-1 font-mono">session: {sessionId}</p>
      </div>

      <div className="space-y-3">
        {scenario.turns.map((turn) => {
          const result = results[turn.turn_number];
          return (
            <div key={turn.turn_number} className="glass-sm p-3 space-y-2">
              {/* Turn header */}
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-white/30 font-mono w-8">
                  #{turn.turn_number}
                </span>
                <LanguageBadge language={turn.language} size="sm" />
              </div>

              {/* User text */}
              <p className="text-sm text-white/80">{turn.user_text}</p>
              {turn.translation && (
                <p className="text-xs text-white/30 italic">{turn.translation}</p>
              )}

              {/* Expected behavior */}
              <p className="text-xs text-violet-400/60">
                Expected: {turn.expected_behavior}
              </p>

              {/* Actions */}
              <div className="flex gap-2">
                <button
                  onClick={() => onSendTurn(turn)}
                  disabled={result?.loading}
                  className="btn-secondary text-xs py-1 px-3 flex items-center gap-1.5"
                >
                  {result?.loading ? (
                    <>
                      <span className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
                      Sending…
                    </>
                  ) : (
                    "▶ Send as Text"
                  )}
                </button>
                <button
                  onClick={() => speakText(turn.user_text, turn.language)}
                  className="btn-secondary text-xs py-1 px-3"
                  title="Read aloud"
                >
                  🔊
                </button>
              </div>

              {/* Response */}
              {result?.error && (
                <p className="text-xs text-red-400 bg-red-500/10 rounded p-2">
                  Error: {result.error}
                </p>
              )}
              {result?.response && (
                <div className="bg-white/3 rounded-lg p-2.5 border border-white/5">
                  <p className="text-[10px] text-white/30 mb-1">Agent Response:</p>
                  <p className="text-xs text-white/80">{result.response}</p>
                  <button
                    onClick={() => speakText(result.response!, turn.language)}
                    className="text-[10px] text-violet-400/50 hover:text-violet-400 mt-1.5 transition-colors"
                  >
                    🔊 Replay
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
