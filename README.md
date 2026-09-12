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

trace = TraceClient("https://trace.danielstephenson.dev", "roam",
                    key=settings.usage_reporting_key,
                    enabled=settings.usage_reporting_enabled)
trace.report("startup", tags={"version": __version__})
trace.report("world-load", tags={"kind": "procedural"})

# on shutdown -- also before a short-lived program exits, so the event is sent
trace.close()
```

## What `report` promises

| Property | Meaning |
|---|---|
| **Returns immediately** | The HTTP call runs on one daemon thread the client owns. A game loop can report from its main thread and no frame waits on the network. |
| **Never raises** | A server that is down, slow, or rejecting the key is a dropped report, not an exception in your program. Drops are logged at `DEBUG` on the `trace` logger, otherwise not at all. |
| **Bounded** | At most 256 reports wait to be sent; past that, new ones are dropped. A trace server that is unreachable for a week costs a few kilobytes, not your memory. |
| **`close()` drains** | Reports already queued get up to the client timeout (5 s total) to be sent before the thread stops, so a CLI that reports and exits at once does not lose its event. Still bounded: an unreachable server delays exit by at most the timeout. |

Reporting is **opt-out**: `enabled=False`, or no key at all, yields a client
that does nothing and costs nothing. A program that runs on other people's
machines should expose that switch in its settings — and say so once, the
first time it runs, so the player knows it is on and where to turn it off.

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
{"application":"roam","name":"startup","tags":{"version":"1.4.0"}}
```

`value` and `tags` are omitted when not given. The server assigns the
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
