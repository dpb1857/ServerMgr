# -*- mode: python; tab-width:8; py-indent-offset:4; indent-tabs-mode:nil -*-

"""
Interface definition and base implementation for all subprocess managers.
"""

import socket
import time

#pylint: disable=R0921
#abstract class not implemented;

class ManagerInterface(object):
    """
    This abstract class defines the interface implemented by all Managers.
    """

    def health(self):
        """
        Check the health of the worker subprocess.

        :raises: **WorkerError** if the worker subprocess is not responding.
        """
        raise NotImplementedError

    def start(self, wait=True, timeout=10.0):
        """
        Start the worker subprocess.

        :param wait: If true, call self.ready_wait() after starting the subprocess.
        :param timeout: When calling ready_wait(), use this timeout value.
        :type timeout: float, number of seconds
        """
        raise NotImplementedError

    def ready_wait(self, timeout=10.0):
        """
        Wait for the worker to be ready to handle requests.

        :param timeout: Give the server this many seconds to start. If the 
          timeout expires before the server has started, 
          kill the server and raise WorkerError.
        :type timeout: float, seconds
        :raises: **WorkerError** if the worker is not ready within the time limit.
        """
        raise NotImplementedError

    def stop(self, wait=True):
        """
        Stop the worker subprocess.
        
        :param wait: If True, wait for the worker to exit.
        :type wait: boolean
        """
        raise NotImplementedError

    def wait(self):
        """Wait for the worker process to exit."""
        raise NotImplementedError

class WorkerError(Exception):
    """Exception raised when a Worker fails to start 
       or fails to respond.
    """

    def __init__(self, exception, *args, **kwargs):
        super(WorkerError, self).__init__(*args, **kwargs)
        self.exception = exception
        
    def __str__(self):
        
        val = super(WorkerError, self).__str__()
        if self.exception == None:
            return val

        return val + " " + str(self.exception)


def address_in_use(host, port):
    """
    Check to see if there is a listener on host:port.

    :param host: the interface to check;
    :type host: string
    :param port: the post to check;
    :type port: int
    :returns: **True** if there is a listener, else **False**.
    """
    try:
        s__ = socket.create_connection((host, port))
        s__.close()
        return True
    except socket.error:
        return False

def address_free_check(host, port):
    """
    Raise an exception if host:port is in use.

    :param host: the interface to check;
    :type host: string
    :param port: the post to check;
    :type port: int

    :raises: **WorkerError** if the address is in use.
    """
    if address_in_use(host, port):
        raise WorkerError(None, "address already in use", host, port)


class BaseProcess(object):
    """
    Base class for class wrapper functionality 
    used by SubprocessWrapper and MultiprocessingWrapper.
    """
    def __init__(self, process_thing):
        self.process = process_thing

    def __getattr__(self, attrib):
        return getattr(self.process, attrib)

class SubprocessWrapper(BaseProcess):
    """
    This class is a wrapper around subprocess.Popen to unify the interface 
    with multiprocssing.Process.
    """
    def join(self, _unused_timeout=None):
        """Add join method to subprocess.Popen."""
        self.process.wait()


class MultiprocessingWrapper(BaseProcess):
    """
    This class is a wrapper around multiprocessing.Process to unify the interface 
    with subprocess.Popen.
    """

    def wait(self):
        """Add wait method to multiprocessing.Process."""
        return self.process.join(None)

    def poll(self):
        """Add poll method to multiprocessing.Process."""
        if self.process.is_alive():
            return None
        return True

def wrap_process(process_thing):
    """Wrap the (Popen, Process) in the proper wrapper to provide uniform functionality."""

    if hasattr(process_thing, "wait"):
        obj = SubprocessWrapper(process_thing)
    else:
        obj = MultiprocessingWrapper(process_thing)
    return obj

        
#pylint: disable=R0922
#abstract class only referenced one time;
class Manager(object):
    """
    :param name: Name of manager, displayed in error and log messages.
    :param kwargs: Any other keyword args will be stored in self.kwargs.

    This is the base implementation of the Manager class.
    
    Implementations are provided for the following methods:

    * ready_wait()
    * stop()
    * wait()
    
    The following methods must be implemented by the subclass:

    * health()
    * start()
    """

    def __init__(self, name="<unnamed>", **kwargs):
        """Initialize the Manager object."""
        self._process = None
        self.name = name
        self.kwargs = kwargs

    def __del__(self):

        self.stop()

    @property
    def process(self):
        "Return the process object."

        return self._process

    @process.setter
    def process(self, process):
        "Wrap the (subprocess.Popen, multiprocessing.Process) with a proxy class."

        self._process = wrap_process(process) if process else None

    def health(self):
        """Check the worker subprocess health.

        :raises: **NotImplementedError** must be implemented by subclass.
        """
        raise NotImplementedError

    def start(self, wait=True, timeout=10.0):
        """
        Start the worker subprocess.

        :raises: **NotImplementedError** must be implemented by subclass.
        """
        raise NotImplementedError        

    def ready_wait(self, timeout=10.0, verbose=False):
        """Wait until the worker subprocess is responding to requests.

        :param timeout: Give the server this many seconds to start. If the 
          timeout expires before the server has started, 
          kill the server and raise WorkerError.
        :type timeout: float, seconds
        :raises: **WorkerError** if the worker is not ready within the time limit.
        :raises: **WorkerError** if there is no subprocess.
        """

        if not self.process:
            raise WorkerError(None, self.name + " No subprocess")

        start_time = time.time()
        time_delta = 0.5
        status = self.process.poll()
        while status == None:  # status == None => process is running;
            try:
                self.health()
                if verbose:
                    print "server %s is ready." % self.name
                return
            except WorkerError:
                pass

            if time.time() - start_time > timeout:
                self.process.terminate()
                self.process.wait()
                self.process = None
                raise WorkerError(None, self.name + " Taking too long to start.")
            
            time.sleep(time_delta)

            status = self.process.poll()

        errors = None
        if hasattr(self.process, "stderr") and self.process.stderr:
            errors = self.process.stderr.read()
        self.process = None
        raise WorkerError(self.name, errors)

    def stop(self, wait=True):
        """
        Terminate the worker subprocess.
        
        :param wait: If True, wait for the worker to exit.
        :type wait: boolean
        """

        if self.process:
            self.process.terminate()

            if wait:
                self.process.wait()

            self.process = None

    def wait(self):
        """Wait for the worker process to exit."""

        if self.process:
            self.process.wait()
            self.process = None
