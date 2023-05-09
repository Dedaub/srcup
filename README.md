# Watchdog srcup

`srcup` is Dedaub's utility CLI for uploading your project's code into the analysis engine of Watchdog.

## Installation

**NOTE**: While `pipx` is not required, it's highly recommended to use it instead of `pip` to ensure our
CLI tool is run in an isolated/clean environment. 

1. [Optional] [Install pipx](https://pypa.github.io/pipx/). This is **recommended**.
2. Install the CLI tool: `pipx install git+https://github.com/Dedaub/srcup#egg=srcup`
3. Test the installation: `srcup --help`
4. [Optional] Install the CLI completions: `srcup --install-completion`

## Usage

The following steps assumes you've acquired/generated a Watchdog API key. This can be done from your Watchdog
profile page.

To upload the sources of a project:
1. Go to the project's root directory
2. **Important**: Make sure the project dependencies have already been setup. This is typicially done by running
`npm install`, `yarn install` or similar -- this step can vary from project to project, depending on the package
manager being used.
3. Run `srcup --api-key <api_key> --framework <project_framework>`. It should be noted that while the framework
parameter is optional, it can help guide the CLI tool. There are cases where multiple build tools/frameworks are
present in a project (e.g. Hardhat for building and Foundry for testing/fuzzing) which can confuse our tool. In
any case, the framework parameter refers to the tool used to **build** the project. If your project only uses one
framework, `srcup` should be able to successfully infer the correct framework.
4. The CLI tool will compile and upload the artifacts to Watchdog. This might take a while. Upon completion, a
Watchdog project URL will be provided.


## Storing the API key

It is possible to store the API key in a file to make future `srcup` invocations simpler. The API key can be stored
in the following places:
- As a standard environment variable in your shell's RC file.
- In `~/.config/dedaub/credentials`

In both cases, the environment variable defintion should be `WD_API_KEY=<api_key>`.
