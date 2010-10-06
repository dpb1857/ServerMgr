

import os
import sys
import urllib

sys.path.insert(0, "..")

import servermgr.nginx


TEST_DIR = "/tmp/nginx_test"

def map_directory(url, directory):

    try:
        m = servermgr.nginx.Manager("localhost", 8080, TEST_DIR)
        m.add_filesystem_mapping(url, directory)
        m.start()
    except Exception, ex:
        print >> sys.stderr, "Failed to start nginx."
        raise

    return m


def read_status_test():

    m = servermgr.nginx.Manager("localhost", 8080, TEST_DIR)
    m.start()
    status = urllib.urlopen("http://localhost:8080/nginx_status").read()
    if not status.startswith("Active connections:"):
        raise Exception("unexpected status returned")

def check_map_url_to_filesystem(url_prefix, dirname):
    
    m = map_directory(url_prefix, dirname)
    
    write_data = "This is a test.\n"
    f = file(os.path.join(dirname, "testdata.txt"), "w")
    f.write(write_data)
    f.close()
    read_data = urllib.urlopen("http://localhost:8080/testdata.txt").read()
    assert write_data == read_data
    m.stop()

def map_tests():

    m = check_map_url_to_filesystem("/", TEST_DIR)
    m = check_map_url_to_filesystem("/mapped", TEST_DIR)
    m = check_map_url_to_filesystem("/mapped/", TEST_DIR)
    m = check_map_url_to_filesystem("/", TEST_DIR+'/')
    m = check_map_url_to_filesystem("/mapped", TEST_DIR+'/')
    m = check_map_url_to_filesystem("/mapped/", TEST_DIR+'/')

def main():
    read_status_test()
    map_tests()

if __name__ == "__main__":
    main()
