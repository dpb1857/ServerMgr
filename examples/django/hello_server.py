#!/usr/bin/env python

"""
Launch a Django webapp serving "Hello, world" pages via fastcgi and a Nginx web server to handle the HTTP front-end.
"""

import os
import signal
import sys

def add_servermgr_to_path():
    """
    locate our servermgr directory and add it to python path for both 
    this process and our subprocesses.
    """

    for dir in ("..", "../..", "../../.."):
        if os.path.exists(os.path.join(dir, "servermgr")):
            pp = os.environ.get("PYTHONPATH", None)
            new_pp = ':'.join(dir, pp) if pp else dir
            os.environ["PYTHONPATH"] = new_pp
            sys.path.insert(0, dir)
            break

def interrupt(_unused_signum, _unused_frame):
    """Handle user stopping with control-C."""
    print >> sys.stderr, "Keyboard interrupt, exiting."
    sys.exit()

def main():

    add_servermgr_to_path()    

    from servermgr import django_app
    from servermgr import nginx

    HTTP_PORT = 8080
    FCGI_PORT = 8081

    signal.signal(signal.SIGINT, interrupt)
    
    django_server = django_app.Manager("localhost", FCGI_PORT, "hello.settings", process_name="Sample Django App: Hello Server")
    django_server.start()
    print >> sys.stderr, "Starting django app..."

    nginx_server = nginx.Manager("localhost", HTTP_PORT, "/tmp/nginx")
    nginx_server.add_fastcgi_mapping("/", "localhost:8081")
    nginx_server.start()
    print >> sys.stderr, "Starting nginx front end on port %d..." % HTTP_PORT

    print >> sys.stderr, "Waiting for nginx to exit..."
    nginx_server.wait()


if __name__ == "__main__":
    main()



