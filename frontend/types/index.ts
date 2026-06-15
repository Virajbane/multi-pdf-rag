export interface SourceDocument {
  content: string;
  filename: string;
  page: number;
  file_id: string;
  relevance_score: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceDocument[];
  processing_time_ms?: number;
  timestamp: Date;
  mcqQuestions?: any[];  // add this line
}

export interface UploadResponse {
  file_id: string;
  filename: string;
  pages: number;
  chunks_created: number;
  message: string;
}

export interface QueryResponse {
  answer: string;
  sources: SourceDocument[];
  question: string;
  processing_time_ms: number;
}

export interface UploadedFile {
  file_id: string;
  filename: string;
  pages: number;
  chunks_created: number;
}