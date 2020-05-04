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
PYTHON_CMD:=source venv/bin/activate && python3
SHELL:=/bin/bash

all: venv

run: venv
	@$(PYTHON_CMD) ./src/server/server.py > /dev/null 2>&1
	@sleep 2

stop:
	-@ps a | grep src/server/server.py | grep -v grep | awk '{ print $$1 }' | xargs -I{} kill {}

venv:
	python3 -m venv venv
	source venv/bin/activate && pip3 install -r requirements.txt

check:
	@cd tests/ui && make check

clean:
	@rm -rf venv
	@cd tests/ui && make clean

recheck:
	@rm -rf venv
	@cd tests/ui && make recheck
