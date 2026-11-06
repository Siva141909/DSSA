# Incident 002: approved Layer 0 retry stopped by the swap-growth limit (2026-11-02 20:25 IST)
- Run: p2d_oracle_L00_s1000. Started 20:25:06. Stopped within about 15 s.
- Stop: swap growth 671 MB, limit 512 MB. Limits unchanged. No third attempt.
- Baseline recorded just before start: swap 0 MB, pressure 1, load 4.60.
  The Mac had restarted at 20:20:57; Brave, WhatsApp, Docker app and Safari were closed.
- Steps executed: unknown, fewer than 200. No checkpoint, result or metric produced.
- Peak footprint and MPS values for this run were not saved: the runner writes them only
  on success. This is a runner gap.
- Folder runs/p2d_oracle_L00_s1000 holds only IN_PROGRESS and is left in place.
- Frozen artifacts: unchanged. Nothing is running.
