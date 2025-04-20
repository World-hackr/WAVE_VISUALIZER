# Waveform Viewer & Player

A PyQt5-based waveform visualization and playback tool that allows you to:

- **Load** WAV audio files via a file dialog
- **Visualize** the waveform in full resolution or downsampled view (1–9×) with a zoom slider
- **Customize** colors interactively via terminal prompts
- **Play/Pause** audio playback with the `P` key
- **Display** a smooth moving playhead on the waveform
- **View** playback controls instruction always visible at the top-right

---

## Features

- **File Dialog**: Browse and select WAV files (`*.wav`).
- **Color Picker**: Choose background, positive waveform, and negative waveform colors from a terminal-based palette.
- **Waveform Rendering**: Full-resolution or adaptive downsampling (press keys 1–9) for fast rendering of large files.
- **Zoom Slider**: Adjust horizontal zoom level (1–1000) to focus on specific time windows.
- **Keyboard Controls**:
  - `P`: Toggle play/pause
  - `1`–`9`: Temporary downsampling factors (release to revert to full resolution)
- **Smooth Playhead**: A yellow vertical line indicates current playback position, updated at ~33 Hz.
- **Persistent Instructions**: `P = Play/Pause` label and downsample status shown in the corner.

---

## Prerequisites

- Python 3.7+
- PyQt5
- PyQt5 Multimedia (`PyQt5.QtMultimedia`)
- NumPy
- SciPy
- pyqtgraph

You can install the dependencies via:

```bash
pip install PyQt5 PyQt5‑Multimedia numpy scipy pyqtgraph
```

---

## Installation

1. **Clone** this repository:
   ```bash
git clone <your-repo-url>
cd <your-repo-directory>
```
2. **Ensure** dependencies are installed (see above).
3. **Run** the application:
   ```bash
python waveform_viewer.py
```

---

## Usage

1. On launch, choose whether to use a custom color palette. If yes, select colors by index.
2. Use the file dialog to open a `.wav` file.
3. The waveform will render in the main window.
4. Controls:
   - **Play/Pause**: Press `P` to start or pause playback. A yellow playhead will sweep across the waveform during playback.
   - **Downsample**: Hold keys `1`–`9` to view a downsampled version (factor corresponds to key). Release to return to full resolution.
   - **Zoom**: Use the slider at the bottom to zoom horizontally (1× to 1000×).
5. The status and instructions appear in the top-right corner.

---

## File Structure

```
├── waveform_viewer.py  # Main application script
├── README.md           # This documentation
└── examples/           # (Optional) Example WAV files
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.

