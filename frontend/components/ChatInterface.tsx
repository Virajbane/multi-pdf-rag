"use client";
import { useState, useRef, useEffect } from "react";
import { queryDocuments, summarizePDF, generateMCQ } from "@/lib/api";
import { Message, UploadedFile } from "@/types";
import SourceCitation from "./SourceCitation";
import MCQQuiz from "./MCQQuiz";

const HINTS = ["Summarize this PDF", "Generate MCQs", "Key takeaways", "What are the main topics?"];

export default function ChatInterface({ uploadedFiles }: { uploadedFiles: UploadedFile[] }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const addUserMsg = (content: string) => {
    setMessages(prev => [...prev, { id: Date.now().toString(), role: "user", content, timestamp: new Date() }]);
  };

  const addAIMsg = (content: string, extras?: Partial<Message>) => {
    setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), role: "assistant", content, timestamp: new Date(), ...extras }]);
  };

  const send = async (q?: string) => {
    const question = (q || input).trim();
    if (!question || isLoading || uploadedFiles.length === 0) return;
    setInput("");
    setIsLoading(true);
    addUserMsg(question);

    try {
      // Handle special commands
      if (question.toLowerCase().includes("summarize")) {
        const result = await summarizePDF(uploadedFiles[0].file_id, "bullet");
        addAIMsg(result.summary);
      } else if (question.toLowerCase().includes("mcq") || question.toLowerCase().includes("quiz")) {
        const result = await generateMCQ(uploadedFiles[0].file_id, 5, "medium");
        addAIMsg("Here are your MCQs:", { mcqQuestions: result.questions });
      } else {
        const result = await queryDocuments(question);
        addAIMsg(result.answer, { sources: result.sources, processing_time_ms: result.processing_time_ms });
      }
    } catch (err: any) {
      addAIMsg(`Error: ${err.message}`);
    } finally {
      setIsLoading(false); }
  };

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div style={{ padding: "16px 24px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between", background: "var(--bg2)" }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>Ask your documents</div>
          <div style={{ fontSize: 11, color: "var(--text3)", fontFamily: "'DM Mono',monospace", marginTop: 2 }}>
            {uploadedFiles.length} document{uploadedFiles.length !== 1 ? "s" : ""} loaded · semantic search active
          </div>
        </div>
        <button onClick={() => setMessages([])} style={{ width: 30, height: 30, borderRadius: 7, border: "1px solid var(--border)", background: "transparent", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text2)" }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.51"/></svg>
        </button>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "24px", display: "flex", flexDirection: "column", gap: 20 }}>
        {messages.length === 0 && (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16, opacity: 0.4, marginTop: "20vh" }}>
            <div style={{ width: 56, height: 56, borderRadius: 14, border: "1px solid var(--border2)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--text3)" strokeWidth="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            </div>
            <div style={{ fontSize: 14, color: "var(--text3)", textAlign: "center" }}>
              {uploadedFiles.length === 0 ? "Upload a PDF to begin" : "Ask anything about your documents"}
            </div>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} style={{ display: "flex", flexDirection: msg.role === "user" ? "row-reverse" : "row", gap: 10, alignItems: "flex-start" }}>
            <div style={{ width: 30, height: 30, borderRadius: 8, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, background: msg.role === "user" ? "var(--accent3)" : "var(--bg4)", border: msg.role === "assistant" ? "1px solid var(--border2)" : "none", color: "#fff" }}>
              {msg.role === "user" ? "U" :
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent2)" strokeWidth="1.8"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>}
            </div>
            <div style={{ maxWidth: "75%" }}>
              <div style={{ padding: "12px 16px", borderRadius: msg.role === "user" ? "12px 4px 12px 12px" : "4px 12px 12px 12px", fontSize: 13, lineHeight: 1.7, background: msg.role === "user" ? "var(--accent3)" : "var(--bg3)", border: msg.role === "assistant" ? "1px solid var(--border)" : "none", color: "var(--text)", whiteSpace: "pre-wrap" }}>
                {msg.content}
                {msg.role === "assistant" && msg.processing_time_ms && (
                  <div style={{ fontSize: 10, fontFamily: "'DM Mono',monospace", color: "var(--text3)", marginTop: 8, paddingTop: 8, borderTop: "1px solid var(--border)", display: "flex", gap: 12 }}>
                    <span><span style={{ display: "inline-block", width: 6, height: 6, borderRadius: "50%", background: "var(--green)", marginRight: 4 }}></span>{msg.sources?.length || 0} chunks</span>
                    <span>{((msg.processing_time_ms || 0) / 1000).toFixed(1)}s</span>
                  </div>
                )}
              </div>
              {msg.sources && <SourceCitation sources={msg.sources} />}
              {(msg as any).mcqQuestions && <div style={{ marginTop: 12 }}><MCQQuiz questions={(msg as any).mcqQuestions} /></div>}
            </div>
          </div>
        ))}

        {isLoading && (
          <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
            <div style={{ width: 30, height: 30, borderRadius: 8, background: "var(--bg4)", border: "1px solid var(--border2)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent2)" strokeWidth="1.8"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>
            </div>
            <div style={{ padding: "14px 16px", background: "var(--bg3)", border: "1px solid var(--border)", borderRadius: "4px 12px 12px 12px", display: "flex", gap: 5 }}>
              {[0, 0.2, 0.4].map((d, i) => (
                <span key={i} style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--accent2)", display: "block", animation: `pulse 1.2s ${d}s infinite` }} />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div style={{ padding: "16px 24px", borderTop: "1px solid var(--border)", background: "var(--bg2)" }}>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 10, background: "var(--bg3)", border: "1px solid var(--border2)", borderRadius: 12, padding: "10px 12px" }}>
          <textarea rows={1} value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            placeholder={uploadedFiles.length === 0 ? "Upload a PDF first..." : "Ask anything about your documents..."}
            disabled={isLoading || uploadedFiles.length === 0}
            style={{ flex: 1, background: "transparent", border: "none", outline: "none", resize: "none", fontSize: 13, fontFamily: "'Syne',sans-serif", color: "var(--text)", lineHeight: 1.6, maxHeight: 120 }} />
          <button onClick={() => send()} disabled={isLoading || !input.trim() || uploadedFiles.length === 0}
            style={{ width: 34, height: 34, background: "var(--accent)", border: "none", borderRadius: 8, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", opacity: (!input.trim() || uploadedFiles.length === 0) ? 0.4 : 1 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </button>
        </div>
        <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
          {HINTS.map(h => (
            <button key={h} onClick={() => send(h)} disabled={uploadedFiles.length === 0}
              style={{ fontSize: 10, fontFamily: "'DM Mono',monospace", color: "var(--text3)", padding: "4px 10px", border: "1px solid var(--border)", borderRadius: 20, background: "transparent", cursor: "pointer" }}>
              {h}
            </button>
          ))}
        </div>
      </div>
      <style>{`@keyframes pulse{0%,60%,100%{opacity:.3;transform:scale(.8)}30%{opacity:1;transform:scale(1)}}`}</style>
    </div>
  );
}