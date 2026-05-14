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

export function speakText(
  text: string,
  lang: string,
  voiceGender: "male" | "female" = "male"
) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const langMap: Record<string, string> = {
    en: "en-US",
    hi: "hi-IN",
    es: "es-ES",
    mixed: "hi-IN",
    unknown: "en-US",
  };
  const targetLang = langMap[lang] ?? "en-US";
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = targetLang;
  utt.rate = 1.0;

  const voices = window.speechSynthesis.getVoices();
  const langCode = targetLang.split("-")[0].toLowerCase();
  const langVoices = voices.filter((v) =>
    v.lang.toLowerCase().startsWith(langCode)
  );

  const maleKeywords = [
    "male", "david", "mark", "richard", "james", "guy", "daniel",
    "alex", "tom", "george", "ryan", "fred", "ralph", "bruce",
    "diego", "jorge", "rishi",
  ];
  const femaleKeywords = [
    "female", "samantha", "victoria", "karen", "moira", "tessa",
    "fiona", "kate", "alice", "anna", "susan", "zira", "hazel",
    "amelie", "paulina", "lekha", "veena",
  ];

  const keywords = voiceGender === "male" ? maleKeywords : femaleKeywords;
  let selectedVoice = langVoices.find((v) =>
    keywords.some((k) => v.name.toLowerCase().includes(k))
  );

  if (!selectedVoice && langVoices.length > 0) {
    // Fallback: second voice for male (often male-pitched), first for female
    selectedVoice =
      voiceGender === "male" && langVoices.length > 1
        ? langVoices[1]
        : langVoices[0];
  }

  if (selectedVoice) utt.voice = selectedVoice;
  window.speechSynthesis.speak(utt);
}
