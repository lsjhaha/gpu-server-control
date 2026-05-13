# GPU Server Control

[中文](README.zh-CN.md)

A small Windows desktop tool for managing remote NVIDIA GPU servers over SSH.

It focuses on two daily pain points in research labs and small GPU clusters:

- Quickly seeing which machines have idle GPUs.
- Moving large conda environments from one server to another without repeating manual packaging, copying, unpacking, and path-fixing steps.

The app is written in Python/Tkinter and can also be packaged as a portable Windows `.exe`.

## Features

- **Compact GPU dashboard**
  - Polls `nvidia-smi` on multiple Linux servers over SSH.
  - Shows one row per server and one progress bar per GPU.
  - Displays utilization and memory usage inside each GPU bar.
  - Highlights idle GPUs based on configurable utilization and memory thresholds.

- **Persistent SSH monitoring**
  - Reuses Paramiko SSH sessions for refreshes instead of reconnecting every time.
  - Supports SSH key login and optional password login.
  - Supports custom SSH ports.

- **Conda environment migration**
  - Packs a source environment with `conda-pack`.
  - Automatically installs `conda-pack` into the source conda base when missing.
  - Writes archives to a shared directory such as `/mnt/share/user/conda-packs`.
  - Unpacks on the target server into `<target conda root>/envs/<env name>`.
  - Runs `conda-unpack` after extraction.
  - Supports different source and target shared mount paths for the same storage.

- **Manage servers from the UI**
  - Add, update, and delete servers without editing JSON by hand.
  - Empty password means key-based login.
  - Non-empty password means password login.

- **GPU Queue Runner integration**
  - Bundles the `gpuq` queue runner script.
  - Installs or syncs `gpuq` to a selected remote server from the GUI.
  - Adds queued training jobs with working directory, command, GPUs, priority, queue name, and conda environment.
  - Starts, stops, and checks the remote daemon.
  - Shows queue status, job details, and logs.

- **English / Chinese UI**
  - The default interface language is English.
  - Switch to Chinese from `Settings`.

## Screenshots

Screenshots are not included in this repository yet. The main window has three tabs:

- `GPU Monitor`
- `Conda Migration`
- `Queue Runner`

## Requirements

For running from source on Windows:

- Python 3.10+
- Tkinter, usually bundled with Python or Miniconda on Windows
- `paramiko`

Install dependencies:

```powershell
pip install -r requirements.txt
```

For remote Linux servers:

- `bash`
- `tar`
- `base64`
- NVIDIA driver and `nvidia-smi` for GPU monitoring
- A working conda/miniconda installation for environment migration
- Network access from the source server to install `conda-pack` if it is not already installed
- `screen` if you use Queue Runner daemon jobs

## Quick Start

Clone the project and create your server config:

```powershell
copy servers.example.json servers.json
notepad servers.json
```

Run from source:

```powershell
python gpu_server_tool.py
```

Or use the launcher:

```powershell
run_gpu_server_tool.bat
```

The launcher tries to find a usable Python, verifies Tkinter and pip, installs dependencies from `requirements.txt`, and then starts the app. A `startup.log` file is written for troubleshooting.

## Portable Windows Build

Build a standalone executable:

```powershell
build_exe.bat
```

The generated app is placed under:

```text
dist/GPU_Server_Control.exe
```

Keep `servers.json` next to the executable:

```text
dist/
  GPU_Server_Control.exe
  servers.json
```

The packaged `.exe` includes Python and Python dependencies, so the target Windows machine does not need Python installed.

## Server Configuration

`servers.json` is an array of server objects:

```json
[
  {
    "alias": "gpu-01",
    "hostname": "192.168.1.101",
    "user": "your_user"
  },
  {
    "alias": "gpu-02",
    "hostname": "example.host.name",
    "user": "root",
    "port": 32761
  },
  {
    "alias": "gpu-03",
    "hostname": "192.168.1.103",
    "user": "your_user",
    "password": "optional_password"
  }
]
```

