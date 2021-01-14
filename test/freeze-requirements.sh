#!/bin/sh
rm -rf venv
python3.9 -m venv venv
venv/bin/pip install -e .[dev]
venv/bin/pip uninstall -y pdoc
venv/bin/pip freeze > requirements-dev.txt
