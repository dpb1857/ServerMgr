# -*- mode: python; tab-width:8; py-indent-offset:4; indent-tabs-mode:nil -*-
#pylint: disable=C0301
#line length;

"""
Nginx process management.

Use this module to configure and manage a dedicated nginx server.
"""

import os
import subprocess
import urllib

import base

class _ConfigBuilder(object):
    """
    Nginx configuration file builder.

    This mixin class provides the methods that can be used to add various types of URL 
    mappings to an Nginx config file.
    """

    CONFIG_TEMPLATE = """

    daemon off;
    error_log  %(logdir)s/error.log;
    pid	   %(rundir)s/nginx.pid;

    events {
      worker_connections 1024;
      use epoll;
    }

    http {
      access_log %(logdir)s/access.log;
      client_body_temp_path %(tmpdir)s 1 2;
      fastcgi_temp_path %(tmpdir)s/fastcgi;
      proxy_temp_path %(tmpdir)s/proxy;
      root %(root)s;
      server_name_in_redirect off;

      server {
        listen %(port)s;

        location /nginx_status {
          stub_status on;
          access_log off;
          allow 127.0.0.1;
          deny all;
        }

    %(config_blocks)s

      }
    }
    """

    FILESYSTEM_BLOCK = """
        location %(url_prefix)s {
          alias %(directory)s;
          autoindex on;
        }
    """

    REDIRECT_BLOCK = """
        location %(url_prefix)s {
          rewrite %(pattern)s %(rewrite)s permanent;
        }
    """

    FCGI_BLOCK = """
        location %(url_prefix)s {
          fastcgi_buffers 256 8k;
          fastcgi_max_temp_file_size 0;
          fastcgi_pass %(destination)s;
          fastcgi_param PATH_INFO $fastcgi_script_name;
          fastcgi_param REQUEST_METHOD $request_method;
          fastcgi_param QUERY_STRING $query_string;
          fastcgi_param CONTENT_TYPE $content_type;
          fastcgi_param CONTENT_LENGTH $content_length;
          fastcgi_param SERVER_NAME $server_name;
          fastcgi_param SERVER_PORT $server_port;
          fastcgi_param SERVER_PROTOCOL $server_protocol;
          fastcgi_pass_header Authorization;
          fastcgi_intercept_errors off;
        }
    """

    HTTP_PROXY_BLOCK = """
        location %(url_prefix)s {
          proxy_set_header X-Forwarded-Host $host;
          proxy_set_header X-Forwarded-Server $host;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_pass %(destination)s;
        }
    """

    @staticmethod
    def _generate_mapping(map_info):
        """Format the configuration section for a particular type of url mapping."""

        block, info_dict = map_info
        config_data = block % info_dict

        return config_data

    def __init__(self, host, port, base_dir, http_root):
        
        self.host = host
        self.port = port
        self.base_dir = base_dir
        self.http_root = http_root
        self.mappings = []

    def _write_config(self, file_handle):
        """Write the nginx configuration file."""

        tmpl_vars = { "etc"    : os.path.join(self.base_dir, "etc", "nginx"),
                      "logdir" : os.path.join(self.base_dir, "logs", "nginx"),
                      "rundir" : os.path.join(self.base_dir, "run"),
                      "tmpdir" : os.path.join(self.base_dir, "tmp", "nginx"),
                      "root"   : self.http_root,
                      "port"   : self.port
                      }

        for key in "etc", "logdir", "rundir", "tmpdir":
            dirname = tmpl_vars[key]
            if not os.path.exists(dirname):
                os.makedirs(dirname)

        config_blocks = []
        for mapping in self.mappings:
            config_blocks.append(_ConfigBuilder._generate_mapping(mapping))

        tmpl_vars["config_blocks"] = ''.join(config_blocks)
        config_data = [_ConfigBuilder.CONFIG_TEMPLATE % tmpl_vars]
        file_handle.write('\n'.join(config_data))

    def add_filesystem_mapping(self, url_prefix, directory):
        """
        Add a mapping from a URL prefix to a filesystem location.

        :param url_prefix: url prefix.
        :type url_prefix: string
        :param directory: directory name
        :type destination: string
        """

        if not directory.endswith("/"):
            directory += "/"

        d__ = dict(url_prefix=url_prefix, directory=directory)
        self.mappings.append((_ConfigBuilder.FILESYSTEM_BLOCK, d__))

    def add_redirect_mapping(self, url_prefix, pattern, rewrite):
        """
        URLs that have the prefix *prefix* are then matched against the regular expression *pattern* and 
        rewritten using *destination*, which may use matched subexpressions from *pattern*.
        See `Nginx Rewrite Module <http://wiki.nginx.org/NginxHttpRewriteModule#Directives>`_ for details.

        :param url_prefix: url prefix.
        :type url_prefix: string
        :param pattern: the re pattern to match against
        :type pattern: string, regular expression
        :param rewrite: the rewrite pattern, which may include matched patterns from *pattern*.
        :type rewrite: string 
        """
        d__ = dict(url_prefix=url_prefix, pattern=pattern, rewrite=rewrite)
        self.mappings.append((_ConfigBuilder.REDIRECT_BLOCK, d__))

    def add_fastcgi_mapping(self, url_prefix, destination):
        """
        Forward requests matching *url_prefix* to the fastcgi server at *destination*.
        
        :param url_prefix: url prefix.
        :type url_prefix: string
        :param destination: destination
        :type destination: string
        """
        d__ = dict(url_prefix=url_prefix, destination=destination)
        self.mappings.append((_ConfigBuilder.FCGI_BLOCK, d__))

    def add_http_mapping(self, url_prefix, destination):
        """
        Act as a reverse proxy, sending URLs matching *url_prefix* to *destination*.
        
        :param url_prefix: url prefix.
        :type url_prefix: string
        :param destination: destination http server
        :type destination: string
        """
        d__ = dict(url_prefix=url_prefix, destination=destination)
        self.mappings.append((_ConfigBuilder.HTTP_PROXY_BLOCK, d__))


