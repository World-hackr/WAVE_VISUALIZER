import sys
import numpy as np
import scipy.io.wavfile as wav
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QTimer
import pyqtgraph as pg

# Smooth rendering
pg.setConfigOptions(antialias=True, useOpenGL=True)

def load_audio(file_path):
    sr, data = wav.read(file_path)
    if data.ndim > 1:
        data = data.mean(axis=1)
    data = data.astype(np.float32)
    data /= np.max(np.abs(data))
    return data, sr

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def colored_block(hex_color, width=4):
    r, g, b = hex_to_rgb(hex_color)
    return f"\033[48;2;{r};{g};{b}m{' ' * width}\033[0m"

def choose_color_terminal(prompt, default, colors):
    items = list(colors.items())
    print("Available colors:")
    for i, (name, hexc) in enumerate(items, 1):
        print(f" {i}. {name}: {hexc} {colored_block(hexc)}")
    sel = input(prompt)
    try:
        idx = int(sel)
        if 1 <= idx <= len(items):
            return items[idx-1][1]
    except:
        pass
    print("Using default:", default)
    return default

class WaveformViewer(QtWidgets.QWidget):
    def __init__(self, audio, sr, times, bg, pos, neg, filepath):
        super().__init__()
        self.full_audio = audio
        self.full_times = times
        self.total_time = times[-1]
        self.center     = self.total_time / 2
        self.colors     = (bg, pos, neg)
        self.plot_bg    = "#222222"
        self.downscale  = 1
        self.cache      = {}
        self.filepath   = filepath

        # media player
        self.player = QMediaPlayer(self)
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(filepath)))
        self.player.stateChanged.connect(self.on_state_changed)

        # timer for smooth playhead updates
        self.timer = QTimer(self)
        self.timer.setInterval(30)                    # ~33 updates/sec
        self.timer.timeout.connect(self._update_playhead)

        self.init_ui()

    def init_ui(self):
        bg, pos, neg = self.colors

        self.setWindowTitle("Waveform Viewer & Player")
        self.resize(900, 620)
        self.setStyleSheet(f"background-color: {bg}")

        main_layout = QtWidgets.QVBoxLayout(self)

        # — Header with the P=Play/Pause message —
        hdr = QtWidgets.QHBoxLayout()
        hdr.addStretch()
        lbl = QtWidgets.QLabel("P = Play/Pause")
        lbl.setStyleSheet("color: white; font-weight: bold;")
        hdr.addWidget(lbl)
        main_layout.addLayout(hdr)

        # — Waveform plot —
        self.plotw = pg.GraphicsLayoutWidget()
        self.plotw.setBackground(self.plot_bg)
        main_layout.addWidget(self.plotw)
        self.plot = self.plotw.addPlot(title="Waveform")
        self.plot.showGrid(x=True, y=True)
        self.plot.setLabel('left', "Amplitude")
        self.plot.setLabel('bottom', "Time (s)")
        self.plot.setYRange(-1, 1, padding=0)
        self.plot._gridPen = pg.mkPen(bg, width=1)

        # Info text for downscale status
        self.info_text = pg.TextItem("", anchor=(1,0), color="w")
        self.info_text.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        self.plot.addItem(self.info_text)

        # Playhead line, hidden until play
        self.playhead = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('y', width=2))
        self.playhead.hide()
        self.plot.addItem(self.playhead)

        # Draw the waveform
        self.draw_waveform()

        # — Zoom slider —
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(1, 1000)
        self.slider.setValue(500)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider.setTickInterval(50)
        self.slider.valueChanged.connect(self.update_zoom)
        main_layout.addWidget(self.slider)
        self.update_zoom(500)

    def draw_waveform(self):
        f = self.downscale
        if f == 1:
            t, a = self.full_times, self.full_audio
        elif f in self.cache:
            t, a = self.cache[f]
        else:
            step = max(1, f)
            t = self.full_times[::step]
            a = self.full_audio[::step]
            self.cache[f] = (t, a)

        pos_data = np.maximum(a, 0)
        neg_data = np.minimum(a, 0)
        if hasattr(self, 'pos_curve'):
            self.pos_curve.setData(t, pos_data)
            self.neg_curve.setData(t, neg_data)
        else:
            _, pos_c, neg_c = self.colors
            self.pos_curve = self.plot.plot(t, pos_data, pen=pg.mkPen(pos_c, width=1))
            self.neg_curve = self.plot.plot(t, neg_data, pen=pg.mkPen(neg_c, width=1))
        self.update_info_text()

    def update_info_text(self):
        vr = self.plot.getViewBox().viewRect()
        x = vr.right()
        y = vr.top()
        msg = "Full resolution" if self.downscale == 1 else f"Downscale: {self.downscale}"
        self.info_text.setText(msg)
        self.info_text.setPos(x, y - 0.05)

    def update_zoom(self, val):
        if val == 500:
            self.plot.setXRange(0, self.total_time, padding=0)
        else:
            scale = val / 500.0
            w     = self.total_time * scale
            L, R  = self.center - w/2, self.center + w/2
            self.plot.setXRange(L, R, padding=0)
        self.update_info_text()

    def set_downscale(self, f):
        if f != self.downscale:
            self.downscale = f
            self.draw_waveform()

    def _update_playhead(self):
        # Called by QTimer ~33 Hz
        sec = self.player.position() / 1000.0
        self.playhead.setPos(sec)

    def on_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            # show playhead and start timer
            self.playhead.show()
            self.timer.start()
        else:
            # pause or stop → stop timer
            self.timer.stop()
            if state == QMediaPlayer.StoppedState:
                # reset playhead
                self.playhead.hide()
                self.playhead.setPos(0)

    def keyPressEvent(self, ev):
        if ev.isAutoRepeat(): return
        k = ev.key()
        if k == QtCore.Qt.Key_P and QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.NoModifier:
            if self.player.state() == QMediaPlayer.PlayingState:
                self.player.pause()
            else:
                self.player.play()
        elif QtCore.Qt.Key_1 <= k <= QtCore.Qt.Key_9 and QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.NoModifier:
            self.set_downscale(k - QtCore.Qt.Key_0)
        else:
            super().keyPressEvent(ev)

    def keyReleaseEvent(self, ev):
        if ev.isAutoRepeat(): return
        k = ev.key()
        if QtCore.Qt.Key_1 <= k <= QtCore.Qt.Key_9:
            self.set_downscale(1)
        else:
            super().keyReleaseEvent(ev)


