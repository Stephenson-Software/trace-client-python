"""trace-client 0.4.0 -- https://github.com/Stephenson-Software/trace-client-python

One call to report that a program was used. Copy ``trace_client.py`` (this
package's single module) into a project as is, or vendor the package; either
way there is nothing else to add.

MIT licensed. Keep this header when vendoring so the file can be found again.
"""
from .trace_client import (ENV_DO_NOT_TRACK, ENV_TRACE_USAGE_REPORTING, INSTALL_TAG, MAX_TAG_LENGTH,
                           MAX_TAGS, REASON_CONFIG, REASON_ENVIRONMENT, REASON_NO_KEY, TraceClient,
                           __version__, environment_opts_out)

__all__ = ["TraceClient", "__version__", "environment_opts_out", "ENV_TRACE_USAGE_REPORTING",
           "ENV_DO_NOT_TRACK", "REASON_ENVIRONMENT", "REASON_CONFIG", "REASON_NO_KEY", "MAX_TAG_LENGTH",
           "MAX_TAGS", "INSTALL_TAG"]
