interface Props {
  language: string;
  label?: string;
  size?: "sm" | "md";
}

const LANG_CONFIG: Record<string, { emoji: string; className: string; defaultLabel: string }> = {
  en: { emoji: "🇺🇸", className: "badge badge-en", defaultLabel: "English" },
  hi: { emoji: "🇮🇳", className: "badge badge-hi", defaultLabel: "Hindi" },
  es: { emoji: "🇪🇸", className: "badge badge-es", defaultLabel: "Spanish" },
  mixed: { emoji: "🔀", className: "badge badge-mixed", defaultLabel: "Mixed" },
  unknown: { emoji: "❓", className: "badge badge-unknown", defaultLabel: "Unknown" },
};

export default function LanguageBadge({ language, label, size = "md" }: Props) {
  const cfg = LANG_CONFIG[language] ?? LANG_CONFIG.unknown;
  const displayLabel = label ?? cfg.defaultLabel;
  return (
    <span className={`${cfg.className} ${size === "sm" ? "text-[10px] py-0.5 px-2" : ""}`}>
      <span>{cfg.emoji}</span>
      <span>{displayLabel}</span>
    </span>
  );
}
