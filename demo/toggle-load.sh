#!/usr/bin/env bash
# Toggle synthetic load against rightsizing-demo/stress-app to flip between
# VPA*UnderProvisioned (load ON) and VPA*OverProvisioned (load OFF) alerts
# within a few minutes. See vpa-aap-implementation.md §17 for the full
# explanation of why the checkpoint/recommender reset below is necessary
# (VPA's recommendation is a slow-decaying weighted percentile, not a live
# usage snapshot, so switching direction quickly requires clearing it).
#
# Usage:
#   demo/toggle-load.sh on    # start load -> CPU under-provisioned in ~2-5 min
#   demo/toggle-load.sh off   # stop load  -> CPU over-provisioned in ~2-5 min
#   demo/toggle-load.sh status
set -euo pipefail

NS="rightsizing-demo"
VPA_NS="openshift-vertical-pod-autoscaler"
VPA_NAME="stress-app-vpa"
CHECKPOINT_NAME="stress-app-vpa-stress-app"
CRONJOB="k6-traffic-gen-cron"

reset_vpa_history() {
  echo "Resetting VPA checkpoint + recommender so the recommendation reacts to fresh samples instead of days-old history..."
  oc delete verticalpodautoscalercheckpoint "${CHECKPOINT_NAME}" -n "${NS}" --ignore-not-found
  oc delete pod -n "${VPA_NS}" -l app=vpa-recommender --ignore-not-found
}

stop_all_jobs() {
  # concurrencyPolicy=Forbid only stops the CronJob controller from launching
  # overlapping runs - it does not stop an already-running Job, and manually
  # created Jobs (from --from=cronjob) aren't tracked by it at all.
  oc get jobs -n "${NS}" -o name 2>/dev/null | xargs -r oc delete -n "${NS}"
}

case "${1:-status}" in
  on)
    oc patch cronjob "${CRONJOB}" -n "${NS}" --type merge -p '{"spec":{"suspend":false}}'
    stop_all_jobs
    oc create job "k6-load-$(date +%s)" -n "${NS}" --from="cronjob/${CRONJOB}"
    reset_vpa_history
    echo "Load ON. Watch: oc adm top pods -n ${NS} -l app=stress-app ; oc get vpa ${VPA_NAME} -n ${NS} -o jsonpath='{.status.recommendation}'"
    ;;
  off)
    oc patch cronjob "${CRONJOB}" -n "${NS}" --type merge -p '{"spec":{"suspend":true}}'
    stop_all_jobs
    reset_vpa_history
    echo "Load OFF. Usage should decay to near-zero within a minute; VPA*OverProvisioned should fire within ~2-5 min."
    ;;
  status)
    echo "--- CronJob ---"; oc get cronjob "${CRONJOB}" -n "${NS}"
    echo "--- Jobs ---"; oc get jobs -n "${NS}"
    echo "--- stress-app usage ---"; oc adm top pods -n "${NS}" -l app=stress-app 2>/dev/null
    echo "--- VPA recommendation ---"; oc get vpa "${VPA_NAME}" -n "${NS}" -o jsonpath='{.status.recommendation.containerRecommendations[0]}'; echo
    ;;
  *)
    echo "Usage: $0 {on|off|status}" >&2
    exit 1
    ;;
esac