class Manager(base.Manager, _ConfigBuilder):
    """
    Nginx manager object.

    :param host: the interface to listen on.
    :type host: string
    :param port: the post to listen on.
    :type port: int
    :param base_dir: the base directory for logs and configuration files.
    :type base_dir: string
    """

    __implements__ = base.ManagerInterface

    def __init__(self, host, port, base_dir, http_root="", *args, **kwargs):

        if not http_root:
            http_root = base_dir

        # super(Manager, self).__init__("Nginx", *args, **kwargs)
        base.Manager.__init__(self, "Nginx", *args, **kwargs)
        _ConfigBuilder.__init__(self, host, port, base_dir, http_root)

        self.process = None

    def health(self):
        """
        Check on the health of the Solr server.
        
        :raises: **base.WorkerError** if the server is not responding.
        """

        try: 
            urllib.urlopen("http://%s:%d/nginx_status" % (self.host, self.port))
        except IOError, ex:
            raise base.WorkerError(ex)

    def start(self, wait=True, timeout=10.0):
        """
        Start the http server.

        :param wait: If true, call self.ready_wait() after starting the subprocess.
        :param timeout: When calling ready_wait(), use this timeout value.
        :type timeout: float, number of seconds
        :raises: **base.WorkerError** if the worker hasn't started before timeout elapses.

        """

        config_file = os.path.join(self.base_dir, "etc", "nginx", "nginx.conf")
        if not os.path.exists(os.path.dirname(config_file)):
            os.makedirs(os.path.dirname(config_file))

        file_handle = file(config_file, "w+")
        self._write_config(file_handle)
        file_handle.close()
        self.process = subprocess.Popen(["nginx",
                                         "-c", config_file],
                                        stdout=file("/dev/null"), 
                                        stderr=subprocess.PIPE,
                                        close_fds=True)
        if wait:
            self.ready_wait(timeout=timeout)

