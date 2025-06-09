import os
import sys
import shutil
import subprocess
import time
from pathlib import Path
import tempfile
from tkinter import Tk, filedialog

import gradio as gr

def get_default_path():
    """Get OS-specific default output directory"""
    if sys.platform.startswith("win"):
        return os.path.join(os.path.expanduser("~"), "Videos", "rotated")
    else:
        return os.path.join(os.path.expanduser("~"), "Movies", "rotated")

def get_folder_path(folder_path: str = "") -> str:
    """
    Opens a folder dialog to select a folder, allowing the user to navigate and choose a folder.
    If no folder is selected, returns the initially provided folder path or an empty string if not provided.
    This function is conditioned to skip the folder dialog on macOS or if specific environment variables are present,
    indicating a possible automated environment where a dialog cannot be displayed.

    Parameters:
    - folder_path (str): The initial folder path or an empty string by default. Used as the fallback if no folder is selected.

    Returns:
    - str: The path of the folder selected by the user, or the initial `folder_path` if no selection is made.

    Raises:
    - TypeError: If `folder_path` is not a string.
    - EnvironmentError: If there's an issue accessing environment variables.
    - RuntimeError: If there's an issue initializing the folder dialog.

    Note:
    - The function checks the `ENV_EXCLUSION` list against environment variables to determine if the folder dialog should be skipped, aiming to prevent its appearance during automated operations.
    - The dialog will also be skipped on macOS (`sys.platform != "darwin"`) as a specific behavior adjustment.
    """
    # Validate parameter type
    if not isinstance(folder_path, str):
        raise TypeError("folder_path must be a string")

    try:
        root = Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        selected_folder = filedialog.askdirectory(initialdir=folder_path or ".")
        root.destroy()
        return selected_folder or folder_path
    except Exception as e:
        raise RuntimeError(f"Error initializing folder dialog: {e}") from e


def create_folder_ui(path="./"):
    with gr.Row():
        text_box = gr.Textbox(
            # label=f"Output directory (default: {get_default_path()})",
            label="Output directory (default:)",
            info="Path",
            lines=1,
            value=path,
        )
        button = gr.Button(value="\U0001f5c0", inputs=text_box, min_width=24)

        button.click(
            lambda: get_folder_path(text_box.value),
            outputs=[text_box],
        )

    return text_box, button

def check_ffmpeg():
    """Check if FFmpeg is installed and return its path."""
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path
    raise RuntimeError("FFmpeg is not installed or not in the system path.")


def rotate_video(input_video, rotation, custom_angle, output_dir):
    """Rotate a video losslessly using FFmpeg and save to output directory."""
    ffmpeg_path = check_ffmpeg()

    if hasattr(input_video, "name"):
        input_video = input_video.name  # Extract the actual file path

    base, ext = os.path.splitext(os.path.basename(input_video))
    output_filename = f"{base}_rotated{ext}"
    output_path = os.path.join(output_dir, output_filename)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Define rotation mapping for lossless transposition
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
        input_video,
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

    try:
        subprocess.run(
            command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        time.sleep(1)  # Ensure the file is completely written
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.decode()}"

    return output_path


def batch_rotate_videos(input_videos, rotation, custom_angle, output_dir, progress=gr.Progress(track_tqdm=True)):
    """Process multiple videos in batch with a progress bar and save to output directory."""
    if not input_videos:
        return "Error: No files uploaded."
    if rotation == "custom" and not custom_angle:
        return "Error: Please provide a custom angle."
    if not output_dir:
        return "Error: Please specify an output directory."

    # Validate output directory
    if not os.path.isdir(output_dir):
        Path(output_dir).mkdir()
        print(f"Creating {output_dir}")
        # return f"Error: {output_dir} is not a valid directory."

    with tempfile.TemporaryDirectory() as tmpdir:
        output_files = []
        total_videos = len(input_videos)

        for i, video in enumerate(input_videos):
            progress(i / total_videos)
            output_file = rotate_video(video, rotation, custom_angle, tmpdir)
            if isinstance(output_file, str) and output_file.startswith("Error"):
                output_files.append(output_file)
            else:
                output_files.append(output_file)
        for file in output_files:
            shutil.move(file, Path(output_dir) / Path(file).name)

    # return output_files
    print(f"Rotate videos saved to: {output_dir}")

def toggle_custom_angle(rotation):
    return gr.update(visible=(rotation == "custom"))

with gr.Blocks() as ffrotate_app:
    title = """
    <center> 
    <h1> FFrotate ⭕️ </h1>
    <b> Powered by ffmpeg </b>
    </center>
    """
    with gr.Blocks(theme="gradio/soft") as demo:
        with gr.Row():
            gr.HTML(title)

    input_videos = gr.Files(label="Input Videos")
    
    rotation = gr.Dropdown(
        ["90", "180", "270", "custom"], label="Rotation Angle (clockwise)"
    )
    custom_angle = gr.Number(label="Custom Angle (degrees)", visible=False)
    rotation.change(toggle_custom_angle, inputs=[rotation], outputs=[custom_angle])
    
    # output_btn = gr.Button(f"Select output directory (default: {get_default_path()})")
    # output_dir = output_btn.click(fn=get_folder_path()) 
    output_dir_textbox, select_dir_btn = create_folder_ui(path=get_default_path())
    output_dir = gr.State()  # Store the selected directory
    
    submit_btn = gr.Button("Rotate Videos")

    submit_btn.click(
        batch_rotate_videos,
        inputs=[input_videos, rotation, custom_angle, output_dir],
        # outputs=[output_videos],
    )

    # output_videos = gr.Files(label="Download Rotated Videos")

if __name__ == "__main__":
    ffrotate_app.launch()
