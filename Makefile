all:
	@echo "Specify a target."

docs:
	pdoc --html --html-dir ./doc --overwrite ./pdoc.py

pypi:
	sudo python2 setup.py register sdist upload

dev-install: docs
	[[ -n "$$VIRTUAL_ENV" ]] || exit
	rm -rf ./dist
	python2 setup.py sdist
	pip install -U dist/*.tar.gz

pep8:
	pep8-python2 pdoc.py pdoc

push:
	git push origin master
	git push github master
