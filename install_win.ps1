Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
New-Item -ItemType Directory -Path "C:\Program Files\ffrotate"
Copy-Item "hooks" -Destination "C:\Program Files\ffrotate"
Copy-Item "runtime_hook.py" -Destination "C:\Program Files\ffrotate"
Copy-Item "ffrotate.py" -Destination "C:\Program Files\ffrotate"
Copy-Item "ffrotate_app.py" -Destination "C:\Program Files\ffrotate"
