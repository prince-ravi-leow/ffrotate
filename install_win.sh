pyinstaller ffrotate_app.py ^
    --collect-data gradio ^
    --collect-data gradio_client ^
    --collect-data safehttpx ^
    --collect-data groovy ^
    --onefile ^
    --windowed ^
    --clean ^
    --additional-hooks-dir=.\hooks ^
    --runtime-hook=.\runtime_hook.py