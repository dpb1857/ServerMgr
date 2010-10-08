# -*- Makefile -*-

PATH := $(shell pwd)/python/bin:$(PATH)

default: help

# Build python virtual environment
#
# Rules to build a python virtual environment that contains the modules
# needed to build the documentation and run the examples.

download:
	mkdir download

python/bin/python: download
	virtualenv python
	mv distribute-*.tar.gz download

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
	rm -f MANIFEST && echo "Rebuilding MANIFEST file..."
	python setup.py sdist
	cd docs/_build/html && zip -r $(shell pwd)/dist/docs.zip .

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
	@echo "Type 'make install' to install the servermgr module."
	@echo "Type 'make check' to run some pre-distribution checks."
	@echo "Type 'make dist' to build the distribution."
	@echo 


clean:
	cd docs/src && make clean
	find . -name \*~ -print|xargs rm -f
	find . -name \*.pyc -print|xargs rm -f
	find . -name \#*\# -print|xargs rm -f
	rm -rf build
	rm -f pip-log.txt
	rm -f pylint.log
	rm -f MANIFEST

check:
	-grep -n pdb servermgr/*.py
	-find docs/src examples servermgr tests -type f -print |xargs grep -n XXX

distclean: clean
	rm -rf python
	rm -rf dist
