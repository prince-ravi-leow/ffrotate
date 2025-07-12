import os
import sys
import subprocess
import shutil
import tempfile
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QFileDialog, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PIL import Image
from tqdm import tqdm

def get_ffmpeg_path():
    if not sys.platform.startswith("win"):
        ffmpeg_path = shutil.which("ffmpeg")
    else:
        ffmpeg_path = shutil.which("ffmpeg.exe")
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not found. Install it and add to PATH.")
    return ffmpeg_path

def get_default_output_path():
    if sys.platform.startswith("win"):
        return os.path.join(os.path.expanduser("~"), "Videos", "rotated")
    else:
        return os.path.join(os.path.expanduser("~"), "Movies", "rotated")

def get_video_duration(input_path):
    ffmpeg_path = get_ffmpeg_path()
    command = [ffmpeg_path, "-i", input_path, "-f", "null", "-"]
    result = subprocess.run(command, stderr=subprocess.PIPE, text=True)
    duration_str = None
    for line in result.stderr.splitlines():
        if "Duration" in line:
            duration_str = line.split("Duration: ")[1].split(",")[0]
            break
    if not duration_str:
        raise RuntimeError("Could not determine video duration.")
    h, m, s = map(float, duration_str.split(":"))
    return h * 3600 + m * 60 + s

def extract_rotated_frame(input_path, rotation, custom_angle):
    ffmpeg_path = get_ffmpeg_path()
    duration = get_video_duration(input_path)
    seek_time = duration / 2
    rotation_map = {
        "90": "transpose=1",
        "180": "transpose=2,transpose=2",
        "270": "transpose=2",
    }
    filter_option = rotation_map[rotation] if rotation != "custom" else f"rotate={custom_angle}*(PI/180):bilinear=0"
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    temp_file.close()
    command = [
        ffmpeg_path, "-y", "-ss", str(seek_time), "-i", input_path,
        "-vf", filter_option, "-vframes", "1", temp_file.name
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return temp_file.name

def rotate_video(input_path, rotation, custom_angle, output_dir):
    ffmpeg_path = get_ffmpeg_path()
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_filename = f"{base}_rotated{ext}"
    output_path = os.path.join(output_dir, output_filename)
    rotation_map = {
        "90": "transpose=1",
        "180": "transpose=2,transpose=2",
        "270": "transpose=2",
    }
    filter_option = rotation_map[rotation] if rotation != "custom" else f"rotate={custom_angle}*(PI/180):bilinear=0"
    command = [
        ffmpeg_path, "-y", "-i", input_path, "-vf", filter_option,
        "-c:v", "libx264", "-crf", "0", "-preset", "ultrafast", output_path
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_path

class FFRotateApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JLP-rotate ⭕️")
        self.setFixedSize(600, 500)
        self.input_files = []
        self.rotation = "90"
        self.custom_angle = 0.0
        self.output_dir = get_default_output_path()
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignTop)

        # Upload Videos
        layout.addWidget(QLabel("Upload Videos:"))
        select_btn = QPushButton("Select Videos")
        select_btn.clicked.connect(self.select_files)
        layout.addWidget(select_btn)

        # Rotation
        layout.addWidget(QLabel("Rotation:"))
        self.rotation_combo = QComboBox()
        self.rotation_combo.addItems(["90", "180", "270", "custom"])
        self.rotation_combo.setCurrentText("90")
        self.rotation_combo.currentTextChanged.connect(self.toggle_custom_angle)
        layout.addWidget(self.rotation_combo)

        self.custom_angle_edit = QLineEdit("0.0")
        self.custom_angle_edit.setEnabled(False)
        layout.addWidget(self.custom_angle_edit)

        # Output Folder
        layout.addWidget(QLabel("Output Folder:"))
        output_frame = QFrame()
        output_layout = QHBoxLayout(output_frame)
        self.output_edit = QLineEdit(self.output_dir)
        output_layout.addWidget(self.output_edit)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.select_output_folder)
        output_layout.addWidget(browse_btn)
        layout.addWidget(output_frame)

        # Buttons
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        preview_btn = QPushButton("Preview")
        preview_btn.clicked.connect(self.show_preview)
        button_layout.addWidget(preview_btn)
        rotate_btn = QPushButton("Rotate Videos")
        rotate_btn.clicked.connect(self.process_videos)
        button_layout.addWidget(rotate_btn)
        layout.addWidget(button_frame)

        # Progress bar placeholder (tqdm integration is simplified)
        self.progress_frame = QFrame()
        layout.addWidget(self.progress_frame)

    def toggle_custom_angle(self, rotation):
        self.rotation = rotation
        self.custom_angle_edit.setEnabled(rotation == "custom")

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Video Files",
            "", "Video Files (*.mp4 *.mov *.avi *.mkv)"
        )
        if files:
            self.input_files = files
            QMessageBox.information(self, "Selected Files", f"{len(self.input_files)} file(s) selected.")

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_dir = folder
            self.output_edit.setText(folder)

    def show_preview(self):
        if not self.input_files:
            QMessageBox.critical(self, "Error", "Please select at least one video file.")
            return

        try:
            input_file = self.input_files[0]
            rotation = self.rotation_combo.currentText()
            try:
                custom_angle = float(self.custom_angle_edit.text())
            except ValueError:
                custom_angle = 0.0

            frame_path = extract_rotated_frame(input_file, rotation, custom_angle)
            img = Image.open(frame_path).convert("RGBA")  # Convert to RGBA for Qt compatibility
            max_size = (400, 300)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Convert PIL image to QImage
            img_data = img.tobytes("raw", "RGBA")
            qimage = QImage(img_data, img.width, img.height, QImage.Format_RGBA8888)

            pixmap = QPixmap.fromImage(qimage)

            preview_window = QMainWindow(self)
            preview_window.setWindowTitle("Preview")
            preview_window.setFixedSize(pixmap.width() + 20, pixmap.height() + 20)
            label = QLabel(preview_window)
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
            preview_window.setCentralWidget(label)
            preview_window.show()

            # Clean up on window close
            def cleanup():
                preview_window.close()
                os.remove(frame_path)
            preview_window.destroyed.connect(cleanup)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate preview: {str(e)}")

    def process_videos(self):
        if not self.input_files:
            QMessageBox.critical(self, "Error", "Please select input video files.")
            return

        output_dir = self.output_edit.text()
        if not os.path.isdir(output_dir):
            QMessageBox.critical(self, "Error", "Invalid output directory.")
            return

        try:
            for input_file in tqdm(self.input_files, desc="Processing videos"):
                rotate_video(input_file, self.rotation_combo.currentText(), 
                           float(self.custom_angle_edit.text()), output_dir)
            QMessageBox.information(self, "Success", f"Rotated {len(self.input_files)} video(s) successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FFRotateApp()
    window.show()
    sys.exit(app.exec())