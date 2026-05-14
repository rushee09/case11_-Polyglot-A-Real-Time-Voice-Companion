// Empty string = relative path → Vite proxy forwards /api/* and /ws/* to backend.
// Set VITE_API_BASE_URL to point at a deployed backend when needed.
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

function getWsBase(): string {
  if (import.meta.env.VITE_WS_BASE_URL) return import.meta.env.VITE_WS_BASE_URL;
  const proto = location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${location.host}`;
}

export interface ChatResponse {
  session_id: string;
  turn_number: number;
  user_text: string;
  detected_language: string;
  language_label: string;
  assistant_response: string;
  response_language: string;
  response_language_label: string;
  language_switched: boolean;
  previous_language?: string;
  memory_snapshot: Record<string, unknown>;
  tool_context?: Record<string, unknown>;
  latency: LatencyBreakdown;
  lm_studio_available: boolean;
  fallback_mode: boolean;
}

export interface LatencyBreakdown {
  audio_upload_ms?: number;
  asr_ms?: number;
  language_detection_ms?: number;
  memory_update_ms?: number;
  tool_ms?: number;
  llm_ms?: number;
  tts_start_ms?: number;
  total_ms: number;
}

export interface HealthResponse {
  status: string;
  lm_studio: string;
  asr: string;
  storage_mode: string;
  whisper_model: string;
  lm_model: string;
}

export async function apiHealth(): Promise<HealthResponse> {
  const r = await fetch(`${API_BASE}/health`);
  if (!r.ok) throw new Error("Backend offline");
  return r.json();
}

export async function apiChat(
  text: string,
  sessionId: string,
  scenarioName?: string
): Promise<ChatResponse> {
  const r = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, session_id: sessionId, scenario_name: scenarioName ?? null }),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail ?? "Chat request failed");
  }
  return r.json();
}

export async function apiTranscribe(audioBlob: Blob): Promise<{
  transcript: string;
  detected_language: string;
  language_label: string;
  latency_ms: number;
}> {
  const fd = new FormData();
  fd.append("file", audioBlob, "recording.webm");
  const r = await fetch(`${API_BASE}/api/transcribe`, { method: "POST", body: fd });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail ?? "Transcription failed");
  }
  return r.json();
}

export async function apiVoiceTurn(
  audioBlob: Blob,
  sessionId: string,
  scenarioName?: string
): Promise<ChatResponse & { transcript: string }> {
  const fd = new FormData();
  fd.append("file", audioBlob, "recording.webm");
  fd.append("session_id", sessionId);
  if (scenarioName) fd.append("scenario_name", scenarioName);
  const r = await fetch(`${API_BASE}/api/voice-turn`, { method: "POST", body: fd });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail ?? "Voice turn failed");
  }
  return r.json();
}

export async function apiDetectLanguage(text: string): Promise<{
  detected_language: string;
  language_label: string;
  confidence?: number;
}> {
  const r = await fetch(`${API_BASE}/api/detect-language`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  return r.json();
}

export async function apiGetScenarios(): Promise<unknown[]> {
  const r = await fetch(`${API_BASE}/api/scenarios`);
  return r.json();
}

export async function apiGetSession(sessionId: string) {
  const r = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
  if (!r.ok) return null;
  return r.json();
}

export async function apiGetSessionLogs(sessionId: string) {
  const r = await fetch(`${API_BASE}/api/sessions/${sessionId}/logs`);
  if (!r.ok) return null;
  return r.json();
}

export function downloadChatCsv() {
  const a = document.createElement("a");
  a.href = `${API_BASE}/api/export-csv`;
  a.download = "polyglot_chat_history.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

export function createWebSocket(sessionId: string): WebSocket {
  return new WebSocket(`${getWsBase()}/ws/session/${sessionId}`);
}

const _maleKeywords = [
  "male", "david", "mark", "richard", "james", "guy", "daniel",
  "alex", "tom", "george", "ryan", "fred", "ralph", "bruce",
  "diego", "jorge", "rishi", "carlos", "miguel", "hendrik",
];
const _femaleKeywords = [
  "female", "samantha", "victoria", "karen", "moira", "tessa",
  "fiona", "kate", "alice", "anna", "susan", "zira", "hazel",
  "amelie", "paulina", "lekha", "veena", "monica", "lucia",
];

const _langMap: Record<string, string> = {
  en: "en-US",
  hi: "hi-IN",
  es: "es-ES",
  // Mixed Hinglish → use English locale for consistent TTS voice
  mixed: "en-US",
  unknown: "en-US",
};

// ── Module-level voice cache ──────────────────────────────────────────────────
// Loaded once; avoids per-call async gaps and prevents onvoiceschanged
// being overwritten when speakText is called before voices have loaded.
let _voiceCache: SpeechSynthesisVoice[] = [];
let _voiceCacheReady = false;

function _populateVoiceCache() {
  if (!( "speechSynthesis" in window)) return;
  const v = window.speechSynthesis.getVoices();
  if (v.length) {
    _voiceCache = v;
    _voiceCacheReady = true;
  } else {
    window.speechSynthesis.addEventListener("voiceschanged", function handler() {
      _voiceCache = window.speechSynthesis.getVoices();
      _voiceCacheReady = true;
      window.speechSynthesis.removeEventListener("voiceschanged", handler);
    });
  }
}

if (typeof window !== "undefined") _populateVoiceCache();
// ─────────────────────────────────────────────────────────────────────────────

function _pickVoice(
  voices: SpeechSynthesisVoice[],
  targetLang: string,
  voiceGender: "male" | "female"
): SpeechSynthesisVoice | undefined {
  const langCode = targetLang.split("-")[0].toLowerCase();

  const exact = voices.filter((v) => v.lang.toLowerCase() === targetLang.toLowerCase());
  const prefix = voices.filter((v) => v.lang.toLowerCase().startsWith(langCode));
  const langVoices = exact.length > 0 ? exact : prefix;
  if (langVoices.length === 0) return undefined;

  const keywords = voiceGender === "male" ? _maleKeywords : _femaleKeywords;
  const oppositeKeywords = voiceGender === "male" ? _femaleKeywords : _maleKeywords;

  // 1. Keyword match for desired gender
  const keywordMatch = langVoices.find((v) =>
    keywords.some((k) => v.name.toLowerCase().includes(k))
  );
  if (keywordMatch) return keywordMatch;

  // 2. Exclude voices that clearly match the opposite gender
  const nonOpposite = langVoices.filter(
    (v) => !oppositeKeywords.some((k) => v.name.toLowerCase().includes(k))
  );
  return nonOpposite[0] ?? langVoices[0];
}

export function speakText(
  text: string,
  lang: string,
  voiceGender: "male" | "female" = "male"
) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();

  const targetLang = _langMap[lang] ?? "en-US";

  function doSpeak(voices: SpeechSynthesisVoice[]) {
    const utt = new SpeechSynthesisUtterance(text);
    utt.lang = targetLang;
    utt.rate = 0.95;
    // Pitch enforces gender as a reliable fallback when no named voice matches
    utt.pitch = voiceGender === "male" ? 0.8 : 1.15;
    const voice = _pickVoice(voices, targetLang, voiceGender);
    if (voice) utt.voice = voice;
    window.speechSynthesis.speak(utt);
  }

  if (_voiceCacheReady) {
    doSpeak(_voiceCache);
  } else {
    // Voices not loaded yet — register a one-shot listener (does NOT overwrite
    // any existing handler, unlike setting onvoiceschanged directly)
    window.speechSynthesis.addEventListener("voiceschanged", function handler() {
      _voiceCache = window.speechSynthesis.getVoices();
      _voiceCacheReady = true;
      window.speechSynthesis.removeEventListener("voiceschanged", handler);
      doSpeak(_voiceCache);
    }, { once: true });
  }
}
