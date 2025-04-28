
define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z0-9_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

PHONY = build

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean:  ## remove development artifacts and working directory
	@rm -fr dist '~build' .pytest_cache .coverage src/smart_admin.egg-info build latest_logs ~SYNC* junit.xml coverage.xml
	@find . -name __pycache__ -o -name .eggs | xargs rm -rf
	@find . -name "*.py?" -o -name "*.min.min.js" -o -name ".DS_Store" -o -name "*.orig" -o -name "*.min.min.js" -o -name "*.min.min.css" -prune | xargs rm -rf

fullclean:  ## remove all development artifacts including tox
	@rm -rf .tox .cache
	$(MAKE) clean

lint:  ## code lint
	pre-commit run --all-files

i18n:  ## i18n support
	cd src && django-admin makemessages --all --settings=aurora.config.settings -d djangojs --pythonpath=. --ignore=~*
	cd src && django-admin makemessages --all --settings=aurora.config.settings --pythonpath=. --ignore=~*
	cd src && django-admin compilemessages --settings=aurora.config.settings --pythonpath=. --ignore=~*
	git commit -m "Update translations"

create-db:
	dropdb -p 5432 --if-exists aurora
	createdb -p 5432 aurora

reset-db: create-db
	./manage.py migrate

reset-migrations:
	@find src -name 000[1-9]*.py -type f -delete
	./manage.py makemigrations aurora
	./manage.py makemigrations i18n
	./manage.py makemigrations security
	./manage.py makemigrations core
	./manage.py makemigrations registration
	./manage.py makemigrations counters
	./manage.py makemigrations dbtemplates

	$(MAKE) create-db

build:
	rm -f dist/*
	uv build
