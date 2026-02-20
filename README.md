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
  pipenv install --dev
  ```
- **Tests**: Run the test suite with pytest:
  ```bash
  pipenv run pytest
  ```
- **Lint/format**: Run ruff:
  ```bash
  pipenv run ruff check offload tests && pipenv run ruff format --check offload tests
  ```
- **Pre-commit** (optional): Install hooks so ruff and format run before each commit:
  ```bash
  pipenv run pre-commit install
  ```
- **Run the GUI**: From the project root:
  ```bash
  pipenv run python -m offload.gui
  ```
  or `pipenv run python offload/gui.py`
- **Build the .app bundle** (macOS): Uses py2app; produces a native arm64 app on Apple Silicon:
  ```bash
  ./compile.sh
  ```
  Or manually: `pipenv run python setup.py py2app`. The built app is in `dist/Offload.app`.

## Credits
- Source Sans Pro https://github.com/adobe-fonts/source-sans-pro