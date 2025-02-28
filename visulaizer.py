import sys
import numpy as np
import scipy.io.wavfile as wav
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

# Enable antialiasing and OpenGL for smooth rendering.
pg.setConfigOptions(antialias=True, useOpenGL=True)

def load_audio(file_path):
    sr, data = wav.read(file_path)
    if data.ndim > 1:
        data = data.mean(axis=1)  # Convert to mono.
    data = data.astype(np.float32)
    data /= np.max(np.abs(data))
    return data, sr

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def colored_block(hex_color, width=4):
    r, g, b = hex_to_rgb(hex_color)
    return f"\033[48;2;{r};{g};{b}m{' ' * width}\033[0m"

def choose_color_terminal(prompt, default_value, colors):
    color_items = list(colors.items())
    print("Available colors:")
    for i, (name, hex_code) in enumerate(color_items, start=1):
        print(f"{i}. {name}: {hex_code} {colored_block(hex_code)}")
    choice = input(prompt)
    try:
        idx = int(choice)
        if 1 <= idx <= len(color_items):
            return color_items[idx-1][1]
        else:
            print("Invalid choice, using default.")
            return default_value
    except ValueError:
        print("Invalid input, using default.")
        return default_value

class WaveformViewer(QtWidgets.QWidget):
    def __init__(self, audio, sr, times, overall_bg, pos_wave, neg_wave):
        super().__init__()
        # Store full-resolution data.
        self.full_audio = audio.copy()
        self.full_times = times.copy()
        self.sr = sr
        self.total_time = times[-1]
        self.center = self.total_time / 2.0

        # Colors from terminal:
        # overall_bg will be used for gridlines,
        # pos_wave for the positive portion,
        # neg_wave for the negative portion.
        self.overall_bg_color = overall_bg  
        self.pos_wave_color = pos_wave      
        self.neg_wave_color = neg_wave      
        self.plot_bg_color = "#222222"       

        # Adaptive downscaling: 1 means full resolution.
        self.downscale_factor = 1
        self.cached_downsamples = {}

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Waveform Viewer")
        self.resize(900, 600)
        self.setStyleSheet("background-color: " + self.overall_bg_color)
        layout = QtWidgets.QVBoxLayout(self)

        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_widget.setBackground(self.plot_bg_color)
        layout.addWidget(self.plot_widget)

        self.plot = self.plot_widget.addPlot(title="Waveform Viewer")
        self.plot.setLabel('left', "Amplitude")
        self.plot.setLabel('bottom', "Time (s)")
        self.plot.showGrid(x=True, y=True)
        self.plot.setYRange(-1, 1, padding=0)
        # Set grid pen to overall_bg_color.
        self.plot._gridPen = pg.mkPen(self.overall_bg_color, width=1)

        # Info text (top-right) for downscale status.
        self.info_text = pg.TextItem("", anchor=(1, 0), color="w")
        self.info_text.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        self.plot.addItem(self.info_text)
        self.info_text.setPos(self.plot.viewRange()[0][1]-10,
                              self.plot.viewRange()[1][1]-10)

        self.draw_waveform()

        # Slider for x-axis zoom: range 1–1000, default 500 = full view.
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(1000)
        self.slider.setValue(500)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider.setTickInterval(50)
        self.slider.valueChanged.connect(self.update_zoom)
        layout.addWidget(self.slider)

        # Set default view: slider = 500 means x from 0 to total_time.
        self.update_zoom(self.slider.value())

    def draw_waveform(self):
        factor = self.downscale_factor
        if factor == 1:
            ds_times = self.full_times
            ds_audio = self.full_audio
        elif factor in self.cached_downsamples:
            ds_times, ds_audio = self.cached_downsamples[factor]
        else:
            step = max(1, factor)
            ds_times = self.full_times[::step]
            ds_audio = self.full_audio[::step]
            self.cached_downsamples[factor] = (ds_times, ds_audio)
        # Split the waveform into positive and negative parts.
        pos_data = np.maximum(ds_audio, 0)
        neg_data = np.minimum(ds_audio, 0)
        # Draw continuous lines (full quality) when no downscaling.
        if hasattr(self, "pos_curve") and hasattr(self, "neg_curve"):
            self.pos_curve.setData(ds_times, pos_data)
            self.neg_curve.setData(ds_times, neg_data)
        else:
            self.pos_curve = self.plot.plot(ds_times, pos_data,
                                            pen=pg.mkPen(self.pos_wave_color, width=1), symbol=None)
            self.neg_curve = self.plot.plot(ds_times, neg_data,
                                            pen=pg.mkPen(self.neg_wave_color, width=1), symbol=None)
        self.update_info_text()

    def update_info_text(self):
        msg = "Full resolution" if self.downscale_factor == 1 else f"Downscale: {self.downscale_factor}"
        self.info_text.setText(msg)
        view_rect = self.plot.getViewBox().viewRect()
        self.info_text.setPos(view_rect.right()-10, view_rect.top()+10)

    def update_zoom(self, slider_value):
        if slider_value == 500:
            self.plot.setXRange(0, self.total_time, padding=0)
        else:
            scale = slider_value / 500.0
            window_length = self.total_time * scale
            left = self.center - window_length / 2.0
            right = self.center + window_length / 2.0
            self.plot.setXRange(left, right, padding=0)
        self.update_info_text()

    def set_downscale_factor(self, factor):
        if factor == self.downscale_factor:
            return
        self.downscale_factor = factor
        self.draw_waveform()

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        # Use number keys 1-9 for adaptive downscaling.
        if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.NoModifier and \
           QtCore.Qt.Key_1 <= event.key() <= QtCore.Qt.Key_9:
            factor = event.key() - QtCore.Qt.Key_0
            self.set_downscale_factor(factor)
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        if QtCore.Qt.Key_1 <= event.key() <= QtCore.Qt.Key_9:
            self.set_downscale_factor(1)
        else:
            super().keyReleaseEvent(event)

