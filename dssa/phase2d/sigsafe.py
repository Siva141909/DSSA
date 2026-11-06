"""Signal handling for the Gate 2 v8 processes (INCIDENT_006).

A job started with `nohup ... &` from a non-interactive shell has SIGINT set to
ignored (POSIX job control), and every child inherits that. Python does not
install its KeyboardInterrupt handler when SIGINT is already ignored, so the
guard's SIGINT and the manual stop had no effect on a running run.

restore() sets SIGINT to raise KeyboardInterrupt and SIGTERM to raise
Terminated (a BaseException), so either signal reaches run_one_v2's existing
`except BaseException` handler, which writes incident.json and re-raises.
Because the handlers are Python functions, exec() resets them to the default
in child processes, where restore() is called again."""
from __future__ import annotations

import ctypes
import os
import signal


class Terminated(BaseException):
    pass


def _term(signum, frame):
    raise Terminated(f"received {signal.Signals(signum).name}")


def restore():
    signal.signal(signal.SIGINT, signal.default_int_handler)
    signal.signal(signal.SIGTERM, _term)


def os_disposition(sig):
    """The kernel's disposition for `sig` in this process, via sigaction(2):
    'default', 'ignored' or 'caught'. Independent of Python's own bookkeeping."""
    libc = ctypes.CDLL(None, use_errno=True)
    buf = ctypes.create_string_buffer(64)
    if libc.sigaction(int(sig), None, buf) != 0:
        return f"error {ctypes.get_errno()}"
    h = int.from_bytes(buf.raw[:ctypes.sizeof(ctypes.c_void_p)], "little")
    return {0: "default", 1: "ignored"}.get(h, "caught")


def report():
    return {"pid": os.getpid(), "ppid": os.getppid(),
            **{s.name: {"os": os_disposition(s), "python": repr(signal.getsignal(s))} for s in (signal.SIGINT, signal.SIGTERM)}}
