PYTHON := python3
PROJECT := androidDeviceManagementServer
BASE_DIR := .
VIRTUAL_ENV := $(BASE_DIR)/venv
SYSTEMD_CLIENT_DIR := $(BASE_DIR)/../androiddeviceclientsystemd
ifeq ($(OS),Windows_NT)
	PYTHON_BIN := $(VIRTUAL_ENV)/Scripts
endif
ifeq ($(shell uname -s),Linux)
	PYTHON_BIN := $(VIRTUAL_ENV)/bin
endif

.PHONY: install bootstrap test coverage build snapshot release patch-release minor-release major-release
.DEFAULT_GOAL := bootstrap

$(BASE_DIR):
	test -d $(BASE_DIR)

 $(SYSTEMD_CLIENT_DIR):
	test -d $(SYSTEMD_CLIENT_DIR)

runserver: $(BASE_DIR)
	env DEBUG=1 $(PYTHON_BIN)/python $(BASE_DIR)/run_server.py

migrate: $(BASE_DIR)
	$(PYTHON_BIN)/python manage.py migrate

createsuperuser: $(BASE_DIR)
	env DEBUG=1 $(PYTHON_BIN)/python manage.py createsuperuser

clean.build: $(BASE_DIR)
	-rm -rf ./build
	-rm -rf ./dist
	-rm -rf ./*.egg-info

clean.coverage: $(BASE_DIR)
	-rm -rf .coverage
	-rm -rf .coverage.ltp.*
	-rm -rf coverage.xml
	-rm -rf htmlcov

clean.db: $(BASE_DIR)
	-rm -f db.sqlite3

clean.virtualenv: $(BASE_DIR)
	-rm -rf $(VIRTUAL_ENV)

clean.client: $(BASE_DIR)
	-rm -rf $(SYSTEMD_CLIENT_DIR)
	-rm -rf systemd_client

clean: clean.build clean.coverage clean.virtualenv clean.db clean.client
	find . -name \*.pyc -o -name \*.pyo -o -name __pycache__ | xargs rm -rf

virtualenv_pip: $(BASE_DIR)
	$(PYTHON) $(BASE_DIR)/setup_server.py

pep8: $(BASE_DIR)
	$(PYTHON_BIN)/pycodestyle --config=./pycodestyle.conf --first --exclude=migrations,systemd_client,venv ./

test: $(BASE_DIR) pep8
	$(PYTHON_BIN)/coverage run -p --omit='*asgi.py,*migrations*,*wsgi.py' --rcfile='.coveragerc' run_tests_all.py

coverage: $(BASE_DIR)
	$(PYTHON_BIN)/coverage combine -a
	$(PYTHON_BIN)/coverage html
	$(PYTHON_BIN)/coverage xml
	$(PYTHON_BIN)/coverage report --skip-covered
	$(PYTHON_BIN)/coverage-badge > ./htmlcov/coverage.svg

build: clean.build
	$(eval export BUILD_VERSION=$(BUILD_VERSION))
	$(PYTHON_BIN)/python setup.py sdist
	@echo INFO: build created

getclient: $(BASE_DIR)/../
	cd ..; git clone git@gitlab.kobil.com:colin.mcmicken/androiddeviceclientsystemd.git

updateclient: $(SYSTEMD_CLIENT_DIR)
	cd $(SYSTEMD_CLIENT_DIR); git pull
	-rm -rf $(SYSTEMD_CLIENT_DIR)/client/cyg_script.bat
	cd $(SYSTEMD_CLIENT_DIR); git checkout client/cyg_script.bat

ifeq ($(OS),Windows_NT)
linkclient: $(BASE_DIR) $(SYSTEMD_CLIENT_DIR)
	cmd /c mklink /D systemd_client ..\androiddeviceclientsystemd\client
endif

ifeq ($(shell uname -s),Linux)
linkclient: $(BASE_DIR) $(SYSTEMD_CLIENT_DIR)
	ln -s $(SYSTEMD_CLIENT_DIR)/client/ systemd_client
endif

all: clean getclient linkclient update retest user

auto: clean getclient linkclient update retest

retest: test coverage

update: virtualenv_pip migrate updateclient

user: createsuperuser

fresh: clean getclient linkclient update

snapshot: build
	@echo INFO: snapshot created