def main():
    """
    You can use this script to start a copy of Nginx.

    Usage: nginx.py [--help] [-h HOST] [-p PORT] [-d DATADIR] [-f FSMAP] [-r REDIRECT] [-c FCGI] [-t HTTP]

    optional arguments:
      --help                show this help message and exit
      -h HOST, --host=HOST  listener hostname
      -p PORT, --port=PORT  listener port
      -d DATADIR, --datadir=DATADIR
                            data directory
      --fsmap FSMAP         add a filesystem mapping
      --redirect REDIRECT   add a redirect
      --fcgi FCGI           add a fastcgi mapping
      --http HTTP           add a http mapping
      --config              print the generated config file and exit

    To specify a filesystem mapping, use the option:
        --fsmap=/some_url_prefix,/somedirectory

    To map a url prefix to a webapp using fcgi, use:
        --fcgi=/some_url_prefix,host:port

    To make a url prefix a reverse proxy for another http server, use:
        --http=/url_prefix,some_other_url

    To make a url redirect elsewhere:
        --redirect=/url_prefix,pattern,rewrite
    """

    import argparse
    import signal
    import sys

    def interrupt(_unused_signum, _unused_frame):
        """Handle user stopping with control-C."""
        print >> sys.stderr, "Keyboard interrupt, exiting."
        sys.exit()

    signal.signal(signal.SIGINT, interrupt)

    help_parser = argparse.ArgumentParser(add_help=False)
    help_parser.add_argument("--help", action='store_true')

    epilog = """
    To specify a filesystem mapping, use the option:
        --fsmap=/some_url_prefix,/somedirectory

    To map a url prefix to a webapp using fcgi, use:
        --fcgi=/some_url_prefix,host:port

    To make a url prefix a reverse proxy for another http server, use:
        --http=/url_prefix,some_other_url

    To make a url redirect elsewhere:
        --redirect=/url_prefix,pattern,rewrite
    """
    parser = argparse.ArgumentParser(parents=[help_parser], add_help=False)
    parser.add_argument("-h", "--host", action="store", help="listener hostname")
    parser.add_argument("-p", "--port", action="store", help="listener port")
    parser.add_argument("-d", "--datadir", action="store", help="directory for config file, log files")
    parser.add_argument("--fsmap", action="append", help="add a filesystem mapping")
    parser.add_argument("--redirect", action="append", help="add a redirect")
    parser.add_argument("--fcgi", action="append", help="add a fastcgi mapping")
    parser.add_argument("--http", action="append", help="add a http mapping")
    parser.add_argument("--config", action="store_true", help="print the generated config file and exit")

    options = parser.parse_args()
    if options.help:
        parser.print_help()
        print epilog
        return
        
    default_host = "localhost"
    default_port = 8080
    default_datadir = "/var/tmp/nginx"

    host = options.host if options.host else default_host
    port = int(options.port) if options.port else default_port
    datadir = options.datadir if options.datadir else default_datadir

    webserver_mgr = Manager(host, port, datadir)

    if options.fsmap:
        for mapping in options.fsmap:
            try:
                url, filesystem = mapping.split(',')
                webserver_mgr.add_filesystem_mapping(url, filesystem)
                print >> sys.stderr, "mapping url prefix '%s' to directory '%s'" % (url, filesystem)
            except ValueError:
                print >> sys.stderr, "cannot process parameter '%s', skipping..." % mapping

    if options.redirect:
        for mapping in options.redirect:
            try:
                prefix, pattern, target = mapping.split(',')
                webserver_mgr.add_redirect_mapping(prefix, pattern, target)
                print >> sys.stderr, "with url prefix '%s', mapping pattern '%s' to target '%s'." % (prefix, pattern, target)
            except ValueError:
                print >> sys.stderr, "cannot process parameter '%s', skipping..." % mapping

    if options.http:
        for mapping in options.http:
            try:
                prefix, destination = mapping.split(',')
                if prefix[-1] != '/':
                    prefix += "/"
                if destination[-1] != '/':
                    destination += "/"
                webserver_mgr.add_http_mapping(prefix, destination)
                print >> sys.stderr, "reverse proxy url prefix '%s' to '%s'." % (prefix, destination)
            except ValueError:
                print >> sys.stderr, "cannot process parameter '%s', skipping..." % mapping

    if options.fcgi:
        for mapping in options.fcgi:
            try:
                prefix, destination = mapping.split(',')
                webserver_mgr.add_fastcgi_mapping(prefix, destination)
                print >> sys.stderr, "FCGI reverse proxy url prefix '%s' to '%s'." % (prefix, destination)
            except ValueError:
                print >> sys.stderr, "cannot process parameter '%s', skipping..." % mapping

    if options.config:
        print "Generated config file:"
        webserver_mgr._write_config(sys.stdout)  #pylint: disable=W0212
        return

    print >> sys.stderr, "starting nginx..."
    webserver_mgr.start()
    print >> sys.stderr, "nginx ready on %s:%d, data_dir is %s." % (host, port, datadir)
    webserver_mgr.wait()

if __name__ == "__main__":
    main()
