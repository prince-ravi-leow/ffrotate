import os
import sys
import subprocess
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tqdm.tk import tqdm
from PIL import Image, ImageTk
import tempfile

def get_ffmpeg_path():
    """Return the path to ffmpeg.exe, handling both dev and PyInstaller environments."""
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        base_path = sys._MEIPASS  # Temporary directory where files are extracted
        ffmpeg_path = os.path.join(base_path, 'ffmpeg', 'ffmpeg.exe' if sys.platform.startswith('win') else 'ffmpeg')
    else:
        # Running in development environment
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg and add it to your PATH, "
                "or include ffmpeg.exe in the 'ffmpeg' folder."
            )
    return ffmpeg_path

def get_default_output_path():
    if sys.platform.startswith("win"):
        return os.path.join(os.path.expanduser("~"), "Videos", "rotated")
    else:
        return os.path.join(os.path.expanduser("~"), "Movies", "rotated")

def get_video_duration(input_path):
    ffmpeg_path = get_ffmpeg_path()
    
    command = [
        ffmpeg_path,
        "-i",
        input_path,
        "-f",
        "null",
        "-"
    ]
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

    if rotation != "custom":
        filter_option = rotation_map[rotation]
    else:
        filter_option = f"rotate={custom_angle}*(PI/180):bilinear=0"

    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    temp_file.close()

    command = [
        ffmpeg_path,
        "-y",
        "-ss",
        str(seek_time),
        "-i",
        input_path,
        "-vf",
        filter_option,
        "-vframes",
        "1",
        temp_file.name
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

    if rotation != "custom":
        filter_option = rotation_map[rotation]
    else:
        filter_option = f"rotate={custom_angle}*(PI/180):bilinear=0"

    command = [
        ffmpeg_path,
        "-y",
        "-i",
        input_path,
        "-vf",
        filter_option,
        "-c:v",
        "libx264",
        "-crf",
        "0",
        "-preset",
        "ultrafast",
        output_path,
    ]

    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_path

class FFRotateApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JLP-rotate ⭕️")
        self.geometry("600x500")
        self.resizable(False, False)

        # Enable DPI awareness on Windows
        if sys.platform.startswith("win"):
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)

        # Variables
        self.input_files = []
        self.rotation_var = tk.StringVar(value="90")
        self.custom_angle_var = tk.DoubleVar(value=0.0)
        self.output_dir_var = tk.StringVar(value=get_default_output_path())

        # Widgets
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Upload Videos:").pack(anchor="w", padx=10, pady=5)
        tk.Button(self, text="Select Videos", command=self.select_files).pack(padx=10, pady=5)

        tk.Label(self, text="Rotation:").pack(anchor="w", padx=10, pady=5)
        rotation_choices = ["90", "180", "270", "custom"]
        self.rotation_menu = ttk.Combobox(self, values=rotation_choices, textvariable=self.rotation_var, state="readonly")
        self.rotation_menu.pack(padx=10, pady=5)
        self.rotation_menu.bind("<<ComboboxSelected>>", self.toggle_custom_angle)

        self.custom_angle_entry = tk.Entry(self, textvariable=self.custom_angle_var, state="disabled")
        self.custom_angle_entry.pack(padx=10, pady=5)

        tk.Label(self, text="Output Folder:").pack(anchor="w", padx=10, pady=5)
        output_frame = tk.Frame(self)
        output_frame.pack(padx=10, pady=5, fill="x")
        tk.Entry(output_frame, textvariable=self.output_dir_var, width=50).pack(side="left", expand=True, fill="x")
        tk.Button(output_frame, text="Browse", command=self.select_output_folder).pack(side="left", padx=5)

        # Add Preview and Rotate buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Preview", command=self.show_preview).pack(side="left", padx=5)
        tk.Button(button_frame, text="Rotate Videos", command=self.process_videos).pack(side="left", padx=5)

        # Frame for TQDM progress bar
        self.progress_frame = tk.Frame(self)
        self.progress_frame.pack(pady=20)

    def toggle_custom_angle(self, event=None):
        if self.rotation_var.get() == "custom":
            self.custom_angle_entry.config(state="normal")
        else:
            self.custom_angle_entry.config(state="disabled")

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Select Video Files", 
            filetypes=[("Video Files", "*.mp4 *.mov *.avi *.mkv")]
        )
        if files:
            self.input_files = list(files)
            messagebox.showinfo("Selected Files", f"{len(self.input_files)} file(s) selected.")

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_dir_var.set(folder)

    def show_preview(self):
        if not self.input_files:
            messagebox.showerror("Error", "Please select at least one video file.")
            return

        try:
            input_file = self.input_files[0]  # Preview only the first video
            rotation = self.rotation_var.get()
            custom_angle = self.custom_angle_var.get()

            # Extract rotated frame
            frame_path = extract_rotated_frame(input_file, rotation, custom_angle)

            # Load and resize image
            img = Image.open(frame_path)
            max_size = (400, 300)  # Max dimensions for preview
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            # Create preview window
            preview_window = tk.Toplevel(self)
            preview_window.title("Preview")
            preview_window.resizable(False, False)

            # Display image
            label = tk.Label(preview_window, image=photo)
            label.image = photo  # Keep a reference
            label.pack(padx=10, pady=10)

            # Clean up
            preview_window.protocol("WM_DELETE_WINDOW", lambda: [preview_window.destroy(), os.remove(frame_path)])

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate preview: {str(e)}")

    def process_videos(self):
        if not self.input_files:
            messagebox.showerror("Error", "Please select input video files.")
            return

        output_dir = self.output_dir_var.get()
        if not os.path.isdir(output_dir):
            messagebox.showerror("Error", "Invalid output directory.")
            return

        try:
            with tqdm(total=len(self.input_files), unit="video", gui=True) as pbar:
                for input_file in self.input_files:
                    rotate_video(input_file, self.rotation_var.get(), self.custom_angle_var.get(), output_dir)
                    pbar.update(1)
                    self.update_idletasks()

            messagebox.showinfo("Success", f"Rotated {len(self.input_files)} video(s) successfully!")

        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    try:
        get_ffmpeg_path()  # Check FFmpeg availability at startup
        app = FFRotateApp()
        app.mainloop()
    except RuntimeError as e:
        messagebox.showerror("Error", str(e))
        sys.exit(1)