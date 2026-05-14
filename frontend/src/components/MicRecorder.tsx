import { useState, useRef, useEffect } from "react";

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
  const [stopping, setStopping] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const srRef = useRef<SpeechRecognition | null>(null);
  const stopTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const countdownIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Grace-period duration in seconds
  const STOP_GRACE_SEC = 2.5;

  function clearStopTimer() {
    if (stopTimerRef.current) clearTimeout(stopTimerRef.current);
    if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
    stopTimerRef.current = null;
    countdownIntervalRef.current = null;
    setStopping(false);
    setCountdown(0);
  }

  // Clean up timers on unmount
  useEffect(() => () => clearStopTimer(), []);

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

  function commitStop() {
    clearStopTimer();
    if (srRef.current) {
      stopBrowserSR();
    } else {
      mediaRef.current?.stop();
      setRecording(false);
    }
  }

  function scheduleStop() {
    setStopping(true);
    setCountdown(Math.ceil(STOP_GRACE_SEC));

    // Tick countdown every second
    countdownIntervalRef.current = setInterval(() => {
      setCountdown((c) => {
        const next = c - 1;
        return next > 0 ? next : 0;
      });
    }, 1000);

    stopTimerRef.current = setTimeout(commitStop, STOP_GRACE_SEC * 1000);
  }

  function cancelStop() {
    clearStopTimer();
    // User is still speaking — keep recording normally
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

  // ── Routing ───────────────────────────────────────────────────────────────
  const useBrowserSR = !asrAvailable;

  function handleClick() {
    if (!recording) {
      // Start fresh
      clearStopTimer();
      useBrowserSR ? startBrowserSR() : startRecording();
    } else if (stopping) {
      // User clicked again during grace period → cancel stop, keep recording
      cancelStop();
    } else {
      // First click to stop → begin grace period
      scheduleStop();
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
            stopping
              ? "bg-amber-500 animate-pulse"
              : recording
              ? "bg-red-500 recording-pulse"
              : "bg-violet-500 hover:bg-violet-400 active:scale-95"
          }`}
        title={
          stopping
            ? `Stopping in ${countdown}s — tap to keep recording`
            : recording
            ? "Stop recording"
            : "Start recording"
        }
      >
        {stopping ? (
          <span className="text-white font-bold text-lg leading-none">{countdown}</span>
        ) : recording ? (
          <span className="w-5 h-5 rounded bg-white" />
        ) : (
          <svg className="w-7 h-7 text-black" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 1a4 4 0 0 0-4 4v6a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4zm-1 18.93V22h2v-2.07A8 8 0 0 0 20 12h-2a6 6 0 0 1-12 0H4a8 8 0 0 0 7 7.93z" />
          </svg>
        )}
      </button>
      {stopping && (
        <span className="text-[9px] text-amber-300/80 font-mono text-center leading-tight">
          tap to keep
        </span>
      )}
      {useBrowserSR && !stopping && (
        <span className="text-[9px] text-amber-400/70 font-mono">browser SR</span>
      )}
    </div>
  );
}
