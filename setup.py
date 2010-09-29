#!/usr/bin/env python

import os
import re

from distutils.core import setup

v = file(os.path.join(os.path.dirname(__file__), 'servermgr', '__init__.py'))
VERSION = re.compile(r'.*__version__ = "(.*?)"', re.S).match(v.read()).group(1)
v.close()

setup(name="servermgr",
      version=VERSION,
      description="Server process configuration and management",
      author="Don Bennett",
      author_email="dpb@donbennett.org",
      url="http://github.com/dpb1857/servermgr/",
      packages=['servermgr',],
      license = "MIT License",
      long_description = """\
Servermgr is a collection of classes that make it easier to manage external programs that are running for the sole benefit of your application.

Sample use cases:

* Your program wants to run its own copy of Postgres with a separate data directory on its own port;
* Your program wants to control its own dedicated copy of Nginx to use as a front-end;

In either of these cases, there is no need to configure multiple programs to run your application - 
you can simply configure the appropriate server manager object and go!
""",
      classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        ],
      )
