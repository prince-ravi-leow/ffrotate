# Install FFmpeg 
**Note:** Special instructions required for Windows:
https://www.geeksforgeeks.org/installation-guide/how-to-install-ffmpeg-on-windows/ 

# Install conda environment
```sh
mamba install jlp-rotate python=3.13.2 uv -y
mamba activate jlp-rotate
uv pip install pillow tqdm pyinstaller
```

# Build app
```sh
pyinstaller --onefile --hidden-import PIL --hidden-import tqdm --noconsole --clean jlp-rotate.py
```