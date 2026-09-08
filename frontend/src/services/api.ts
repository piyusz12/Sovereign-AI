/**
 * Sovereign AI Workbench — Central API Client
 *
 * Handles zero-egress local API calls, JWT authentication, and automatic fallback.
 */

const API_BASE = ''; // Uses Vite proxy or relative URL

export interface AuthUser {
  username: string;
  role: string;
  department: string;
}

export interface ChatResult {
  response: string;
  route?: {
    task_type: string;
    model: string;
    reason: string;
  };
  duration_ms?: number;
  sources?: Array<{
    document_id: string;
    title: string;
    snippet: string;
  }>;
}

export interface SearchDoc {
  document_id: string;
  title: string;
  page?: number;
  relevance_score: number;
  snippet: string;
}

export interface WorkflowRunResponse {
  workflow_name: string;
  trace_id: string;
  status: string;
  total_duration_ms: number;
  steps: Array<{
    name: string;
    status: string;
    duration_ms: number;
    details?: string;
  }>;
  deliverables?: string[];
  error?: string;
}

class ApiClient {
  private token: string | null = null;
  private currentUser: AuthUser | null = null;
  private initPromise: Promise<void> | null = null;

  constructor() {
    // Restore token from localStorage if available
    const savedToken = localStorage.getItem('sovereign_jwt');
    const savedUser = localStorage.getItem('sovereign_user');
    if (savedToken) {
      this.token = savedToken;
    }
    if (savedUser) {
      try {
        this.currentUser = JSON.parse(savedUser);
      } catch {
        this.currentUser = null;
      }
    }
  }

  public async ensureAuthenticated(): Promise<string> {
    if (this.token && this.currentUser) {
      return this.token;
    }
    if (!this.initPromise) {
      this.initPromise = this.loginDefault();
    }
    await this.initPromise;
    return this.token || '';
  }

  public async loginDefault(): Promise<void> {
    try {
      await this.login('admin', 'admin123');
    } catch (err) {
      console.warn('Auto-login as admin failed, operating in offline/demo mode:', err);
    }
  }

  public async login(username: string, password: string): Promise<AuthUser> {
    const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Authentication failed');
    }

    const data = await res.json();
    this.token = data.access_token;
    this.currentUser = data.user;
    if (this.token) {
      localStorage.setItem('sovereign_jwt', this.token);
    }
    if (this.currentUser) {
      localStorage.setItem('sovereign_user', JSON.stringify(this.currentUser));
    }
    return this.currentUser!;
  }

  public logout() {
    this.token = null;
    this.currentUser = null;
    this.initPromise = null;
    localStorage.removeItem('sovereign_jwt');
    localStorage.removeItem('sovereign_user');
  }

  public getUser(): AuthUser | null {
    return this.currentUser;
  }

  private async fetchAuth(
    url: string,
    options: RequestInit = {},
    retryAfterLogin = true,
  ): Promise<Response> {
    await this.ensureAuthenticated();
    const headers = new Headers(options.headers || {});
    if (this.token) {
      headers.set('Authorization', `Bearer ${this.token}`);
    }
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401 && retryAfterLogin) {
      this.logout();
      await this.loginDefault();
      if (this.token) {
        return this.fetchAuth(url, options, false);
      }
    }

    return response;
  }

  // --- Health & Sovereignty ---
  public async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  }

  public async getSovereigntyStatus() {
    const res = await fetch(`${API_BASE}/sovereignty`);
    if (!res.ok) throw new Error('Failed to get sovereignty status');
    return res.json();
  }

  // --- Models ---
  public async getModelStatus() {
    const res = await fetch(`${API_BASE}/api/v1/models/status`);
    if (!res.ok) throw new Error('Failed to fetch model status');
    return res.json();
  }

  public async loadModel(modelId: string) {
    const res = await fetch(`${API_BASE}/api/v1/models/${encodeURIComponent(modelId)}/load`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to load model');
    return res.json();
  }

  public async unloadModel(modelId: string) {
    const res = await fetch(`${API_BASE}/api/v1/models/${encodeURIComponent(modelId)}/unload`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to unload model');
    return res.json();
  }

  // --- Chat ---
  public async chat(message: string, model?: string, taskType?: string): Promise<ChatResult> {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        model: model || undefined,
        task_type: taskType || undefined,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Chat request failed' }));
      throw new Error(err.detail || `Server error: ${res.status}`);
    }
    return res.json();
  }

  public async classify(message: string) {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/classify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    if (!res.ok) throw new Error('Classification failed');
    return res.json();
  }

  // --- Coding ---
  public async generateCode(prompt: string, language: string = 'python', context?: string) {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/code/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt,
        language,
        context: context || undefined,
        temperature: 0.2,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Code generation failed' }));
      throw new Error(err.detail || `Server error: ${res.status}`);
    }
    return res.json();
  }

  public async executeCode(code: string, language: string = 'python') {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, language }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Code execution failed' }));
      throw new Error(err.detail || `Server error: ${res.status}`);
    }
    return res.json();
  }

  // --- Vision ---
  public async analyzeVision(prompt: string, images: string[]) {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/vision/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt,
        images,
        temperature: 0.2,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Vision analysis failed' }));
      throw new Error(err.detail || `Server error: ${res.status}`);
    }
    return res.json();
  }

  // --- Knowledge / RAG ---
  public async uploadDocument(
    file: File,
    department: string = 'engineering',
    accessLevel: string = 'engineering',
    description?: string
  ) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('department', department);
    formData.append('access_level', accessLevel);
    if (description) formData.append('description', description);

    const res = await this.fetchAuth(`${API_BASE}/api/v1/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || `Server error: ${res.status}`);
    }
    return res.json();
  }

  public async searchDocuments(query: string, department?: string, topK: number = 5, rerank: boolean = true) {
    const userRole = this.currentUser?.role || 'admin';
    const res = await this.fetchAuth(`${API_BASE}/api/v1/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        user_role: userRole,
        department_filter: department || undefined,
        top_k: topK,
        rerank,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Search failed' }));
      throw new Error(err.detail || `Server error: ${res.status}`);
    }
    return res.json();
  }

  // --- Workflows ---
  public async runWorkflow(workflowName: string, inputs: Record<string, any>): Promise<WorkflowRunResponse> {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/workflows/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workflow_name: workflowName,
        inputs,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Workflow execution failed' }));
      throw new Error(err.detail || `Server error: ${res.status}`);
    }
    return res.json();
  }

  // --- Security & Audit ---
  public async getSecurityDashboard() {
    const res = await fetch(`${API_BASE}/api/v1/security/dashboard`);
    if (!res.ok) throw new Error('Failed to fetch security dashboard');
    return res.json();
  }

  public async getAuditEvents(limit: number = 50, offset: number = 0, action?: string) {
    let url = `${API_BASE}/api/v1/audit/events?limit=${limit}&offset=${offset}`;
    if (action) url += `&action=${encodeURIComponent(action)}`;
    const res = await this.fetchAuth(url);
    if (!res.ok) throw new Error('Failed to fetch audit events');
    return res.json();
  }
}

export const api = new ApiClient();
