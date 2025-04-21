# Installation + running
## UNIX
### Install
* **Pre-requisites** 
    - `conda`/`mamba` installation
    - `FFmpeg` installation
    - *Note: here it's assumed `FFmpeg` is readily accessible from the terminal with the `ffmpeg` command. You can test this by running `which ffmpeg` in your Terminal. If it it's not, consider installing it via [brew](https://brew.sh/)* 

* Install `ffrotate` environment by executing following in Terminal:
```sh
mamba env create -f env_unix.yml -y
mamba activate ffrotate
sh install_unix.sh
```

### Run
* Run by accessing the bundled app file in the `dist/` directory.

## Windows
### Install
* The only pre-requisite is a working version of `conda`/`mamba`, which is accessible via the PowerShell
    - [`miniforge` download](https://conda-forge.org/download/)
    - Enable `conda` access via PowerShell
    ```ps1
    mamba init powershell
    ```
* Install `ffrotate` environment by executing following in PowerShell:
    ```ps1
    mamba env create -f env_win.yml -y    
    ```
* (Optional) Diagnose whether conda ffmpeg in activated environment is active by running: 
    ```ps1
    (Get-Command ffmpeg).Path
    ```
* Move repo `ffrotate-main` to C-drive
### Run
* Right click `run_ffrotate.ps1` > "Run with PowerShell"
    - `Type "A" + [Enter]`
* (Optional) Create shortcut which can be placed anywhere you want; run same way as the previous method