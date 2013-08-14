all:
	@echo "Specify a target."

docs:
	pdoc --html --html-dir ./doc --overwrite ./pdoc.py

pypi: README.rst
	sudo python2 setup.py register sdist upload

README.rst: pdoc.py pdoc-docstring
	pandoc -f markdown -t rst -o README.rst pdoc-docstring
	rm -f pdoc-docstring

pdoc-docstring: pdoc.py
	./extract-docstring > pdoc-docstring

dev-install: docs README.rst
	[[ -n "$$VIRTUAL_ENV" ]] || exit
	rm -rf ./dist
	python2 setup.py sdist
	pip install -U dist/*.tar.gz

pep8:
	pep8-python2 pdoc.py pdoc

push:
	git push origin master
	git push github master
