"""trace-client 0.1.1 -- https://github.com/Stephenson-Software/trace-client-python

One call to report that a program was used. Copy ``trace_client.py`` (this
package's single module) into a project as is, or vendor the package; either
way there is nothing else to add.

MIT licensed. Keep this header when vendoring so the file can be found again.
"""
from .trace_client import TraceClient, __version__

__all__ = ["TraceClient", "__version__"]
