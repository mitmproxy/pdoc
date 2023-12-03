#!/usr/bin/env sh
set -ex
cd -- "$(dirname -- "$0")/.."

pip-compile --all-extras --allow-unsafe --output-file=requirements-dev.txt pyproject.toml
