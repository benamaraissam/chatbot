import { useEffect, useState } from "react";
import { useChatbot } from "../hooks";
import { CopyButton } from "./CopyButton";

interface CodeBlockProps {
  language?: string;
  children: string;
}

export function CodeBlock({ language, children }: CodeBlockProps) {
  const [html, setHtml] = useState<string | null>(null);
  const resolvedTheme = useChatbot((s) => s.resolvedTheme);
  const shikiTheme = resolvedTheme === "dark" ? "github-dark" : "github-light";

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { codeToHtml } = await import("shiki");
        const out = await codeToHtml(children, {
          lang: language ?? "text",
          theme: shikiTheme,
        });
        if (!cancelled) setHtml(out);
      } catch {
        if (!cancelled) setHtml(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [children, language, shikiTheme]);

  return (
    <div className="cb-code-block">
      <div className="cb-code-block-header">
        <span className="cb-code-block-lang">{language ?? "code"}</span>
        <CopyButton text={children} ariaLabel="Copy code" />
      </div>
      <div className="cb-code-block-scroll">
        {html ? (
          <div
            className="cb-code-block-shiki"
            dangerouslySetInnerHTML={{ __html: html }}
          />
        ) : (
          <pre className="cb-code-block-fallback">
            <code>{children}</code>
          </pre>
        )}
      </div>
    </div>
  );
}
