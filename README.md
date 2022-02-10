<p align="center">
<a href="https://pdoc.dev/"><img alt="pdoc" src="https://pdoc.dev/logo.svg" width="200" height="100" /></a>
<br><br>
<a href="https://pdoc.dev/docs/pdoc.html"><img height="20" alt="pdoc documentation" src="https://shields.mitmproxy.org/badge/docs-pdoc.dev-brightgreen.svg"></a>
<a href="https://github.com/mitmproxy/pdoc/actions?query=branch%3Amain"><img height="20" alt="CI Status" src="https://shields.mitmproxy.org/github/workflow/status/mitmproxy/pdoc/CI?label=CI&logo=github"></a>
<a href="https://codecov.io/gh/mitmproxy/pdoc"><img height="20" alt="Code Coverage" src="https://shields.mitmproxy.org/codecov/c/github/mitmproxy/pdoc/main.svg?label=codecov&logo=codecov&logoColor=white"></a>
<a href="https://pypi.python.org/pypi/pdoc"><img height="20" alt="PyPI Version" src="https://shields.mitmproxy.org/pypi/v/pdoc.svg"></a>
<a href="https://pypi.python.org/pypi/pdoc"><img height="20" alt="Supported Python Versions" src="https://shields.mitmproxy.org/pypi/pyversions/pdoc.svg"></a>
</p>

API Documentation for Python Projects.


# Example

`pdoc -o ./html pdoc` generates this website: [pdoc.dev/docs](https://pdoc.dev/docs/pdoc.html).

# Installation
```shell
pip install pdoc
```

pdoc is compatible with Python 3.7 and newer.


# Usage

```shell
pdoc your_python_module
# or
pdoc ./my_project.py
```

Run `pdoc pdoc` to see pdoc's own documentation, 
run `pdoc --help` to view the command line flags, 
or check our [hosted copy of the documentation](https://pdoc.dev/docs/pdoc.html).


# Features

pdoc's main feature is a focus on simplicity: pdoc aims to do one thing and do it well.  


* Documentation is plain Markdown. There are no added special syntax rules.
* First-class support for type annotations and all other modern Python 3 features.
* Builtin web server with live reloading.
* Customizable HTML templates.
* Understands numpydoc and Google-style docstrings.
* Standalone HTML output without additional dependencies.
  
Under the hood...

* `pdoc` will automatically link identifiers in your docstrings to their corresponding documentation.
* `pdoc` respects your `__all__` variable when present.
* `pdoc` will traverse the abstract syntax tree to extract type annotations and docstrings from constructors as well.
* `pdoc` will automatically try to resolve type annotation string literals as forward references.
* `pdoc` will use inheritance to resolve type annotations and docstrings for class members. 
  
If you have substantially more complex documentation needs, we recommend using [Sphinx](https://www.sphinx-doc.org/)!


## Contributing

As an open source project, pdoc welcomes contributions of all forms.

[![Dev Guide](https://shields.mitmproxy.org/badge/dev_docs-CONTRIBUTING.md-blue)](https://github.com/mitmproxy/pdoc/blob/main/CONTRIBUTING.md)

Also, please feel free to join our developer Slack!

[![Slack Developer Chat](https://shields.mitmproxy.org/badge/slack-mitmproxy-E01563.svg)](http://slack.mitmproxy.org/)


## pdoc vs. pdoc3

**This project is not associated with "pdoc3", which has not only falsely assumed our name, but previously engaged in conduct aimed at misleading users - including making erroneous entries on the official Python Wiki and relicensing the codebase despite the protestations of the original team. It's with some regret that the maintainer of pdoc3 has been uncooperative when seeking a solution to these issues. For further details see [issue 64 on pdoc3/pdoc](https://github.com/pdoc3/pdoc/issues/64).**

In contrast the `pdoc` project strives to uphold a healthy community where everyone is treated with respect, and contributions are welcome from all - as long as they adhere to basic civility. We expressly distance ourselves from the actions of the "pydoc3" project and it's maintainer.

----

The pdoc project was originally created by [Andrew Gallant](https://github.com/BurntSushi) 
and is currently maintained by [Maximilian Hils](https://github.com/mhils).
