"use client";
import { useState } from "react";

interface Option { label: string; text: string; }
interface Question {
  question: string;
  options: Option[];
  correct_answer: string;
  explanation: string;
}

export default function MCQQuiz({ questions }: { questions: Question[] }) {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [showResults, setShowResults] = useState(false);

  const score = Object.entries(answers).filter(
    ([i, a]) => a === questions[parseInt(i)].correct_answer
  ).length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {questions.map((q, qi) => (
        <div key={qi} style={{ background: "var(--bg3)", border: "1px solid var(--border)", borderRadius: 10, padding: 16 }}>
          <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text)", marginBottom: 12, lineHeight: 1.6 }}>
            <span style={{ color: "var(--accent2)", fontFamily: "'DM Mono',monospace", marginRight: 8 }}>Q{qi + 1}.</span>
            {q.question}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {q.options.map((opt) => {
              const selected = answers[qi] === opt.label;
              const correct = opt.label === q.correct_answer;
              let bg = "var(--bg4)";
              let border = "var(--border)";
              let color = "var(--text2)";
              if (showResults && correct) { bg = "rgba(52,211,153,0.1)"; border = "var(--green)"; color = "var(--green)"; }
              if (showResults && selected && !correct) { bg = "rgba(248,113,113,0.1)"; border = "var(--red)"; color = "var(--red)"; }
              if (!showResults && selected) { bg = "rgba(124,109,250,0.1)"; border = "var(--accent)"; color = "var(--accent2)"; }

              return (
                <div key={opt.label} onClick={() => !showResults && setAnswers(prev => ({ ...prev, [qi]: opt.label }))}
                  style={{ padding: "10px 14px", borderRadius: 8, border: `1px solid ${border}`, background: bg, cursor: showResults ? "default" : "pointer", display: "flex", gap: 10, alignItems: "center", transition: "all 0.15s" }}>
                  <span style={{ fontFamily: "'DM Mono',monospace", fontSize: 11, color, fontWeight: 600, width: 16 }}>{opt.label}</span>
                  <span style={{ fontSize: 13, color }}>{opt.text}</span>
                </div>
              );
            })}
          </div>
          {showResults && answers[qi] && (
            <div style={{ marginTop: 10, padding: "8px 12px", background: "var(--bg4)", borderRadius: 6, fontSize: 11, color: "var(--text3)", lineHeight: 1.6 }}>
              💡 {q.explanation}
            </div>
          )}
        </div>
      ))}

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        {showResults && (
          <div style={{ fontSize: 13, fontFamily: "'DM Mono',monospace", color: score === questions.length ? "var(--green)" : "var(--accent2)" }}>
            Score: {score}/{questions.length}
          </div>
        )}
        <button onClick={() => { if (showResults) { setAnswers({}); setShowResults(false); } else setShowResults(true); }}
          disabled={Object.keys(answers).length < questions.length && !showResults}
          style={{ marginLeft: "auto", padding: "8px 20px", background: "var(--accent)", border: "none", borderRadius: 8, color: "#fff", fontSize: 12, fontFamily: "'DM Mono',monospace", cursor: "pointer", opacity: Object.keys(answers).length < questions.length && !showResults ? 0.4 : 1 }}>
          {showResults ? "Try Again" : "Check Answers"}
        </button>
      </div>
    </div>
  );
}