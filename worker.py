#!/data/data/com.termux/files/usr/bin/python3
"""Demo: a tiny program with running "manners" (its mode, and whether
it's paused) that a DIFFERENT session's controller.py can change live,
over a Link -- and it prints its own status back over that same link
every tick, so the controller can read it. Run this on its own to see
it locally; controller.py is what opens it in a real new session.

    python3 worker.py [link-name]
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from link import Link

DELAYS = {"slow": 1.0, "fast": 0.2}

HELP = [
    "commands: /mode slow|fast, /pause, /resume, /quit, /help",
    "(the leading / is optional -- 'pause' works same as '/pause')",
]


def run(name="demo"):
    state = {"mode": "slow", "paused": False, "count": 0}
    link = Link(name, side="b")
    print("worker started -- linked as 'b' on '%s'" % name)
    while True:
        cmd = link.recv_nowait()
        if cmd is not None:
            print("got command: " + cmd)
            # Every other command surface in this whole family (chatshell,
            # programs) takes "/word ...", so this one should too, rather
            # than being the one place that quietly only ever worked
            # without a slash -- accept either, strip it if it's there.
            words = cmd.strip().lstrip("/").split()
            if not words:
                pass
            elif words[0] in ("help", "?"):
                for line in HELP:
                    link.send(line)
            elif words[0] == "mode" and len(words) > 1 and words[1] in DELAYS:
                state["mode"] = words[1]
            elif words[0] == "pause":
                state["paused"] = True
            elif words[0] == "resume":
                state["paused"] = False
            elif words[0] == "quit":
                link.send("bye")
                break
            else:
                link.send("not understood: '%s' -- try /help" % words[0])
        if not state["paused"]:
            state["count"] += 1
        status = "count=%d mode=%s %s" % (
            state["count"], state["mode"], "paused" if state["paused"] else "running")
        print(status)
        link.send(status)
        time.sleep(DELAYS[state["mode"]])


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "demo")
