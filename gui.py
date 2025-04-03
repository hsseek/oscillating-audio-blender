import sys
import numpy as np
import wave
import os
import configparser
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QSpinBox, QDoubleSpinBox, QLineEdit, QProgressBar,
    QTextEdit, QSlider
)
from PyQt6.QtCore import Qt
from scipy.io.wavfile import write
from pydub import AudioSegment

class AudioBlender(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Oscillating Audio Blender")
        self.load_config()
        self.setup_ui()

    def load_config(self):
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.defaults = {
            "file_1": self.config.get("FILES", "file_1", fallback=""),
            "file_2": self.config.get("FILES", "file_2", fallback=""),
            "cycle_minutes": self.config.getint("TIMING", "cycle_minutes", fallback=1),
            "gain_1": self.config.getfloat("MIX", "gain_1", fallback=1.0),
            "gain_2": self.config.getfloat("MIX", "gain_2", fallback=1.0),
            "blend_1_start": self.config.getfloat("MIX", "blend_1_start", fallback=0.2),
            "blend_1_middle": self.config.getfloat("MIX", "blend_1_middle", fallback=0.8),
            "sample_rate": self.config.getint("AUDIO", "sample_rate", fallback=22050),
        }

    def setup_ui(self):
        layout = QVBoxLayout()

        # File 1
        file_1_layout = QHBoxLayout()
        self.file_1_input = QLineEdit(self.defaults["file_1"])
        self.file_1_input.setMinimumWidth(200)
        file_1_btn = QPushButton("Browse")
        file_1_btn.clicked.connect(lambda: self.browse_file(self.file_1_input))
        self.gain_1 = QDoubleSpinBox()
        self.gain_1.setRange(0.1, 10.0)
        self.gain_1.setValue(self.defaults["gain_1"])
        file_1_layout.addWidget(QLabel("File 1:"))
        file_1_layout.addWidget(self.file_1_input)
        file_1_layout.addWidget(file_1_btn)
        file_1_layout.addWidget(QLabel("Gain:"))
        file_1_layout.addWidget(self.gain_1)
        layout.addLayout(file_1_layout)

        # File 2
        file_2_layout = QHBoxLayout()
        self.file_2_input = QLineEdit(self.defaults["file_2"])
        self.file_2_input.setMinimumWidth(200)
        file_2_btn = QPushButton("Browse")
        file_2_btn.clicked.connect(lambda: self.browse_file(self.file_2_input))
        self.gain_2 = QDoubleSpinBox()
        self.gain_2.setRange(0.1, 10.0)
        self.gain_2.setValue(self.defaults["gain_2"])
        file_2_layout.addWidget(QLabel("File 2:"))
        file_2_layout.addWidget(self.file_2_input)
        file_2_layout.addWidget(file_2_btn)
        file_2_layout.addWidget(QLabel("Gain:"))
        file_2_layout.addWidget(self.gain_2)
        layout.addLayout(file_2_layout)

        # Output file
        output_layout = QHBoxLayout()
        default_filename = f"oscbldr-{self.defaults['cycle_minutes']}-{int(self.defaults['gain_1'] * 10):02d}-{int(self.defaults['gain_2'] * 10):02d}-{int(self.defaults['blend_1_start'] * 100):02d}-{int(self.defaults['blend_1_middle'] * 100):02d}.ogg"
        self.output_path = QLineEdit(default_filename)
        self.output_path.setMinimumWidth(200)
        output_btn = QPushButton("Save As")
        output_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(QLabel("Output File:"))
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(output_btn)
        layout.addLayout(output_layout)

        # Blend sliders
        blend_layout = QVBoxLayout()
        label_width = 120

        # Start
        start_row = QHBoxLayout()
        self.blend_1_start_slider = QSlider(Qt.Orientation.Horizontal)
        self.blend_1_start_slider.setRange(0, 100)
        self.blend_1_start_slider.setValue(int(self.defaults["blend_1_start"] * 100))
        self.blend_1_start_spin = QDoubleSpinBox()
        self.blend_1_start_spin.setRange(0.0, 1.0)
        self.blend_1_start_spin.setSingleStep(0.01)
        self.blend_1_start_spin.setValue(self.defaults["blend_1_start"])
        self.blend_1_start_slider.valueChanged.connect(lambda val: self.blend_1_start_spin.setValue(val / 100))
        self.blend_1_start_spin.valueChanged.connect(lambda val: self.blend_1_start_slider.setValue(int(val * 100)))
        start_label = QLabel("File 1 at start:")
        start_label.setFixedWidth(label_width)
        start_row.addWidget(start_label)
        start_row.addWidget(self.blend_1_start_slider)
        start_row.addWidget(self.blend_1_start_spin)

        # Middle
        middle_row = QHBoxLayout()
        self.blend_1_mid_slider = QSlider(Qt.Orientation.Horizontal)
        self.blend_1_mid_slider.setRange(0, 100)
        self.blend_1_mid_slider.setValue(int(self.defaults["blend_1_middle"] * 100))
        self.blend_1_mid_spin = QDoubleSpinBox()
        self.blend_1_mid_spin.setRange(0.0, 1.0)
        self.blend_1_mid_spin.setSingleStep(0.01)
        self.blend_1_mid_spin.setValue(self.defaults["blend_1_middle"])
        self.blend_1_mid_slider.valueChanged.connect(lambda val: self.blend_1_mid_spin.setValue(val / 100))
        self.blend_1_mid_spin.valueChanged.connect(lambda val: self.blend_1_mid_slider.setValue(int(val * 100)))
        middle_label = QLabel("File 1 in middle:")
        middle_label.setFixedWidth(label_width)
        middle_row.addWidget(middle_label)
        middle_row.addWidget(self.blend_1_mid_slider)
        middle_row.addWidget(self.blend_1_mid_spin)

        # End (mirrors start)
        end_row = QHBoxLayout()
        self.blend_1_end_slider = QSlider(Qt.Orientation.Horizontal)
        self.blend_1_end_slider.setRange(0, 100)
        self.blend_1_end_slider.setValue(int(self.defaults["blend_1_start"] * 100))  # mirror start
        self.blend_1_end_spin = QDoubleSpinBox()
        self.blend_1_end_spin.setRange(0.0, 1.0)
        self.blend_1_end_spin.setSingleStep(0.01)
        self.blend_1_end_spin.setValue(self.defaults["blend_1_start"])
        self.blend_1_end_slider.setEnabled(False)
        self.blend_1_end_spin.setEnabled(False)
        self.blend_1_start_slider.valueChanged.connect(self.blend_1_end_slider.setValue)
        self.blend_1_start_spin.valueChanged.connect(self.blend_1_end_spin.setValue)
        end_label = QLabel("File 1 at end:")
        end_label.setFixedWidth(label_width)
        end_row.addWidget(end_label)
        end_row.addWidget(self.blend_1_end_slider)
        end_row.addWidget(self.blend_1_end_spin)

        blend_layout.addLayout(start_row)
        blend_layout.addLayout(middle_row)
        blend_layout.addLayout(end_row)
        layout.addLayout(blend_layout)

        # Cycle duration
        cycle_layout = QHBoxLayout()
        self.duration = QSpinBox()
        self.duration.setRange(1, 180)
        self.duration.setValue(self.defaults["cycle_minutes"])
        cycle_layout.addWidget(QLabel("Cycle Duration (min):"))
        cycle_layout.addWidget(self.duration)
        layout.addLayout(cycle_layout)

        # Generate button
        self.export_btn = QPushButton("Generate .ogg File")
        self.export_btn.clicked.connect(self.generate_audio)
        layout.addWidget(self.export_btn)

        # Progress and log
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        layout.addWidget(self.status_log)

        self.setLayout(layout)

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.status_log.append(f"{timestamp} [{level}] {message}")
        self.status_log.verticalScrollBar().setValue(self.status_log.verticalScrollBar().maximum())

    def browse_file(self, target):
        file, _ = QFileDialog.getOpenFileName(self, "Select WAV File", filter="WAV files (*.wav)")
        if file:
            target.setText(file)

    def browse_output(self):
        file, _ = QFileDialog.getSaveFileName(self, "Save As", filter="OGG files (*.ogg)")
        if file:
            self.output_path.setText(file)

    def load_wav(self, path):
        with wave.open(path, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            return np.frombuffer(frames, dtype=np.int16)

    def generate_audio(self):
        file_1_path = self.file_1_input.text()
        file_2_path = self.file_2_input.text()
        output_file = self.output_path.text()
        sample_rate = self.defaults["sample_rate"]

        if not os.path.exists(file_1_path) or not os.path.exists(file_2_path):
            self.log("Invalid file paths.", level="ERROR")
            return

        self.log("Loading WAV files...")
        audio_1 = self.load_wav(file_1_path).astype(np.float64)
        audio_2 = self.load_wav(file_2_path).astype(np.float64)
        self.log("Files loaded.")

        length = min(len(audio_1), len(audio_2))
        audio_1 = audio_1[:length] * self.gain_1.value()
        audio_2 = audio_2[:length] * self.gain_2.value()
        self.log("Applied manual gain.")

        blend_1_start_val = self.blend_1_start_spin.value()
        blend_1_mid_val = self.blend_1_mid_spin.value()
        total_seconds = self.duration.value() * 60
        output = np.zeros(total_seconds * sample_rate, dtype=np.float64)
        self.progress.setValue(0)
        self.log("Generating blended audio...")

        for i in range(len(output)):
            t = i / sample_rate
            # Cosine-shaped blend: start → middle → end
            blend = blend_1_start_val + (blend_1_mid_val - blend_1_start_val) * (
                1 - np.cos(2 * np.pi * t / total_seconds)) / 2
            sample_1 = audio_1[i % length]
            sample_2 = audio_2[i % length]
            output[i] = sample_1 * blend + sample_2 * (1 - blend)
            if i % (len(output) // 100) == 0:
                self.progress.setValue(int(i / len(output) * 100))

        self.progress.setValue(100)
        max_val = np.max(np.abs(output))
        if max_val > 32767:
            self.log("Applying limiter to prevent clipping.", level="WARNING")
            output = output / max_val * 32767
        output = output.astype(np.int16)

        temp_wav = "temp_output.wav"
        write(temp_wav, sample_rate, output)
        self.log("Temporary WAV file written.")

        AudioSegment.from_wav(temp_wav).export(output_file, format="ogg", bitrate="32k")
        os.remove(temp_wav)

        self.log(f"Export complete: {output_file}", level="SUCCESS")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioBlender()
    window.show()
    sys.exit(app.exec())
