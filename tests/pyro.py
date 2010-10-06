
import os
import sys
import urllib

import Pyro.core

sys.path.insert(0, "..")

import servermgr.pyro
import servermgr.pyro_service


NS_HOST = "localhost"
NS_PORT = 8200
NS_DIR = "/tmp/pyro_test"

TEST_SERVICE = "math_service"

class MathService(Pyro.core.ObjBase):

    def __init__(self):

        Pyro.core.ObjBase.__init__(self)

    def health(self):
        return True

    def add(self, *args):

        val = reduce(lambda x,y: x+y, args, 0)
        return val

def local_add(self, *args):

    val = reduce(lambda x,y: x+y, args, 0)
    return val

def pyro_ns_test():

    m = servermgr.pyro.Manager(NS_HOST, NS_PORT, NS_DIR)
    m.start()
    m.health()
    m.stop()

def pyro_server_test():

    m = servermgr.pyro.Manager(NS_HOST, NS_PORT, NS_DIR)
    m.start()
    m2 = servermgr.pyro_service.Manager(TEST_SERVICE, MathService(), NS_HOST, NS_PORT)
    m2.start()
    client = Pyro.core.getProxyForURI("PYRONAME://%(host)s:%(port)d/%(service)s" \
                                          % dict(host=NS_HOST, port=NS_PORT, service=TEST_SERVICE))
    for i in range(1, 10):
        v = range(i)
        r1 = local_add(*v)
        r2 = client.add(*v)
        print "vector:", v, "sum:", r1, r2
        assert r1 == r2

    m2.stop()
    m.stop()

def main():
    pyro_ns_test()
    pyro_server_test()

if __name__ == "__main__":
    main()

