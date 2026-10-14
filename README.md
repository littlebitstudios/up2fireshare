# up2fireshare

A CLI for uploading game clips to the Fireshare self-hosted gaming media collection system.

## Installation

up2fireshare is a Python package uploaded to PyPI so it can be installed with pip or pipx (preferably pipx).

```sh
pipx install up2fireshare
```

Most Linux distros provide pipx for running Python-based CLI tools, it can also be installed as `pip install pipx` on Windows or in cases where there is no distro package for pipx (for MacOS with `brew` (https://brew.sh), install with `brew install pipx`).

## Usage

On first use you'll need to copy the `example-config.yaml` file to your PC as `[HOME FOLDER]/.littlebitstudios/up2fireshare/config.yaml`.

Your home folder should be `/home/username` on Linux, `/Users/username` on MacOS, or `C:/Users/Your Name` on Windows. If Windows was set up with a Microsoft Account, the home folder will be `C:/Users/[first 5 letters of email]`.

The most basic way to run the program is
```sh
up2fireshare /path/to/media/file
```
You can also use `-g` to specify a game name (this game must be one you've added already from Fireshare's interface), the name is case-insensitive. You can also use `-f` to specify the folder name within Fireshare to upload to.

If you want to use Fireshare's tags, you can use `-t "tag1, tag2, ..."` to upload with tags.

To upload multiple files at once, just add more than one file. For an entire folder, use `/path/to/media/folder/*`. Do note that when uploading multiple files, you can't use a title (`-n`) and all other options are copied across the files. Useful if you're uploading an entire folder that's categorized by game.

The program's full helptext can be seen with `up2fireshare -h`.

## Licensing/Credits

This tool is open-source under the MIT license. See the LICENSE file.

This tool interacts with Fireshare (https://github.com/shaneisrael/fireshare), open-source software under the GPL-3.0 license.