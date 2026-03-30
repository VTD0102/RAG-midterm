
import { useCallback, useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { Send, Square } from "lucide-react";
import MessageBubble, { Message } from "./MessageBubble";
import { streamChatWithEvents, SourceDocument } from "@/lib/api";

interface ChatWindowProps {
  sessionId: string;
}

export default function ChatWindow({ sessionId }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef(false);

  // Reset messages on session change
  useEffect(() => {
    setMessages([]);
  }, [sessionId]);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 150) + "px";
  };

  const sendMessage = useCallback(async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage: Message = {
      id: uuidv4(),
      role: "user",
      content: input.trim(),
    };
    const aiMessageId = uuidv4();
    const aiMessage: Message = {
      id: aiMessageId,
      role: "assistant",
      content: "",
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, aiMessage]);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    setIsStreaming(true);
    abortRef.current = false;

    await streamChatWithEvents(
      userMessage.content,
      sessionId,
      (token) => {
        if (abortRef.current) return;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMessageId ? { ...m, content: m.content + token } : m
          )
        );
      },
      (sources: SourceDocument[]) => {
        setMessages((prev) =>
          prev.map((m) => (m.id === aiMessageId ? { ...m, sources } : m))
        );
      },
      () => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMessageId ? { ...m, isStreaming: false } : m
          )
        );
        setIsStreaming(false);
      },
      (err) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMessageId
              ? { ...m, content: `⚠️ Lỗi: ${err}`, isStreaming: false }
              : m
          )
        );
        setIsStreaming(false);
      }
    );
  }, [input, isStreaming, sessionId]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleStop = () => {
    abortRef.current = true;
    setIsStreaming(false);
    setMessages((prev) =>
      prev.map((m) => (m.isStreaming ? { ...m, isStreaming: false } : m))
    );
  };

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        height: "100%",
        overflow: "hidden",
        background: "var(--bg-base)",
      }}
    >
      {/* Messages area */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "24px 24px 8px",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "12px",
              color: "var(--text-muted)",
            }}
          >
            <div
              style={{
                fontSize: "40px",
                filter: "drop-shadow(0 0 16px var(--accent-glow))",
              }}
            >
              🤖
            </div>
            <div style={{ fontSize: "18px", color: "var(--text-secondary)", fontWeight: 600 }}>
              Hỏi bất cứ điều gì về tài liệu của bạn
            </div>
            <div style={{ fontSize: "13px", maxWidth: "360px", textAlign: "center" }}>
              Upload tài liệu ở thanh bên trái, sau đó đặt câu hỏi. AI sẽ tìm kiếm và tổng hợp thông tin từ tài liệu của bạn.
            </div>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div
        style={{
          padding: "16px 24px",
          borderTop: "1px solid var(--border)",
          background: "var(--bg-surface)",
        }}
      >
        <div
          style={{
            display: "flex",
            gap: "10px",
            alignItems: "flex-end",
            background: "var(--bg-elevated)",
            border: "1px solid var(--border-bright)",
            borderRadius: "14px",
            padding: "10px 12px",
            transition: "border-color 0.2s",
          }}
          onFocus={() => {}}
        >
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Nhập câu hỏi… (Enter để gửi, Shift+Enter để xuống dòng)"
            rows={1}
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              resize: "none",
              color: "var(--text-primary)",
              fontSize: "14px",
              lineHeight: "1.6",
              fontFamily: "inherit",
              maxHeight: "150px",
              overflowY: "auto",
            }}
          />

          {isStreaming ? (
            <button
              onClick={handleStop}
              title="Dừng"
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "10px",
                background: "var(--error)",
                border: "none",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                transition: "opacity 0.2s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.8")}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
            >
              <Square size={14} color="#fff" fill="#fff" />
            </button>
          ) : (
            <button
              onClick={sendMessage}
              disabled={!input.trim()}
              title="Gửi"
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "10px",
                background: input.trim() ? "var(--accent)" : "var(--bg-hover)",
                border: "none",
                cursor: input.trim() ? "pointer" : "not-allowed",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                transition: "background 0.2s, opacity 0.2s",
              }}
              onMouseEnter={(e) => {
                if (input.trim()) e.currentTarget.style.opacity = "0.85";
              }}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
            >
              <Send size={15} color={input.trim() ? "#fff" : "var(--text-muted)"} />
            </button>
          )}
        </div>
        <div style={{ textAlign: "center", color: "var(--text-muted)", fontSize: "11px", marginTop: "8px" }}>
          Powered by Google Gemini · Pinecone · LangChain
        </div>
      </div>
    </div>
  );
}
