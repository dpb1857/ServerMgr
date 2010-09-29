# -*- Makefile -*-

PATH := $(shell pwd)/python/bin:$(PATH)

default: help

# Build python virtual environment
#
# Rules to build a python virtual environment that contains the modules
# needed to build the documentation and run the examples.

python/bin/python:
	virtualenv python
	rm -f distribute-*.tar.gz

packages:
	pip install --requirement=requirements.txt --download-cache=download

python: python/bin/python packages

.PHONY: python

#
# Run pylint on the module;
#

pylint:
	(cd servermgr && pylint --disable=I0011,C0301 --include-ids=y *.py 2>&1) | tee pylint.log

#
# Build the documentation
#

docs:
	cd docs/src && make html

.PHONY: docs

#
# Build the distribution;
#

dist: docs
	python setup.py sdist

#
# Install the module;
#

install:
	python setup.py install sdist

#
# All targets
#

all: python docs install dist

help:
	@echo 
	@echo "Type 'make python' to build a local virtualenv python."
	@echo "Type 'make pylint' to run pylint on the module."
	@echo "Type 'make docs' to build the documentation."
	@echo "Type 'make dist' to build the distribution."
	@echo "Type 'make install' to install the servermgr module."
	@echo 


clean:
	cd docs/src && make clean
	find . -name \*~ -print|xargs rm -f
	find . -name \*.pyc -print|xargs rm -f
	find . -name \#*\# -print|xargs rm -f
	rm -rf build
	rm -f pip-log.txt
	rm -f pylint.log

check:

distclean: clean
	rm -rf python
	rm -rf dist
