choco config set --name="'webRequestTimeoutSeconds'" --value="'3600'"
choco config set --name="'commandExecutionTimeoutSeconds'" --value="'14400'"

choco install -y %PYTHON_PACKAGE% --version=%PYTHON_VERSION% --timeout=14400

set PATH=%PYTHON_BIN%;%PYTHON_BIN%\Scripts;%PATH%

pip install virtualenv
python -m virtualenv \venv
set PATH=%VENV_DIR%;%PATH%

where python
python --version
pip install -U pip setuptools
pip install %PYTHON_INSTALL_PKGS%
pip --version
