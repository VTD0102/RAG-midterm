
import { Session, fetchSessions, deleteSession } from "@/lib/api";
import { useEffect, useState } from "react";
import { MessageSquare, Plus, Trash2, Bot, RefreshCw } from "lucide-react";
import UploadPanel from "./UploadPanel";
import FileManager from "./FileManager";

interface SidebarProps {
  currentSessionId: string;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
}

export default function Sidebar({ currentSessionId, onSelectSession, onNewSession }: SidebarProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);

  const load = async () => {
    setLoading(true);
    const data = await fetchSessions();
    setSessions(data);
    setLoading(false);
  };

  useEffect(() => { load(); }, [currentSessionId]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await deleteSession(id);
    if (id === currentSessionId) onNewSession();
    await load();
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });
  };

  return (
    <aside
      style={{
        width: "260px",
        minWidth: "260px",
        height: "100%",
        background: "var(--bg-surface)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "20px 16px 12px",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          gap: "10px",
        }}
      >
        <div
          style={{
            width: "30px",
            height: "30px",
            borderRadius: "8px",
            background: "var(--accent-dim)",
            border: "1px solid var(--accent)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
          className="animate-glow"
        >
          <Bot size={16} color="var(--accent-bright)" />
        </div>
        <div>
          <div style={{ color: "var(--text-primary)", fontWeight: 600, fontSize: "14px" }}>
            RAG Chatbot
          </div>
          <div style={{ color: "var(--text-muted)", fontSize: "11px" }}>Gemini × Pinecone</div>
        </div>
      </div>

      {/* Actions */}
      <div style={{ padding: "12px" }}>
        <button
          onClick={onNewSession}
          style={{
            width: "100%",
            padding: "9px 12px",
            background: "var(--accent)",
            color: "#fff",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "6px",
            fontWeight: 600,
            fontSize: "13px",
            transition: "opacity 0.2s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.85")}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
        >
          <Plus size={15} />
          Cuộc trò chuyện mới
        </button>
      </div>

      {/* Sessions list */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0 8px" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "4px 8px 6px",
          }}
        >
          <span style={{ color: "var(--text-muted)", fontSize: "11px", fontWeight: 600, letterSpacing: "0.05em" }}>
            LỊCH SỬ
          </span>
          <button
            onClick={load}
            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)" }}
          >
            <RefreshCw size={12} style={{ display: "block" }} className={loading ? "animate-spin" : ""} />
          </button>
        </div>

        {sessions.length === 0 ? (
          <div style={{ padding: "16px 8px", color: "var(--text-muted)", fontSize: "12px", textAlign: "center" }}>
            Chưa có cuộc trò chuyện nào
          </div>
        ) : (
          sessions.map((s) => (
            <div
              key={s.session_id}
              onClick={() => onSelectSession(s.session_id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 10px",
                borderRadius: "8px",
                cursor: "pointer",
                background: s.session_id === currentSessionId ? "var(--bg-hover)" : "transparent",
                border: s.session_id === currentSessionId ? "1px solid var(--border-bright)" : "1px solid transparent",
                marginBottom: "2px",
                transition: "background 0.15s",
              }}
              onMouseEnter={(e) => {
                if (s.session_id !== currentSessionId)
                  e.currentTarget.style.background = "var(--bg-elevated)";
              }}
              onMouseLeave={(e) => {
                if (s.session_id !== currentSessionId)
                  e.currentTarget.style.background = "transparent";
              }}
            >
              <MessageSquare size={13} color="var(--text-muted)" style={{ flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    color: "var(--text-primary)",
                    fontSize: "12px",
                    fontWeight: 500,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {s.title}
                </div>
                <div style={{ color: "var(--text-muted)", fontSize: "10px" }}>
                  {s.message_count} tin · {formatDate(s.last_active)}
                </div>
              </div>
              <button
                onClick={(e) => handleDelete(e, s.session_id)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  color: "var(--text-muted)",
                  padding: "4px",
                  opacity: 0.5,
                  transition: "opacity 0.15s, color 0.15s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.opacity = "1";
                  e.currentTarget.style.color = "var(--error)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.opacity = "0.5";
                  e.currentTarget.style.color = "var(--text-muted)";
                }}
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Upload documents */}
      <div
        style={{
          borderTop: "1px solid var(--border)",
          padding: "12px",
        }}
      >
        <button
          onClick={() => setShowUpload(!showUpload)}
          style={{
            width: "100%",
            padding: "7px 12px",
            background: "var(--bg-elevated)",
            color: "var(--text-secondary)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            cursor: "pointer",
            fontSize: "12px",
            fontWeight: 500,
            marginBottom: showUpload ? "10px" : 0,
            display: "flex",
            alignItems: "center",
            gap: "6px",
            transition: "border-color 0.2s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--accent)")}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
        >
          📂 {showUpload ? "Ẩn quản lý tài liệu" : "Quản lý / Upload tài liệu"}
        </button>
        {showUpload && (
          <>
            <UploadPanel />
            <FileManager />
          </>
        )}
      </div>
    </aside>
  );
}
