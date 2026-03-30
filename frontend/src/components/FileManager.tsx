import { useEffect, useState } from "react";
import { FileItem, getFiles, deleteFile } from "@/lib/api";
import { FileText, Trash2, Loader, RefreshCw } from "lucide-react";

export default function FileManager() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [deletingFile, setDeletingFile] = useState<string | null>(null);

  const loadFiles = async () => {
    setLoading(true);
    try {
      const data = await getFiles();
      setFiles(data);
    } catch (err) {
      console.error("Failed to load files", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const handleDelete = async (filename: string) => {
    if (!window.confirm(`Xóa file "${filename}" khỏi dữ liệu và Pinecone?`)) return;
    setDeletingFile(filename);
    try {
      await deleteFile(filename);
      await loadFiles();
    } catch (err) {
      alert(`Lỗi: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setDeletingFile(null);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "12px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ color: "var(--text-muted)", fontSize: "11px", fontWeight: 600, letterSpacing: "0.05em" }}>
          TÀI LIỆU ĐÃ TẢI LÊN ({files.length})
        </span>
        <button
          onClick={loadFiles}
          style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)" }}
        >
          <RefreshCw size={12} style={{ display: "block" }} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      {files.length === 0 ? (
        <div style={{ color: "var(--text-muted)", fontSize: "12px", textAlign: "center", padding: "8px" }}>
          Chưa có tài liệu nào
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "6px", maxHeight: "200px", overflowY: "auto", paddingRight: "4px" }}>
          {files.map((f) => (
            <div
              key={f.filename}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 10px",
                background: "var(--bg-elevated)",
                borderRadius: "8px",
                border: "1px solid var(--border)",
                fontSize: "12px",
                opacity: deletingFile === f.filename ? 0.5 : 1,
              }}
            >
              <FileText size={14} color="var(--accent)" style={{ flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ color: "var(--text-primary)", fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {f.filename}
                </div>
                <div style={{ color: "var(--text-muted)", marginTop: 2, fontSize: "10px" }}>
                  {formatSize(f.size_bytes)}
                </div>
              </div>
              <button
                onClick={() => handleDelete(f.filename)}
                disabled={deletingFile === f.filename}
                style={{
                  background: "none",
                  border: "none",
                  cursor: deletingFile === f.filename ? "not-allowed" : "pointer",
                  color: "var(--text-muted)",
                  padding: "4px",
                  transition: "color 0.15s",
                }}
                onMouseEnter={(e) => {
                  if (deletingFile !== f.filename) e.currentTarget.style.color = "var(--error)";
                }}
                onMouseLeave={(e) => {
                  if (deletingFile !== f.filename) e.currentTarget.style.color = "var(--text-muted)";
                }}
              >
                {deletingFile === f.filename ? <Loader size={12} className="animate-spin" /> : <Trash2 size={12} />}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
