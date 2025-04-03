# Oscillating Audio Blender

This is a simple GUI tool to blend two WAV files using an oscillating pattern over time, and export the result as an OGG file.

## Features

- Load two WAV files and blend them over time
- Custom gain, blend shape (start → middle → end)
- Clean GUI with PyQt6
- Export to `.ogg` format
- Uses `config.ini` to remember default settings

## Requirements

- Python 3.9 or newer
- `ffmpeg` installed and available in PATH (for OGG export)

## Setup

1. **Install Python**  
   Download and install from: https://www.python.org/downloads/

2. **Install dependencies**  
   Open a terminal (Command Prompt or PowerShell), navigate to this folder, and run:

   ```bash
   pip install -r requirements.txt
   ```

3. **Install ffmpeg (for audio export)**  
   Download from: https://ffmpeg.org/download.html  
   Add `ffmpeg/bin` to your system PATH.

4. **Run the app**

   ```bash
   python gui_audio_blender.py
   ```

## Configuration

The app loads default values from `config.ini` (optional). Example:

```ini
[FILES]
file_1 = pink.wav
file_2 = brown.wav

[TIMING]
cycle_minutes = 1

[MIX]
gain_1 = 1.0
gain_2 = 2.0
blend_min = 0.1
blend_max = 0.9

[AUDIO]
sample_rate = 22050
```

## Exporting to `.exe`

To generate a `.exe` file for distribution:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed gui_audio_blender.py
```

The resulting `.exe` will be in the `dist/` folder.
