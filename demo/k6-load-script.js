import http from 'k6/http';

// Sized for the rightsizing-demo stress-app fake-service load knobs
// (LOAD_CPU_PERCENTAGE=100/1 core, LOAD_MEMORY_PER_REQUEST=4MiB, TIMING ~250-650ms).
// Even a handful of concurrent requests already exceeds the container's 406m
// CPU limit (each one asks for up to a full core), so VUs here mainly control
// how much concurrent LOAD_MEMORY_PER_REQUEST memory piles up at once - kept
// moderate to avoid the Go runtime/HTTP server itself getting so starved of
// scheduling time that health probes stop responding (see git history on
// this file for what happens if you crank this too high).
// Suspending k6-traffic-gen-cron (see demo/toggle-load.sh) stops all new
// requests, so load drops to ~0 immediately and usage decays toward baseline
// within a few VPA recommender cycles, flipping the alerts to
// *OverProvisioned instead of *UnderProvisioned.
export const options = {
  scenarios: {
    sustained_pressure: {
      executor: 'constant-vus',
      vus: 40,
      duration: '2h',
    },
  },
};

export default function () {
  http.get('http://stress-app.rightsizing-demo.svc.cluster.local/', {
    timeout: '15s',
  });
  // No sleep: each VU immediately re-requests once its in-flight request
  // completes, so steady-state concurrency stays ~= vus the whole run.
}
