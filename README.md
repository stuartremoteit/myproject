# myproject
another place to test my projects

## remote.it offline watchdog

`scripts/remoteit-offline-watchdog.sh` is meant to run *on* a remote.it-managed
device (deployed via remote.it Scripting). It checks that the device can both
run its remote.it agent (`systemctl is-active remoteit`) and reach
`https://api.remote.it`. If that check keeps failing for more than 24 hours
(configurable via `OFFLINE_THRESHOLD_HOURS`), it reboots the device.

### Deploying

1. Push `scripts/remoteit-offline-watchdog.sh` to the device via remote.it
   Scripting (or copy it manually, e.g. to `/usr/local/sbin/`).
2. Make it executable: `chmod +x remoteit-offline-watchdog.sh`.
3. Schedule it to run periodically, e.g. every 15 minutes via cron:
   ```
   */15 * * * * /usr/local/sbin/remoteit-offline-watchdog.sh
   ```
   or via a remote.it scheduled script job with the same interval.

### Configuration (environment variables)

| Variable | Default | Purpose |
| --- | --- | --- |
| `OFFLINE_THRESHOLD_HOURS` | `24` | How long the connectivity check must keep failing before rebooting |
| `BOOT_GRACE_MINUTES` | `10` | Skip rebooting within this long after a boot, to give services time to reconnect |
| `REMOTEIT_SERVICE` | `remoteit` | systemd unit name for the remote.it agent |
| `CHECK_URL` | `https://api.remote.it` | URL used to confirm outbound connectivity |
| `STATE_DIR` | `/var/lib/remoteit-watchdog` | Where the last-known-online timestamp is stored |

The script requires root (to reboot) and `flock`/`curl`/`systemctl` to be
available on the device.
