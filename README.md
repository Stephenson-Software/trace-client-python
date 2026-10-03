# trace-client (Python)

**One call to report that a program was used.**

A standard-library-only Python 3.8+ client for a [trace](https://trace.danielstephenson.dev)
server — the central place a fleet of programs reports usage events to. The
whole library is one file, `trace_client/trace_client.py`, and the integration
on the program side is meant to stay one call. The Java counterpart is
[trace-client-java](https://github.com/Stephenson-Software/trace-client-java);
the two speak the same wire format and make the same promises.

```python
from trace_client import TraceClient

trace = TraceClient("https://trace.danielstephenson.dev", "roam", __version__,
                    key=settings.usage_reporting_key,
                    enabled=settings.usage_reporting_enabled)
trace.report("startup")
trace.report("world-load", tags={"kind": "procedural"})

# on shutdown -- also before a short-lived program exits, so the event is sent
trace.close()
```

## Every event carries the program's version

The third argument to `TraceClient` is the program's own version, and it is
required: a missing or blank one, or one over 255 characters after trimming,
raises `ValueError`. Every event the client sends — `startup`, `command`,
anything else — carries it as the tag `version`, so every event can be tied
to a release, not just `startup`. An event that passes its own `version` tag
keeps it, and the dict passed as `tags` is never modified. There is no need
to tag `startup` by hand any more.

Before 0.3.0, the constructor took two positional arguments and only events
tagged by hand carried a version. Upgrading is one argument —
`TraceClient(base_url, application, __version__, key=..., enabled=...)` —
and any `tags={"version": __version__}` passed to `report` can be dropped.

## Every event carries a random installation ID

Since 0.4.0, every event can also carry the tag `install`: a random ID for
the installation, so the trace server can count **distinct installations**
("active installs in the last 30 days") rather than raw events — the same
idea as trace-client-java's server ID and bStats' `serverUuid`. It is said
out loud here because it is the one thing the client sends that is the same
from one event to the next.

**What it is.** A random `uuid.uuid4()`. It is not derived from anything —
not a hostname, an IP address, a MAC address, a player, an account or a
path. It identifies no person and no address; all it can say is "these
events came from the same installation". (The trace server still sees the
IP address of every HTTP request, as every web server does.)

**Where it lives.** Wherever the program says — there is no default location
and no hidden file. Without `install_id=` or `install_id_file=`, no ID is
made up, nothing is written, and no `install` tag is sent. The simplest way
in is a file next to the program's own settings:

```python
trace = TraceClient("https://trace.danielstephenson.dev", "roam", __version__,
                    key=settings.usage_reporting_key,
                    enabled=settings.usage_reporting_enabled,
                    install_id_file=os.path.join(settings_dir, "trace-install-id"))
```

The first time an *enabled* client starts, it writes a new random UUID to
that file (creating parent directories) and reuses it on every later run.
The first line that is an ID (`[A-Za-z0-9_.-]`, at most 255 characters) is
the one used. If the file cannot be read or written, a fresh ID is used in
memory for that run only — the constructor never raises over it, and a file
that exists but cannot be read is never overwritten.

A program that already keeps its own settings can pass the ID instead:

```python
trace = TraceClient(url, "roam", __version__, key=key,
                    install_id=settings.get("install_id"))  # None or blank: none sent
```

`install_id=` is trimmed, wins over `install_id_file=`, and over 255
characters raises `ValueError`, like the version. An event that passes its
own `install` tag keeps it, and `install` is never added to an event that
already has 32 tags (the server's limit). `trace.install_id` returns the ID
in use (`None` when disabled or when there is none), so a program can print
it.

`TraceClient.install_id_from_file(path)` is the same load-or-create step on
its own, for a program that wants the ID for something else. Called
directly, it writes the file whatever the opt-outs say — pass the path as
`install_id_file=` to keep the guarantee below.

**Resetting it.** Delete the file; the next start writes a new one. Or put
your own value on its first line.

**Opting out.** Every [opt-out](#turning-it-off) also stops the ID: a
disabled client never generates one, never reads or writes the file, and
sends nothing.

## What `report` promises

| Property | Meaning |
|---|---|
| **Returns immediately** | The HTTP call runs on one daemon thread the client owns. A game loop can report from its main thread and no frame waits on the network. |
| **Never raises** | A server that is down, slow, or rejecting the key is a dropped report, not an exception in your program. Drops are logged at `DEBUG` on the `trace` logger, otherwise not at all. |
| **Bounded** | At most 256 reports wait to be sent; past that, new ones are dropped. A trace server that is unreachable for a week costs a few kilobytes, not your memory. |
| **`close()` drains** | Reports already queued get up to the client timeout (5 s total) to be sent before the thread stops, so a CLI that reports and exits at once does not lose its event. Still bounded: an unreachable server delays exit by at most the timeout. |

## Turning it off

Reporting is **opt-out**. Any one of these yields a client that does nothing
and costs nothing; the first that applies is the reason:

- **Environment, for every trace-reporting program at once:**
  `TRACE_USAGE_REPORTING=off` (also `false`, `0`, `no`; case-insensitive) or
  `DO_NOT_TRACK=1` (also `true`, `yes`; the
  [consoledonottrack.com](https://consoledonottrack.com) convention). The
  constructor checks these before anything else, so they win over the
  program's own setting. Any other value, or an unset variable, leaves that
  setting in charge.
- **The program's own setting:** `enabled=False`.
- **No key** (or a blank one).

`client.disabled_reason` says which one applied — `"environment"`, `"config"`
or `"no key"` — and is `None` when the client reports, so a program can log
it. A program that runs on other people's machines should expose the
`enabled` switch in its settings — and say so once, the first time it runs,
so the player knows reporting is on, that `TRACE_USAGE_REPORTING=off` turns
it off, and where the details are:
<https://github.com/Stephenson-Software/trace#usage-reporting>.

## Getting it

**Copy the file.** `trace_client/trace_client.py` has no dependencies. Drop
it into your source tree (as `trace_client.py`), keep the header so it can be
found again, and you are done.

**Or vendor the package** — copy the `trace_client/` directory — if you prefer
`from trace_client import TraceClient` unchanged.

There is no PyPI package yet; the file is the distribution.

## The wire format

`POST {base_url}/api/metrics` with `Authorization: Bearer <key>` and a body of

```json
{"application":"roam","name":"command","value":1.0,"tags":{"name":"home","version":"1.4.0"}}
```

`value` is omitted when not given; `tags` always holds at least `version`, and
`install` when the client has an [installation ID](#every-event-carries-a-random-installation-id). The server assigns the
timestamp. A `201` is success; anything else is logged at `DEBUG` and dropped.

## Keys

A key identifies the program to the server and lets the operator revoke it;
it is scoped to *reporting only*. Because it ships inside the program, it
cannot prove anything — treat trace data as best-effort telemetry, which is
what it is. Ask the trace operator for a key for your program.

## In the browser (Pyodide)

Pyodide has no real threads and no outbound sockets, so build the client with
`enabled=False` there. Nothing is lost: the desktop build reports.

## Building

```
python -m unittest -v
```

Tests run the client against the standard library's own `ThreadingHTTPServer`
on a loopback port. CI runs them on Python 3.8, 3.10 and 3.12.

## License

MIT.
