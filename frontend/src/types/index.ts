export interface Document {
  id: string;
  title: string;
  content: string;
  summary?: string;
  tags: string[];
  uploadedAt: Date;
  fileType: string;
  size: number;
}

export interface QueryResponse {
  answer: string;
  sources: {
    documentId: string;
    title: string;
    snippet: string;
    relevanceScore: number;
  }[];
  confidence: number;
}

export interface UploadResponse {
  documentId: string;
  status: 'processing' | 'completed' | 'error';
  message: string;
}

export interface SearchFilters {
  tags?: string[];
  dateRange?: {
    start: Date;
    end: Date;
  };
  fileType?: string[];
}