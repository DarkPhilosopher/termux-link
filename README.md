# termux-link

A command in one Termux session that changes how a *different* program
is running in a *different, independent* Termux session -- with both
sides able to read each other's output, live, both ways.

Requested directly (paraphrased): "one termux session opened in a
python script, for termux text commands to change the program's
manners how it's running in a different termux session, [with] a
different program made to read the output of the other both ways."

Two separate pieces, because the request is actually two separate
things stacked together:

## 1. `link.py` -- the two-way channel itself

A pair of named pipes (FIFOs) under `~/.termux-link/<name>/`, one per
direction. Either side opens a `Link(name, side="a"|"b")` -- order
doesn't matter, neither has to wait for the other to exist first -- and
gets `.send(text)` to say something, plus either `.recv()`/
`.recv_nowait()` or an `on_line` callback to hear whatever the other
side says, as it arrives, on a background thread.

This half is fully working and tested (right here in this sandbox,
using two ordinary background processes standing in for "two sessions"
-- the channel itself doesn't know or care whether the two ends are
literally two Termux tabs or just two processes): mode changes, pause/
resume, and quit all round-tripped correctly, both directions.

## 2. `open_session.py` -- actually opening the second session

Uses Termux's own `RUN_COMMAND` intent to start a script in a **brand
new, independent Termux session** (its own tab, visible in Termux's
session list) -- not a background subprocess of the caller, a real
separate session the same way opening a new tab by hand would be.

**One-time setup, on the device itself:**

```
echo "allow-external-apps = true" >> ~/.termux/termux.properties
termux-reload-settings
```

Termux refuses `RUN_COMMAND` from anywhere -- including from Termux
itself -- until that line is there; it's a deliberate safety switch,
since it lets a script start arbitrary commands.

**This half is NOT verified** -- there's no real Android activity
manager in the sandbox this was built in to actually fire the intent
and watch a session open. Written carefully from Termux's own
documented `RUN_COMMAND` format, but please try it for real and tell
me what happens (or doesn't).

## Try the demo

Two Termux sessions, side by side:

```
# session 1
python3 worker.py demo

# session 2
python3 controller.py
```

Type `mode fast`, `mode slow`, `pause`, `resume`, or `quit` into
session 2 -- session 1's own status line (which it's printing on its
own, independently) changes to match, live, and session 2 prints back
whatever session 1 says on every tick. Or let `controller.py` open
`worker.py`'s session for you, once RUN_COMMAND is set up:

```
python3 controller.py /data/data/com.termux/files/home/termux-link/worker.py
```

## Using it in your own two programs

```python
from link import Link

link = Link("mylink", side="a", on_line=lambda text: print("got:", text))
link.send("do the thing")
```

The other program does the same with `side="b"` and the same link
name -- that's the whole contract. One reader per end, not a broadcast
channel: fine for exactly this, two sessions talking to each other.
