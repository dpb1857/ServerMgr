# -*- mode: python; tab-width:8; py-indent-offset:4; indent-tabs-mode:nil -*-
#pylint: disable=C0301
#line length;

"""
Pyro service process management.

Use this module to manage a pyro service.
"""

import multiprocessing
import signal
import sys

import Pyro.core
import Pyro.errors

import base
import my_setproctitle

class Manager(base.Manager):
    """
    Pyro service manager object.

    :param service_name: the Pyro service name for this module.
    :param service: The object used to handle Pyro requests.
    :param ns_host: Pyro nameserver host.
    :param ns_port: Pyro nameserver port.
    :type ns_port: int
    """
    __implements__ = base.ManagerInterface

    def __init__(self, service_name, service, ns_host, ns_port, process_name="Pyro Service", **kwargs):
        
        super(Manager, self).__init__(**kwargs)

        self.ns_host = ns_host
        self.ns_port = ns_port
        self.service_name = service_name
        self.service = service
        self.process_name = process_name

    def health(self):
        """
        Check the health of the Pyro Server.

        :raises: **base.WorkerError** if we cannot invoke the **health** method of the Pyro Server.
        """
        try:
            proxy = Pyro.core.getProxyForURI("PYRONAME://%s:%d/%s" % (self.ns_host, self.ns_port, self.service_name))
            proxy.health()
        except Exception, ex:
            raise base.WorkerError(ex)


    def start(self, wait=True, timeout=10.0):
        """
        Launch the Pyro Service in a fresh python environment.

        :param host:   the nameserver host
        :param port:   the nameserver port
        :type port: int
        :keyword process_name: the displayed program name;
        :keyword module_name: execute function 'main' in the named module;
        """

        def unregister():
            "Unregister the service."

            try:
                ns.unregister(self.service_name)
            except Pyro.errors.NamingError:
                pass

        def launch_pyro_service():
            "Start the service."

            def interrupt(_unused_signum, _unused_frame):
                sys.exit()

            if self.process_name:
                my_setproctitle.setproctitle(self.process_name)

            Pyro.core.initServer()
            unregister()

            daemon = Pyro.core.Daemon()
            daemon.useNameServer(ns)
            daemon.connect(self.service, self.service_name)
            signal.signal(signal.SIGINT, interrupt)

            try: 
                daemon.requestLoop()
            finally:
                daemon.shutdown(True)
                del daemon
                try: 
                    unregister(self.service_name)
                except Exception:
                    pass

        try:
            ns = Pyro.naming.NameServerLocator().getNS(host=self.ns_host, port=self.ns_port)
        except Pyro.errors.PyroError, ex:
            raise IOError("Cannot connect to Pyro nameserver at %s:%d" % (self.ns_host, self.ns_port), ex)

        process = multiprocessing.Process(target=launch_pyro_service)
        process.start()
        self.process = process

        if wait:
            self.ready_wait(timeout=timeout)


def main():
    """main routine."""

    import optparse

    parser = optparse.OptionParser(usage="usage: %prog [options] modulename servicename")
    parser.add_option("-n", "--nameserver", action="store", dest="nameserver", help="Pyro Nameserver as host:port")
    parser.add_option("-p", "--ps", action="store", dest="nameserver", help="ps display string")
    (options, fixed_args) = parser.parse_args()

    (service_name, module_name) = fixed_args
    # XXX print the help message if fixed_args is not the right length;
    # XXX extract ps string from options;
    # XXX extract nameserver specs from options;

    server = Manager(service_name, module_name, ns_host="localhost", ns_port=7504, process_name="Testing: crawler")
    server.start()
    server.wait()

if __name__ == "__main__":
    main()
