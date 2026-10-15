# up2fireshare

A CLI for uploading game clips to the Fireshare self-hosted gaming media collection system.

This project's code is replicated on [GitWorkshop](https://gitworkshop.dev/npub1pra8zgw2hrckthu0xexs5k7xvz5mt6rsfk09e9egehnj7q8mpp9s8vr6v5/up2fireshare), [GitHub](https://github.com/littlebitstudios/up2fireshare) (GitHub Actions publishes PyPI release), [Tangled](https://tangled.org/littlebitstudios.com/up2fireshare), and [Radicle](https://radicle.network/nodes/rad.littlebitstudios.com/rad:z3t7dKZxEKKAGjbZWEGzEh2Po1DB9).

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
You can also use `-g` to specify a game name (this game must be one you've added already from Fireshare's interface), the name is case-insensitive. You can also use `-f` to specify the folder name within Fireshare to upload to. When a local folder is provided, its name is used for `-f` by default.

If you want to use Fireshare's tags, you can use `-t "tag1, tag2, ..."` to upload with tags.

To upload multiple files at once, add more than one file or provide a folder. By default, only files directly in a folder are uploaded. Use `-r` to include files in all its subfolders; with `-r`, each file is assigned to a Fireshare folder named after its local parent folder. An explicit `-f` overrides these defaults. When the upload contains multiple files, you can't use a title (`-n`); all other options are copied across the files.

The program's full helptext can be seen with `up2fireshare -h`.

## Licensing/Credits

This tool is open-source under the MIT license. See the LICENSE file.

This tool interacts with Fireshare (https://github.com/shaneisrael/fireshare), open-source software under the GPL-3.0 license.