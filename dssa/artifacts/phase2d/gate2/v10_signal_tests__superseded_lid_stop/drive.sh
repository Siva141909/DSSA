#!/bin/bash
# Usage: drive.sh <mode>. Launches the harness exactly like production, from a
# non-interactive shell with nohup ... &, then applies the external action.
T="$(dirname "$0")"; mode="$1"; PH="/Users/siva/Documents/Major project/dssa/phase2d"
cd "$PH"
nohup caffeinate -dims ../venv/bin/python -B "$T/harness.py" "$T" "$mode" > "$T/$mode.out" 2>&1 &
sleep 2
seq=$(pgrep -f "harness.py $T $mode" | while read p; do ps -o comm= -p $p | grep -qi python && echo $p; done | head -1)
caf=$(pgrep -f "caffeinate -dims ../venv/bin/python -B $T/harness.py $T $mode" | head -1)
R="$T/$mode/runs"
for i in $(seq 1 120); do
  case $mode in
    reload_guard) [ -f "$R/RELOAD_STARTED" ] && break;;
    early_signal) pgrep -P $seq -f 'run_one_v10.py' >/dev/null && [ -d "$R/p2d_oracle_L15_s2000_a2" ] && break;;
    *) [ -f "$R/TRAINING_STARTED" ] && break;;
  esac; sleep 1; done
child=$(pgrep -P $seq -f 'run_one_v10.py|verify_reload_v8.py' | head -1)
echo "== $mode: caffeinate=$caf sequence=$seq child=$child"
echo "-- process tree before action:"; ps -o pid,ppid,pgid,stat,command -p $caf,$seq,$child | cut -c1-150
t0=$(python3 -c 'import time;print(time.time())')
case $mode in
  manual_child_sigint|early_signal) echo "-- action: documented manual stop: kill -INT \$(pgrep -P $seq -f 'run_one_v10.py|verify_reload_v8.py')"; kill -INT $(pgrep -P $seq -f 'run_one_v10.py|verify_reload_v8.py');;
  child_sigterm) echo "-- action: kill -TERM $child"; kill -TERM $child;;
  seq_sigint) echo "-- action: kill -INT $seq (sequence)"; kill -INT $seq;;
  seq_sigterm) echo "-- action: kill -TERM $seq (sequence)"; kill -TERM $seq;;
  *) echo "-- action: injected guard hazard ($mode)";;
esac
for i in $(seq 1 240); do kill -0 $seq 2>/dev/null || break; sleep 1; done
t1=$(python3 -c 'import time;print(time.time())')
echo "-- sequence alive after wait: $(kill -0 $seq 2>/dev/null && echo YES || echo no); child alive: $(kill -0 $child 2>/dev/null && echo YES || echo no); seconds from action to sequence exit: $(python3 -c "print(round($t1-$t0,1))")"
echo "-- leftover test processes: $(pgrep -f "$T" | tr '\n' ' ')"
