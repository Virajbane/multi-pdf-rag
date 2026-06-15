const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function uploadPDF(file: File): Promise<import("@/types").UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Upload failed");
  }

  return res.json();
}

export async function queryDocuments(
  question: string,
  fileIds?: string[],
  k: number = 5
): Promise<import("@/types").QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, file_ids: fileIds || null, k }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Query failed");
  }

  return res.json();
}

export async function streamQuery(
  question: string,
  onToken: (token: string) => void,
  onDone: () => void,
  fileIds?: string[]
): Promise<void> {
  const res = await fetch(`${API_BASE}/query/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, file_ids: fileIds || null, k: 5 }),
  });

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split("\n");

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const token = line.slice(6);
        if (token === "[DONE]") {
          onDone();
          return;
        }
        onToken(token);
      }
    }
  }
}

export async function summarizePDF(
  file_id: string,
  style: "concise" | "detailed" | "bullet" = "bullet"
): Promise<{ summary: string; file_id: string; style: string }> {
  const res = await fetch(`${API_BASE}/summarize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id, style }),
  });
  if (!res.ok) throw new Error("Summarization failed");
  return res.json();
}

export async function generateMCQ(
  file_id: string,
  num_questions: number = 5,
  difficulty: "easy" | "medium" | "hard" = "medium"
): Promise<{ questions: any[]; file_id: string }> {
  const res = await fetch(`${API_BASE}/mcq`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id, num_questions, difficulty }),
  });
  if (!res.ok) throw new Error("MCQ generation failed");
  return res.json();
}