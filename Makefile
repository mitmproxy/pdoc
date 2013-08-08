pypi:
	sudo python2 setup.py register sdist upload

tags:
	ctags -R

pypi-meta:
	python2 setup.py register

pep8:
	pep8-python2 pdoc.py pdoc

push:
	git push origin master
	git push github master