def main():
    app = QtWidgets.QApplication(sys.argv)
    colors_dict = {
        "Black": "#000000",
        "Electric Blue": "#0000FF",
        "Neon Purple": "#BF00FF",
        "Bright Cyan": "#00FFFF",
        "Vibrant Magenta": "#FF00FF",
        "Neon Green": "#39FF14",
        "Hot Pink": "#FF69B4",
        "Neon Orange": "#FF4500",
        "Bright Yellow": "#FFFF00",
        "Electric Lime": "#CCFF00",
        "Vivid Red": "#FF0000",
        "Deep Sky Blue": "#00BFFF",
        "Vivid Violet": "#9F00FF",
        "Fluorescent Pink": "#FF1493",
        "Laser Lemon": "#FFFF66",
        "Screamin' Green": "#66FF66",
        "Ultra Red": "#FF2400",
        "Radical Red": "#FF355E",
        "Vivid Orange": "#FFA500",
        "Electric Indigo": "#6F00FF"
    }
    use_custom = input("Do you want to choose a custom color palette? (y/n): ").strip().lower() == "y"
    if use_custom:
        overall_bg = choose_color_terminal("Choose overall background color (enter number): ", "#000000", colors_dict)
        pos_wave = choose_color_terminal("Choose positive waveform color (enter number): ", "#39FF14", colors_dict)
        neg_wave = choose_color_terminal("Choose negative waveform color (enter number): ", "#39FF14", colors_dict)
    else:
        overall_bg = "#000000"
        pos_wave = "#39FF14"
        neg_wave = "#39FF14"

    file_dialog = QtWidgets.QFileDialog()
    file_dialog.setNameFilter("WAV files (*.wav)")
    file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
    if file_dialog.exec_():
        wav_file = file_dialog.selectedFiles()[0]
    else:
        print("No file selected. Exiting.")
        sys.exit(0)

    audio, sr = load_audio(wav_file)
    total_time = len(audio) / sr
    times = np.linspace(0, total_time, len(audio))

    viewer = WaveformViewer(audio, sr, times, overall_bg, pos_wave, neg_wave)
    viewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
