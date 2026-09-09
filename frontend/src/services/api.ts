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
    // No auto-login — user must authenticate through the login page
    throw new Error('Not authenticated');
  }

  public async login(username: string, password: string, rememberMe = false): Promise<AuthUser> {
    const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, remember_me: rememberMe }),
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
    if (rememberMe) {
      localStorage.setItem('sovereign_remembered_user', JSON.stringify({ username }));
    } else {
      localStorage.removeItem('sovereign_remembered_user');
    }
    return this.currentUser!;
  }

  public async signup(params: {
    username: string;
    password: string;
    role?: string;
    department?: string;
    rememberMe?: boolean;
  }): Promise<AuthUser> {
    const res = await fetch(`${API_BASE}/api/v1/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: params.username,
        password: params.password,
        role: params.role || 'engineering',
        department: params.department,
        remember_me: params.rememberMe ?? false,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Signup failed' }));
      throw new Error(err.detail || 'Sign up failed');
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
    if (params.rememberMe) {
      localStorage.setItem('sovereign_remembered_user', JSON.stringify({ username: params.username }));
    } else {
      localStorage.removeItem('sovereign_remembered_user');
    }
    return this.currentUser!;
  }

  public logout() {
    this.token = null;
    this.currentUser = null;
    localStorage.removeItem('sovereign_jwt');
    localStorage.removeItem('sovereign_user');
    localStorage.removeItem('sovereign_remembered_user');
  }

  public clearSavedCredentials() {
    localStorage.removeItem('sovereign_remembered_user');
  }

  public getUser(): AuthUser | null {
    return this.currentUser;
  }

  private async fetchAuth(
    url: string,
    options: RequestInit = {},
  ): Promise<Response> {
    // If we have a token, attach it; don't throw if not authenticated
    // (some calls might be attempted during auth flow)
    const headers = new Headers(options.headers || {});
    if (this.token) {
      headers.set('Authorization', `Bearer ${this.token}`);
    }
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // Token expired or invalid — force re-login
      this.logout();
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
    const res = await this.fetchAuth(`${API_BASE}/api/v1/models/status`);
    if (!res.ok) throw new Error('Failed to fetch model status');
    return res.json();
  }

  public async loadModel(modelId: string) {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/models/${encodeURIComponent(modelId)}/load`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to load model' }));
      throw new Error(err.detail || 'Failed to load model');
    }
    return res.json();
  }

  public async unloadModel(modelId: string) {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/models/${encodeURIComponent(modelId)}/unload`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to unload model' }));
      throw new Error(err.detail || 'Failed to unload model');
    }
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

  public async clearAuditEvents(): Promise<void> {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/audit/events`, { method: 'DELETE' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to clear audit logs' }));
      throw new Error(err.detail || 'Failed to clear audit logs');
    }
  }

  // --- Workflows (RBAC-aware) ---
  public async getAvailableWorkflows(): Promise<string[]> {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/workflows/available`);
    if (!res.ok) throw new Error('Failed to fetch available workflows');
    const data = await res.json();
    return data.workflows || [];
  }

  // --- Admin: User Management ---
  public async register(
    username: string,
    password: string,
    role: string,
    department: string,
  ) {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, role, department }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(err.detail || `Server error: ${res.status}`);
    }
    return res.json();
  }

  public async listUsers() {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/auth/users`);
    if (!res.ok) throw new Error('Failed to fetch users');
    return res.json();
  }

  // ── Strategic Sovereign Architecture ─────────────────────────────────────

  // Attestation & TEE
  public async getAttestationChallenge() {
    const res = await fetch(`${API_BASE}/api/v1/attestation/challenge`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to generate challenge');
    return res.json();
  }

  public async getAttestationReport() {
    const res = await fetch(`${API_BASE}/api/v1/attestation/report`);
    if (!res.ok) throw new Error('Failed to fetch attestation report');
    return res.json();
  }

  public async verifyAttestationQuote(nonce: string, quote_hex?: string) {
    const res = await fetch(`${API_BASE}/api/v1/attestation/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nonce, quote_hex }),
    });
    if (!res.ok) throw new Error('Attestation verification failed');
    return res.json();
  }

  public async exportAttestationProofs(nonce: string, quote_hex?: string) {
    const res = await fetch(`${API_BASE}/api/v1/attestation/export-proofs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nonce, quote_hex }),
    });
    if (!res.ok) throw new Error('Exporting proofs failed');
    return res.json();
  }

  // MCP Governance Firewall & ZKP Gateway
  public async evaluateMcpTool(tool_name: string, args: Record<string, any>, user_id: string, role: string, jurisdiction: string = 'IN_COUNTRY') {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/mcp/evaluate-tool`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool_name, arguments: args, user_id, role, jurisdiction }),
    });
    if (!res.ok) throw new Error('MCP evaluation failed');
    return res.json();
  }

  public async getActiveMcpTokens() {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/mcp/active-tokens`);
    if (!res.ok) throw new Error('Failed to fetch active MCP tokens');
    return res.json();
  }

  public async generateZkpRangeProof(value: number, threshold: number, operator: string = '<=', predicate_name: string = 'budget_limit') {
    const res = await fetch(`${API_BASE}/api/v1/zkp/generate-range-proof`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value, threshold, operator, predicate_name }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Proof generation failed' }));
      throw new Error(err.detail || 'ZKP Range Proof failed');
    }
    return res.json();
  }

  public async verifyZkpProof(proof: Record<string, any>) {
    const res = await fetch(`${API_BASE}/api/v1/zkp/verify-proof`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ proof }),
    });
    if (!res.ok) throw new Error('ZKP verification failed');
    return res.json();
  }

  // Mantic Scaffold Meta-Prompting
  public async runManticScaffold(objective: string, custom_layers?: any[]) {
    const res = await fetch(`${API_BASE}/api/v1/meta/mantic-scaffold`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ objective, custom_layers }),
    });
    if (!res.ok) throw new Error('Mantic Scaffold analysis failed');
    return res.json();
  }

  // CyberScan & Tamper-Proof Audit
  public async runCyberScan(target_directory?: string, code_snippet?: string) {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/security/cyberscan/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_directory, code_snippet }),
    });
    if (!res.ok) throw new Error('CyberScan execution failed');
    return res.json();
  }

  public async getAuditLedger() {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/security/audit-ledger`);
    if (!res.ok) throw new Error('Failed to fetch audit ledger');
    return res.json();
  }

  // Verifiable RAG
  public async queryVerifiableRag(query: string, documents: any[], user_clearance: string = 'INTERNAL', similarity_threshold: number = 0.65) {
    const res = await this.fetchAuth(`${API_BASE}/api/v1/rag/verifiable-query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, documents, user_clearance, similarity_threshold }),
    });
    if (!res.ok) throw new Error('Verifiable RAG query failed');
    return res.json();
  }

  // Infrastructure Telemetry
  public async getTelemetryFusion() {
    const res = await fetch(`${API_BASE}/api/v1/telemetry/fusion`);
    if (!res.ok) throw new Error('Failed to fetch telemetry fusion');
    return res.json();
  }

  // Unified Trust Layer
  public async getTrustOverview() {
    const res = await fetch(`${API_BASE}/api/v1/trust/overview`);
    if (!res.ok) throw new Error('Failed to fetch trust layer overview');
    return res.json();
  }

  public async evaluateEvidenceGate(
    query: string = 'Inspect valve V-204 status and SOP pressure limits',
    user_clearance: string = 'INTERNAL',
    threshold: number = 0.65,
    simulate_refusal: boolean = false
  ) {
    const res = await fetch(`${API_BASE}/api/v1/trust/evidence-eval`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, user_clearance, threshold, simulate_refusal }),
    });
    if (!res.ok) throw new Error('Evidence gate evaluation failed');
    return res.json();
  }

  public async getProvenanceSample() {
    const res = await fetch(`${API_BASE}/api/v1/trust/provenance-sample`);
    if (!res.ok) throw new Error('Failed to fetch provenance sample');
    return res.json();
  }

  public async getMcpEvents() {
    const res = await fetch(`${API_BASE}/api/v1/trust/mcp-events`);
    if (!res.ok) throw new Error('Failed to fetch MCP firewall events');
    return res.json();
  }
}

export const api = new ApiClient();
