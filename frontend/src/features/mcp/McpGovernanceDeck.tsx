import { useState } from 'react';
import {
  ShieldAlert,
  Terminal,
  Lock,
  CheckCircle2,
  XCircle,
  Sparkles
} from 'lucide-react';
import { api } from '@/services/api';
import { useAuth } from '@/features/auth/useAuth';

export function McpGovernanceDeck() {
  const { user } = useAuth();
  const [toolName, setToolName] = useState('query_database');
  const [argsJson, setArgsJson] = useState('{"sql": "SELECT * FROM telemetry_logs LIMIT 10;"}');
  const [evalResult, setEvalResult] = useState<any>(null);
  const [evalLoading, setEvalLoading] = useState(false);

  // ZKP State
  const [zkpValue, setZkpValue] = useState<number>(45);
  const [zkpThreshold, setZkpThreshold] = useState<number>(100);
  const [zkpProof, setZkpProof] = useState<any>(null);
  const [zkpVerifyStatus, setZkpVerifyStatus] = useState<string | null>(null);
  const [zkpLoading, setZkpLoading] = useState(false);

  const handleEvaluateTool = async () => {
    setEvalLoading(true);
    try {
      const parsedArgs = JSON.parse(argsJson);
      const res = await api.evaluateMcpTool(
        toolName,
        parsedArgs,
        user?.username || 'engineer_dev',
        user?.role || 'software_engineer',
        'IN_COUNTRY'
      );
      setEvalResult(res);
    } catch (err: any) {
      setEvalResult({
        allowed: false,
        verdict: 'EVALUATION_ERROR',
        reason: err.message || 'Invalid JSON syntax or firewall rejection',
      });
    } finally {
      setEvalLoading(false);
    }
  };

  const handleGenerateZkp = async () => {
    setZkpLoading(true);
    setZkpVerifyStatus(null);
    try {
      const proof = await api.generateZkpRangeProof(zkpValue, zkpThreshold, '<=', 'budget_limit');
      setZkpProof(proof);
    } catch (err: any) {
      alert(`ZKP Error: ${err.message}`);
    } finally {
      setZkpLoading(false);
    }
  };

  const handleVerifyZkp = async () => {
    if (!zkpProof) return;
    try {
      const res = await api.verifyZkpProof(zkpProof);
      setZkpVerifyStatus(res.valid ? 'VALIDATED_NO_PLAINTEXT_DISCLOSED' : 'INVALID_PROOF');
    } catch (err: any) {
      setZkpVerifyStatus(`FAILED: ${err.message}`);
    }
  };

  return (
    <main className="flex-1 flex flex-col h-full overflow-y-auto bg-[var(--color-deck-void)] p-6 space-y-6">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[var(--color-deck-border)]">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-wide text-white flex items-center gap-2">
              MCP GOVERNANCE FIREWALL & ZKP GATEWAY
              <span className="text-xs px-2 py-0.5 rounded font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20">
                ACTIVE INTERCEPTION
              </span>
            </h1>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
              Deterministic AST safety validation, single-use invocation tokens, and zero-knowledge inter-agent predicates.
            </p>
          </div>
        </div>
      </header>

      {/* Grid: 2 Columns (MCP Firewall Simulator vs ZKP Console) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* COLUMN 1: MCP FIREWALL SIMULATOR */}
        <section className="p-5 rounded-xl border border-[var(--color-deck-border)] bg-[var(--color-deck-surface)] flex flex-col space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--color-deck-border)] pb-3">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-amber-400" />
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">TOOL INVOCATION FIREWALL</h2>
            </div>
            <span className="text-xs font-mono text-emerald-400">LEAST_PRIVILEGE ACTIVE</span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-zinc-400 mb-1 font-mono uppercase text-[10px]">MCP Tool Identifier</label>
              <select
                value={toolName}
                onChange={(e) => setToolName(e.target.value)}
                className="w-full bg-[var(--color-deck-void)] border border-[var(--color-deck-border)] rounded-lg p-2.5 text-white font-mono focus:border-amber-400 outline-none"
              >
                <option value="query_database">query_database (SQL Data Source)</option>
                <option value="execute_python_code">execute_python_code (Sandbox Execution)</option>
                <option value="read_local_document">read_local_document (Document Store)</option>
                <option value="load_model">load_model (Hardware Weights Switch)</option>
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-zinc-400 font-mono uppercase text-[10px]">Arguments Payload (JSON)</label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setArgsJson('{"sql": "SELECT * FROM users LIMIT 5;"}')}
                    className="text-[10px] text-zinc-400 hover:text-white underline cursor-pointer"
                  >
                    Safe SQL
                  </button>
                  <button
                    onClick={() => setArgsJson('{"sql": "DROP TABLE users; --"}')}
                    className="text-[10px] text-red-400 hover:text-red-300 underline cursor-pointer"
                  >
                    Malicious SQL
                  </button>
                </div>
              </div>
              <textarea
                value={argsJson}
                onChange={(e) => setArgsJson(e.target.value)}
                rows={4}
                className="w-full bg-[var(--color-deck-void)] border border-[var(--color-deck-border)] rounded-lg p-2.5 text-amber-300 font-mono focus:border-amber-400 outline-none resize-none"
              />
            </div>

            <button
              onClick={handleEvaluateTool}
              disabled={evalLoading}
              className="w-full py-2.5 rounded-lg text-xs font-semibold tracking-wider bg-amber-500 hover:bg-amber-400 text-black transition-colors cursor-pointer flex items-center justify-center gap-2"
            >
              {evalLoading ? 'EVALUATING AST & JURISDICTION...' : 'EVALUATE WITH MCP FIREWALL'}
            </button>
          </div>

          {/* Interception Result Card */}
          {evalResult && (
            <div className={`mt-3 p-4 rounded-lg border ${evalResult.allowed ? 'bg-emerald-500/5 border-emerald-500/30' : 'bg-red-500/5 border-red-500/30'}`}>
              <div className="flex items-center gap-2 mb-2">
                {evalResult.allowed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400" />
                )}
                <span className={`text-xs font-bold uppercase tracking-wider ${evalResult.allowed ? 'text-emerald-400' : 'text-red-400'}`}>
                  VERDICT: {evalResult.verdict || (evalResult.allowed ? 'APPROVED' : 'DENIED')}
                </span>
              </div>
              <p className="text-xs text-zinc-300 mb-2">{evalResult.reason || evalResult.violation_reason}</p>
              {evalResult.execution_token && (
                <div className="mt-2 pt-2 border-t border-emerald-500/20 text-[10px] font-mono text-emerald-300 break-all">
                  <span className="text-zinc-500 block">Single-Use Scoped Execution Token:</span>
                  {evalResult.execution_token}
                </div>
              )}
            </div>
          )}
        </section>

        {/* COLUMN 2: ZERO-KNOWLEDGE PROOF (ZKP) GATEWAY */}
        <section className="p-5 rounded-xl border border-[var(--color-deck-border)] bg-[var(--color-deck-surface)] flex flex-col space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--color-deck-border)] pb-3">
            <div className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-emerald-400" />
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">MULTI-AGENT ZKP GATEWAY</h2>
            </div>
            <span className="text-xs font-mono text-zinc-400">PEDERSEN COMMITMENTS</span>
          </div>

          <div className="space-y-3 text-xs">
            <p className="text-[var(--color-text-muted)]">
              Prove numerical compliance (e.g. <code>budget &lt;= threshold</code>) between collaborating agents without disclosing the confidential plaintext number.
            </p>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-zinc-400 mb-1 font-mono uppercase text-[10px]">Secret Witness Value ($)</label>
                <input
                  type="number"
                  value={zkpValue}
                  onChange={(e) => setZkpValue(Number(e.target.value))}
                  className="w-full bg-[var(--color-deck-void)] border border-[var(--color-deck-border)] rounded-lg p-2 text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-zinc-400 mb-1 font-mono uppercase text-[10px]">Public Threshold ($)</label>
                <input
                  type="number"
                  value={zkpThreshold}
                  onChange={(e) => setZkpThreshold(Number(e.target.value))}
                  className="w-full bg-[var(--color-deck-void)] border border-[var(--color-deck-border)] rounded-lg p-2 text-white font-mono"
                />
              </div>
            </div>

            <button
              onClick={handleGenerateZkp}
              disabled={zkpLoading}
              className="w-full py-2.5 rounded-lg text-xs font-semibold tracking-wider bg-emerald-500 hover:bg-emerald-400 text-black transition-colors cursor-pointer flex items-center justify-center gap-2"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {zkpLoading ? 'GENERATING PROOF...' : 'GENERATE ZERO-KNOWLEDGE PROOF'}
            </button>
          </div>

          {/* Generated ZKP Proof Display */}
          {zkpProof && (
            <div className="mt-3 p-4 rounded-lg bg-[var(--color-deck-void)] border border-[var(--color-deck-border)] space-y-2 text-xs font-mono">
              <div className="flex items-center justify-between">
                <span className="text-emerald-400 font-bold">{zkpProof.statement}</span>
                <span className="text-[10px] text-zinc-500">Fiat-Shamir</span>
              </div>
              <div className="text-[10px] text-zinc-400 break-all">
                <span className="text-zinc-500 block">Pedersen Commitment:</span>
                {zkpProof.commitment}
              </div>
              <div className="text-[10px] text-zinc-400 break-all">
                <span className="text-zinc-500 block">Sigma Protocol Signature:</span>
                {zkpProof.proof_signature}
              </div>

              <div className="pt-2 flex items-center justify-between">
                <button
                  onClick={handleVerifyZkp}
                  className="px-3 py-1.5 rounded text-[11px] font-semibold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 cursor-pointer"
                >
                  VERIFY PROOF (ZERO-KNOWLEDGE)
                </button>
                {zkpVerifyStatus && (
                  <span className="text-[11px] font-bold text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    {zkpVerifyStatus}
                  </span>
                )}
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
