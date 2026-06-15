"use client";
import { useState } from "react";
import { SourceDocument } from "@/types";

export default function SourceCitation({ sources }: { sources: SourceDocument[] }) {
  const [open, setOpen] = useState(false);
  if (!sources.length) return null;
  return (
    <div style={{ marginTop: 10, background: "var(--bg4)", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden", fontSize: 11 }}>
      <div onClick={() => setOpen(!open)} style={{ padding: "8px 12px", cursor: "pointer", color: "var(--text2)", display: "flex", alignItems: "center", gap: 6, fontFamily: "'DM Mono', monospace" }}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/></svg>
        {sources.length} source{sources.length > 1 ? "s" : ""} · {sources[0]?.filename}
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginLeft: "auto", transform: open ? "rotate(180deg)" : "none", transition: "0.2s" }}><polyline points="6 9 12 15 18 9"/></svg>
      </div>
      {open && sources.map((src, i) => (
        <div key={i} style={{ padding: "8px 12px", borderTop: "1px solid var(--border)", display: "flex", gap: 10 }}>
          <div style={{ background: "rgba(124,109,250,0.15)", color: "var(--accent2)", padding: "2px 7px", borderRadius: 4, fontFamily: "'DM Mono',monospace", fontSize: 9, whiteSpace: "nowrap", flexShrink: 0, alignSelf: "flex-start", marginTop: 1 }}>
            p.{src.page} · {src.relevance_score.toFixed(2)}
          </div>
          <div style={{ color: "var(--text3)", lineHeight: 1.5 }}>{src.content.slice(0, 120)}...</div>
        </div>
      ))}
    </div>
  );
}