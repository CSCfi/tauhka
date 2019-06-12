all:
	python3 setup.py sdist bdist_wheel

install:
	pip3 install --user dist/*.whl

uninstall:
	pip3 uninstall tauhka

check:
	pycodestyle  --show-source --show-pep8 tauhka
