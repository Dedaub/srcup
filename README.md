# Watchdog srcup

`srcup` is Dedaub's utility CLI for uploading your project's code into the analysis engine of Watchdog.

## Installation

**NOTE**: While `pipx` is not required, it's highly recommended to use it instead of `pip` to ensure our
CLI tool is run in an isolated/clean environment. 

1. [Optional] [Install pipx](https://pypa.github.io/pipx/). This is **recommended**.
2. Install the CLI tool: `pipx install git+https://github.com/Dedaub/srcup#egg=srcup`
3. Test the installation: `srcup --help`
4. [Optional] Install the CLI completions: `srcup --install-completion`


## Updating

### For pipx installation
```bash
pipx upgrade srcup
```

### For plain pip installation
```bash
pip install --upgrade srcup
```

## Usage

The following steps assumes you've acquired/generated a Watchdog API key. This can be done from your Watchdog
profile page (top right corner of the UI, top right button in the header of that page).

To upload the sources of a project:
1. Go to the project's root directory
2. **Important**: Make sure the project dependencies have already been setup. This is typicially done by running
`npm install`, `yarn install` or similar -- this step can vary from project to project, depending on the package
manager being used.
3. Run `srcup --api-key <api_key> --framework <project_framework>`. (See "Storing the API key" later in this doc, 
which will simplify the command in future runs.) Note that, while the `framework`
parameter is optional, it can help guide the CLI tool. There are cases where multiple build tools/frameworks are
present in a project (e.g., Hardhat for building and Foundry for testing/fuzzing) which can confuse our tool. In
any case, the framework parameter refers to the tool used to **build** the project. If your project only uses one
framework, `srcup` should be able to successfully infer the correct framework.
4. The CLI tool will compile and upload the artifacts to Watchdog. This might take a while. Upon completion, a
Watchdog project URL will be provided.

## A note regarding the layout of the project
Right now, `srcup` assumes that the project to be uploaded has the default file layout of the underlying build system. Until the tool provides the ability to override the default paths,
one might need to momentarily use the default layout of the specified build system for the uploading process to work seamlessly.

### Build-system-specific notes
- The layout of a `hardhat` project should be inferred automatically by the tool. This is done via an invokation to `hardhat`'s console (the default output directory is `artifacts`)
- The output directory of a `foundry` project should be `out` (default directory)
- The output directory of a `truffle` project should be `build/contracts` (default directory)

## Storing the API key

It is possible to store the API key in a file to make future `srcup` invocations simpler. The API key can be stored
in the following places:
- As a standard environment variable in your shell's RC file.
- In `~/.config/dedaub/credentials`

In both cases, the environment variable defintion should be `WD_API_KEY=<api_key>`.