Fields:

- `alias`: Short display name. Must be unique.
- `hostname`: IP address or domain name.
- `user`: SSH username.
- `port`: Optional SSH port. Defaults to `22`.
- `password`: Optional. If omitted or empty, the app uses key-based login.

For key login, the default key path is:

```text
%USERPROFILE%\.ssh\id_ed25519
```

If that key is missing, Paramiko falls back to the SSH agent or default key lookup.

## Conda Migration Workflow

In the `Conda Migration` tab, choose:

- Source server
- Source miniconda root
- Environment name
- Target server
- Target miniconda root
- Target environment name
- Source shared directory
- Optional target shared directory

The app performs:

```text
1. SSH to source server.
2. Check <source conda root>/envs/<env>.
3. Ensure conda-pack is installed in source base.
4. Pack the env to <source shared dir>/conda-packs/*.tar.gz.
5. SSH to target server.
6. Map the archive path when source and target shared mount paths differ.
7. Extract to <target conda root>/envs/<target env>.
8. Run conda-unpack.
```

### Different Shared Mount Paths

Sometimes the same storage is mounted under different paths on different servers.

Example:

```text
Source shared dir: /mnt/share-a/user
Target shared dir: /mnt/share-b/user
```

In this case, fill both fields. The app rewrites the archive path before unpacking on the target.

## Queue Runner Workflow

The `Queue Runner` tab wraps the bundled `queue_runner/gpuq` command-line scheduler.

Typical use:

```text
1. Select a server.
2. Set a remote gpuq directory, for example /mnt/share/user/gpu-queue-runner.
3. Click Install/Sync. The app uploads gpuq, makes it executable, runs init, and runs doctor.
4. Add jobs from the GUI.
5. Start the daemon.
6. Refresh status or view logs.
```

Each queued job can specify:

- Working directory
- Command
- GPUs, for example `0,1,2,3` or `all`
- Queue name
- Priority
- Conda environment

`gpuq` starts jobs inside remote `screen` sessions and injects `CUDA_VISIBLE_DEVICES` by default.

## Important Notes

- Do not commit your real `servers.json` if it contains private IPs, usernames, passwords, or temporary cloud SSH hosts.
- Prefer SSH keys over storing passwords in `servers.json`.
- Very large conda environments may take a long time to pack or unpack.
- `conda-pack` may fail on severely inconsistent environments. The app uses `--ignore-missing-files` and `--ignore-editable-packages` to tolerate common research-environment issues, but a broken env may still need manual cleanup.
- The target conda root must already exist. This tool migrates environments; it does not install Miniconda on the target server.

## Troubleshooting

### `servers.json format error`

JSON does not allow a trailing comma after the last item:

```json
[
  {"alias": "gpu-01", "hostname": "192.168.1.101", "user": "me"}
]
```

Use the `Manage Servers` button in the app to avoid hand-editing mistakes.

### `Cannot find conda executable`

Check the miniconda root path. It should be the root directory, not the `bin` directory:

```text
/data/user/miniconda3
```

The app expects:

```text
/data/user/miniconda3/bin/conda
```

### `Archive is not visible on target server`

The target server cannot see the archive path produced on the source server. Common causes:

- Source and target do not share the same storage.
- The same storage is mounted at a different path on the target.
- Permissions prevent the target user from reading the archive.

Use the `Target shared` field when mount paths differ.

### GPU monitor says connection failed

Check:

- Hostname/IP and SSH port.
- Username.
- Whether the Windows machine can reach the server.
- Whether key or password login is configured correctly.
- Whether `nvidia-smi` exists on the remote server.

## Development

Run syntax check:

```powershell
python -m py_compile gpu_server_tool.py
```

Build executable:

```powershell
build_exe.bat
```

## License

No license has been selected yet. Add a license before publishing if you want others to reuse or modify the project.
