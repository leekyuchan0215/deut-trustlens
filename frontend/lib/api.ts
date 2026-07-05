import {
  mockAnalyze,
  mockHistory,
  mockProgress,
  mockReanalyze,
  mockRefine,
  mockResultDetail,
  mockResultSummary,
} from "@/lib/mockEngine";
import {
  AnalyzeRequest,
  AnalyzeResponse,
  ApiError,
  ApiErrorBody,
  HealthResponse,
  HistoryQuery,
  HistoryResponse,
  ProgressResponse,
  ReanalyzeRequest,
  ReanalyzeResponse,
  RefinePromptRequest,
  RefinePromptResponse,
  ResultDetailResponse,
  ResultSummaryResponse,
} from "@/lib/types";

export const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError(
      { code: "NETWORK_ERROR", message: "서버에 연결할 수 없습니다.", details: null },
      undefined,
    );
  }

  if (!response.ok) {
    let body: ApiErrorBody | null = null;
    try {
      body = (await response.json()) as ApiErrorBody;
    } catch {
      // ignore parse failure, fall through to generic error
    }
    if (body?.error) {
      throw new ApiError(body.error, response.status);
    }
    throw new ApiError(
      { code: "UNKNOWN_ERROR", message: `요청이 실패했습니다. (${response.status})`, details: null },
      response.status,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

// simulate small network latency so mock loading/error states are visible in the UI
function mockDelay<T>(factory: () => T): Promise<T> {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      try {
        resolve(factory());
      } catch (err) {
        reject(err);
      }
    }, 250);
  });
}

export const api = {
  async health(): Promise<HealthResponse> {
    if (USE_MOCK) {
      return mockDelay(() => ({
        status: "ok",
        service: "TrustLens API",
        environment: "development",
        use_mock: true,
        database_connected: true,
        pgvector_enabled: true,
      }));
    }
    return request<HealthResponse>("/api/v1/health");
  },

  async refinePrompt(body: RefinePromptRequest): Promise<RefinePromptResponse> {
    if (USE_MOCK) {
      return mockDelay(() => mockRefine(body.question, body.answer_purpose));
    }
    return request<RefinePromptResponse>("/api/refine-prompt", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  async analyze(body: AnalyzeRequest): Promise<AnalyzeResponse> {
    if (USE_MOCK) {
      return mockDelay(() => mockAnalyze(body));
    }
    return request<AnalyzeResponse>("/api/analyze", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  async progress(questionId: string): Promise<ProgressResponse> {
    if (USE_MOCK) {
      return mockDelay(() => mockProgress(questionId));
    }
    return request<ProgressResponse>(`/api/progress/${questionId}`);
  },

  async resultSummary(questionId: string): Promise<ResultSummaryResponse> {
    if (USE_MOCK) {
      return mockDelay(() => mockResultSummary(questionId));
    }
    return request<ResultSummaryResponse>(`/api/result/${questionId}`);
  },

  async resultDetail(questionId: string): Promise<ResultDetailResponse> {
    if (USE_MOCK) {
      return mockDelay(() => mockResultDetail(questionId));
    }
    return request<ResultDetailResponse>(`/api/result/${questionId}/detail`);
  },

  async history(query: HistoryQuery): Promise<HistoryResponse> {
    if (USE_MOCK) {
      return mockDelay(() => {
        const { items, total } = mockHistory(query);
        return {
          items,
          total,
          limit: query.limit ?? 20,
          offset: query.offset ?? 0,
        };
      });
    }
    const params = new URLSearchParams();
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        params.set(key, String(value));
      }
    });
    return request<HistoryResponse>(`/api/history?${params.toString()}`);
  },

  async reanalyze(questionId: string, body?: ReanalyzeRequest): Promise<ReanalyzeResponse> {
    if (USE_MOCK) {
      return mockDelay(() => mockReanalyze(questionId, body?.answer_purpose));
    }
    return request<ReanalyzeResponse>(`/api/reanalyze/${questionId}`, {
      method: "POST",
      body: JSON.stringify(body ?? {}),
    });
  },
};

export { ApiError };
