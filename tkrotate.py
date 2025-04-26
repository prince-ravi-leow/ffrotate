import os
import sys
import subprocess
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def get_default_output_path():
    if sys.platform.startswith("win"):
        return os.path.join(os.path.expanduser("~"), "Videos", "rotated")
    else:
        return os.path.join(os.path.expanduser("~"), "Movies", "rotated")


def rotate_video(input_path, rotation, custom_angle, output_dir):
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not found. Install it and add to PATH.")

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
        self.title("FFrotate ⭕️")
        self.geometry("600x400")

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

        tk.Button(self, text="Rotate Videos", command=self.process_videos).pack(pady=20)

    def toggle_custom_angle(self, event=None):
        if self.rotation_var.get() == "custom":
            self.custom_angle_entry.config(state="normal")
        else:
            self.custom_angle_entry.config(state="disabled")

    def select_files(self):
        files = filedialog.askopenfilenames(title="Select Video Files", filetypes=[("Video Files", "*.mp4 *.mov *.avi *.mkv")])
        if files:
            self.input_files = list(files)
            messagebox.showinfo("Selected Files", f"{len(self.input_files)} file(s) selected.")

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_dir_var.set(folder)

    def process_videos(self):
        if not self.input_files:
            messagebox.showerror("Error", "Please select input video files.")
            return

        output_dir = self.output_dir_var.get()
        if not os.path.isdir(output_dir):
            messagebox.showerror("Error", "Invalid output directory.")
            return

        try:
            for input_file in self.input_files:
                rotate_video(input_file, self.rotation_var.get(), self.custom_angle_var.get(), output_dir)
            messagebox.showinfo("Success", f"Rotated {len(self.input_files)} video(s) successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    app = FFRotateApp()
    app.mainloop()
