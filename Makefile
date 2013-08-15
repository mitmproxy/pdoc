all:
	@echo "Specify a target."

docs:
	pdoc --html --html-dir ./doc --overwrite ./pdoc.py

pypi: longdesc.rst
	sudo python2 setup.py register sdist upload

longdesc.rst: pdoc.py docstring
	pandoc -f markdown -t rst -o longdesc.rst docstring
	rm -f docstring

docstring: pdoc.py
	./extract-docstring > docstring

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
