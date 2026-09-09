/**
 * LoginPage — Premium dark-mode glassmorphism login & signup screen
 *
 * Matches the Sovereign Command Deck design system.
 * Supports:
 * - Sign In & Sign Up with role assignment
 * - Remember Credentials toggle with localStorage persistence
 */

import { useState, useEffect, type FormEvent } from 'react';
import {
  Shield,
  AlertCircle,
  Loader2,
  Eye,
  EyeOff,
  UserCheck,
  KeyRound,
  Check,
  Crown,
  Code2,
  TrendingUp,
  Activity,
  Package,
  Users,
  Cpu,
  Lock,
} from 'lucide-react';
import { api } from '@/services/api';
import { useAppStore } from '@/store/appStore';

export interface SystemRoleInfo {
  id: string;
  name: string;
  badge: string;
  icon: typeof Crown;
  color: string;
  department: string;
  workflows: string[];
  canManageModels: boolean;
  description: string;
}

export const ALL_ROLES: SystemRoleInfo[] = [
  {
    id: 'admin',
    name: 'Admin',
    badge: 'ALL ACCESS',
    icon: Crown,
    color: '#F59E0B',
    department: 'all',
    workflows: ['Coding', 'Inspection', 'PID Vision', 'Assistance'],
    canManageModels: true,
    description: 'Full sovereign access to all workflows, system administration, and unrestricted model lifecycle control.',
  },
  {
    id: 'engineering',
    name: 'Engineering',
    badge: 'CODE & MODELS',
    icon: Code2,
    color: '#3B82F6',
    department: 'engineering, operations, public',
    workflows: ['Coding', 'Assistance'],
    canManageModels: true,
    description: 'Dedicated coding & agent execution, 4-bit quantized LLM routing, and full model load/unload permissions.',
  },
  {
    id: 'finance',
    name: 'Finance',
    badge: 'VISION & FISCAL',
    icon: TrendingUp,
    color: '#10B981',
    department: 'finance, procurement, public',
    workflows: ['Inspection', 'PID Vision', 'Assistance'],
    canManageModels: false,
    description: 'Fiscal analysis, budget auditing, vision models & document generation. No coding workflow access.',
  },
  {
    id: 'operations',
    name: 'Operations',
    badge: 'OPS & TELEMETRY',
    icon: Activity,
    color: '#EC4899',
    department: 'operations, engineering, public',
    workflows: ['Inspection', 'PID Vision', 'Assistance'],
    canManageModels: false,
    description: 'Field telemetry, SOP compliance, equipment logs, and inspection workflows.',
  },
  {
    id: 'procurement',
    name: 'Procurement',
    badge: 'SUPPLY CHAIN',
    icon: Package,
    color: '#8B5CF6',
    department: 'procurement, finance, public',
    workflows: ['Inspection', 'Assistance'],
    canManageModels: false,
    description: 'Vendor evaluations, purchase orders, contract auditing, and supply chain inspection.',
  },
  {
    id: 'hr',
    name: 'HR',
    badge: 'PEOPLE & POLICY',
    icon: Users,
    color: '#06B6D4',
    department: 'hr, public',
    workflows: ['Assistance'],
    canManageModels: false,
    description: 'Company policies, onboarding guides, compliance records, and assistant reasoning.',
  },
];

