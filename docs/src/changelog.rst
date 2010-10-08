
ChangeLog
=========

v0.2.2 10/8/2010
----------------

Fixed bad MANIFEST file that caused pyro files to be left out.

v0.2.1 10/6/2010
----------------

Use muliprocessing module when launching python in its own process.
    
* Use multiprocessing to launch Django_app and Pyro_service.
* Wrap the subprocess.Popen and multiprocessing.Subprocess objects in another class to provide a common API.
* Renamed base.ManagerBase -> base.Manager.
* Add tests for nginx and pyro.
* Update docs.

v0.2.0 9/28/2010
----------------

initial public release
