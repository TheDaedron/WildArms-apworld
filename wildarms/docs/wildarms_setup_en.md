# Wild Arms Setup Guide

## Required Software

-  [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) or [MultiworldGG](https://github.com/MultiworldGG/MultiworldGG/releases)
- Wild Arms .apworld [wildarms.apworld](https://github.com/TheDaedron/WildArms-apworld/releases)
- [BizHawk 2.10 (x64)](https://tasvideos.org/BizHawk/ReleaseHistory) or later
- Your legally obtained Wild Arms (USA) disc image, as a .BIN and .CUE. The .BIN must have the MD5 `19f6de83eb8b7525d7bf8eb27566ce30`.

## Other important guides

- [Setup guide for Archipelago](../../generic/docs/setup_en.md#installing-the-archipelago-software), required in order to install the apworld

## Installation Instructions

1. Download the **Wild Arms .apworld file** and double-click it to install it into the "custom_worlds/" subdirectory of your Archipelago install directory
2. Create your .yaml settings file (see below) and generate a seed with it.
3. Generating a seed reads your Wild Arms .BIN. Pick it when asked, or set `rom_file` under `wildarms_settings` in `host.yaml`.
4. Download the .apwildarms patch file that was built by the server while generating. This turns your disc image into the modified ROM.
5. Run "Open Patch" in the Archipelago Launcher and select the .apwildarms file.
6. If everything went fine, the modified .BIN and .CUE are created in the same folder as the .apwildarms file, and both BizHawk and the client launched.
7. Connect the client to the AP server of your choice, then start a new game.

Load only saves made with the current seed. A save from another seed or from an unmodified game makes the client show an error and deliver nothing.

## Create a Config (.yaml) File

To get the template YAML file:
1. Install the .apworld file as instructed above
2. If the Archipelago Launcher was running on your computer, close it
3. Run the Archipelago Launcher
4. Click on "Generate Template Settings"
5. It should open a directory in file explorer. Pick the file named `Wild Arms.yaml`

Each option is described on the options page and in the template file.
