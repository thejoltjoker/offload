![Offload](https://offload.app/apple-touch-icon.png)
# Offload App
Offload is a simple tool for offloading files from memory cards and external drives using checksum verification.

## Features

- Transfer files from a memory card or removable drive.
- Checksum verification using xxhash.
- File renaming based on date or other relevant variables.
- Keep your files organized in date based folder structures.

## Usage

1. Download the latest version of the app from [the website](https://offload.app).
2. Run the app.
3. Enjoy!

## Development

The project supports **macOS on Apple Silicon (M1)** and Intel. Python 3.12+ is required.

- **Setup**: Install Python 3.12 (e.g. via [Homebrew](https://brew.sh) or [pyenv](https://github.com/pyenv/pyenv)), then:
  ```bash
  uv sync --all-extras
  ```
- **Tests**: Run the test suite with pytest:
  ```bash
  uv run pytest
  ```
- **Lint/format**: Run ruff:
  ```bash
  uv run ruff check offload tests && uv run ruff format --check offload tests
  ```
- **Pre-commit** (optional): Install hooks so ruff and format run before each commit:
  ```bash
  uv run pre-commit install
  ```
- **Run the CLI**: From the project root:
  ```bash
  uv run python -m offload.app
  ```
  This starts interactive mode. To provide paths directly:
  ```bash
  uv run python -m offload.app -s /Volumes/MY_CARD -d ~/Pictures/Offload
  ```
  Useful flags include:
  - `-f`, `--folder-structure`: `original`, `taken_date` (default), `offload_date`, `year`, `year_month`, or `flat`
  - `-p`, `--prefix`: `taken_date`, `taken_date_time`, `offload_date`, a custom prefix, or `none`
  - `-n`, `--name`: rename files
  - `-m`, `--move`: move files instead of copying
  - `--dryrun`: preview without transferring files
  - `--debug-log`: show debug logging
- **Run the GUI**: From the project root:
  ```bash
  uv run python -m offload.gui
  ```
  or `uv run python offload/gui.py`
- **Build the .app bundle** (macOS): Uses py2app; produces a native arm64 app on Apple Silicon:
  ```bash
  make zip      # build .app and create dist/Offload.zip
  make all      # build, zip, copy to website assets and /Applications
  ```
  Or manually: `uv run --python 3.12 --extra build python setup.py py2app`. The built app is in `dist/Offload.app`.

## Credits
- Source Sans Pro https://github.com/adobe-fonts/source-sans-pro