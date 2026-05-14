import { useState, useEffect, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import {
  apiChat, apiVoiceTurn, apiHealth, speakText,
  type ChatResponse, type HealthResponse,
} from "../api/client";
import { SCENARIOS } from "../data/scenarios";
import ConversationPanel from "../components/ConversationPanel";
import MicRecorder from "../components/MicRecorder";
import TextChatBox from "../components/TextChatBox";
import MemoryPanel from "../components/MemoryPanel";
import LatencyPanel from "../components/LatencyPanel";
import LanguageBadge from "../components/LanguageBadge";
import StatusTimeline from "../components/StatusTimeline";
import { useAuth } from "../context/AuthContext";
import { getUserChatsKey } from "../context/AuthContext";

interface ConvTurn {
  role: "user" | "assistant";
  text: string;
  detected_language?: string;
  language_label?: string;
  language_switched?: boolean;
  previous_language?: string;
  latency_ms?: number;
  turn_number?: number;
}

interface LangSwitchEvent {
  turn_number: number;
  from_lang: string;
  to_lang: string;
  timestamp: string;
}

interface Chat {
  id: string;
  title: string;
  sessionId: string;
  turns: ConvTurn[];
  memory: Record<string, unknown>;
  scenario: string;
  lastLatency: ChatResponse["latency"] | null;
  lastLmAvailable: boolean;
  lastFallback: boolean;
  detectedLang: string;
  createdAt: number;
  languageSwitches: LangSwitchEvent[];
}

type PipelineStage = "idle" | "recording_received" | "transcribing" | "language_detected" | "updating_memory" | "calling_llm" | "response_ready";

const PIPELINE_STAGES = [
  { id: "recording_received", label: "Received" },
  { id: "transcribing", label: "ASR" },
  { id: "language_detected", label: "Lang" },
  { id: "updating_memory", label: "Memory" },
  { id: "calling_llm", label: "LLM" },
  { id: "response_ready", label: "Done" },
];

const STAGE_ORDER: PipelineStage[] = [
  "recording_received", "transcribing", "language_detected",
  "updating_memory", "calling_llm", "response_ready",
];

function createNewChat(): Chat {
  return {
    id: uuidv4(),
    title: "New Chat",
    sessionId: uuidv4(),
    turns: [],
    memory: {},
    scenario: "",
    lastLatency: null,
    lastLmAvailable: true,
    lastFallback: false,
    detectedLang: "en",
    createdAt: Date.now(),
    languageSwitches: [],
  };
}

export default function VoiceAgentPage() {
  const { user } = useAuth();
  const chatsKey = getUserChatsKey(user?.username ?? "guest");

  const [chats, setChats] = useState<Chat[]>(() => {
    try {
      const raw = localStorage.getItem(getUserChatsKey(user?.username ?? "guest"));
      if (raw) {
        const saved = JSON.parse(raw) as Chat[];
        if (Array.isArray(saved) && saved.length > 0) return saved;
      }
    } catch { /* ignore */ }
    return [createNewChat()];
  });
  const [activeChatId, setActiveChatId] = useState<string>(() => {
    try {
      const raw = localStorage.getItem(getUserChatsKey(user?.username ?? "guest"));
      if (raw) {
        const saved = JSON.parse(raw) as Chat[];
        if (Array.isArray(saved) && saved.length > 0) return saved[0].id;
      }
    } catch { /* ignore */ }
    const initial = createNewChat();
    return initial.id;
  });
  const [voiceGender, setVoiceGender] = useState<"male" | "female">("male");
  const [stage, setStage] = useState<PipelineStage>("idle");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiHealth().then(setHealth).catch(() => null);
  }, []);

  // Persist chats to localStorage whenever they change (per user)
  useEffect(() => {
    try {
      localStorage.setItem(chatsKey, JSON.stringify(chats));
    } catch { /* quota exceeded — ignore */ }
  }, [chats, chatsKey]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chats, activeChatId]);

  const activeChat = chats.find((c) => c.id === activeChatId) ?? chats[0];

  function updateActiveChat(updater: (chat: Chat) => Partial<Chat>) {
    setChats((prev) =>
      prev.map((c) =>
        c.id === activeChat.id ? { ...c, ...updater(c) } : c
      )
    );
  }

  function newChat() {
    const chat = createNewChat();
    setChats((prev) => [chat, ...prev]);
    setActiveChatId(chat.id);
    setStage("idle");
    setError("");
  }

  function deleteChat(chatId: string, e: React.MouseEvent) {
    e.stopPropagation();
    setChats((prev) => {
      const remaining = prev.filter((c) => c.id !== chatId);
      if (remaining.length === 0) {
        const fresh = createNewChat();
        setActiveChatId(fresh.id);
        return [fresh];
      }
      if (activeChatId === chatId) {
        setActiveChatId(remaining[0].id);
      }
      return remaining;
    });
  }

  async function processResponse(resp: ChatResponse & { transcript?: string }) {
    const userText = resp.transcript ?? resp.user_text;
    const newTurns: ConvTurn[] = [
      {
        role: "user",
        text: userText,
        detected_language: resp.detected_language,
        language_label: resp.language_label,
        turn_number: resp.turn_number,
      },
      {
        role: "assistant",
        text: resp.assistant_response,
        detected_language: resp.response_language,
        language_label: resp.response_language_label,
        language_switched: resp.language_switched,
        previous_language: resp.previous_language,
        latency_ms: resp.latency.total_ms,
        turn_number: resp.turn_number,
      },
    ];

    updateActiveChat((chat) => {
      const updatedTurns = [...chat.turns, ...newTurns];
      const title =
        chat.turns.length === 0
          ? userText.slice(0, 42) + (userText.length > 42 ? "…" : "")
          : chat.title;

      // Track language switch for this turn
      const updatedSwitches = resp.language_switched && resp.previous_language
        ? [
            ...chat.languageSwitches,
            {
              turn_number: resp.turn_number,
              from_lang: resp.previous_language,
              to_lang: resp.detected_language,
              timestamp: new Date().toISOString(),
            } satisfies LangSwitchEvent,
          ]
        : chat.languageSwitches;

      return {
        turns: updatedTurns,
        title,
        memory: resp.memory_snapshot,
        lastLatency: resp.latency,
        lastLmAvailable: resp.lm_studio_available,
        lastFallback: resp.fallback_mode,
        detectedLang: resp.detected_language,
        languageSwitches: updatedSwitches,
      };
    });

    setStage("response_ready");
    speakText(resp.assistant_response, resp.response_language, voiceGender);
  }

  async function handleTextSend(text: string) {
    setLoading(true);
    setError("");
    setStage("recording_received");
    try {
      setStage("language_detected");
      setStage("updating_memory");
      setStage("calling_llm");
      const resp = await apiChat(text, activeChat.sessionId, activeChat.scenario || undefined);
      await processResponse(resp);
    } catch (e) {
      setError((e as Error).message);
      setStage("idle");
    } finally {
      setLoading(false);
    }
  }

  async function handleAudio(blob: Blob) {
    setLoading(true);
    setError("");
    setStage("recording_received");
    try {
      setStage("transcribing");
      const resp = await apiVoiceTurn(blob, activeChat.sessionId, activeChat.scenario || undefined);
      await processResponse(resp as ChatResponse & { transcript: string });
    } catch (e) {
      const msg = (e as Error).message;
      if (msg.includes("faster-whisper")) {
        setError("ASR unavailable — switch to text mode or install faster-whisper");
      } else {
        setError(msg);
      }
      setStage("idle");
    } finally {
      setLoading(false);
    }
  }

  const stageItems = PIPELINE_STAGES.map((s) => ({
    ...s,
    active: stage === s.id,
    done: stage !== "idle" && STAGE_ORDER.indexOf(stage as PipelineStage) > STAGE_ORDER.indexOf(s.id as PipelineStage),
  }));

  return (
    <div className="flex h-[calc(100vh-52px)] overflow-hidden">
      {/* ── Sidebar ── */}
      <aside
        className={`${
          sidebarOpen ? "w-64" : "w-0"
        } transition-all duration-300 overflow-hidden flex-shrink-0 border-r border-white/[0.06] backdrop-blur-xl bg-black/20 flex flex-col`}
      >
        {/* User info + new chat button */}
        <div className="p-3 border-b border-white/[0.06] flex-shrink-0 space-y-2">
          {/* Logged-in user pill */}
          <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-violet-500/10 border border-violet-500/20">
            <div className="w-6 h-6 rounded-full bg-violet-500/30 flex items-center justify-center text-xs font-bold text-violet-300 uppercase flex-shrink-0">
              {user?.username?.[0] ?? "?"}
            </div>
            <span className="text-xs font-medium text-violet-300 truncate">{user?.username}</span>
          </div>
          <button
            onClick={newChat}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-white/10 hover:bg-white/5 text-sm text-white/60 hover:text-white transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New chat
          </button>
        </div>

        {/* Chat list */}
        <div className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
          {chats.map((chat) => (
            <div
              key={chat.id}
              className={`group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                chat.id === activeChatId
                  ? "bg-white/10 text-white"
                  : "text-white/50 hover:bg-white/5 hover:text-white/80"
              }`}
              onClick={() => { setActiveChatId(chat.id); setError(""); }}
            >
              <svg
                className="w-3.5 h-3.5 flex-shrink-0 opacity-50"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              <span className="text-xs truncate flex-1 leading-relaxed">{chat.title}</span>
              {/* Language switch badge */}
              {chat.languageSwitches.length > 0 && (
                <span className="flex-shrink-0 text-[9px] font-bold bg-yellow-500/15 text-yellow-400 border border-yellow-500/25 rounded px-1 py-0.5">
                  {chat.languageSwitches.length}🔀
                </span>
              )}
              {chats.length > 1 && (
                <button
                  onClick={(e) => deleteChat(chat.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-0.5 hover:text-red-400 transition-all flex-shrink-0"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          ))}
        </div>

        {/* Language switch log for active chat */}
        <div className="px-3 py-2.5 border-t border-white/[0.06] flex-shrink-0">
          <p className="text-[10px] text-white/30 uppercase tracking-wider mb-1.5 px-1 flex items-center gap-1">
            Lang Switches
            {activeChat?.languageSwitches.length > 0 && (
              <span className="ml-auto text-yellow-400 font-bold">{activeChat.languageSwitches.length}</span>
            )}
          </p>
          {!activeChat || activeChat.languageSwitches.length === 0 ? (
            <p className="text-[10px] text-white/20 px-1">No switches in this chat</p>
          ) : (
            <div className="space-y-1 max-h-28 overflow-y-auto pr-1">
              {activeChat.languageSwitches.map((sw, i) => (
                <div key={i} className="flex items-center gap-1.5 text-[10px] px-1 py-0.5 rounded bg-white/[0.03]">
                  <span className="font-mono text-white/25">#{sw.turn_number}</span>
                  <LanguageBadge language={sw.from_lang} size="sm" />
                  <span className="text-white/25">→</span>
                  <LanguageBadge language={sw.to_lang} size="sm" />
                  <span className="ml-auto text-white/20 font-mono">{new Date(sw.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Voice gender selector */}
        <div className="p-3 border-t border-white/[0.06] flex-shrink-0">
          <p className="text-[10px] text-white/30 uppercase tracking-wider mb-2 px-1">AI Voice</p>
          <div className="flex gap-1.5">
            <button
              onClick={() => setVoiceGender("male")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                voiceGender === "male"
                  ? "bg-blue-500/20 border border-blue-500/40 text-blue-300"
                  : "border border-white/10 text-white/40 hover:text-white/70 hover:border-white/20"
              }`}
            >
              ♂ Male
            </button>
            <button
              onClick={() => setVoiceGender("female")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                voiceGender === "female"
                  ? "bg-pink-500/20 border border-pink-500/40 text-pink-300"
                  : "border border-white/10 text-white/40 hover:text-white/70 hover:border-white/20"
              }`}
            >
              ♀ Female
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main area ── */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Top bar */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-white/[0.06] flex-shrink-0 flex-wrap gap-y-2">
          {/* Sidebar toggle */}
          <button
            onClick={() => setSidebarOpen((o) => !o)}
            className="p-1.5 rounded-lg hover:bg-white/5 text-white/40 hover:text-white transition-colors flex-shrink-0"
            title="Toggle sidebar"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <h2 className="text-sm font-semibold text-white/80 truncate max-w-[180px] flex-shrink-0">
            {activeChat?.title ?? "New Chat"}
          </h2>

          <div className="flex items-center gap-2 ml-auto flex-wrap justify-end">
            {health && (
              <span
                className={`text-xs px-2 py-1 rounded-full border flex-shrink-0 ${
                  health.lm_studio.startsWith("connected")
                    ? "bg-violet-500/10 text-violet-400 border-violet-500/25"
                    : "bg-red-500/10 text-red-400 border-red-500/25"
                }`}
              >
                LM: {health.lm_studio.startsWith("connected") ? "✓ " + health.lm_model : "✗ offline"}
              </span>
            )}
            <select
              value={activeChat?.scenario ?? ""}
              onChange={(e) => updateActiveChat(() => ({ scenario: e.target.value }))}
              className="input text-xs py-1 w-40 flex-shrink-0"
            >
              <option value="">No scenario</option>
              {SCENARIOS.map((s) => (
                <option key={s.name} value={s.name}>{s.title.split("—")[0].trim()}</option>
              ))}
            </select>
            {activeChat && <LanguageBadge language={activeChat.detectedLang} />}
          </div>
        </div>

        {/* Pipeline status bar */}
        {stage !== "idle" && (
          <div className="px-4 pt-2 flex-shrink-0">
            <StatusTimeline stages={stageItems} />
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div className="mx-4 mt-2 flex-shrink-0 glass-sm p-3 border-red-500/30 bg-red-500/5 text-red-400 text-sm rounded-lg">
            {error}
          </div>
        )}

        {/* Body: conversation + right panels */}
        <div className="flex-1 flex gap-4 overflow-hidden px-4 py-3 min-h-0">
          {/* Chat column */}
          <div className="flex-1 flex flex-col overflow-hidden min-w-0">
            {/* Message list */}
            <div className="flex-1 overflow-y-auto pr-1 min-h-0">
              {activeChat && (
                <ConversationPanel turns={activeChat.turns} voiceGender={voiceGender} thinking={loading} />
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input area */}
            <div className="glass-card p-3 mt-3 flex-shrink-0">
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0 text-center">
                  <MicRecorder
                    onAudioReady={handleAudio}
                    onTranscript={handleTextSend}
                    asrAvailable={health?.asr === "available"}
                    disabled={loading}
                  />
                  <p className="text-[10px] text-white/30 mt-1">
                    {loading ? "Processing…" : "Record"}
                  </p>
                </div>
                <div className="text-white/20 text-xs flex-shrink-0">or</div>
                <div className="flex-1 min-w-0">
                  <TextChatBox onSend={handleTextSend} disabled={loading} />
                </div>
              </div>
            </div>
          </div>

          {/* Right panels */}
          <div className="w-60 flex-shrink-0 space-y-3 overflow-y-auto hidden lg:block">
            {activeChat && <MemoryPanel memory={activeChat.memory} />}
            {activeChat?.lastLatency && (
              <LatencyPanel
                latency={activeChat.lastLatency}
                lmAvailable={activeChat.lastLmAvailable}
                fallback={activeChat.lastFallback}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
