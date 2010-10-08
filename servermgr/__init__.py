# -*- mode: python; tab-width:8; py-indent-offset:4; indent-tabs-mode:nil -*-

"""
Servermgr is a collection of classes that make it easier to manage external programs that are running for the sole benefit of your application.

Sample use cases:

* Your program wants to run its own copy of Postgres with a separate data directory on its own port;
* Your program wants to control its own dedicated copy of Nginx to use as a front-end;

In either of these cases, there is no need to configure multiple programs to run your application - 
you can simply configure the appropriate server manager object and go!
"""

__version__ = "0.2.2"
