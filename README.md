ghbin
=====

A tool for installing applications distributed as binary releases on GitHub.

Python Dependencies: requests, python-magic

Inspired by [ginstall.sh](https://github.com/whalehub/ginstall.sh)

### Disclaimer

I've tested this successfully with several different GitHub repositories that provide various binaries both as direct downloads like AppImages and in compressed tar/gz/zip files, but I can't guarantee it will work with all repositories and file formats. Issues and/or Pull Requests to resolve incompatibilities are welcome though.


### Features

* Works with most GitHub repositories (such as [owenthereal/ccat](https://github.com/owenthereal/ccat)) that have a Releases section with binaries (even if they're in a compressed tar/gz/zip file) available for download.

* Can list details of all configured repositories and the latest release version available.

* Moves downloaded binaries to the configured folder path (which you could add to your $PATH environment variable for convenience) and makes them executable.

### Usage

If no configuration file is found, a "first-run wizard" will guide you through the setup. You'll need a [GitHub Personal Access Token](https://github.com/settings/tokens) so the tool can use the GitHub API with higher rate limits.

    Usage: python ghbin.py [command] <app/repo>
    Config File: /home/daniel/.ghbin.json

    A tool for installing applications distributed as binary releases on GitHub.

    Run without parameters for a summary of all configured repositories.

    Commands:
        add <repo path> - Add a GitHub repository to track with the format: user/reponame
        install <app name> - Install an application from the configured repositories

    Examples:
        python ghbin.py add owenthereal/ccat
        python ghbin.py install ccat

### Future Improvements

* Support for script files (*.py, *.sh, etc) that are distributed in the same way through GitHub Releases.

* In cases where there are multiple compatible Release items for download, the user currently selects which one to use each time. Ideally, this selection would be stored and correctly determined the next time even if the version number on the Release item has changed.

* Versioning / update-detection capability like a "real" package manager. The ability to track/determine the current version of an installed application and check if an update is available.

* The ability to setup overrides or specific install "instructions" for applications that include multiple binaries or supporting files.

* Better error detection/handling when something doesn't correctly download/extract/install correctly.