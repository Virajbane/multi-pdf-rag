"use client";
import { useState } from "react";
import PDFUploader from "@/components/PDFUploader";
import ChatInterface from "@/components/ChatInterface";
import { UploadedFile } from "@/types";

const INITIALS = (name: string) => name.split(/[\s._-]/)[0].slice(0, 2).toUpperCase();
const COLORS = ["rgba(124,109,250,0.15)", "rgba(52,211,153,0.12)", "rgba(251,191,36,0.12)", "rgba(248,113,113,0.12)"];
const TEXT_COLORS = ["var(--accent2)", "var(--green)", "var(--amber)", "var(--red)"];

export default function Home() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", height: "100vh" }}>

      {/* Sidebar */}
      <aside style={{ background: "var(--bg2)", borderRight: "1px solid var(--border)", display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ padding: "20px 20px 16px", borderBottom: "1px solid var(--border)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
            <div style={{ width: 32, height: 32, background: "var(--accent3)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text)" }}>RAG Assistant</div>
              <div style={{ fontSize: 11, color: "var(--text3)", fontFamily: "'DM Mono',monospace" }}>qwen2.5 · chromadb</div>
            </div>
          </div>
        </div>

        <PDFUploader onUpload={(f) => setUploadedFiles(prev => [...prev, f])} />

        {uploadedFiles.length > 0 && (
          <div style={{ flex: 1, overflowY: "auto", padding: "0 12px 12px" }}>
            <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "1.5px", color: "var(--text3)", textTransform: "uppercase", padding: "12px 8px 8px", fontFamily: "'DM Mono',monospace" }}>
              Documents ({uploadedFiles.length})
            </div>
            {uploadedFiles.map((f, i) => (
              <div key={f.file_id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px", borderRadius: 8, marginBottom: 2, background: i === 0 ? "rgba(124,109,250,0.1)" : "transparent", border: i === 0 ? "1px solid rgba(124,109,250,0.2)" : "1px solid transparent" }}>
                <div style={{ width: 28, height: 28, borderRadius: 6, background: COLORS[i % COLORS.length], color: TEXT_COLORS[i % TEXT_COLORS.length], display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 700, fontFamily: "'DM Mono',monospace", flexShrink: 0 }}>
                  {INITIALS(f.filename)}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 500, color: "var(--text)", overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis" }}>{f.filename}</div>
                  <div style={{ fontSize: 10, color: "var(--text3)", fontFamily: "'DM Mono',monospace" }}>{f.pages} pages · {f.chunks_created} chunks</div>
                </div>
                <button onClick={() => setUploadedFiles(prev => prev.filter(x => x.file_id !== f.file_id))}
                  style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text3)", opacity: 0, padding: 4 }}
                  onMouseEnter={e => (e.currentTarget.style.opacity = "1")}
                  onMouseLeave={e => (e.currentTarget.style.opacity = "0")}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </aside>

      {/* Chat */}
      <main style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <ChatInterface uploadedFiles={uploadedFiles} />
      </main>
    </div>
  );
}