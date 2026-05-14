import { useState, useRef } from "react";

// Extend Window to include webkit-prefixed Speech Recognition
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}

interface Props {
  onAudioReady: (blob: Blob) => void;
  /** Called with transcript text when browser Speech Recognition is used as fallback */
  onTranscript?: (text: string) => void;
  /** When false, use browser Speech Recognition instead of sending a blob to the backend */
  asrAvailable?: boolean;
  disabled?: boolean;
}

export default function MicRecorder({
  onAudioReady,
  onTranscript,
  asrAvailable = true,
  disabled,
}: Props) {
  const [recording, setRecording] = useState(false);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const srRef = useRef<SpeechRecognition | null>(null);

  // ── Browser Speech Recognition fallback ──────────────────────────────────
  function startBrowserSR() {
    const SR = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!SR) {
      alert(
        "Your browser does not support speech recognition.\n" +
          "Please type your message instead, or install faster-whisper on the backend."
      );
      return;
    }
    const sr = new SR();
    sr.lang = "en-US";
    sr.interimResults = false;
    sr.maxAlternatives = 1;
    sr.continuous = false;
    srRef.current = sr;

    sr.onresult = (e) => {
      const text = e.results[0]?.[0]?.transcript ?? "";
      if (text.trim()) onTranscript?.(text.trim());
    };
    sr.onerror = (e) => {
      console.warn("[SpeechRecognition] error", e.error);
      setRecording(false);
    };
    sr.onend = () => setRecording(false);

    sr.start();
    setRecording(true);
  }

  function stopBrowserSR() {
    srRef.current?.stop();
    setRecording(false);
  }

  // ── MediaRecorder path (backend Whisper) ─────────────────────────────────
  async function startRecording() {
    if (!navigator.mediaDevices) {
      alert("Microphone not available in this browser.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        onAudioReady(blob);
        stream.getTracks().forEach((t) => t.stop());
      };
      mr.start();
      mediaRef.current = mr;
      setRecording(true);
    } catch (err) {
      alert("Could not access microphone: " + (err as Error).message);
    }
  }

  function stopRecording() {
    mediaRef.current?.stop();
    setRecording(false);
  }

  // ── Routing ───────────────────────────────────────────────────────────────
  const useBrowserSR = !asrAvailable;

  function handleClick() {
    if (recording) {
      useBrowserSR ? stopBrowserSR() : stopRecording();
    } else {
      useBrowserSR ? startBrowserSR() : startRecording();
    }
  }

  return (
    <div className="flex flex-col items-center gap-1">
      <button
        type="button"
        disabled={disabled}
        onClick={handleClick}
        className={`relative w-16 h-16 rounded-full flex items-center justify-center transition-all
          disabled:opacity-40 disabled:cursor-not-allowed ${
            recording
              ? "bg-red-500 recording-pulse"
              : "bg-violet-500 hover:bg-violet-400 active:scale-95"
          }`}
        title={recording ? "Stop recording" : "Start recording"}
      >
        {recording ? (
          <span className="w-5 h-5 rounded bg-white" />
        ) : (
          <svg className="w-7 h-7 text-black" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 1a4 4 0 0 0-4 4v6a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4zm-1 18.93V22h2v-2.07A8 8 0 0 0 20 12h-2a6 6 0 0 1-12 0H4a8 8 0 0 0 7 7.93z" />
          </svg>
        )}
      </button>
      {useBrowserSR && (
        <span className="text-[9px] text-amber-400/70 font-mono">browser SR</span>
      )}
    </div>
  );
}
