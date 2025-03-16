"""Gradio app for rotating videos using ffmpeg"""

import gradio as gr
import subprocess
import os
import shutil
import time

def check_ffmpeg():
    """Check if FFmpeg is installed and return its path."""
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path
    raise RuntimeError("FFmpeg is not installed or not in the system path.")

def rotate_video(input_video, rotation, custom_angle):
    """Rotate a video losslessly using FFmpeg."""
    ffmpeg_path = check_ffmpeg()

    # Ensure input_video is a string
    if hasattr(input_video, "name"):
        input_video = input_video.name  # Extract the actual file path
    
    base, ext = os.path.splitext(input_video)
    output_video = f"{base}_rotated{ext}"
    
    # Define rotation mapping for lossless transposition
    rotation_map = {
        "90": "transpose=1",
        "180": "transpose=2,transpose=2",
        "270": "transpose=2"
    }
    
    if rotation != "custom":
        filter_option = rotation_map[rotation]
    else:
        filter_option = f"rotate={custom_angle}*(PI/180):bilinear=0"
    
    command = [
        ffmpeg_path, "-y", "-i", input_video, "-vf", filter_option,
        "-c:v", "libx264", "-crf", "0", "-preset", "ultrafast",
        output_video
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(1)  # Ensure the file is completely written
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.decode()}"
    
    return output_video

def batch_rotate_videos(input_videos, rotation, custom_angle):
    """Process multiple videos in batch."""
    if not input_videos:
        return "Error: No files uploaded."
    
    if rotation == "custom" and not custom_angle:
        return "Error: Please provide a custom angle."
    
    output_files = []
    for video in input_videos:
        output_files.append(rotate_video(video, rotation, custom_angle))
    
    return output_files  # Return list of rotated files

with gr.Blocks() as ffrotate_app:
    gr.Markdown("# Lossless Video Rotator (FFmpeg) - Batch Mode")
    input_videos = gr.Files(label="Upload Videos")  
    rotation = gr.Dropdown(["90", "180", "270", "custom"], label="Rotation Angle")
    custom_angle = gr.Number(label="Custom Angle (degrees)", visible=False)
    output_videos = gr.Files(label="Download Rotated Videos")  
    
    def toggle_custom_angle(rotation):
        return gr.update(visible=(rotation == "custom"))
    
    rotation.change(toggle_custom_angle, inputs=[rotation], outputs=[custom_angle])
    submit_btn = gr.Button("Rotate Videos")
    submit_btn.click(batch_rotate_videos, inputs=[input_videos, rotation, custom_angle], outputs=[output_videos])

if __name__ == "__main__":
    ffrotate_app.launch()
