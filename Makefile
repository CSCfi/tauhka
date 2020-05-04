################################################################
# This file is part of Tauhka project.
#
# License: MIT
#
# Author(s):
#     Juhapekka Piiroinen <juhapekka.piiroinen@criticalforce.fi>
#     Juhapekka Piiroinen <juhapekka.piiroinen@csc.fi>
#
# Copyright (c) 2020 Critical Force Oy
# Copyright (c) 2019 CSC - IT Center for Science Ltd.
# All Rights Reserved.
################################################################
SHELL:=/bin/bash
PYTHON_CMD:=source venv/bin/activate && python3

all: venv check
	python3 setup.py sdist bdist_wheel

venv:
	python3 -m venv venv
	source venv/bin/activate && pip3 install -r requirements.txt

install:
	pip3 install --user dist/*.whl

uninstall:
	pip3 uninstall tauhka

check: venv
	-@./venv/bin/pycodestyle --show-source --show-pep8 tauhka
	@cd tests/ui && make check

clean:
	@cd tests/ui && make clean

recheck:
	@cd tests/ui && make recheck

security:
	dependency-check --format JSON --format HTML --scan . --enableExperimental --disableOssIndex --prettyPrint --failOnCVSS 1
	open dependency-check-report.html

dependency-check:
	brew install dependency-check

