import os
import subprocess
import sys
from os.path import join as jp, dirname, abspath, normcase as nc, expanduser

SUFFIXES = {"osx": ".sh",
            "linux": ".sh",
            "windows": ".cmd"}

if __name__ == "__main__":
    environ = os.environ
    os_name = environ["TRAVIS_OS_NAME"]

    if os_name == "windows":
        environ["PYTHON_PACKAGE"] = "python%s" % (environ["PYTHON_VERSION"][0])
        environ["PYTHON_BIN"] = abspath("\\Python%s%s" %
                                        (environ["PYTHON_VERSION"][0], environ["PYTHON_VERSION"][2]))
        venv_bin_dir = nc(abspath("\\venv\\Scripts"))
        environ["VENV_DIR"] = venv_bin_dir
    else:
        venv_name = "venv-%s" % environ["PYTHON_VERSION"]
        venv_bin_dir = nc(jp(expanduser("~"), ".pyenv", "versions",
                             venv_name,
                             "bin"))
        environ["PYTHON_VENV_NAME"] = venv_name
        environ["VENV_DIR"] = venv_bin_dir

    script_dir = nc(abspath(dirname(sys.modules["__main__"].__file__)))
    if sys.argv[1] == "install":
        script = nc(jp(script_dir, "travis_%s%s" % (sys.argv[1], SUFFIXES[os_name])))
        print("Executing script %r" % script)
        subprocess.check_call([script], env=environ)
