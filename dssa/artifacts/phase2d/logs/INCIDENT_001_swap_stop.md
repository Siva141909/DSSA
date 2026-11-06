# Incident 001: pilot stopped at run 2 by the swap-growth limit (2026-11-02 20:12 IST)
- Run: p2d_oracle_L00_s1000. Stopped 8 s after process start, at the first batch tick.
- Stop: swap growth 858 MB, limit 512 MB. Runtime guard worked as designed.
- Training steps executed in that run: 0 (raised before the first batch was drawn).
- Results and checkpoints saved for that run: none. Directory holds only IN_PROGRESS.
- Run 1, p2d_ctrl_K0_s1000: complete and verified.
- Frozen artifacts: unchanged after the stop.
- Swap used: about 3.0 GB before launch, 3.75 GB after. Cause not established; other
  applications were running (Brave, Docker, WhatsApp, Claude).
- The incomplete directory is untouched. The runner will not reuse it. No retry without
  research-lead authorization.

## Follow-up (research-lead decision)
- Verified: directory held only IN_PROGRESS; no checkpoint, no result, no step log line.
  The exception was raised in make_batch, before logits, backward or optimizer.step, so
  0 optimizer steps ran.
- Renamed, not deleted, to runs/p2d_oracle_L00_s1000__ABORTED_attempt1_swapstop.
- One Layer 0 retry approved, under unchanged limits, after supervisor confirmation.

## CORRECTION (2026-11-02, after Incident 002)
The statements above that attempt 1 stopped "at the first batch tick" with "0 optimizer
steps" are NOT established and are withdrawn. tick() runs at every step, the traceback
does not give the step number, and the step counter was lost when the process stopped.
The first log line appears only at step 200. Established facts: fewer than 200 steps ran;
no checkpoint, result or metric was produced. The exact step count is unknown.
