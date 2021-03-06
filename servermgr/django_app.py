# -*- mode: python; tab-width:8; py-indent-offset:4; indent-tabs-mode:nil -*-
#pylint: disable=C0301
#line length;

"""
Django process management.

Use this module to run a django app.
"""

import multiprocessing
import os
import socket
import sys

import base
import my_setproctitle


def get_module_directory(module_name):
    """Find the filesystem directory where a module lives."""

    try:
        __import__(module_name)
        app_dir = os.path.dirname(sys.modules[module_name].__file__)
        return app_dir
    except ImportError, ex:
        print >> sys.stderr, ex
        print >> sys.stderr, "Cannot find settings module " + module_name
        sys.exit(1)

class Manager(base.Manager):
    """
    Django manager object.

    :param host: the interface to listen on.
    :param port: the port to listen on.
    :type port: int
    :param settings: name of the django settings module
    :keyword name: the program name
    :keyword process_name: the string to diplay in 'ps'
    """

    __implements__ = base.ManagerInterface

    def __init__(self, host, port, settings, name="DjangoApp", process_name=None, **kwargs):

        super(Manager, self).__init__(name=name, **kwargs)

        self.host = host
        self.port = port
        self.settings = settings
        self.settings_dir = get_module_directory(settings)
        self.process_name = process_name

    def health(self):
        """
        Check the health of the django subprocess.

        :raises: **base.WorkerError** if we cannot create a socket connection to app.
        """
        try:
            s__ = socket.create_connection((self.host, self.port))
            s__.close()
        except socket.error, ex:
            raise base.WorkerError(ex)

    def start(self, wait=True, timeout=10.0):
        """
        Start the Django app in its own process.

        :param wait: If true, call self.ready_wait() after starting the subprocess.
        :param timeout: When calling ready_wait(), use this timeout value.
        :type timeout: float, number of seconds
        :raises: **base.WorkerError** if the worker hasn't started before timeout elapses.
        """

        def launch_django():
            "The Django subprocess."

            if self.process_name:
                my_setproctitle.setproctitle(self.process_name)

            sys.path.insert(0, self.settings_dir)
            os.environ["DJANGO_SETTINGS_MODULE"] = self.settings
            from django.core.management.commands import runfcgi
            cmd = runfcgi.Command()

            # XXX We should allow configuration of the options below;
            cmd.handle("host="+self.host,
                       "port="+str(self.port),
                       "method=prefork",
                       "daemonize=False",
                       "maxchildren=2",
                       "maxspare=2")
            
        process = multiprocessing.Process(target=launch_django)
        process.start()
        self.process = process        

        if wait:
            self.ready_wait(timeout=timeout)

def main():
    """main routine."""

    import optparse
    import subprocess

    default_host = "localhost"
    
    parser = optparse.OptionParser(usage="usage: %prog [options]")
    parser.add_option("-H", "--host", action="store", dest="host", help="django app host")
    parser.add_option("-p", "--port", action="store", dest="port", help="django app port")
    parser.add_option("-s", "--settings", action="store", dest="settings", help="Django settings module name")
    parser.add_option("-f", "--fcgi", action="store_true", dest="fcgi", help="Run fcgi subprocess")
    parser.add_option("-n", "--name", action="store", dest="name", help="process name")

    (options, _unused_args) = parser.parse_args()

    default_port = 8001 if options.fcgi else 8000
    host = options.host if options.host else default_host
    port = int(options.port) if options.port else default_port
    settings = options.settings
    process_name = options.name

    if options.fcgi:
        print >> sys.stderr, "Creating fcgi server on %s:%d" % (host, port)
        server = Manager(host, port, settings, process_name=process_name)
        print >> sys.stderr, "starting server..."
        server.start()
        print >> sys.stderr, "server ready."
        server.wait()
    else:
        os.chdir(get_module_directory(settings))
        subshell = subprocess.Popen(["python", 
                                     "manage.py", 
                                     "runserver",
                                     "%s:%d" % (host, port)],
                                    )
        subshell.wait()

if __name__ == "__main__":
    main()
