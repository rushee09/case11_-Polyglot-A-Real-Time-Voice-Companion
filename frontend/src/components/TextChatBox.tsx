import { useState } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function TextChatBox({ onSend, disabled, placeholder }: Props) {
  const [text, setText] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        className="input flex-1"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder ?? "Type a message or use the mic…"}
        disabled={disabled}
        autoComplete="off"
        spellCheck={false}
      />
      <button
        type="submit"
        disabled={!text.trim() || disabled}
        className="btn-primary px-5"
      >
        Send
      </button>
    </form>
  );
}
