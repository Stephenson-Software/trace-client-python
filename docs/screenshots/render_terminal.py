"""Runs examples/demo.py and writes its real output as a terminal-styled
HTML page, which media.json then screenshots. Usage:

    python docs/screenshots/render_terminal.py OUT.html
"""
import html
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
COMMAND = ["python", "examples/demo.py"]

PAGE = """<!doctype html><meta charset="utf-8"><title>demo</title>
<style>
body {{ margin: 0; background: #e8eaed; font: 15px/1.5 "DejaVu Sans Mono", monospace; }}
#term {{ display: inline-block; margin: 24px; background: #0d1117; color: #c9d1d9;
        border-radius: 10px; box-shadow: 0 4px 18px #0004; min-width: 1000px; }}
.bar {{ padding: 9px 14px; background: #161b22; border-radius: 10px 10px 0 0; }}
.bar i {{ display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 6px; }}
pre {{ margin: 0; padding: 14px 20px 18px; font: inherit; white-space: pre; }}
.p {{ color: #7ee787; }}
</style>
<div id="term"><div class="bar"><i style="background:#ff5f56"></i><i style="background:#ffbd2e"></i><i style="background:#27c93f"></i></div>
<pre><span class="p">$</span> {command}
{output}</pre></div>
"""


def main(out):
    env = {k: v for k, v in os.environ.items() if k not in ("TRACE_USAGE_REPORTING", "DO_NOT_TRACK")}
    result = subprocess.run([sys.executable] + COMMAND[1:], cwd=ROOT, env=env, check=True,
                            capture_output=True, text=True)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as page:
        page.write(PAGE.format(command=html.escape(" ".join(COMMAND)),
                               output=html.escape(result.stdout.rstrip("\n"))))


if __name__ == "__main__":
    main(sys.argv[1])
