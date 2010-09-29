# -*- mode: python; tab-width:8; py-indent-offset:4; indent-tabs-mode:nil -*-
#pylint: disable=C0301
#line length;

"""
Pyro module management.

Use this module to manage a Pyro name server.
"""

import os
import subprocess
import sys

import base
import my_setproctitle

class Manager(base.ManagerBase):
    """Pyro manager object.

    :param host: the interface to listen on.
    :param port: the port to listen on.
    :type port: int
    :param data_dir: name of the pyro data directory
    :keyword name: the program name
    :keyword process_name: the string to diplay in 'ps'
    """

    __implements__ = base.ManagerInterface

    def __init__(self, host, port, data_dir, *args, **kwargs):
        
        super(Manager, self).__init__("Pyro", *args, **kwargs)

        self.host = host
        self.port = port
        self.data_dir = data_dir

    def health(self):
        """
        Check Pyro health.

        :raises: **base.WorkerError** if we cannot locate the Pyro name server.
        """
        
        import Pyro.naming

        try:
            Pyro.naming.NameServerLocator().getNS(host=self.host, port=self.port)
        except Pyro.errors.PyroError, ex:
            raise base.WorkerError(ex)
    
    def start(self, wait=True, timeout=10.0):
        """
        Launch the Pyro name server in its own process.
        
        :param wait: If true, call self.ready_wait() after starting the subprocess.
        :param timeout: When calling ready_wait(), use this timeout value.
        :type timeout: float, number of seconds
        :raises: **base.WorkerError** if the worker hasn't started before timeout elapses.
        """

        os.environ["PYRO_STORAGE"] = self.data_dir
        launch_prog = '\n'.join(
            ["""from servermgr import pyro;"""
             """pyro.Manager.launch(host="%s", port=%d, process_name="%s")"""
             ]) % (self.host, self.port, self.process_name)

        self.process = subprocess.Popen(["python", "-c", launch_prog])

        if wait:
            self.ready_wait(timeout=timeout)

    @staticmethod
    def launch(**kwargs):
        """
        Launch the Pyro nameserver in a fresh python environment.

        :param host:   the nameserver host
        :param port:   the nameserver port
        :type port: int
        :param process_name: the displayed program name;
        """

        pname = kwargs.get("process_name", None)
        if pname:
            my_setproctitle.setproctitle(pname)

        import Pyro.naming
        Pyro.naming.main(["-n", kwargs["host"], "-p", kwargs["port"], "-d"])


def interrupt(_unused_signum, _unused_frame):
    """Handle user stopping with control-C."""
    print >> sys.stderr, "Keyboard interrupt, exiting."
    sys.exit()

def main():
    """
    You can use this script to start a copy of the pyro nameserver; however, you could 
    just as easily run the **pyro-ns** script installed by pyro.

    Usage: pyro.py [options]

    Options:
      -h, --help            show this help message and exit
      -H HOST, --host=HOST  Pyro nameserver hostname
      -p PORT, --port=PORT  Pyro nameserver port
      -d DATADIR, --datadir=DATADIR
                            Pyro data directory
"""
    
    import optparse
    import signal

    signal.signal(signal.SIGINT, interrupt)

    default_host = "localhost"
    default_port = 7604
    default_datadir = "/tmp"

    parser = optparse.OptionParser(usage="usage: %prog [options]\nFor help, run: %prog -h")
    parser.add_option("-H", "--host", action="store", dest="host", help="Pyro nameserver hostname")
    parser.add_option("-p", "--port", action="store", dest="port", help="Pyro nameserver port")
    parser.add_option("-d", "--datadir", action="store", dest="datadir", help="Pyro data directory")

    (options, _unused_args) = parser.parse_args()

    host = default_host
    if options.host:
        host = options.host

    port = default_port
    if options.port:
        port = int(options.port)

    datadir = default_datadir
    if options.datadir:
        datadir = options.datadir

    server = Manager(host, port,  datadir, 
                     process_name="Pyro nameserver")
    print "starting nameserver"
    server.start()
    print "nameserver ready"
    server.wait()

if __name__ == "__main__":
    main()
