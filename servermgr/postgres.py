# -*- mode: python; tab-width:8; py-indent-offset:4; indent-tabs-mode:nil -*-
#pylint: disable=C0301
#line length;

"""
Postgres process management.

Use this module to initialize a postgres data directory and to 
manage a postgres server.

Environment Variables
---------------------

POSTGRES_VERSION - if specified, this will be the default version of postgres. The 
documentation for the **Manager** class describes how the version of postgres is chosen.

"""

import copy
import os
import psycopg2
import subprocess

import base

class DatabaseException(base.WorkerError):
    """Database exceptions."""

def _check_lockdir_permissions():
    """
    Make sure we have permission to create a postgres postfile.
    
    :raises: **DatabaseException** if we do not have write permission on the lockfile directory.
    """
    
    if not os.access("/var/run/postgresql", os.W_OK):
        raise DatabaseException("We require write access to the postgres lockfile directory, /var/run/postgresql.")

def _get_default_postgres_version():
    """
    Select the default version of postgres to use. 

    If the environment variable POSTGRES_VERSION is set, use that.
    Otherwise, use the largest numbered directory in /usr/lib/postgresql.

    :returns: the default version of postgres, or **None** if we can't determine the default postgres version.
    """

    environ_version = os.environ.get("POSTGRES_VERSION", None)
    if environ_version:
        return environ_version

    # Pick the version with the largest number in the directory /usr/lib/postgresql;
    try:
        return max([(float(d), d) for d in os.listdir("/usr/lib/postgresql")])[1]
    # bad directory;
    except OSError: 
        pass
    # can't convert name to a float;
    except ValueError: 
        pass
    
    return None


def _env_with_postgres_path(pg_version):
    """
    Return a new environment with Postgres bin directories append to the end.
    """

    env = copy.copy(os.environ)
    new_path_element = "/usr/lib/postgresql/%s/bin" % pg_version
    env["PATH"] += ":" + new_path_element
    return env, new_path_element

def _initialize_directory(directory, pg_version):
    """Initialize a postgres data directory.

    :param directory: Name of the postgres data directory.
    :param pg_version: The version of postgres to use.
    :raises: **OSError** if subprocess execution fails.
    :raises: **DatabaseException** on initdb error.
    """

    env, new_path_elem = _env_with_postgres_path(pg_version)
    try:
        process = subprocess.Popen(["initdb", "-D", directory], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE,
                                   close_fds=True, env=env)
    except OSError, ex:
        ex.strerror += ": initdb; new path element:" + new_path_elem
        raise ex

    process.wait()

    messages = process.stdout.read()
    errors = process.stderr.read()
    if errors.find("WARNING") >= 0:
        messages += errors
        errors = ""

    if errors:
        raise DatabaseException(errors)

    return messages

class Manager(base.ManagerBase):
    """
    Postgres manager object.

    Selecting the postgres version: 

    * Use the version specified by the pg_version parameter.
    * If pg_version is not specified, use the environment variable POSTGRES_VERSION.
    * If the environment variable is not set, use the highest numbered version in the
      directory /usr/lib/postgresql.

    :param host: the interface to listen on.
    :type host: string
    :param port: the post to listen on.
    :type port: int
    :param db_dir: the database data directory.
    :type db_dir: string
    :param initialize: If this flag is true, the database data directory will be initialized iff 
      the data directory does not already exist.
    :type initialize: bool
    :param pg_version: Version of postgres to use. 
    :type pg_version: string

    :raises: **DatabaseException** if data directory initialization fails.
    """

    __implements__ = base.ManagerInterface

    def __init__(self, host, port, db_dir, initialize=False, pg_version="", **kwargs):

        super(Manager, self).__init__("Postgres", **kwargs)

        _check_lockdir_permissions()

        if not pg_version:
            pg_version = _get_default_postgres_version()
            if not pg_version:
                raise DatabaseException("could not select a version of postgres to use.")
            
        self.host = host
        self.port = port
        self.db_dir = db_dir
        self.pg_version = pg_version

        if initialize and not os.path.exists(db_dir):
            _initialize_directory(db_dir, pg_version)
        
    def health(self):
        """
        Check manager health.

        :raises: **WorkerError** if we cannot connect to the database
        """

        try:
            psycopg2.connect(database="postgres", port=self.port)
            return
        except psycopg2.OperationalError, ex:
            raise base.WorkerError(ex)

    def start(self, wait=True, timeout=10.0):
        """Launch the postgres process.
        
        :param wait: If true, call self.ready_wait() after starting the subprocess.
        :param timeout: When calling ready_wait(), use this timeout value.
        :raises: **OSError** if postgres fails to launch.
        """

        base.address_free_check(self.host, self.port)
        env, new_path_elem = _env_with_postgres_path(self.pg_version)
        try:
            self.process = subprocess.Popen(["postgres", 
                                             "-D", self.db_dir,
                                             "-h", self.host,
                                             "-p", str(self.port)],
                                            stdout=file("/dev/null"), stderr=subprocess.PIPE,
                                            close_fds=True, env=env)
        except OSError, ex:
            ex.strerror += ": postgres; new path element:" + new_path_elem
            raise ex

        if wait:
            self.ready_wait(timeout=timeout)


def main():
    """
    You can use this script to start a copy of postgres.

    Usage: postgres.py [options]

    Options:
      -h, --help            show this help message and exit
      -H HOST, --host=HOST  listener hostname
      -p PORT, --port=PORT  listener port
      -d DATADIR, --datadir=DATADIR
                            data directory
      -i INITIALIZE, --init=INITIALIZE
                            initialize data directory
      -v VERSION, --version=VERSION
                            postgres version
    """

    import optparse
    import signal
    import sys
    
    def to_bool(val):
        """Convert boolean string to an actual bool"""
        return dict(True=True, False=False)[val]

    def interrupt(_unused_signum, _unused_frame):
        """Handle user stopping with control-C."""
        print >> sys.stderr, "Keyboard interrupt, exiting."
        sys.exit()

    signal.signal(signal.SIGINT, interrupt)

    default_host = "localhost"
    default_port = 15432
    default_datadir = os.environ.get("POSTGRES_DATA", "/var/tmp/pg_data")
    default_initialize = True
    default_version = ""

    parser = optparse.OptionParser(usage="usage: %prog [options]")
    parser.add_option("-H", "--host", action="store", dest="host", help="listener hostname")
    parser.add_option("-p", "--port", action="store", dest="port", help="listener port")
    parser.add_option("-d", "--datadir", action="store", dest="datadir", help="data directory")
    parser.add_option("-i", "--init", action="store", dest="initialize", help="initialize data directory")
    parser.add_option("-v", "--version", action="store", dest="version", help="postgres version")

    (options, _unused_args) = parser.parse_args()

    host = options.host if options.host else default_host
    port = int(options.port) if options.port else default_port
    datadir = options.datadir if options.datadir else default_datadir
    initialize = to_bool(options.initialize) if options.initialize else default_initialize
    pg_version = options.version if options.version else default_version

    db_manager = Manager(host, port, datadir, initialize=initialize, pg_version=pg_version)
    print >> sys.stderr, "starting database..."
    db_manager.start()
    print >> sys.stderr, "database ready on %s:%d using data directory %s." % (host, port, datadir)
    db_manager.wait()

if __name__ == "__main__":
    main()
