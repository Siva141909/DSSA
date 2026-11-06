# Gate 2 recovery v5 launch record

- Launched: 2026-11-03 14:44:34 IST, under research-lead approval.
- Manifest: manifest_gate2_recovery_v5.json, SHA-256 d4cfcb74fd298aa468dc4d3949a739255d32db3b1917a5860b175ddd332341d4 (62 runs).
- Sequence process: PID 39146 (run_gate2_v5.py), parent launchd (detached); caffeinate PID 39148.
- First run: p2d_oracle_L02_s1000_a2, PID 39153.
- Pre-launch checks, all passed:
  - dummy guard tests for sleep, charger, lid, thermal and manual stop
  - manifest and evidence verification
  - Keep Downloaded pinned, 0 cloud-only files
  - preflight
- Manual safe stop, targeting only this sequence's current child:
  `kill -INT $(pgrep -P 39146 -f 'run_one_v5.py|verify_reload.py')`
  The run writes incident.json, and the sequence then stops by rule. Do not close the lid.
