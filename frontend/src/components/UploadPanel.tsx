
import { useCallback, useRef, useState } from "react";
import { ingestFile } from "@/lib/api";
import { Upload, FileText, CheckCircle, AlertCircle, Loader } from "lucide-react";

interface UploadState {
  file: File;
  status: "uploading" | "done" | "error";
  message: string;
  chunks?: number;
}

export default function UploadPanel() {
  const [uploads, setUploads] = useState<UploadState[]>([]);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const processFile = async (file: File) => {
    const entry: UploadState = { file, status: "uploading", message: "Đang xử lý…" };
    setUploads((prev) => [entry, ...prev]);

    try {
      const result = await ingestFile(file);
      setUploads((prev) =>
        prev.map((u) =>
          u.file === file
            ? { ...u, status: "done", message: result.message, chunks: result.chunks_indexed }
            : u
        )
      );
    } catch (err: any) {
      setUploads((prev) =>
        prev.map((u) =>
          u.file === file ? { ...u, status: "error", message: err.message } : u
        )
      );
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    Array.from(e.dataTransfer.files).forEach(processFile);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    Array.from(e.target.files || []).forEach(processFile);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onClick={() => inputRef.current?.click()}
        style={{
          border: `2px dashed ${dragging ? "var(--accent)" : "var(--border)"}`,
          borderRadius: "10px",
          padding: "20px 12px",
          textAlign: "center",
          cursor: "pointer",
          background: dragging ? "var(--accent-dim)" : "var(--bg-elevated)",
          transition: "all 0.2s",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "8px",
        }}
      >
        <Upload size={22} color={dragging ? "var(--accent-bright)" : "var(--text-muted)"} />
        <span style={{ color: "var(--text-secondary)", fontSize: "12px" }}>
          Kéo thả hoặc <span style={{ color: "var(--accent-bright)" }}>chọn file</span>
        </span>
        <span style={{ color: "var(--text-muted)", fontSize: "11px" }}>
          PDF, TXT, DOCX, MD
        </span>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt,.md,.docx,.doc"
          multiple
          style={{ display: "none" }}
          onChange={handleChange}
        />
      </div>

      {/* Upload history */}
      {uploads.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "6px",  maxHeight: "200px", overflowY: "auto" }}>
          {uploads.map((u, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "8px",
                padding: "8px 10px",
                background: "var(--bg-elevated)",
                borderRadius: "8px",
                border: "1px solid var(--border)",
                fontSize: "12px",
              }}
            >
              <FileText size={14} color="var(--text-muted)" style={{ flexShrink: 0, marginTop: 1 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ color: "var(--text-primary)", fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {u.file.name}
                </div>
                <div style={{ color: u.status === "error" ? "var(--error)" : "var(--text-muted)", marginTop: 2 }}>
                  {u.status === "done" ? `✓ ${u.chunks} chunks indexed` : u.message}
                </div>
              </div>
              {u.status === "uploading" && <Loader size={13} color="var(--accent)" className="animate-spin" />}
              {u.status === "done"      && <CheckCircle size={13} color="var(--success)" />}
              {u.status === "error"     && <AlertCircle size={13} color="var(--error)" />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
