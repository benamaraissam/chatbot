import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { CodeBlock } from "./CodeBlock";

interface MarkdownMessageProps {
  content: string;
}

export function MarkdownMessage({ content }: MarkdownMessageProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      className="cb-prose cb-max-w-none cb-min-w-0 cb-text-[13px] cb-leading-[1.55] cb-text-cb-text
        [&_a]:cb-text-cb-primary [&_a]:cb-underline [&_a]:cb-underline-offset-2
        [&_blockquote]:cb-border-l-2 [&_blockquote]:cb-border-cb-border [&_blockquote]:cb-pl-3 [&_blockquote]:cb-text-cb-muted
        [&_h1]:cb-text-lg [&_h1]:cb-font-semibold [&_h2]:cb-text-base [&_h2]:cb-font-semibold
        [&_ol]:cb-my-2 [&_ol]:cb-list-decimal [&_ol]:cb-pl-5
        [&_p]:cb-my-2 [&_p:first-child]:cb-mt-0 [&_p:last-child]:cb-mb-0
        [&_table]:cb-my-2 [&_table]:cb-block [&_table]:cb-max-w-full [&_table]:cb-overflow-x-auto [&_table]:cb-border-collapse [&_table]:cb-text-xs
        [&_td]:cb-border [&_td]:cb-border-cb-border [&_td]:cb-px-2 [&_td]:cb-py-1
        [&_th]:cb-border [&_th]:cb-border-cb-border [&_th]:cb-bg-[var(--cb-surface-hover)] [&_th]:cb-px-2 [&_th]:cb-py-1 [&_th]:cb-text-left
        [&_ul]:cb-my-2 [&_ul]:cb-list-disc [&_ul]:cb-pl-5"
      components={{
        pre({ children }) {
          return <>{children}</>;
        },
        a({ href, children, ...props }) {
          return (
            <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
              {children}
            </a>
          );
        },
        code({ className, children, ...props }) {
          const text = String(children).replace(/\n$/, "");
          const match = /language-(\w+)/.exec(className ?? "");
          const inline = !match && !text.includes("\n");
          if (inline) {
            return (
              <code
                className="cb-rounded cb-bg-[var(--cb-surface-hover)] cb-px-1.5 cb-py-0.5 cb-font-mono cb-text-[0.85em]"
                {...props}
              >
                {text}
              </code>
            );
          }
          return <CodeBlock language={match?.[1]}>{text}</CodeBlock>;
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
