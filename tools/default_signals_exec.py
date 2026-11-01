"""Run a command in a new session with SIGINT/SIGQUIT at SIG_DFL.

Bash leaves SIGINT ignored for background children; tests/tooling expect
KeyboardInterrupt, so the child must start with default dispositions.
"""
import os, signal, sys

pid = os.fork()
if pid == 0:
    os.setsid()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGQUIT, signal.SIG_DFL)
    os.execvp(sys.argv[1], sys.argv[1:])
signal.signal(signal.SIGINT, signal.SIG_IGN)
print(f"child pid {pid}", flush=True)
_, status = os.waitpid(pid, 0)
sys.exit(os.waitstatus_to_exitcode(status))
