# Wave Visualizer

This project is a PyQtGraph-based waveform viewer that allows you to visualize WAV files in full resolution with advanced features such as adaptive downscaling, zoom control, and customizable color schemes via terminal input.

## Features

- **Full-Resolution Display:**  
  By default, the entire waveform is rendered in full resolution using smooth, continuous lines.

- **Adaptive Downscaling:**  
  Press any number key (1–9) to temporarily downscale the waveform (reducing the number of plotted samples) for smoother interactions. Releasing the key restores full quality. Higher numbers lead to more aggressive downscaling.

- **Zoom Slider:**  
  A horizontal slider (range 1–1000, default at 500) allows you to smoothly zoom in and out along the x-axis. When the slider is at 500, the full waveform is displayed (from 0 to the total duration).

- **Customizable Colors:**  
  Before opening a file, the program prompts you in the terminal to select custom colors for:
  - Overall background (used for gridlines)
  - Positive portion of the waveform
  - Negative portion of the waveform

- **Performance Optimizations:**  
  Adaptive downscaling uses cached downsampled arrays to ensure smooth performance even with large files.

## Requirements

- Python 3.x
- [PyQt5](https://pypi.org/project/PyQt5/)
- [pyqtgraph](https://pypi.org/project/pyqtgraph/)
- [numpy](https://pypi.org/project/numpy/)
- [scipy](https://pypi.org/project/scipy/)

Install the required packages via pip:

```bash
pip install PyQt5 pyqtgraph numpy scipy
