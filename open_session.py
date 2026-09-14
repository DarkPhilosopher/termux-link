"""Opens a brand-new, INDEPENDENT Termux session that runs a given
script -- the "one termux session opened in a python script" half of
this. Not testable from this sandbox (there's no real Android activity
manager here) -- verified only by reading Termux's own RUN_COMMAND
documentation carefully; try it for real and tell me what happens.

One-time setup this needs, done once on the device itself:

    echo "allow-external-apps = true" >> ~/.termux/termux.properties
    termux-reload-settings

Termux refuses RUN_COMMAND from anywhere -- including from Termux
itself -- until that's set. It's a deliberate safety switch: RUN_COMMAND
can start arbitrary commands, so it's off unless you turn it on.

The target script needs to be executable and start with a shebang
line, e.g. `#!/data/data/com.termux/files/usr/bin/python3` -- same as
worker.py in this same folder.
"""

import subprocess


def open_termux_session(script_path, args=None, session_name=None):
    """Starts script_path running in a brand new Termux session (a new
    tab, visible in Termux's own session list) -- NOT a background
    process, and not the session this function is called from."""
    cmd = [
        "am", "startservice",
        "--user", "0",
        "-n", "com.termux/com.termux.app.RunCommandService",
        "-a", "com.termux.RUN_COMMAND",
        "--es", "com.termux.RUN_COMMAND_PATH", script_path,
        "--ez", "com.termux.RUN_COMMAND_BACKGROUND", "false",
    ]
    if args:
        cmd += ["--esa", "com.termux.RUN_COMMAND_ARGUMENTS", ",".join(args)]
    if session_name:
        cmd += ["--es", "com.termux.RUN_COMMAND_SESSION_ACTION", "0"]
        cmd += ["--es", "com.termux.RUN_COMMAND_SESSION_NAME", session_name]
    subprocess.run(cmd, check=True)
