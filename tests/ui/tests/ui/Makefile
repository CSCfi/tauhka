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
UNAME_S := $(shell uname -s)

ifneq (,$(wildcard /opt/google/chrome/chrome))
CHROME_VERSION:=$(shell /opt/google/chrome/chrome --version|grep -o "[0-9\.]\+"|head -1|tr '.' '\n'|head -1)
else
ifeq ($(UNAME_S),Darwin)
CHROME_VERSION:=$(shell /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --version|grep -o "[0-9\.]\+"|head -1|tr '.' '\n'|head -1)
else
CHROME_VERSION:=$(shell chromium --version|grep -o "[0-9\.]\+"|head -1|tr '.' '\n'|head -1)
endif
endif

ifeq ($(UNAME_S),Linux)
CHROME_DRIVER:=chromedriver_linux64.zip
endif
ifeq ($(UNAME_S),Darwin)
CHROME_DRIVER:=chromedriver_mac64.zip
endif

all: $(CHROME_DRIVER)

venv:
	@python3 -m venv venv
	@#source venv/bin/activate && pip3 install https://github.com/Tauhka/tauhka/archive/master.zip
	@source venv/bin/activate && pip3 install ../../../..
	@source venv/bin/activate && pip3 install -r requirements.txt

LATEST_RELEASE_$(CHROME_VERSION):
	@curl -O https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$(CHROME_VERSION)

$(CHROME_DRIVER): LATEST_RELEASE_$(CHROME_VERSION)
	@curl -O https://chromedriver.storage.googleapis.com/$(shell cat LATEST_RELEASE_$(CHROME_VERSION))/$(CHROME_DRIVER)
	@unzip $(CHROME_DRIVER)

clean:
	@rm -f chromedriver
	@rm -f chromedriver_*.zip
	@rm -rf venv
	@rm -rf __pycache__
	@rm -rf views/__pycache__
	@rm -f LATEST_RELEASE*

check: venv $(CHROME_DRIVER)
	-@venv/bin/pycodestyle --show-source --show-pep8 .
	@cd ../.. && make run &
	@$(PYTHON_CMD) -m unittest discover

recheck:
	@rm -rf venv
	@rm -rf __pycache__
	@rm -rf views/__pycache__
	@make check
