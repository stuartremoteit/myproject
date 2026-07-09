#!/usr/bin/env bash
set -euo pipefail

# Reboots this device if it has been unable to reach remote.it for more
# than OFFLINE_THRESHOLD_HOURS. Intended to be deployed to devices via
# remote.it Scripting and run periodically (e.g. every 15 minutes via cron
# or a remote.it scheduled script job).

OFFLINE_THRESHOLD_HOURS="${OFFLINE_THRESHOLD_HOURS:-24}"
BOOT_GRACE_MINUTES="${BOOT_GRACE_MINUTES:-10}"
STATE_DIR="${STATE_DIR:-/var/lib/remoteit-watchdog}"
STATE_FILE="$STATE_DIR/last-online"
LOCK_FILE="${LOCK_FILE:-/var/run/remoteit-watchdog.lock}"
LOG_TAG="remoteit-watchdog"
REMOTEIT_SERVICE="${REMOTEIT_SERVICE:-remoteit}"
CHECK_URL="${CHECK_URL:-https://api.remote.it}"
CURL_TIMEOUT=10

log() {
  logger -t "$LOG_TAG" "$*" 2>/dev/null || true
  echo "$*"
}

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  log "Another run is already in progress, exiting."
  exit 0
fi

mkdir -p "$STATE_DIR"

is_online() {
  systemctl is-active --quiet "$REMOTEIT_SERVICE" 2>/dev/null || return 1
  curl -fsS --max-time "$CURL_TIMEOUT" -o /dev/null "$CHECK_URL" || return 1
  return 0
}

now=$(date +%s)

# First run on a device: seed the state file instead of assuming it has
# been offline since the epoch.
if [ ! -f "$STATE_FILE" ]; then
  echo "$now" > "$STATE_FILE"
  log "No prior state found; initializing last-online timestamp."
  exit 0
fi

if is_online; then
  echo "$now" > "$STATE_FILE"
  log "Connectivity OK."
  exit 0
fi

last_online=$(cat "$STATE_FILE")
offline_seconds=$(( now - last_online ))
threshold_seconds=$(( OFFLINE_THRESHOLD_HOURS * 3600 ))

log "Connectivity check failed. Offline for $(( offline_seconds / 3600 ))h $(( (offline_seconds % 3600) / 60 ))m."

if [ "$offline_seconds" -lt "$threshold_seconds" ]; then
  exit 0
fi

# Don't reboot again within a few minutes of booting; give services a
# chance to reconnect before the watchdog fires on the same outage.
uptime_seconds=$(cut -d. -f1 /proc/uptime)
grace_seconds=$(( BOOT_GRACE_MINUTES * 60 ))
if [ "$uptime_seconds" -lt "$grace_seconds" ]; then
  log "Within post-boot grace period (${uptime_seconds}s uptime); skipping reboot this cycle."
  exit 0
fi

log "Offline for over ${OFFLINE_THRESHOLD_HOURS}h. Rebooting device."
# Reset the timestamp so the next boot starts a fresh offline countdown
# rather than rebooting again immediately if it's still offline.
echo "$now" > "$STATE_FILE"
sync
/sbin/shutdown -r now "remoteit-watchdog: rebooting after ${OFFLINE_THRESHOLD_HOURS}h offline"
