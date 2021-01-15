#!/usr/bin/env sh
set -ex
cd -- "$(dirname -- "$0")"

rm -rf freeze-venv
python3.9 -m venv freeze-venv
freeze-venv/bin/python -m pip install -U pip
freeze-venv/bin/pip install -e ..[dev]
freeze-venv/bin/pip uninstall -y pdoc
freeze-venv/bin/pip freeze > ../requirements-dev.txt
rm -rf freeze-venv
