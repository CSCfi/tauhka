PYTHON_CMD:=source venv/bin/activate && python3

all: venv check

venv:
	python3 -m venv venv
	#source venv/bin/activate && pip3 install https://github.com/CSCfi/tauhka/archive/master.zip
	source venv/bin/activate && pip3 install ../../../..
	source venv/bin/activate && pip3 install -r requirements.txt

chromedriver:
	curl -O https://chromedriver.storage.googleapis.com/74.0.3729.6/chromedriver_mac64.zip
	unzip chromedriver_mac64.zip

clean:
	@rm -f chromedriver
	@rm -f chromedriver_*.zip
	@rm -rf venv
	@rm -rf __pycache__
	@rm -rf views/__pycache__

check: venv chromedriver
	@venv/bin/pycodestyle --show-source --show-pep8 .
	$(PYTHON_CMD) -m unittest discover
