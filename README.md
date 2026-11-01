# Photo Downloader

Photo-Downloader copies image and video files from a source path(typically an SD card path) to a destination path, and creates a directory tree based on the modification date of the file.  This is hardcoded to the small subset of image and video files that I work with.  The folder structure is also hardcoded to my preference. 

This was created to replace what I used to solely use Rapid Photo Downloader to do.  But, in the mos recent version, it continuously crashes in Kubuntu 18.04.1 LTS.  So, this is super simple, and it works.

## GUI

Launch the folder picker app with:

```
python .\photo_downloader_gui.py
```

Choose a source and destination folder, then select **Preview** to see how many
media files are ready to copy and how many are already present. Select **Copy
files** to start the copy. The app remembers your last-used folders in
`%USERPROFILE%\.photo_downloader_gui.json`.

The text window shows the same per-file scan messages as the CLI, followed by
the preview summary and each destination path as it is copied.

## Development setup with uv

The app uses Python's standard library, so no packages are needed to run it.
These steps create an isolated environment and install PyInstaller only for
building the executable.

### Windows (PowerShell)

Install uv if needed:

```
winget install --id=astral-sh.uv -e
```

If PowerShell cannot find `uv` after reopening, add WinGet's uv folder to your
persistent user PATH:

```
$uvDir = (Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\astral-sh.uv*\uv.exe" | Select-Object -First 1).DirectoryName
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (($userPath -split ";") -notcontains $uvDir) {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$uvDir", "User")
}
```

Restart PowerShell (or VS Code), then verify with `uv --version`. Navigate to
the project folder and create and activate a virtual environment:

```
uv venv --python 3.12
.\.venv\Scripts\Activate.ps1
```

Run the GUI:

```
python .\photo_downloader_gui.py
```

Build a standalone Windows executable:

```
uv pip install pyinstaller
python -m PyInstaller --onefile --windowed --name PhotoDownloader photo_downloader_gui.py
```

The executable is `dist\PhotoDownloader.exe`; double-click it to run. If
PowerShell blocks activation, use the venv's Python directly instead:

```
.\.venv\Scripts\python.exe .\photo_downloader_gui.py
```

### Linux (Debian or Ubuntu)

Install uv if needed, then open a new terminal:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Tkinter is provided by the operating system on many Linux distributions. On
Debian or Ubuntu, install it for the system Python, then create the virtual
environment from that same Python:

```
sudo apt update
sudo apt install python3-tk
cd /path/to/photo-downloader
uv venv --python /usr/bin/python3
source .venv/bin/activate
```

Check that Tkinter is available and run the GUI:

```
python -m tkinter
python photo_downloader_gui.py
```

Build a standalone Linux executable:

```
uv pip install pyinstaller
python -m PyInstaller --onefile --windowed --name PhotoDownloader photo_downloader_gui.py
```

The executable is `dist/PhotoDownloader`. Run it from a terminal with
`./dist/PhotoDownloader`, or make it executable and launch it from your file
manager. If Tkinter is missing, install the matching Tk package for the Python
interpreter used by the virtual environment (for Fedora, this is commonly
`python3-tkinter`).

PyInstaller is not a cross-compiler: build on Windows for Windows, and on Linux
for Linux. Linux executables can depend on the system's glibc, so build on an
older Linux distribution if you need to support older systems. The
`--windowed` option hides the console; logs still appear in the app's text
window. The executable does not need uv or a separate Python installation.