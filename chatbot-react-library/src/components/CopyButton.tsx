import { Check, Copy } from "lucide-react";
import { useState } from "react";

interface CopyButtonProps {
  text: string;
  /** Accessible label when not showing visible text */
  ariaLabel?: string;
  /** Show "Copy" / "Copied" label beside icon */
  showLabel?: boolean;
  className?: string;
}

export function CopyButton({
  text,
  ariaLabel = "Copy to clipboard",
  showLabel = true,
  className = "",
}: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!text.trim()) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard denied */
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      className={`cb-copy-btn ${copied ? "cb-copy-btn--copied" : ""} ${className}`.trim()}
      aria-label={copied ? "Copied" : ariaLabel}
    >
      {copied ? <Check size={14} strokeWidth={2.25} /> : <Copy size={14} strokeWidth={2.25} />}
      {showLabel && <span>{copied ? "Copied" : "Copy"}</span>}
    </button>
  );
}