export function LoginPage() {
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('engineering');
  const [rememberCredentials, setRememberCredentials] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { setCurrentUser } = useAppStore();

  const activeRoleObj = ALL_ROLES.find((r) => r.id === role) || ALL_ROLES[1];

  // Load remembered credentials on mount
  useEffect(() => {
    try {
      const remembered = localStorage.getItem('sovereign_remembered_user');
      if (remembered) {
        const parsed = JSON.parse(remembered);
        if (parsed?.username) {
          setUsername(parsed.username);
          setRememberCredentials(true);
        }
      }
    } catch {
      // Ignore parse error
    }
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (mode === 'signup') {
      if (password.length < 4) {
        setError('Password must be at least 4 characters long');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match');
        return;
      }
    }

    setLoading(true);

    try {
      if (mode === 'signin') {
        const user = await api.login(username, password, rememberCredentials);
        setCurrentUser(user);
      } else {
        const deptMap: Record<string, string> = {
          admin: 'all',
          engineering: 'engineering',
          finance: 'finance',
          operations: 'operations',
          procurement: 'procurement',
          hr: 'hr',
        };
        const dept = deptMap[role] || 'engineering';
        const user = await api.signup({
          username,
          password,
          role,
          department: dept,
          rememberMe: rememberCredentials,
        });
        setCurrentUser(user);
      }
    } catch (err: any) {
      setError(err.message || (mode === 'signup' ? 'Registration failed' : 'Authentication failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="h-screen w-full flex items-center justify-center relative overflow-hidden"
      style={{ backgroundColor: 'var(--color-deck-void)' }}
    >
      {/* Ambient background effects */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `
            radial-gradient(ellipse 600px 400px at 30% 20%, rgba(245, 158, 11, 0.04), transparent),
            radial-gradient(ellipse 500px 500px at 70% 80%, rgba(59, 130, 246, 0.03), transparent),
            radial-gradient(ellipse 800px 300px at 50% 50%, rgba(255, 255, 255, 0.01), transparent)
          `,
        }}
      />

      {/* Subtle grid overlay */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />

      {/* Auth Card */}
      <div
        className={`relative z-10 w-full ${mode === 'signup' ? 'max-w-xl' : 'max-w-md'} mx-4 rounded-2xl p-7 transition-all duration-300`}
        style={{
          backgroundColor: 'rgba(15, 17, 23, 0.88)',
          border: '1px solid var(--color-deck-border)',
          backdropFilter: 'blur(24px)',
          boxShadow: `
            0 0 80px rgba(245, 158, 11, 0.03),
            0 25px 50px rgba(0, 0, 0, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.03)
          `,
        }}
      >
        {/* Branding Header */}
        <div className="flex flex-col items-center mb-6">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center mb-3"
            style={{
              backgroundColor: 'var(--color-amber-muted)',
              border: '1px solid var(--color-amber-border)',
              boxShadow: '0 0 30px var(--color-amber-glow)',
            }}
          >
            <Shield className="w-6 h-6" style={{ color: 'var(--color-amber-primary)' }} />
          </div>
          <h1
            className="text-lg font-bold tracking-[0.25em]"
            style={{ color: 'var(--color-text-primary)' }}
          >
            SOVEREIGN AI
          </h1>
          <p
            className="text-[11px] tracking-[0.2em] mt-0.5"
            style={{ color: 'var(--color-text-muted)' }}
          >
            COMMAND DECK
          </p>
        </div>

        {/* Mode Switcher Tabs (Sign In / Sign Up) */}
        <div
          className="flex p-1 rounded-xl mb-6 border"
          style={{
            backgroundColor: 'var(--color-deck-deep)',
            borderColor: 'var(--color-deck-border)',
          }}
        >
          <button
            type="button"
            onClick={() => {
              setMode('signin');
              setError('');
            }}
            className="flex-1 py-1.5 text-xs font-semibold tracking-wider rounded-lg transition-all cursor-pointer"
            style={{
              backgroundColor: mode === 'signin' ? 'var(--color-deck-elevated)' : 'transparent',
              color: mode === 'signin' ? 'var(--color-amber-primary)' : 'var(--color-text-muted)',
              boxShadow: mode === 'signin' ? '0 2px 8px rgba(0,0,0,0.3)' : 'none',
              border: mode === 'signin' ? '1px solid var(--color-amber-border)' : '1px solid transparent',
            }}
          >
            SIGN IN
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('signup');
              setError('');
            }}
            className="flex-1 py-1.5 text-xs font-semibold tracking-wider rounded-lg transition-all cursor-pointer"
            style={{
              backgroundColor: mode === 'signup' ? 'var(--color-deck-elevated)' : 'transparent',
              color: mode === 'signup' ? 'var(--color-amber-primary)' : 'var(--color-text-muted)',
              boxShadow: mode === 'signup' ? '0 2px 8px rgba(0,0,0,0.3)' : 'none',
              border: mode === 'signup' ? '1px solid var(--color-amber-border)' : '1px solid transparent',
            }}
          >
            SIGN UP
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg mb-4 text-xs"
            style={{
              backgroundColor: 'var(--color-error-muted)',
              border: '1px solid var(--color-error-border)',
              color: 'var(--color-error)',
            }}
          >
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Username */}
          <div>
            <label
              htmlFor="auth-username"
              className="block text-[11px] font-semibold tracking-wider mb-1.5 font-label"
              style={{ color: 'var(--color-text-muted)' }}
            >
              USERNAME
            </label>
            <input
              id="auth-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              autoComplete="username"
              placeholder="e.g. engineer1, analyst"
              className="w-full px-3.5 py-2.5 rounded-lg text-xs transition-all outline-none"
              style={{
                backgroundColor: 'var(--color-deck-surface)',
                border: '1px solid var(--color-deck-border)',
                color: 'var(--color-text-primary)',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-amber-border)';
                e.currentTarget.style.boxShadow = '0 0 0 2px var(--color-amber-muted)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-deck-border)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            />
          </div>

          {/* Role selection bar (Sign Up mode only) */}
          {mode === 'signup' && (
            <div className="space-y-2 pt-1">
              <div className="flex items-center justify-between">
                <label
                  className="block text-[11px] font-semibold tracking-wider font-label"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  ROLE SELECTION BAR
                </label>
                <span
                  className="text-[10px] font-mono px-2 py-0.5 rounded border uppercase tracking-wider font-bold"
                  style={{
                    color: activeRoleObj.color,
                    borderColor: `${activeRoleObj.color}40`,
                    backgroundColor: `${activeRoleObj.color}15`,
                  }}
                >
                  {activeRoleObj.name} · {activeRoleObj.badge}
                </span>
              </div>

              {/* Segmented Bar with all roles */}
              <div
                className="p-1 rounded-xl border grid grid-cols-3 sm:grid-cols-6 gap-1"
                style={{
                  backgroundColor: 'var(--color-deck-deep)',
                  borderColor: 'var(--color-deck-border)',
                }}
              >
                {ALL_ROLES.map((r) => {
                  const Icon = r.icon;
                  const isSelected = role === r.id;
                  return (
                    <button
                      key={r.id}
                      type="button"
                      onClick={() => setRole(r.id)}
                      className="flex flex-col items-center justify-center py-2 px-1 rounded-lg border transition-all cursor-pointer group"
                      style={{
                        backgroundColor: isSelected ? 'var(--color-deck-elevated)' : 'transparent',
                        borderColor: isSelected ? r.color : 'transparent',
                        boxShadow: isSelected ? `0 0 10px ${r.color}30` : 'none',
                      }}
                      title={`${r.name} (${r.badge}): ${r.description}`}
                    >
                      <Icon
                        className="w-4 h-4 mb-1 transition-transform group-hover:scale-110"
                        style={{
                          color: isSelected ? r.color : 'var(--color-text-muted)',
                        }}
                      />
                      <span
                        className="text-[10px] font-bold tracking-tight text-center leading-none"
                        style={{
                          color: isSelected ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                        }}
                      >
                        {r.name}
                      </span>
                      {isSelected && (
                        <div
                          className="w-1 h-1 rounded-full mt-1.5"
                          style={{ backgroundColor: r.color }}
                        />
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Active Role Privilege Inspector Strip */}
              <div
                className="p-3 rounded-xl border text-xs transition-all space-y-2"
                style={{
                  backgroundColor: 'var(--color-deck-surface)',
                  borderColor: 'var(--color-deck-border)',
                }}
              >
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2">
                    <activeRoleObj.icon className="w-4 h-4 flex-shrink-0" style={{ color: activeRoleObj.color }} />
                    <span className="font-bold text-xs" style={{ color: 'var(--color-text-primary)' }}>
                      {activeRoleObj.name}
                    </span>
                    <span
                      className="text-[10px] px-1.5 py-0.5 rounded font-mono"
                      style={{
                        backgroundColor: 'var(--color-deck-elevated)',
                        color: 'var(--color-text-secondary)',
                        border: '1px solid var(--color-deck-border)',
                      }}
                    >
                      dept: {activeRoleObj.department}
                    </span>
                  </div>

                  {activeRoleObj.canManageModels ? (
                    <span
                      className="text-[10px] font-mono px-2 py-0.5 rounded font-semibold flex items-center gap-1"
                      style={{
                        backgroundColor: 'rgba(16, 185, 129, 0.12)',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                        color: '#10B981',
                      }}
                    >
                      <Cpu className="w-3 h-3" />
                      LOAD / UNLOAD MODELS
                    </span>
                  ) : (
                    <span
                      className="text-[10px] font-mono px-2 py-0.5 rounded font-semibold flex items-center gap-1"
                      style={{
                        backgroundColor: 'rgba(100, 116, 139, 0.12)',
                        border: '1px solid rgba(100, 116, 139, 0.25)',
                        color: 'var(--color-text-muted)',
                      }}
                    >
                      <Lock className="w-3 h-3" />
                      MODELS RESTRICTED
                    </span>
                  )}
                </div>

                <p className="text-[11px] leading-relaxed" style={{ color: 'var(--color-text-muted)' }}>
                  {activeRoleObj.description}
                </p>

                <div className="flex items-center gap-1.5 flex-wrap pt-0.5">
                  <span className="text-[10px] font-semibold tracking-wider font-label" style={{ color: 'var(--color-text-dim)' }}>
                    WORKFLOWS:
                  </span>
                  {activeRoleObj.workflows.map((wf) => (
                    <span
                      key={wf}
                      className="text-[10px] px-2 py-0.5 rounded font-medium"
                      style={{
                        backgroundColor: 'var(--color-deck-elevated)',
                        color: wf === 'Coding' ? 'var(--color-amber-primary)' : 'var(--color-text-secondary)',
                        border: '1px solid var(--color-deck-border)',
                      }}
                    >
                      {wf}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Password */}
          <div>
            <label
              htmlFor="auth-password"
              className="block text-[11px] font-semibold tracking-wider mb-1.5 font-label"
              style={{ color: 'var(--color-text-muted)' }}
            >
              PASSWORD
            </label>
            <div className="relative">
              <input
                id="auth-password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                placeholder="Enter password"
                className="w-full px-3.5 py-2.5 pr-10 rounded-lg text-xs transition-all outline-none"
                style={{
                  backgroundColor: 'var(--color-deck-surface)',
                  border: '1px solid var(--color-deck-border)',
                  color: 'var(--color-text-primary)',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-amber-border)';
                  e.currentTarget.style.boxShadow = '0 0 0 2px var(--color-amber-muted)';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-deck-border)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded transition-colors cursor-pointer"
                style={{ color: 'var(--color-text-muted)' }}
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          {/* Confirm Password (Sign Up mode only) */}
          {mode === 'signup' && (
            <div>
              <label
                htmlFor="auth-confirm-password"
                className="block text-[11px] font-semibold tracking-wider mb-1.5 font-label"
                style={{ color: 'var(--color-text-muted)' }}
              >
                CONFIRM PASSWORD
              </label>
              <input
                id="auth-confirm-password"
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                autoComplete="new-password"
                placeholder="Re-enter password"
                className="w-full px-3.5 py-2.5 rounded-lg text-xs transition-all outline-none"
                style={{
                  backgroundColor: 'var(--color-deck-surface)',
                  border: '1px solid var(--color-deck-border)',
                  color: 'var(--color-text-primary)',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-amber-border)';
                  e.currentTarget.style.boxShadow = '0 0 0 2px var(--color-amber-muted)';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-deck-border)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              />
            </div>
          )}

          {/* Remember Credentials Checkbox */}
          <div className="flex items-center justify-between pt-1">
            <label
              htmlFor="remember-credentials"
              className="flex items-center gap-2 cursor-pointer select-none text-xs"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              <div
                onClick={() => setRememberCredentials(!rememberCredentials)}
                className="w-4 h-4 rounded flex items-center justify-center border transition-all cursor-pointer"
                style={{
                  backgroundColor: rememberCredentials ? 'var(--color-amber-primary)' : 'var(--color-deck-surface)',
                  borderColor: rememberCredentials ? 'var(--color-amber-primary)' : 'var(--color-deck-border)',
                }}
              >
                {rememberCredentials && <Check className="w-3 h-3 text-slate-950 font-bold" />}
              </div>
              <span className="text-[11px]">Remember credentials</span>
            </label>

            <span className="text-[10px] flex items-center gap-1" style={{ color: 'var(--color-text-muted)' }}>
              <KeyRound className="w-3 h-3" />
              Secure Local Storage
            </span>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !username || !password || (mode === 'signup' && !confirmPassword)}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-xs font-bold tracking-wider transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer mt-2"
            style={{
              backgroundColor: loading ? 'var(--color-amber-muted)' : 'var(--color-amber-primary)',
              color: loading ? 'var(--color-amber-primary)' : '#0a0b0f',
              boxShadow: loading ? 'none' : '0 0 20px var(--color-amber-glow)',
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.currentTarget.style.backgroundColor = 'var(--color-amber-hover)';
                e.currentTarget.style.transform = 'translateY(-1px)';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.currentTarget.style.backgroundColor = 'var(--color-amber-primary)';
                e.currentTarget.style.transform = 'translateY(0)';
              }
            }}
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                {mode === 'signup' ? 'REGISTERING...' : 'AUTHENTICATING...'}
              </>
            ) : mode === 'signup' ? (
              <>
                <UserCheck className="w-3.5 h-3.5" />
                CREATE ACCOUNT
              </>
            ) : (
              'SIGN IN'
            )}
          </button>
        </form>

        {/* Toggle mode link */}
        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={() => {
              setMode(mode === 'signin' ? 'signup' : 'signin');
              setError('');
            }}
            className="text-[11px] transition-colors cursor-pointer hover:underline"
            style={{ color: 'var(--color-amber-primary)' }}
          >
            {mode === 'signin' ? "Don't have an account? Sign up here" : 'Already have an account? Sign in'}
          </button>
        </div>

        {/* Footer info */}
        <div className="mt-6 pt-4 border-t" style={{ borderColor: 'var(--color-deck-border)' }}>
          <div className="flex items-center justify-center gap-2 text-[11px]" style={{ color: 'var(--color-text-dim)' }}>
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{
                backgroundColor: 'var(--color-verified)',
                boxShadow: '0 0 6px var(--color-verified-glow)',
              }}
            />
            <span style={{ color: 'var(--color-text-muted)' }}>LOCAL ONLY</span>
            <span className="mx-1">·</span>
            <span style={{ color: 'var(--color-text-muted)' }}>ZERO EGRESS</span>
            <span className="mx-1">·</span>
            <span style={{ color: 'var(--color-text-muted)' }}>SOVEREIGN</span>
          </div>
        </div>
      </div>
    </div>
  );
}
