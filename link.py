"""termux_link -- a bidirectional channel between two INDEPENDENT
Termux sessions, each running its own Python program: one side sends
plain-text commands that change how the program on the OTHER side is
running, and either side can read whatever the other prints out, live,
both directions at once, regardless of which one started first.

Requested directly (paraphrased): a script in one Termux session that
sends text commands changing how a different program behaves in a
different, independent Termux session, with the two able to read each
other's output both ways.

Under the hood, a link "name" is a pair of named pipes (FIFOs), under
~/.termux-link/<name>/ -- one per direction, a2b and b2a. A
Link(name, side) knows which of the pair it writes and which it reads:
side "a" writes a2b and reads b2a; side "b" writes b2a and reads a2b.
Reading happens on a background thread so it never blocks whatever
else the program is doing; each complete line that arrives either goes
to a callback you supply (on_line) or queues up for recv()/recv_nowait().

FIFOs, not a socket: no port number to agree on ahead of time, nothing
to bind that a stale second instance could leave claimed -- two
processes that just open the same two named files under the same name,
in opposite directions, are linked. The tradeoff: only ONE reader may
usefully be alive on a given end at a time (a second one competes for
lines instead of each getting a copy) -- fine for exactly the
two-sessions case this was built for, not a broadcast channel.
"""

import os
import queue
import threading

BASE_DIR = os.path.join(os.path.expanduser("~"), ".termux-link")


def _paths(name):
    d = os.path.join(BASE_DIR, name)
    return d, os.path.join(d, "a2b"), os.path.join(d, "b2a")


def _ensure_fifo(path):
    if not os.path.exists(path):
        os.mkfifo(path)


class Link:
    def __init__(self, name, side, on_line=None):
        if side not in ("a", "b"):
            raise ValueError("side must be 'a' or 'b'")
        d, a2b, b2a = _paths(name)
        os.makedirs(d, exist_ok=True)
        _ensure_fifo(a2b)
        _ensure_fifo(b2a)
        write_path = a2b if side == "a" else b2a
        read_path = b2a if side == "a" else a2b
        # O_RDWR on a FIFO never blocks, even with nobody on the other
        # end yet -- the standard trick to dodge the fact that a plain
        # O_WRONLY/O_RDONLY open on a FIFO blocks until a reader/writer
        # shows up on the other end, which would otherwise force both
        # sides to start in one particular order (or deadlock if they
        # both open in the "wrong" order at once).
        self._wfd = os.open(write_path, os.O_RDWR)
        self._rfd = os.open(read_path, os.O_RDWR)
        self._q = queue.Queue()
        self._on_line = on_line
        self._buf = b""
        self._stop = False
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        while not self._stop:
            try:
                chunk = os.read(self._rfd, 4096)
            except OSError:
                break
            if not chunk:
                continue
            self._buf += chunk
            while b"\n" in self._buf:
                line, self._buf = self._buf.split(b"\n", 1)
                text = line.decode("utf-8", "replace")
                if self._on_line is not None:
                    self._on_line(text)
                else:
                    self._q.put(text)

    def send(self, text):
        os.write(self._wfd, (text.rstrip("\n") + "\n").encode("utf-8"))

    def recv_nowait(self):
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return None

    def recv(self, timeout=None):
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self):
        self._stop = True
        for fd in (self._rfd, self._wfd):
            try:
                os.close(fd)
            except OSError:
                pass
