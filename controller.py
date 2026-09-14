#!/data/data/com.termux/files/usr/bin/python3
"""Demo: type commands here (mode fast / mode slow / pause / resume /
quit) and worker.py -- running in its OWN, separate Termux session --
changes how it's running, live, and its status lines print right here
as they arrive.

    python3 controller.py                        # link to a worker started manually
    python3 controller.py /path/to/worker.py      # also opens that worker in a new session
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from link import Link
from open_session import open_termux_session


def run(name="demo", worker_path=None):
    if worker_path:
        open_termux_session(worker_path, args=[name])
    link = Link(name, side="a", on_line=lambda line: print("worker says: " + line))
    print("controller linked as 'a' on '%s'" % name)
    print("try: mode fast / mode slow / pause / resume / quit")
    while True:
        try:
            said = input("> ")
        except EOFError:
            break
        if not said.strip():
            continue
        link.send(said)
        if said.strip() == "quit":
            break


if __name__ == "__main__":
    worker = sys.argv[1] if len(sys.argv) > 1 else None
    run("demo", worker)
