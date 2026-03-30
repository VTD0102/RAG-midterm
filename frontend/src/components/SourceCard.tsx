
import { SourceDocument } from "@/lib/api";
import { ChevronDown, ChevronUp, FileText } from "lucide-react";
import { useState } from "react";

interface SourceCardProps {
  sources: SourceDocument[];
}

export default function SourceCard({ sources }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div
      style={{
        marginTop: "8px",
        border: "1px solid var(--border)",
        borderRadius: "8px",
        overflow: "hidden",
        fontSize: "12px",
      }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          gap: "6px",
          padding: "8px 12px",
          background: "var(--bg-elevated)",
          color: "var(--text-secondary)",
          border: "none",
          cursor: "pointer",
          textAlign: "left",
          transition: "background 0.2s",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-hover)")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "var(--bg-elevated)")}
      >
        <FileText size={13} color="var(--accent)" />
        <span style={{ flex: 1, color: "var(--accent-bright)" }}>
          {sources.length} nguồn tài liệu
        </span>
        {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
      </button>

      {expanded && (
        <div style={{ background: "var(--bg-surface)" }}>
          {sources.map((src, i) => (
            <div
              key={i}
              style={{
                padding: "10px 12px",
                borderTop: "1px solid var(--border)",
                display: "flex",
                flexDirection: "column",
                gap: "4px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <span
                  style={{
                    background: "var(--accent-dim)",
                    color: "var(--accent-bright)",
                    borderRadius: "4px",
                    padding: "1px 6px",
                    fontWeight: 600,
                  }}
                >
                  [{i + 1}]
                </span>
                <span style={{ color: "var(--accent-bright)", fontWeight: 500 }}>
                  {src.source}
                  {src.page !== undefined && src.page !== null
                    ? ` — trang ${src.page + 1}`
                    : ""}
                </span>
              </div>
              <p style={{ color: "var(--text-muted)", lineHeight: 1.5 }}>
                {src.content.length > 200
                  ? src.content.slice(0, 200) + "…"
                  : src.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
