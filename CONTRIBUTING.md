Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit helps,
and credit will always be given.

You can contribute in many ways:

# Types of Contributions

### Report Bugs

Report bugs Under Tab Issues in **_GitHub issues_**.

If you are reporting a bug, please include:

- XmlCli Version: ____
- IFWI/BIOS Label/Version: ____
- Source link of IFWI/BIOS used: ____
- Your operating system name and version: ____
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug corresponding logs and/or screenshots.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

### Write Documentation

XmlCli could always use more documentation, whether as part of the
official XmlCli docs, docstrings in scripts, or even on the web in blog posts,
articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue at **_Github Issues_**.

If you are proposing a feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

# Get Started!


Ready to contribute? Here's how to set up `xmlcli` for local development.

1. Fork this repo on GitHub.

2. Clone your fork locally:

```shell
git clone <url-of-forked-repo>
```

3. Create a branch for local development:

```shell
git checkout -b name-of-your-bugfix-or-feature
```

Now you can make your changes locally.

4. Your changes must follow below guideline before you make pull request:
   - [PEP 8](https://www.python.org/dev/peps/pep-0008/) -- Style Guide for Python Code
   - Unittest if you are integrating new feature
   - [Bandit](https://github.com/PyCQA/bandit) scan with [project configuration](.github/ipas_default.config)

5. Commit your changes and push your branch to GitHub::

```shell
git add .
git commit -m "Your detailed description of your changes."
git push origin name-of-your-bugfix-or-feature
```

6. Submit a pull request through the GitHub website.

7. Merge of the pull request is subject to fulfillment of below cases:
   - Pass static code analysis
     - Checkmarx or Coverity for python files
     - KW or Coverity for C files
   - BDBA scan for 3rd party binaries
   - Snyk scan for 3rd party libraries
   - Bandit guideline scan
   - `Pylint` scan
   - Antivirus and Malware scan

# Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in [README](README.md).
3. The pull request should work for Python 3.6 or above and for PyPy.