def main():
    app = QtWidgets.QApplication(sys.argv)

    # — Color selection —
    colors = {
        "Black": "#000000", "Electric Blue": "#0000FF", "Neon Purple": "#BF00FF",
        "Bright Cyan": "#00FFFF", "Vibrant Magenta": "#FF00FF", "Neon Green": "#39FF14",
        "Hot Pink": "#FF69B4", "Neon Orange": "#FF4500", "Bright Yellow": "#FFFF00",
        "Electric Lime": "#CCFF00", "Vivid Red": "#FF0000", "Deep Sky Blue": "#00BFFF",
        "Vivid Violet": "#9F00FF", "Fluorescent Pink": "#FF1493", "Laser Lemon": "#FFFF66",
        "Screamin' Green": "#66FF66", "Ultra Red": "#FF2400", "Radical Red": "#FF355E",
        "Vivid Orange": "#FFA500", "Electric Indigo": "#6F00FF"
    }
    use_custom = input("Use custom palette? (y/n): ").strip().lower() == "y"
    if use_custom:
        bg = choose_color_terminal("Overall background #: ", "#000000", colors)
        pw = choose_color_terminal("Positive wave #:    ", "#39FF14", colors)
        nw = choose_color_terminal("Negative wave #:    ", "#39FF14", colors)
    else:
        bg, pw, nw = "#000000", "#39FF14", "#39FF14"

    # — File dialog —
    fd = QtWidgets.QFileDialog()
    fd.setNameFilter("WAV files (*.wav)")
    fd.setFileMode(QtWidgets.QFileDialog.ExistingFile)
    if not fd.exec_():
        print("No file selected. Exiting.")
        sys.exit(0)
    path = fd.selectedFiles()[0]

    audio, sr = load_audio(path)
    times = np.linspace(0, len(audio)/sr, len(audio))

    w = WaveformViewer(audio, sr, times, bg, pw, nw, path)
    w.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
