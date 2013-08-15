all:
	@echo "Specify a target."

docs:
	pdoc --html --html-dir ./doc --overwrite ./pdoc.py

pypi: longdesc.rst
	sudo python2 setup.py register sdist upload

longdesc.rst: pdoc.py pdoc-docstring
	pandoc -f markdown -t rst -o longdesc.rst pdoc-docstring
	rm -f pdoc-docstring

pdoc-docstring: pdoc.py
	./extract-docstring > pdoc-docstring

dev-install: docs longdesc.rst
	[[ -n "$$VIRTUAL_ENV" ]] || exit
	rm -rf ./dist
	python setup.py sdist
	pip install -U dist/*.tar.gz

pep8:
	pep8-python2 pdoc.py pdoc

push:
	git push origin master
	git push github master
