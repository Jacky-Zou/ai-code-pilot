export type ProviderName = "openai" | "deepseek" | (string & {});

export interface HealthResponse {
  status: "ok";
  service: string;
}

export interface ToolResult {
  name: string;
  arguments: Record<string, unknown>;
  result: unknown;
  error: string | null;
}

export interface CodeReference {
  file_path: string;
  line_number: number | null;
  snippet: string | null;
  score: number | null;
}

export interface ChatRequest {
  message: string;
  project_path?: string | null;
  provider?: ProviderName | null;
  model?: string | null;
  conversation_id?: string | null;
  api_key?: string | null;
  base_url?: string | null;
}

export interface ChatResponse {
  answer: string;
  provider: string;
  model: string;
  tool_calls: ToolResult[];
  references: CodeReference[];
  conversation_id: string;
  patch_suggestions?: unknown[];
}

export interface ProjectIndexRequest {
  project_path: string;
}

export interface ProjectIndexResponse {
  status: "success";
  indexed_files: number;
  chunks: number;
  project_name: string;
  project_path: string;
  size_bytes: number;
  line_count: number;
  languages: Array<{ label: string; files: number; percent: number }>;
  tech_stack: string[];
  architecture: string[];
  structure: string[];
  summary: string;
  likely_purpose: string;
}

export interface ProjectSearchRequest {
  query: string;
  top_k?: number;
}

export interface ProjectSearchResult {
  file_path: string;
  start_line: number;
  end_line: number;
  content: string;
  score: number;
}

export interface ProjectSearchResponse {
  results: ProjectSearchResult[];
}

export interface ApiErrorBody {
  error: string;
  detail: string | Record<string, unknown> | Array<Record<string, unknown>> | null;
}

export class ApiClientError extends Error {
  status: number;
  body: ApiErrorBody | null;

  constructor(message: string, status: number, body: ApiErrorBody | null = null) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.body = body;
  }
}

export interface ApiClientOptions {
  baseUrl?: string;
  fetcher?: typeof fetch;
}

const DEFAULT_BASE_URL = "http://localhost:8000";

function getBaseUrl(baseUrl?: string): string {
  const configuredUrl = baseUrl ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_BASE_URL;
  return configuredUrl.replace(/\/+$/, "");
}

async function readJson<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text) {
    return undefined as T;
  }
  return JSON.parse(text) as T;
}

async function request<TResponse, TBody = unknown>(
  path: string,
  options: ApiClientOptions & {
    method?: "GET" | "POST";
    body?: TBody;
  } = {}
): Promise<TResponse> {
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher(`${getBaseUrl(options.baseUrl)}${path}`, {
    method: options.method ?? "GET",
    headers: options.body === undefined ? undefined : { "Content-Type": "application/json" },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    cache: "no-store"
  });

  if (!response.ok) {
    const errorBody = await readJson<ApiErrorBody>(response).catch(() => null);
    const message = errorBody?.detail
      ? `${errorBody.error}: ${JSON.stringify(errorBody.detail)}`
      : `API request failed with status ${response.status}`;
    throw new ApiClientError(message, response.status, errorBody);
  }

  return readJson<TResponse>(response);
}

export function getHealth(options?: ApiClientOptions): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health", options);
}

export function sendChat(requestBody: ChatRequest, options?: ApiClientOptions): Promise<ChatResponse> {
  return request<ChatResponse, ChatRequest>("/api/chat", {
    ...options,
    method: "POST",
    body: requestBody
  });
}

export function indexProject(
  requestBody: ProjectIndexRequest,
  options?: ApiClientOptions
): Promise<ProjectIndexResponse> {
  return request<ProjectIndexResponse, ProjectIndexRequest>("/api/projects/index", {
    ...options,
    method: "POST",
    body: requestBody
  });
}

export function searchProject(
  requestBody: ProjectSearchRequest,
  options?: ApiClientOptions
): Promise<ProjectSearchResponse> {
  return request<ProjectSearchResponse, ProjectSearchRequest>("/api/projects/search", {
    ...options,
    method: "POST",
    body: requestBody
  });
}

export interface ListModelsRequest {
  provider: string;
  api_key: string;
  base_url?: string | null;
}

export interface ListModelsResponse {
  provider: string;
  models: string[];
}

export function listProviderModels(
  requestBody: ListModelsRequest,
  options?: ApiClientOptions
): Promise<ListModelsResponse> {
  return request<ListModelsResponse, ListModelsRequest>("/api/providers/models", {
    ...options,
    method: "POST",
    body: requestBody
  });
}
