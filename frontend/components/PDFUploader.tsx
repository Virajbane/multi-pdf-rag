"use client";
import { useState, useRef } from "react";
import { uploadPDF } from "@/lib/api";
import { UploadedFile } from "@/types";

interface Props { onUpload: (file: UploadedFile) => void; }

export default function PDFUploader({ onUpload }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file.name.endsWith(".pdf")) { setError("Only PDFs accepted"); return; }
    setIsUploading(true); setError(null);
    try {
      const result = await uploadPDF(file);
      onUpload({ file_id: result.file_id, filename: result.filename, pages: result.pages, chunks_created: result.chunks_created });
    } catch (err: any) { setError(err.message); }
    finally { setIsUploading(false); }
  };

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => { e.preventDefault(); setIsDragging(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
      style={{
        margin: "16px", border: `1px dashed ${isDragging ? "var(--accent)" : "var(--border2)"}`,
        borderRadius: "10px", padding: "20px", textAlign: "center", cursor: "pointer",
        background: isDragging ? "rgba(124,109,250,0.06)" : "var(--bg3)", transition: "all 0.2s",
        opacity: isUploading ? 0.6 : 1, pointerEvents: isUploading ? "none" : "auto"
      }}>
      <input ref={inputRef} type="file" accept=".pdf" style={{ display: "none" }}
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
      <div style={{ width: 36, height: 36, margin: "0 auto 10px", background: "rgba(124,109,250,0.12)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
        {isUploading
          ? <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent2)" strokeWidth="2"><path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/><path d="M9 12l2 2 4-4"/></svg>
          : <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent2)" strokeWidth="1.8"><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/></svg>}
      </div>
      <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text)", marginBottom: 3 }}>
        {isUploading ? "Processing..." : "Drop PDF here"}
      </div>
      <div style={{ fontSize: 11, color: "var(--text3)" }}>
        {isUploading ? "Embedding chunks into ChromaDB" : "or click to browse · max 50MB"}
      </div>
      {error && <div style={{ marginTop: 8, fontSize: 11, color: "var(--red)" }}>{error}</div>}
    </div>
  );
}