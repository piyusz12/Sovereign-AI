import { useAppStore } from './src/store/appStore.ts';
import { useMissionStore } from './src/store/missionStore.ts';

console.log('🧪 Starting Frontend State & Functional Verification...\n');

let failed = 0;
function assert(condition, message) {
  if (!condition) {
    console.error(`  ❌ FAILED: ${message}`);
    failed++;
  } else {
    console.log(`  ✅ PASSED: ${message}`);
  }
}

// ── Test 1: App Store Telemetry, Hardware & Routing ────────────
console.log('--- Testing AppStore ---');
const appState = useAppStore.getState();
assert(appState.telemetry !== undefined, 'Initial telemetry exists');
assert(appState.hardware.name !== undefined, `Hardware profile initialized: ${appState.hardware.name}`);

// Update Telemetry
appState.updateTelemetry({
  vram_used_mb: 7120,
  vram_total_mb: 16384,
  gpu_percent: 78,
  tokens_per_sec: 42.5
});
const updatedTelemetry = useAppStore.getState().telemetry;
assert(updatedTelemetry.vram_used_mb === 7120, 'VRAM used updated to 7120 MB');
assert(updatedTelemetry.gpu_percent === 78, 'GPU percent updated to 78%');
assert(updatedTelemetry.tokens_per_sec === 42.5, 'Tokens/sec updated to 42.5');

// Update Routing
appState.updateRouting({
  task_type: 'Coding Task',
  selected_model: 'Qwen2.5-Coder-7B',
  reason: 'Optimal code synthesis efficiency'
});
const updatedRouting = useAppStore.getState().routing;
assert(updatedRouting.task_type === 'Coding Task', 'Task type routed correctly');
assert(updatedRouting.selected_model === 'Qwen2.5-Coder-7B', 'Selected model matches');

// Update Trust
appState.updateTrust({
  is_local: true,
  external_connections: 0
});
const updatedTrust = useAppStore.getState().trust;
assert(updatedTrust.is_local === true, 'Data sovereignty confirmed local');
assert(updatedTrust.external_connections === 0, 'Zero external connections verified');

// ── Test 2: Mission Store Lifecycle ────────────────────────────
console.log('\n--- Testing MissionStore ---');
const missionState = useMissionStore.getState();

// Create Mission
const mission = missionState.createMission(
  'Analyze cooling loop valve pressure drops',
  'document',
  ['cooling_spec.pdf']
);

assert(typeof mission.id === 'string' && mission.id.startsWith('mission-'), `Mission created with ID: ${mission.id}`);
assert(mission.command === 'Analyze cooling loop valve pressure drops', 'Mission command matches');
assert(mission.type === 'document', 'Mission type set to document');
assert(mission.pipeline.length > 0, `Pipeline initialized with ${mission.pipeline.length} steps: ${mission.pipeline.map(s => s.name).join(' -> ')}`);

// Retrieve Mission
const retrievedMission = missionState.getMission(mission.id);
assert(retrievedMission !== undefined && retrievedMission.id === mission.id, 'Mission retrieved via getMission()');

// Active Mission
missionState.setActiveMission(mission.id);
assert(missionState.getActiveMission()?.id === mission.id, 'Active mission selected via getActiveMission()');

// Pipeline Step Transitions
const firstStep = mission.pipeline[0];
assert(firstStep.status === 'queued', `First step (${firstStep.name}) starts queued`);

missionState.updatePipelineStep(mission.id, firstStep.id, { status: 'running', duration_ms: 120 });
let currentStep = missionState.getMission(mission.id)?.pipeline.find(s => s.id === firstStep.id);
assert(currentStep?.status === 'running', 'Step transitioned to running');

missionState.updatePipelineStep(mission.id, firstStep.id, { status: 'verified', duration_ms: 240, details: 'Parsed 14 pages' });
currentStep = missionState.getMission(mission.id)?.pipeline.find(s => s.id === firstStep.id);
assert(currentStep?.status === 'verified', 'Step transitioned to verified');

// Evidence Claims
missionState.addEvidence(mission.id, {
  id: 'ev-1',
  claim: 'Valve V-102 exhibits 12% pressure drop under nominal flow',
  confidence: 0.96,
  sources: [{ title: 'cooling_spec.pdf', location: 'Page 8, Table 3.2' }]
});
const updatedMission = missionState.getMission(mission.id);
assert(updatedMission?.evidence.length === 1, 'Evidence claim added to mission');
assert(updatedMission?.evidence[0].confidence === 0.96, 'Evidence confidence recorded');

// Trace Events
missionState.addTraceEntry(mission.id, 'Ingestion completed successfully', 'cooling_spec.pdf indexed', firstStep.id);
const trace = missionState.getMission(mission.id)?.trace;
assert(trace !== undefined && trace.length > 0, 'Trace log entry recorded');

// Mission Status
missionState.updateMissionStatus(mission.id, 'executing');
assert(missionState.getMission(mission.id)?.status === 'executing', 'Mission status updated to executing');

// Mission Completion
missionState.completeMission(mission.id, {
  type: 'document',
  filename: 'cooling_report.docx',
  content: 'Valve analysis complete'
});
assert(missionState.getMission(mission.id)?.status === 'completed', 'Mission status updated to completed');
assert(missionState.getMission(mission.id)?.output?.filename === 'cooling_report.docx', 'Mission output attached');

// Replay Controls
missionState.startReplay(mission.id);
assert(useMissionStore.getState().isReplayMode === true, 'Replay mode started');
missionState.setReplayStep(2);
assert(useMissionStore.getState().replayStep === 2, 'Replay step scrubbed to 2');
missionState.stopReplay();
assert(useMissionStore.getState().isReplayMode === false, 'Replay mode stopped');

console.log('\n--- Summary ---');
if (failed === 0) {
  console.log('🎉 ALL FRONTEND FUNCTIONS, STORES, AND PIPELINE STATE CHECKS PASSED!');
  process.exit(0);
} else {
  console.error(`❌ ${failed} checks failed.`);
  process.exit(1);
}
