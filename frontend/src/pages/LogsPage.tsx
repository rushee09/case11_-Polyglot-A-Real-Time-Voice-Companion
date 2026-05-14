import { useState } from "react";
import { apiGetSessionLogs } from "../api/client";
import LanguageBadge from "../components/LanguageBadge";

interface Message {
  turn_number: number;
  role: string;
  transcript: string;
  detected_language: string;
  response_language: string;
  response_text: string;
  latency_ms: number;
  created_at: string;
}

interface SwitchEvent {
  turn_number: number;
  from_language: string;
  to_language: string;
  confidence: number;
  created_at: string;
}

interface LatencyLog {
  turn_number: number;
  asr_ms: number;
  language_detection_ms: number;
  memory_update_ms: number;
  tool_ms: number;
  llm_ms: number;
  total_ms: number;
}

interface LogData {
  session_id: string;
  messages: Message[];
  language_switch_events: SwitchEvent[];
  latency_logs: LatencyLog[];
}

export default function LogsPage() {
  const [sessionId, setSessionId] = useState("");
  const [logs, setLogs] = useState<LogData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"messages" | "switches" | "latency">("messages");

  async function fetchLogs() {
    if (!sessionId.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiGetSessionLogs(sessionId.trim());
      if (!data) throw new Error("Session not found");
      setLogs(data as LogData);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold mb-1">Session Logs</h1>
        <p className="text-sm text-white/40">
          Enter a session ID to view conversation logs, language switch events, and latency data.
        </p>
      </div>

      {/* Session ID input */}
      <div className="flex gap-3">
        <input
          className="input flex-1"
          placeholder="Paste session ID (UUID)…"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && fetchLogs()}
        />
        <button onClick={fetchLogs} disabled={loading || !sessionId.trim()} className="btn-primary px-6">
          {loading ? "Loading…" : "Fetch Logs"}
        </button>
      </div>

      {error && (
        <div className="glass-sm p-3 text-red-400 text-sm border-red-500/20 bg-red-500/5">
          {error}
        </div>
      )}

      {logs && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: "Messages", value: logs.messages.length },
              { label: "Lang Switches", value: logs.language_switch_events.length },
              { label: "Latency Records", value: logs.latency_logs.length },
            ].map((item) => (
              <div key={item.label} className="glass p-4 text-center">
                <p className="text-2xl font-bold text-violet-400">{item.value}</p>
                <p className="text-xs text-white/40 mt-1">{item.label}</p>
              </div>
            ))}
          </div>

          {/* Tabs */}
          <div className="flex gap-1 border-b border-white/5 pb-1">
            {(["messages", "switches", "latency"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-1.5 text-sm rounded-t-lg transition-colors capitalize ${
                  tab === t
                    ? "bg-violet-500/10 text-violet-400"
                    : "text-white/40 hover:text-white"
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {/* Messages */}
          {tab === "messages" && (
            <div className="space-y-3">
              {logs.messages.length === 0 && (
                <p className="text-sm text-white/30 text-center py-8">No messages logged yet</p>
              )}
              {logs.messages.map((msg, i) => (
                <div key={i} className="glass p-4 space-y-2">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="text-xs font-mono text-white/30">#{msg.turn_number}</span>
                    <span className={`text-xs font-medium ${msg.role === "user" ? "text-blue-400" : "text-violet-400"}`}>
                      {msg.role}
                    </span>
                    <LanguageBadge language={msg.detected_language} size="sm" />
                    {msg.latency_ms && (
                      <span className="ml-auto text-xs font-mono text-white/30">
                        {msg.latency_ms.toFixed(0)} ms
                      </span>
                    )}
                    <span className="text-xs text-white/20">{new Date(msg.created_at).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-sm text-white/70">{msg.transcript}</p>
                  {msg.response_text && (
                    <p className="text-xs text-white/40 border-t border-white/5 pt-2">
                      → {msg.response_text}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Language switch events */}
          {tab === "switches" && (
            <div className="space-y-2">
              {logs.language_switch_events.length === 0 && (
                <p className="text-sm text-white/30 text-center py-8">No language switches detected</p>
              )}
              {logs.language_switch_events.map((ev, i) => (
                <div key={i} className="glass p-3 flex items-center gap-4">
                  <span className="text-xs font-mono text-white/30">Turn #{ev.turn_number}</span>
                  <LanguageBadge language={ev.from_language} size="sm" />
                  <span className="text-white/30">→</span>
                  <LanguageBadge language={ev.to_language} size="sm" />
                  {ev.confidence && (
                    <span className="text-xs text-white/30">conf: {ev.confidence.toFixed(2)}</span>
                  )}
                  <span className="ml-auto text-xs text-white/20">{new Date(ev.created_at).toLocaleTimeString()}</span>
                </div>
              ))}
            </div>
          )}

          {/* Latency logs */}
          {tab === "latency" && (
            <div className="space-y-2">
              {logs.latency_logs.length === 0 && (
                <p className="text-sm text-white/30 text-center py-8">No latency data yet</p>
              )}
              {logs.latency_logs.map((lat, i) => (
                <div key={i} className="glass p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-white/40">Turn #{lat.turn_number}</span>
                    <span className={`text-xs font-bold font-mono ${lat.total_ms < 800 ? "text-violet-400" : lat.total_ms < 1200 ? "text-yellow-400" : "text-red-400"}`}>
                      {lat.total_ms?.toFixed(0)} ms total
                    </span>
                  </div>
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 text-[10px]">
                    {[
                      ["ASR", lat.asr_ms],
                      ["Lang", lat.language_detection_ms],
                      ["Mem", lat.memory_update_ms],
                      ["Tool", lat.tool_ms],
                      ["LLM", lat.llm_ms],
                    ].map(([label, val]) => (
                      val != null && (
                        <div key={label as string} className="glass-sm p-1.5 text-center">
                          <p className="text-white/30">{label as string}</p>
                          <p className="font-mono text-white/60">{(val as number)?.toFixed(0)}ms</p>
                        </div>
                      )
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
