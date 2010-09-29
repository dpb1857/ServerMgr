# -*- mode: python; tab-width:8; py-indent-offset:4; indent-tabs-mode:nil -*-

"""
Either import the real setproctitle, or define a noop stub.
"""

import sys

try: 
    from setproctitle import setproctitle  #pylint: disable=W0611
except ImportError:
    print >> sys.stderr, "Warning: could not import setproctitle module."
    def setproctitle(*_unused_args, **_unused_kwargs):
        """Use this setproctitle stub if we can't load the real thing."""
        pass
