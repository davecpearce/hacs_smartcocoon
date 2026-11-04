# Contribution guidelines

Contributing to this project should be as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## Github is used for everything

Github is used to host code, to track issues and feature requests, as well as accept pull requests.

Pull requests are the best way to propose changes to the codebase.

1. Fork the repo and create your branch from `main`.
2. If you've changed something, update the documentation.
3. Make sure your code lints (`make lint`).
4. Test your contribution (`make test`).
5. Issue that pull request!

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](../../issues)

GitHub issues are used to track public bugs.
Report a bug by [opening a new issue](../../issues/new/choose); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People _love_ thorough bug reports. I'm not even kidding.

## Use a Consistent Coding Style

Code is formatted and linted with [ruff](https://docs.astral.sh/ruff/), plus pylint,
mypy and [prettier](https://prettier.io/), all run through
[pre-commit](https://pre-commit.com/). CI runs exactly the same hooks:

```bash
pip install pre-commit
pre-commit install          # run the hooks on every commit
pre-commit run --all-files  # or: make lint
```

## Test your code modification

```bash
make install   # requirements_test.txt + editable install
make test      # pytest with coverage
```

You need Python 3.13.2 or later, or use the VS Code devcontainer, which also runs a
Home Assistant instance with the integration linked in. See
[README_DEVELOPMENT.md](README_DEVELOPMENT.md) for the devcontainer and for the
checks CI runs.

Add tests for what you change. For a bug fix, make sure the new test fails without
the fix.

Changes to how the integration talks to the SmartCocoon cloud usually belong in the
[pysmartcocoon](https://github.com/davecpearce/pysmartcocoon) library, not here.

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
