
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Bot, User } from "lucide-react";
import SourceCard from "./SourceCard";
import { SourceDocument } from "@/lib/api";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceDocument[];
  isStreaming?: boolean;
}

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className="animate-fade-in"
      style={{
        display: "flex",
        flexDirection: isUser ? "row-reverse" : "row",
        gap: "12px",
        padding: "4px 0",
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: "34px",
          height: "34px",
          borderRadius: "50%",
          background: isUser ? "var(--accent-dim)" : "rgba(124,111,205,0.25)",
          border: `1px solid ${isUser ? "var(--border)" : "var(--accent)"}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          marginTop: "2px",
        }}
      >
        {isUser ? (
          <User size={16} color="var(--text-secondary)" />
        ) : (
          <Bot size={16} color="var(--accent-bright)" />
        )}
      </div>

      {/* Bubble */}
      <div style={{ maxWidth: "75%", display: "flex", flexDirection: "column", gap: "4px" }}>
        <div
          style={{
            background: isUser ? "var(--user-bubble)" : "var(--ai-bubble)",
            border: "1px solid var(--border)",
            borderRadius: isUser ? "16px 4px 16px 16px" : "4px 16px 16px 16px",
            padding: "12px 16px",
            lineHeight: 1.65,
            color: "var(--text-primary)",
            fontSize: "14px",
          }}
        >
          {isUser ? (
            <span style={{ whiteSpace: "pre-wrap" }}>{message.content}</span>
          ) : (
            <div className="prose">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, inline, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || "");
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={vscDarkPlus as any}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, "")}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>

              {/* Typing indicator */}
              {message.isStreaming && message.content === "" && (
                <div style={{ display: "flex", gap: "4px", padding: "4px 0", alignItems: "center" }}>
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <SourceCard sources={message.sources} />
        )}
      </div>
    </div>
  );
}
