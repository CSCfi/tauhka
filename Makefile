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
	@venv/bin/pycodestyle --show-source --show-pep8 tauhka
	@cd tests/ui && make check

clean:
	@cd tests/ui && make clean

recheck: clean check
