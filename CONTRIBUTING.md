# Contributing

As an open source project, pdoc welcomes contributions of all forms. If you would like to bring the project forward,
please consider contributing in the following areas:

- **Maintenance:** We are *incredibly* thankful for individuals who are stepping up and helping with maintenance. This
  includes (but is not limited to) helping out other users, creating minimal examples for existing bug reports, updating
  documentation, fixing minor bugs that have recently been reported, reviewing pull requests, or picking up stale ones.
- **Code Contributions:** We actively mark issues that we consider are
  [good first contributions](https://github.com/mitmproxy/pdoc/labels/help-wanted). If you intend to work on a larger
  contribution to the project, please come talk to us first. We are very careful not to introduce any feature creep.

## Development Setup

To get started hacking on pdoc, please install a recent version of Python (we recommend at least Python 3.9). Then, do
the following:

```shell
git clone https://github.com/mitmproxy/pdoc.git
cd pdoc
pip3 install -e .[dev]
```

## Testing

If you've followed the procedure above, you already have all the development requirements installed, and you can run the
basic test suite with [tox](https://tox.readthedocs.io/):

```shell
tox
```

Please ensure that all patches are accompanied by matching changes in the test suite. The project strictly maintains
100% test coverage.

### Fixing Snapshot Tests

pdoc makes heavy use of snapshot tests, which compare the rendered output with a stored copy in the [test/testdata](test/testdata) directory.
These tests are very useful to catch regressions, but also have a tendency to break quickly. If you encounter failing snapshot tests, run

```shell
python3 ./test/test_snapshot.py
```
to overwrite the stored snapshots with the new rendered output. This will fix the tests.

## Documentation

Please check [docs/README.md](./docs/README.md) for instructions.


## Release Process

If you are the current maintainer of pdoc,
you can perform the following steps to ship a release:

1. Make sure that...
   - you are on the `main` branch with a clean working tree.
   - `tox` is passing without errors.
2. Bump the version in [`pdoc/__init__.py`](pdoc/__init__.py).
3. Update [`CHANGELOG.md`](./CHANGELOG.md).
4. Re-render the website: `docs/make.py`
5. Commit the changes and tag them.
   - Convention: Tag name is `v` + version number, e.g. `v1.0.1`.
6. Manually confirm the CI deploy step on GitHub.
