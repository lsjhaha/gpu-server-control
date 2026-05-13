from __future__ import annotations

import csv
import base64
import datetime as dt
import json
import queue
import shutil
import subprocess
import threading
import time
import tkinter as tk
import sys
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox, ttk

try:
    import paramiko
except ImportError:  # pragma: no cover - handled at runtime in the UI
    paramiko = None


APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
SERVERS_FILE = APP_DIR / "servers.json"
SETTINGS_FILE = APP_DIR / "settings.json"
DEFAULT_IDENTITY_FILE = Path.home() / ".ssh" / "id_ed25519"
DEFAULT_SHARED_DIR = "/mnt/share/user"
DEFAULT_SOURCE_CONDA_ROOT = "/data/user/miniconda3"
DEFAULT_TARGET_CONDA_ROOT = "/data/user/miniconda3"
DEFAULT_QUEUE_RUNNER_DIR = "/mnt/share/user/gpu-queue-runner"
LOCAL_GPUQ_FILE = RESOURCE_DIR / "queue_runner" / "gpuq"
SSH_TIMEOUT_S = 8

TEXTS = {
    "en": {
        "subtitle": "SSH GPU monitoring, conda migration, and queue runner",
        "settings": "Settings",
        "servers": "Servers",
        "gpu_tab": "GPU Monitor",
        "conda_tab": "Conda Migration",
        "queue_tab": "Queue Runner",
        "free": "Free",
        "online": "Online",
        "busy": "Busy",
        "auto": "Auto",
        "every": "Every",
        "idle": "Idle",
        "refresh": "Refresh",
        "manage_servers": "Manage Servers",
        "not_refreshed": "Not refreshed yet",
        "preparing": "Preparing to connect to servers",
        "refreshing_gpu": "Refreshing GPU status...",
        "connecting": "Connecting",
        "connection_failed": "Connection failed",
        "free_count": "Free",
        "last_refresh": "Last refresh",
        "idle_hint": "Green means idle. Red means busy or memory usage is above the threshold.",
        "source_env": "Source Environment",
        "source_env_hint": "Pack an existing environment to a shared directory",
        "target_env": "Target Environment",
        "target_env_hint": "Unpack into target miniconda envs directory",
        "server": "Server",
        "conda_root": "miniconda root",
        "env_name": "Environment name",
        "target_env_name": "Target env name",
        "source_env_placeholder": "<source env>",
        "source_server_placeholder": "<source server>",
        "target_server_placeholder": "<target server>",
        "shared_dir": "Source shared",
        "target_shared": "Target shared",
        "target_shared_hint": "Blank = same as source",
        "overwrite": "Overwrite target env if it exists",
        "start_migration": "Start Migration",
        "preview": "Preview",
        "current_state": "Current State",
        "migration_log": "Migration Log",
        "clear": "Clear",
        "waiting": "Waiting",
        "queue_server": "Server",
        "queue_dir": "Remote gpuq dir",
        "install_sync": "Install/Sync",
        "add_job": "Add Job",
        "name": "Name",
        "cwd": "CWD",
        "command": "Command",
        "gpus": "GPUs",
        "queue": "Queue",
        "priority": "Priority",
        "conda_env": "Conda env",
        "add_to_queue": "Add to Queue",
        "operations": "Operations",
        "daemon_status": "Daemon Status",
        "start_daemon": "Start Daemon",
        "stop_daemon": "Stop Daemon",
        "queue_list": "Queue List",
        "daemon_logs": "Daemon Logs",
        "job_id": "Job ID",
        "show": "Show",
        "logs": "Logs",
        "retry": "Retry",
        "cancel": "Cancel",
        "queue_output": "Queue Runner Output",
        "ready": "Ready",
        "language": "Language",
        "save": "Save",
        "close": "Close",
    },
    "zh": {
        "subtitle": "SSH GPU 监控、conda 环境迁移与任务排队",
        "settings": "设置",
        "servers": "服务器",
        "gpu_tab": "GPU 监控",
        "conda_tab": "Conda 环境迁移",
        "queue_tab": "任务队列",
        "free": "空闲",
        "online": "在线",
        "busy": "占用",
        "auto": "自动",
        "every": "每",
        "idle": "空闲阈值",
        "refresh": "刷新",
        "manage_servers": "管理服务器",
        "not_refreshed": "尚未刷新",
        "preparing": "正在准备连接服务器",
        "refreshing_gpu": "正在刷新 GPU 状态...",
        "connecting": "正在连接",
        "connection_failed": "连接失败",
        "free_count": "空闲",
        "last_refresh": "最后刷新",
        "idle_hint": "绿色表示空闲，红色表示正在使用或显存超过阈值。",
        "source_env": "源环境",
        "source_env_hint": "将已有环境打包到共享目录",
        "target_env": "目标环境",
        "target_env_hint": "解压到目标 miniconda 的 envs 目录",
        "server": "服务器",
        "conda_root": "miniconda 根目录",
        "env_name": "环境名",
        "target_env_name": "目标环境名",
        "source_env_placeholder": "<源环境名>",
        "source_server_placeholder": "<源服务器>",
        "target_server_placeholder": "<目标服务器>",
        "shared_dir": "源共享目录",
        "target_shared": "目标共享目录",
        "target_shared_hint": "留空表示与源一致",
        "overwrite": "目标环境已存在时覆盖",
        "start_migration": "开始迁移",
        "preview": "流程预览",
        "current_state": "当前状态",
        "migration_log": "迁移日志",
        "clear": "清空",
        "waiting": "等待中",
        "queue_server": "服务器",
        "queue_dir": "远端 gpuq 目录",
        "install_sync": "安装/同步",
        "add_job": "添加任务",
        "name": "名称",
        "cwd": "运行目录",
        "command": "命令",
        "gpus": "GPU",
        "queue": "队列",
        "priority": "优先级",
        "conda_env": "Conda 环境",
        "add_to_queue": "加入队列",
        "operations": "操作",
        "daemon_status": "守护状态",
        "start_daemon": "启动守护",
        "stop_daemon": "停止守护",
        "queue_list": "队列列表",
        "daemon_logs": "守护日志",
        "job_id": "任务 ID",
        "show": "查看",
        "logs": "日志",
        "retry": "重试",
        "cancel": "取消",
        "queue_output": "队列输出",
        "ready": "就绪",
        "language": "语言",
        "save": "保存",
        "close": "关闭",
    },
}

BG = "#f5f7fb"
SURFACE = "#ffffff"
SURFACE_SOFT = "#eef3f8"
TEXT = "#17202a"
MUTED = "#607080"
BORDER = "#d7dee8"
GREEN = "#1f8a4c"
GREEN_BG = "#e8f6ef"
RED = "#bd3c2f"
RED_BG = "#fdecea"
AMBER = "#9a6500"
AMBER_BG = "#fff4d8"
BLUE = "#2868c7"
BLUE_BG = "#e8f0ff"
DARK = "#101923"


@dataclass(frozen=True)
class Server:
    alias: str
    hostname: str
    user: str
    port: int = 22
    ssh_host: str = ""
    password: str = ""

    @property
    def target(self) -> str:
        return f"{self.user}@{self.hostname}"

    @property
    def display_target(self) -> str:
        target = f"{self.user}@{self.hostname}:{self.port}"
        if self.ssh_host:
            return f"{self.ssh_host} -> {target}"
        return target

    @property
    def label(self) -> str:
        port = "" if self.port == 22 else f":{self.port}"
        # return f"{self.alias} ({self.hostname}{port})"
        return f"{self.alias}"  # 只显示别名


@dataclass
class GpuInfo:
    index: str
    uuid: str
    name: str
    mem_total_mb: int
    mem_used_mb: int
    util_percent: int
    temperature_c: int | None

    def is_free(self, util_threshold: int, mem_threshold_mb: int) -> bool:
        return self.util_percent <= util_threshold and self.mem_used_mb <= mem_threshold_mb

    @property
    def mem_percent(self) -> int:
        if self.mem_total_mb <= 0:
            return 0
        return min(100, round(self.mem_used_mb * 100 / self.mem_total_mb))


def load_servers() -> list[Server]:
    if not SERVERS_FILE.exists():
        example_file = APP_DIR / "servers.example.json"
        if example_file.exists():
            return [
                Server(alias="example-gpu-01", hostname="192.168.1.101", user="your_user"),
            ]
        raise FileNotFoundError(f"找不到服务器配置文件: {SERVERS_FILE}")
    try:
        data = json.loads(SERVERS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"servers.json format error: {exc.msg} at line {exc.lineno}, column {exc.colno}.\n"
            "Tip: do not leave a comma after the last server item."
        ) from exc
    servers: list[Server] = []
    for item in data:
        servers.append(
            Server(
                alias=str(item["alias"]).strip(),
                hostname=str(item["hostname"]).strip(),
                user=str(item["user"]).strip(),
                port=int(item.get("port", 22)),
                ssh_host=str(item.get("ssh_host", "")).strip(),
                password=str(item.get("password", "")),
            )
        )
    return servers


def save_servers(servers: list[Server]) -> None:
    data = [
        {
            "alias": server.alias,
            "hostname": server.hostname,
            "user": server.user,
            **({"port": server.port} if server.port != 22 else {}),
            **({"password": server.password} if server.password else {}),
        }
        for server in servers
    ]
    tmp = SERVERS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(SERVERS_FILE)


def load_app_settings() -> dict[str, str]:
    if not SETTINGS_FILE.exists():
        return {"language": "en"}
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"language": "en"}
    language = str(data.get("language", "en"))
    return {"language": language if language in TEXTS else "en"}


def save_app_settings(settings: dict[str, str]) -> None:
    SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ssh_binary() -> str:
    path = shutil.which("ssh")
    if not path:
        raise RuntimeError("找不到 ssh。请在 Windows 中启用 OpenSSH Client。")
    return path


def ssh_args(server: Server, timeout_s: int = SSH_TIMEOUT_S) -> list[str]:
    if server.password:
        raise RuntimeError("This server is configured for password login. Install/use paramiko for password-based commands.")
    args = [
        ssh_binary(),
        "-o",
        "BatchMode=yes",
        "-o",
        f"ConnectTimeout={timeout_s}",
    ]
    if DEFAULT_IDENTITY_FILE.exists():
        args.extend(["-i", str(DEFAULT_IDENTITY_FILE), "-o", "IdentitiesOnly=yes"])
    if server.port != 22:
        args.extend(["-p", str(server.port)])
    args.append(server.target)
    return args


def connect_ssh_client(server: Server):
    if paramiko is None:
        raise RuntimeError("paramiko is not installed")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs = {
        "hostname": server.hostname,
        "username": server.user,
        "port": server.port,
        "timeout": SSH_TIMEOUT_S,
        "banner_timeout": SSH_TIMEOUT_S,
        "auth_timeout": SSH_TIMEOUT_S,
    }
    if server.password:
        kwargs["password"] = server.password
        kwargs["look_for_keys"] = False
        kwargs["allow_agent"] = False
    elif DEFAULT_IDENTITY_FILE.exists():
        kwargs["key_filename"] = str(DEFAULT_IDENTITY_FILE)
        kwargs["look_for_keys"] = False
        kwargs["allow_agent"] = False
    else:
        kwargs["look_for_keys"] = True
        kwargs["allow_agent"] = True
    client.connect(**kwargs)
    transport = client.get_transport()
    if transport is not None:
        transport.set_keepalive(20)
    return client


def run_remote_script(server: Server, script: str, timeout_s: int = 120) -> subprocess.CompletedProcess[str]:
    if paramiko is not None:
        client = connect_ssh_client(server)
        try:
            command = "bash -s"
            stdin, stdout, stderr = client.exec_command(command, timeout=None)
            stdout.channel.settimeout(None)
            stdin.write(script.replace("\r\n", "\n").replace("\r", "\n"))
            stdin.channel.shutdown_write()
            out = stdout.read().decode("utf-8", "replace")
            err = stderr.read().decode("utf-8", "replace")
            code = stdout.channel.recv_exit_status()
            return subprocess.CompletedProcess(command, code, out, err)
        finally:
            client.close()
    args = ssh_args(server, min(timeout_s, SSH_TIMEOUT_S)) + ["bash", "-s"]
    script_bytes = script.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    proc = subprocess.run(
        args,
        input=script_bytes,
        capture_output=True,
        timeout=timeout_s,
        check=False,
    )
    return subprocess.CompletedProcess(
        proc.args,
        proc.returncode,
        proc.stdout.decode("utf-8", "replace"),
        proc.stderr.decode("utf-8", "replace"),
    )


class PersistentSshPool:
    def __init__(self) -> None:
        self._clients: dict[str, object] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._guard = threading.Lock()

    def close_all(self) -> None:
        with self._guard:
            clients = list(self._clients.values())
            self._clients.clear()
            self._locks.clear()
        for client in clients:
            try:
                client.close()
            except Exception:
                pass

    def run(self, server: Server, command: str, timeout_s: int = 20) -> subprocess.CompletedProcess[str]:
        if paramiko is None:
            return run_remote_script(server, command, timeout_s=timeout_s)
        lock = self._lock_for(server)
        with lock:
            client = self._client_for(server)
            try:
                return self._exec(client, command, timeout_s)
            except Exception:
                self._drop(server)
                client = self._client_for(server)
                return self._exec(client, command, timeout_s)

    def _key(self, server: Server) -> str:
        return server.alias

    def _lock_for(self, server: Server) -> threading.Lock:
        key = self._key(server)
        with self._guard:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]

    def _client_for(self, server: Server):
        key = self._key(server)
        with self._guard:
            client = self._clients.get(key)
        if client is not None and self._is_alive(client):
            return client

        if paramiko is None:
            raise RuntimeError("paramiko is not installed")
        client = connect_ssh_client(server)
        with self._guard:
            self._clients[key] = client
        return client

    def _drop(self, server: Server) -> None:
        key = self._key(server)
        with self._guard:
            client = self._clients.pop(key, None)
        if client is not None:
            try:
                client.close()
            except Exception:
                pass

    def _is_alive(self, client: object) -> bool:
        try:
            transport = client.get_transport()
            return bool(transport and transport.is_active())
        except Exception:
            return False

    def _exec(self, client: object, command: str, timeout_s: int) -> subprocess.CompletedProcess[str]:
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout_s)
        try:
            stdin.close()
        except Exception:
            pass
        out = stdout.read().decode("utf-8", "replace")
        err = stderr.read().decode("utf-8", "replace")
        code = stdout.channel.recv_exit_status()
        return subprocess.CompletedProcess(command, code, out, err)


def parse_int(value: str, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_gpu_csv(text: str) -> list[GpuInfo]:
    rows = csv.reader(line for line in text.splitlines() if line.strip())
    gpus: list[GpuInfo] = []
    for row in rows:
        if len(row) < 7:
            continue
        index, uuid, name, mem_total, mem_used, util, temp = [cell.strip() for cell in row[:7]]
        temperature = None if temp in {"", "[Not Supported]", "N/A"} else parse_int(temp, 0)
        gpus.append(
            GpuInfo(
                index=index,
                uuid=uuid,
                name=name,
                mem_total_mb=parse_int(mem_total),
                mem_used_mb=parse_int(mem_used),
                util_percent=parse_int(util),
                temperature_c=temperature,
            )
        )
    return gpus


def query_gpus(server: Server, pool: PersistentSshPool | None = None) -> tuple[list[GpuInfo], str]:
    command = "nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.used,utilization.gpu,temperature.gpu --format=csv,noheader,nounits"
    proc = pool.run(server, command, timeout_s=20) if pool else run_remote_script(server, command, timeout_s=20)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout).strip()
        return [], err or f"ssh 退出码 {proc.returncode}"
    return parse_gpu_csv(proc.stdout), ""


def shell_single_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def pack_script(conda_root: str, env_name: str, shared_dir: str) -> str:
    return f"""set -euo pipefail
CONDA_ROOT={shell_single_quote(conda_root)}
ENV_NAME={shell_single_quote(env_name)}
SHARED_DIR={shell_single_quote(shared_dir)}
PACK_DIR="$SHARED_DIR/conda-packs"
ENV_DIR="$CONDA_ROOT/envs/$ENV_NAME"
mkdir -p "$PACK_DIR"

if [ ! -x "$CONDA_ROOT/bin/conda" ]; then
  echo "Cannot find conda executable: $CONDA_ROOT/bin/conda" >&2
  exit 10
fi

if [ ! -d "$ENV_DIR" ]; then
  echo "Cannot find conda env directory: $ENV_DIR" >&2
  echo "Available envs under $CONDA_ROOT/envs:" >&2
  ls -1 "$CONDA_ROOT/envs" >&2 || true
  exit 13
fi

if [ -x "$CONDA_ROOT/bin/conda-pack" ]; then
  PACK_CMD="$CONDA_ROOT/bin/conda-pack"
elif "$CONDA_ROOT/bin/python" -c "import conda_pack" >/dev/null 2>&1; then
  PACK_CMD="$CONDA_ROOT/bin/python -m conda_pack"
else
  echo "conda-pack is not installed in base. Installing it automatically..."
  if "$CONDA_ROOT/bin/python" -m pip --version >/dev/null 2>&1; then
    "$CONDA_ROOT/bin/python" -m pip install conda-pack || "$CONDA_ROOT/bin/python" -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple conda-pack
  else
    "$CONDA_ROOT/bin/conda" install -y -n base -c conda-forge conda-pack
  fi
  if [ -x "$CONDA_ROOT/bin/conda-pack" ]; then
    PACK_CMD="$CONDA_ROOT/bin/conda-pack"
  elif "$CONDA_ROOT/bin/python" -c "import conda_pack" >/dev/null 2>&1; then
    PACK_CMD="$CONDA_ROOT/bin/python -m conda_pack"
  else
    echo "Failed to install conda-pack automatically. Install it manually in base and retry." >&2
    exit 12
  fi
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
HOST="$(hostname -s 2>/dev/null || hostname)"
ARCHIVE="$PACK_DIR/${{ENV_NAME}}_${{HOST}}_${{STAMP}}.tar.gz"
echo "Packing $ENV_NAME to $ARCHIVE"
$PACK_CMD -p "$ENV_DIR" -o "$ARCHIVE" --force --ignore-missing-files --ignore-editable-packages
chmod a+r "$ARCHIVE" || true
echo "__ARCHIVE__=$ARCHIVE"
"""


def unpack_script(
    conda_root: str,
    target_env_name: str,
    archive_path: str,
    overwrite: bool,
    source_shared_dir: str = "",
    target_shared_dir: str = "",
) -> str:
    overwrite_flag = "1" if overwrite else "0"
    return f"""set -euo pipefail
CONDA_ROOT={shell_single_quote(conda_root)}
TARGET_ENV_NAME={shell_single_quote(target_env_name)}
ARCHIVE={shell_single_quote(archive_path)}
SOURCE_SHARED_DIR={shell_single_quote(source_shared_dir)}
TARGET_SHARED_DIR={shell_single_quote(target_shared_dir)}
OVERWRITE={overwrite_flag}
if [ -n "$SOURCE_SHARED_DIR" ] && [ -n "$TARGET_SHARED_DIR" ] && [ "$SOURCE_SHARED_DIR" != "$TARGET_SHARED_DIR" ]; then
  case "$ARCHIVE" in
    "$SOURCE_SHARED_DIR"/*)
      ARCHIVE="$TARGET_SHARED_DIR/${{ARCHIVE#"$SOURCE_SHARED_DIR"/}}"
      ;;
  esac
fi
DEST="$CONDA_ROOT/envs/$TARGET_ENV_NAME"

if [ ! -x "$CONDA_ROOT/bin/conda" ]; then
  echo "Cannot find conda executable: $CONDA_ROOT/bin/conda" >&2
  exit 20
fi
if [ ! -f "$ARCHIVE" ]; then
  echo "Archive is not visible on target server: $ARCHIVE" >&2
  exit 21
fi

if [ -e "$DEST" ]; then
  if [ "$OVERWRITE" = "1" ]; then
    rm -rf "$DEST"
  else
    echo "Target env already exists: $DEST" >&2
    echo "Enable overwrite if you really want to replace it." >&2
    exit 22
  fi
fi

mkdir -p "$DEST"
echo "Unpacking $ARCHIVE to $DEST"
tar -xzf "$ARCHIVE" -C "$DEST"

if [ -x "$DEST/bin/conda-unpack" ]; then
  PATH="$DEST/bin:$PATH" "$DEST/bin/conda-unpack"
else
  echo "Warning: conda-unpack was not found. The env may still contain old absolute paths." >&2
fi

echo "__DEST__=$DEST"
"""


def gpuq_install_script(remote_dir: str, payload_b64: str) -> str:
    return f"""set -euo pipefail
REMOTE_DIR={shell_single_quote(remote_dir)}
PAYLOAD={shell_single_quote(payload_b64)}
mkdir -p "$REMOTE_DIR"
printf '%s' "$PAYLOAD" | base64 -d > "$REMOTE_DIR/gpuq"
chmod +x "$REMOTE_DIR/gpuq"
cd "$REMOTE_DIR"
./gpuq init
./gpuq doctor
echo "__GPUQ_DIR__=$REMOTE_DIR"
"""


def gpuq_command_script(remote_dir: str, args: list[str]) -> str:
    quoted_args = " ".join(shell_single_quote(arg) for arg in args)
    return f"""set -euo pipefail
REMOTE_DIR={shell_single_quote(remote_dir)}
if [ ! -x "$REMOTE_DIR/gpuq" ]; then
  echo "gpuq is not installed or executable at: $REMOTE_DIR/gpuq" >&2
  exit 80
fi
cd "$REMOTE_DIR"
./gpuq {quoted_args}
"""


class ScrollFrame(tk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, bg=BG)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=BG)
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_inner_configure(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        if self.winfo_containing(event.x_root, event.y_root):
            bbox = self.canvas.bbox("all")
            if not bbox:
                return
            content_height = bbox[3] - bbox[1]
            if content_height <= self.canvas.winfo_height():
                self.canvas.yview_moveto(0)
                return
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class ServerSettingsWindow(tk.Toplevel):
    def __init__(self, app: "App", servers: list[Server]) -> None:
        super().__init__(app)
        self.app = app
        self.title("Server Settings")
        self.geometry("620x420")
        self.minsize(600, 400)
        self.configure(bg=BG)
        self.servers = list(servers)
        self.alias_var = tk.StringVar()
        self.hostname_var = tk.StringVar()
        self.port_var = tk.StringVar(value="22")
        self.user_var = tk.StringVar(value="your_user")
        self.password_var = tk.StringVar()

        self.transient(app)
        self._build()
        self._refresh_list()

    def _build(self) -> None:
        body = tk.Frame(self, bg=BG, padx=12, pady=12)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(1, weight=1)

        tk.Label(body, text="Servers", bg=BG, fg=TEXT, font=("Segoe UI", 13, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(body, text="Edit alias, host, and user for GPU polling.", bg=BG, fg=MUTED).grid(row=0, column=1, sticky="e")

        list_frame = tk.Frame(body, bg=SURFACE, bd=1, relief="solid", padx=8, pady=8)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(10, 10))
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        self.listbox = tk.Listbox(list_frame, height=12, exportselection=False)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        form = tk.Frame(body, bg=SURFACE, bd=1, relief="solid", padx=12, pady=12)
        form.grid(row=1, column=1, sticky="nsew", pady=(10, 10))
        form.grid_columnconfigure(1, weight=1)

        tk.Label(form, text="Alias", bg=SURFACE, fg=MUTED).grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(form, textvariable=self.alias_var).grid(row=0, column=1, sticky="ew", pady=6)
        tk.Label(form, text="Host/IP", bg=SURFACE, fg=MUTED).grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(form, textvariable=self.hostname_var).grid(row=1, column=1, sticky="ew", pady=6)
        tk.Label(form, text="Port", bg=SURFACE, fg=MUTED).grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(form, textvariable=self.port_var).grid(row=2, column=1, sticky="ew", pady=6)
        tk.Label(form, text="User", bg=SURFACE, fg=MUTED).grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(form, textvariable=self.user_var).grid(row=3, column=1, sticky="ew", pady=6)
        tk.Label(form, text="Password", bg=SURFACE, fg=MUTED).grid(row=4, column=0, sticky="w", pady=6)
        ttk.Entry(form, textvariable=self.password_var, show="*").grid(row=4, column=1, sticky="ew", pady=6)
        tk.Label(form, text="Leave blank to use SSH key.", bg=SURFACE, fg=MUTED, font=("Segoe UI", 8)).grid(row=5, column=1, sticky="w")

        actions = tk.Frame(form, bg=SURFACE)
        actions.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(actions, text="Add", command=self._add).pack(side="left")
        ttk.Button(actions, text="Update", command=self._update).pack(side="left", padx=6)
        ttk.Button(actions, text="Delete", command=self._delete).pack(side="left")
        ttk.Button(actions, text="Clear", command=self._clear).pack(side="left", padx=6)

        bottom = tk.Frame(body, bg=BG)
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew")
        ttk.Button(bottom, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(bottom, text="Save && Apply", command=self._save).pack(side="right", padx=8)

    def _refresh_list(self) -> None:
        self.listbox.delete(0, "end")
        for server in self.servers:
            auth = "password" if server.password else "key"
            self.listbox.insert("end", f"{server.alias}   {server.user}@{server.hostname}:{server.port}   [{auth}]")

    def _selected_index(self) -> int | None:
        selection = self.listbox.curselection()
        if not selection:
            return None
        return int(selection[0])

    def _on_select(self, _event: tk.Event) -> None:
        idx = self._selected_index()
        if idx is None:
            return
        server = self.servers[idx]
        self.alias_var.set(server.alias)
        self.hostname_var.set(server.hostname)
        self.port_var.set(str(server.port))
        self.user_var.set(server.user)
        self.password_var.set(server.password)

    def _read_form(self) -> Server | None:
        alias = self.alias_var.get().strip()
        hostname = self.hostname_var.get().strip()
        port_text = self.port_var.get().strip() or "22"
        user = self.user_var.get().strip()
        password = self.password_var.get()
        if not alias or not hostname or not user:
            messagebox.showerror("Missing Field", "Alias, host/IP, and user are required.", parent=self)
            return None
        if any(ch.isspace() for ch in alias):
            messagebox.showerror("Invalid Alias", "Alias cannot contain whitespace.", parent=self)
            return None
        try:
            port = int(port_text)
        except ValueError:
            messagebox.showerror("Invalid Port", "Port must be a number.", parent=self)
            return None
        if port < 1 or port > 65535:
            messagebox.showerror("Invalid Port", "Port must be between 1 and 65535.", parent=self)
            return None
        return Server(alias=alias, hostname=hostname, port=port, user=user, password=password)

    def _add(self) -> None:
        server = self._read_form()
        if server is None:
            return
        if any(existing.alias == server.alias for existing in self.servers):
            messagebox.showerror("Duplicate Alias", "Alias already exists. Use Update instead.", parent=self)
            return
        self.servers.append(server)
        self._refresh_list()
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(len(self.servers) - 1)

    def _update(self) -> None:
        idx = self._selected_index()
        if idx is None:
            messagebox.showinfo("No Selection", "Select a server to update.", parent=self)
            return
        server = self._read_form()
        if server is None:
            return
        if any(i != idx and existing.alias == server.alias for i, existing in enumerate(self.servers)):
            messagebox.showerror("Duplicate Alias", "Alias already exists.", parent=self)
            return
        self.servers[idx] = server
        self._refresh_list()
        self.listbox.selection_set(idx)

    def _delete(self) -> None:
        idx = self._selected_index()
        if idx is None:
            messagebox.showinfo("No Selection", "Select a server to delete.", parent=self)
            return
        del self.servers[idx]
        self._refresh_list()
        self._clear()

    def _clear(self) -> None:
        self.alias_var.set("")
        self.hostname_var.set("")
        self.port_var.set("22")
        self.user_var.set("your_user")
        self.password_var.set("")
        self.listbox.selection_clear(0, "end")

    def _save(self) -> None:
        if not self.servers:
            messagebox.showerror("No Servers", "Add at least one server.", parent=self)
            return
        self.app.apply_server_settings(self.servers)
        self.destroy()


class AppSettingsWindow(tk.Toplevel):
    def __init__(self, app: "App") -> None:
        super().__init__(app)
        self.app = app
        self.title(app.tr("settings"))
        self.geometry("360x160")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.language_var = tk.StringVar(value="中文" if app.language == "zh" else "English")
        self.transient(app)
        self._build()

    def _build(self) -> None:
        body = tk.Frame(self, bg=BG, padx=16, pady=16)
        body.pack(fill="both", expand=True)
        tk.Label(body, text=self.app.tr("language"), bg=BG, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Combobox(body, values=["English", "中文"], textvariable=self.language_var, state="readonly").pack(fill="x", pady=(8, 16))
        buttons = tk.Frame(body, bg=BG)
        buttons.pack(fill="x")
        ttk.Button(buttons, text=self.app.tr("close"), command=self.destroy).pack(side="right")
        ttk.Button(buttons, text=self.app.tr("save"), command=self._save).pack(side="right", padx=(0, 8))

    def _save(self) -> None:
        self.app.set_language("zh" if self.language_var.get() == "中文" else "en")
        self.destroy()


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("GPU Server Control")
        self.geometry("1260x820")
        self.minsize(1080, 700)
        self.configure(bg=BG)

        self.app_settings = load_app_settings()
        self.language = self.app_settings.get("language", "en")
        self.servers = load_servers()
        self.server_by_label = {server.label: server for server in self.servers}
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.refresh_running = False
        self.migration_running = False

        self.auto_refresh = tk.BooleanVar(value=True)
        self.refresh_interval_s = tk.IntVar(value=15)
        self.util_threshold = tk.IntVar(value=5)
        self.mem_threshold_mb = tk.IntVar(value=1000)
        self.last_refresh_at = tk.StringVar(value="尚未刷新")
        self.summary_free_var = tk.StringVar(value="-")
        self.summary_online_var = tk.StringVar(value="-")
        self.summary_busy_var = tk.StringVar(value="-")
        self.summary_hint_var = tk.StringVar(value="正在准备连接服务器")
        self.status_vars: dict[str, dict[str, tk.StringVar]] = {}
        self.gpu_frames: dict[str, tk.Frame] = {}
        self.count_labels: dict[str, tk.Label] = {}
        self.gpu_widgets: dict[str, dict[str, dict[str, object]]] = {}
        self.queue_running = False
        self.ssh_pool = PersistentSshPool()
        self.settings_window: tk.Toplevel | None = None
        self.app_settings_window: tk.Toplevel | None = None

        self._configure_style()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(200, self._poll_queue)
        self.after(500, self.refresh_gpus)
        self.after(1000, self._auto_refresh_tick)

    def tr(self, key: str) -> str:
        return TEXTS.get(self.language, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))

    def set_language(self, language: str) -> None:
        if language not in TEXTS:
            language = "en"
        self.language = language
        self.app_settings["language"] = language
        save_app_settings(self.app_settings)
        self._rebuild_tabs()

    def _on_close(self) -> None:
        self.ssh_pool.close_all()
        self.destroy()

    def open_server_settings(self) -> None:
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return
        self.settings_window = ServerSettingsWindow(self, self.servers)

    def open_app_settings(self) -> None:
        if self.app_settings_window is not None and self.app_settings_window.winfo_exists():
            self.app_settings_window.lift()
            return
        self.app_settings_window = AppSettingsWindow(self)

    def apply_server_settings(self, servers: list[Server]) -> None:
        save_servers(servers)
        self.ssh_pool.close_all()
        self.servers = load_servers()
        self.server_by_label = {server.label: server for server in self.servers}
        self.status_vars.clear()
        self.gpu_frames.clear()
        self.count_labels.clear()
        self.gpu_widgets.clear()
        self.summary_free_var.set("-")
        self.summary_online_var.set("-")
        self.summary_busy_var.set("-")
        self.last_refresh_at.set("Not refreshed yet")

        self._rebuild_tabs()
        self.refresh_gpus()

    def _rebuild_tabs(self) -> None:
        current = self.notebook.index(self.notebook.select()) if hasattr(self, "notebook") else 0
        if hasattr(self, "main_frame"):
            self.main_frame.destroy()
        self.status_vars.clear()
        self.gpu_frames.clear()
        self.count_labels.clear()
        self.gpu_widgets.clear()
        self.summary_free_var.set("-")
        self.summary_online_var.set("-")
        self.summary_busy_var.set("-")
        self.last_refresh_at.set(self.tr("not_refreshed"))
        self.summary_hint_var.set(self.tr("preparing"))
        self._build_ui()
        self.notebook.select(min(current, 2))

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Microsoft YaHei UI", 10), background=BG, foreground=TEXT)
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 9), font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("Muted.TLabel", background=BG, foreground=MUTED)
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Microsoft YaHei UI", 22, "bold"))
        style.configure("Section.TLabel", background=BG, foreground=TEXT, font=("Microsoft YaHei UI", 13, "bold"))
        style.configure("Card.TFrame", background=SURFACE, relief="solid", borderwidth=1)
        style.configure("Card.TLabel", background=SURFACE, foreground=TEXT)
        style.configure("CardMuted.TLabel", background=SURFACE, foreground=MUTED)
        style.configure("Accent.TButton", font=("Microsoft YaHei UI", 10, "bold"), padding=(14, 8))
        style.configure("TButton", padding=(10, 6))
        style.configure("TEntry", padding=6)
        style.configure("Horizontal.TProgressbar", troughcolor=SURFACE_SOFT, bordercolor=BORDER, background=BLUE)

    def _build_ui(self) -> None:
        self.main_frame = tk.Frame(self, bg=BG)
        self.main_frame.pack(fill="both", expand=True)
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=18, pady=(16, 8))
        header.grid_columnconfigure(1, weight=1)
        ttk.Label(header, text="GPU Server Control", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text=self.tr("subtitle"), style="Muted.TLabel").grid(row=0, column=1, sticky="w", padx=(16, 12), pady=(9, 0))
        ttk.Button(header, text=self.tr("servers"), command=self.open_server_settings).grid(row=0, column=2, sticky="e", pady=(4, 0), padx=(0, 8))
        ttk.Button(header, text=self.tr("settings"), command=self.open_app_settings).grid(row=0, column=3, sticky="e", pady=(4, 0))

        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        self.notebook = notebook
        self.monitor_tab = tk.Frame(notebook, bg=BG)
        self.migrate_tab = tk.Frame(notebook, bg=BG)
        self.queue_tab = tk.Frame(notebook, bg=BG)
        notebook.add(self.monitor_tab, text=self.tr("gpu_tab"))
        notebook.add(self.migrate_tab, text=self.tr("conda_tab"))
        notebook.add(self.queue_tab, text=self.tr("queue_tab"))
        self._build_monitor_tab()
        self._build_migrate_tab()
        self._build_queue_tab()
        self._bind_preview_updates()

    def _build_monitor_tab(self) -> None:
        top = tk.Frame(self.monitor_tab, bg=BG)
        top.pack(fill="x", pady=(8, 6))

        stats = tk.Frame(top, bg=BG)
        stats.pack(side="left", fill="x", expand=True)
        self._summary_tile(stats, self.tr("free"), self.summary_free_var, GREEN_BG, GREEN).pack(side="left", padx=(0, 6))
        self._summary_tile(stats, self.tr("online"), self.summary_online_var, BLUE_BG, BLUE).pack(side="left", padx=6)
        self._summary_tile(stats, self.tr("busy"), self.summary_busy_var, AMBER_BG, AMBER).pack(side="left", padx=6)

        controls = tk.Frame(top, bg=SURFACE, bd=1, relief="solid", padx=8, pady=6)
        controls.pack(side="right")
        ttk.Checkbutton(controls, text=self.tr("auto"), variable=self.auto_refresh).grid(row=0, column=0, padx=(0, 8))
        ttk.Label(controls, text=self.tr("every")).grid(row=0, column=1)
        ttk.Spinbox(controls, from_=5, to=300, width=4, textvariable=self.refresh_interval_s).grid(row=0, column=2, padx=(4, 8))
        ttk.Label(controls, text="s").grid(row=0, column=3, padx=(0, 10))
        ttk.Label(controls, text=self.tr("idle")).grid(row=0, column=4)
        ttk.Spinbox(controls, from_=0, to=100, width=4, textvariable=self.util_threshold).grid(row=0, column=5, padx=(4, 2))
        ttk.Label(controls, text="% /").grid(row=0, column=6)
        ttk.Spinbox(controls, from_=0, to=80000, increment=100, width=6, textvariable=self.mem_threshold_mb).grid(row=0, column=7, padx=(4, 2))
        ttk.Label(controls, text="MB").grid(row=0, column=8, padx=(0, 10))
        ttk.Button(controls, text=self.tr("refresh"), command=self.refresh_gpus).grid(row=0, column=9)
        ttk.Button(controls, text=self.tr("manage_servers"), command=self.open_server_settings).grid(row=0, column=10, padx=(8, 0))

        hint_row = tk.Frame(self.monitor_tab, bg=BG)
        hint_row.pack(fill="x", pady=(0, 4))
        ttk.Label(hint_row, textvariable=self.summary_hint_var, style="Muted.TLabel").pack(side="left")
        ttk.Label(hint_row, textvariable=self.last_refresh_at, style="Muted.TLabel").pack(side="right")

        self.scroll = ScrollFrame(self.monitor_tab)
        self.scroll.pack(fill="both", expand=True)
        for idx, server in enumerate(self.servers):
            row = tk.Frame(self.scroll.inner, bg=SURFACE, bd=1, relief="solid", padx=8, pady=5)
            row.grid(row=idx, column=0, sticky="ew", padx=2, pady=3)
            row.grid_columnconfigure(1, weight=1)
            self.scroll.inner.grid_columnconfigure(0, weight=1)

            host_var = tk.StringVar(value=server.label)
            count_var = tk.StringVar(value="waiting")
            status_var = tk.StringVar(value=f"SSH: {server.display_target}")

            left = tk.Frame(row, bg=SURFACE, width=150)
            left.grid(row=0, column=0, sticky="nsw", padx=(0, 8))
            left.grid_propagate(False)
            tk.Label(left, textvariable=host_var, bg=SURFACE, fg=TEXT, anchor="w", font=("Segoe UI", 10, "bold")).pack(fill="x")
            tk.Label(left, text=server.user, bg=SURFACE, fg=MUTED, anchor="w", font=("Segoe UI", 8)).pack(fill="x")

            gpu_frame = tk.Frame(row, bg=SURFACE)
            gpu_frame.grid(row=0, column=1, sticky="ew")

            right = tk.Frame(row, bg=SURFACE, width=76)
            right.grid(row=0, column=2, sticky="nse", padx=(8, 0))
            right.grid_propagate(False)
            count_label = tk.Label(right, textvariable=count_var, bg=AMBER_BG, fg=AMBER, padx=6, pady=2, font=("Segoe UI", 9, "bold"))
            count_label.pack(fill="x", expand=True)

            self.status_vars[server.alias] = {"host": host_var, "count": count_var, "status": status_var}
            self.gpu_frames[server.alias] = gpu_frame
            self.count_labels[server.alias] = count_label

    def _summary_tile(self, parent: tk.Widget, title: str, value: tk.StringVar, bg: str, fg: str) -> tk.Frame:
        tile = tk.Frame(parent, bg=bg, padx=10, pady=6)
        tk.Label(tile, text=title, bg=bg, fg=fg, font=("Segoe UI", 8, "bold")).pack(side="left")
        tk.Label(tile, textvariable=value, bg=bg, fg=fg, font=("Segoe UI", 15, "bold")).pack(side="left", padx=(8, 0))
        return tile

    def _build_migrate_tab(self) -> None:
        body = tk.Frame(self.migrate_tab, bg=BG)
        body.pack(fill="both", expand=True, pady=(12, 0))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(2, weight=1)

        labels = [server.label for server in self.servers]
        self.source_server_var = tk.StringVar(value=labels[0] if labels else "")
        self.target_server_var = tk.StringVar(value=labels[1] if len(labels) > 1 else (labels[0] if labels else ""))
        self.source_conda_root_var = tk.StringVar(value=DEFAULT_SOURCE_CONDA_ROOT)
        self.target_conda_root_var = tk.StringVar(value=DEFAULT_TARGET_CONDA_ROOT)
        self.env_name_var = tk.StringVar()
        self.target_env_name_var = tk.StringVar()
        self.shared_dir_var = tk.StringVar(value=DEFAULT_SHARED_DIR)
        self.target_shared_dir_var = tk.StringVar()
        self.overwrite_var = tk.BooleanVar(value=False)
        self.preview_var = tk.StringVar(value="")
        self.migration_step_var = tk.StringVar(value=self.tr("waiting"))

        source_card = self._form_card(body, self.tr("source_env"), self.tr("source_env_hint"))
        source_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        target_card = self._form_card(body, self.tr("target_env"), self.tr("target_env_hint"))
        target_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))

        self._field(source_card, 1, self.tr("server"), ttk.Combobox(source_card, values=labels, textvariable=self.source_server_var, state="readonly"))
        self._field(source_card, 2, self.tr("conda_root"), ttk.Entry(source_card, textvariable=self.source_conda_root_var))
        self._field(source_card, 3, self.tr("env_name"), ttk.Entry(source_card, textvariable=self.env_name_var))

        self._field(target_card, 1, self.tr("server"), ttk.Combobox(target_card, values=labels, textvariable=self.target_server_var, state="readonly"))
        self._field(target_card, 2, self.tr("conda_root"), ttk.Entry(target_card, textvariable=self.target_conda_root_var))
        self._field(target_card, 3, self.tr("target_env_name"), ttk.Entry(target_card, textvariable=self.target_env_name_var))

        options = tk.Frame(body, bg=SURFACE, bd=1, relief="solid", padx=14, pady=12)
        options.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        options.grid_columnconfigure(1, weight=1)
        tk.Label(options, text=self.tr("shared_dir"), bg=SURFACE, fg=TEXT, font=("Microsoft YaHei UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Entry(options, textvariable=self.shared_dir_var).grid(row=0, column=1, sticky="ew")
        tk.Label(options, text=self.tr("target_shared"), bg=SURFACE, fg=TEXT, font=("Microsoft YaHei UI", 10, "bold")).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        ttk.Entry(options, textvariable=self.target_shared_dir_var).grid(row=1, column=1, sticky="ew", pady=(10, 0))
        tk.Label(options, text=self.tr("target_shared_hint"), bg=SURFACE, fg=MUTED, font=("Segoe UI", 8)).grid(row=1, column=2, sticky="w", padx=16, pady=(10, 0))
        ttk.Checkbutton(options, text=self.tr("overwrite"), variable=self.overwrite_var).grid(row=0, column=2, padx=16)
        self.migrate_button = ttk.Button(options, text=self.tr("start_migration"), command=self.start_migration, style="Accent.TButton")
        self.migrate_button.grid(row=0, column=3)

        lower = tk.Frame(body, bg=BG)
        lower.grid(row=2, column=0, columnspan=2, sticky="nsew")
        lower.grid_columnconfigure(0, weight=1)
        lower.grid_columnconfigure(1, weight=1)
        lower.grid_rowconfigure(1, weight=1)

        preview = tk.Frame(lower, bg=SURFACE, bd=1, relief="solid", padx=14, pady=12)
        preview.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 12))
        tk.Label(preview, text=self.tr("preview"), bg=SURFACE, fg=TEXT, font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w")
        tk.Label(preview, textvariable=self.preview_var, bg=SURFACE, fg=MUTED, justify="left", anchor="w").pack(fill="x", pady=(8, 0))

        progress = tk.Frame(lower, bg=SURFACE, bd=1, relief="solid", padx=14, pady=12)
        progress.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=(0, 12))
        tk.Label(progress, text=self.tr("current_state"), bg=SURFACE, fg=TEXT, font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w")
        tk.Label(progress, textvariable=self.migration_step_var, bg=SURFACE, fg=BLUE, font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w", pady=(8, 8))
        self.migration_progress = ttk.Progressbar(progress, mode="indeterminate")
        self.migration_progress.pack(fill="x")

        log_panel = tk.Frame(lower, bg=SURFACE, bd=1, relief="solid", padx=12, pady=12)
        log_panel.grid(row=1, column=0, columnspan=2, sticky="nsew")
        log_panel.grid_rowconfigure(1, weight=1)
        log_panel.grid_columnconfigure(0, weight=1)
        tk.Label(log_panel, text=self.tr("migration_log"), bg=SURFACE, fg=TEXT, font=("Microsoft YaHei UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Button(log_panel, text=self.tr("clear"), command=lambda: self.migration_log.delete("1.0", "end")).grid(row=0, column=1, sticky="e")
        self.migration_log = tk.Text(log_panel, height=16, wrap="word", font=("Consolas", 10), bg=DARK, fg="#d7e2ee", insertbackground="#d7e2ee", relief="flat")
        self.migration_log.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        self._update_preview()

    def _form_card(self, parent: tk.Widget, title: str, subtitle: str) -> tk.Frame:
        card = tk.Frame(parent, bg=SURFACE, bd=1, relief="solid", padx=14, pady=12)
        card.grid_columnconfigure(1, weight=1)
        tk.Label(card, text=title, bg=SURFACE, fg=TEXT, font=("Microsoft YaHei UI", 13, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        tk.Label(card, text=subtitle, bg=SURFACE, fg=MUTED).grid(row=0, column=1, sticky="e")
        return card

    def _field(self, parent: tk.Frame, row: int, label: str, widget: tk.Widget) -> None:
        tk.Label(parent, text=label, bg=SURFACE, fg=MUTED).grid(row=row, column=0, sticky="w", pady=(12, 0), padx=(0, 10))
        widget.grid(row=row, column=1, sticky="ew", pady=(12, 0))

    def _build_queue_tab(self) -> None:
        body = tk.Frame(self.queue_tab, bg=BG)
        body.pack(fill="both", expand=True, pady=(12, 0))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(2, weight=1)

        labels = [server.label for server in self.servers]
        self.queue_server_var = tk.StringVar(value=labels[0] if labels else "")
        self.queue_dir_var = tk.StringVar(value=DEFAULT_QUEUE_RUNNER_DIR)
        self.queue_name_var = tk.StringVar()
        self.queue_cwd_var = tk.StringVar()
        self.queue_command_var = tk.StringVar()
        self.queue_gpus_var = tk.StringVar(value="all")
        self.queue_group_var = tk.StringVar(value="default")
        self.queue_priority_var = tk.StringVar(value="0")
        self.queue_conda_env_var = tk.StringVar()
        self.queue_job_id_var = tk.StringVar()
        self.queue_status_var = tk.StringVar(value=self.tr("ready"))

        top = tk.Frame(body, bg=SURFACE, bd=1, relief="solid", padx=12, pady=10)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        top.grid_columnconfigure(1, weight=1)
        top.grid_columnconfigure(3, weight=1)
        tk.Label(top, text=self.tr("queue_server"), bg=SURFACE, fg=MUTED).grid(row=0, column=0, sticky="w")
        ttk.Combobox(top, values=labels, textvariable=self.queue_server_var, state="readonly").grid(row=0, column=1, sticky="ew", padx=(8, 14))
        tk.Label(top, text=self.tr("queue_dir"), bg=SURFACE, fg=MUTED).grid(row=0, column=2, sticky="w")
        ttk.Entry(top, textvariable=self.queue_dir_var).grid(row=0, column=3, sticky="ew", padx=(8, 14))
        ttk.Button(top, text=self.tr("install_sync"), command=self.queue_install).grid(row=0, column=4, padx=(0, 6))
        ttk.Button(top, text=self.tr("refresh"), command=self.queue_refresh).grid(row=0, column=5)

        actions = tk.Frame(body, bg=SURFACE, bd=1, relief="solid", padx=12, pady=10)
        actions.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=(0, 10))
        actions.grid_columnconfigure(1, weight=1)
        tk.Label(actions, text=self.tr("add_job"), bg=SURFACE, fg=TEXT, font=("Microsoft YaHei UI", 12, "bold")).grid(row=0, column=0, columnspan=4, sticky="w")
        self._queue_field(actions, 1, self.tr("name"), ttk.Entry(actions, textvariable=self.queue_name_var), col=0)
        self._queue_field(actions, 2, self.tr("cwd"), ttk.Entry(actions, textvariable=self.queue_cwd_var), col=0)
        self._queue_field(actions, 3, self.tr("command"), ttk.Entry(actions, textvariable=self.queue_command_var), col=0)
        self._queue_field(actions, 4, self.tr("gpus"), ttk.Entry(actions, textvariable=self.queue_gpus_var, width=12), col=0)
        self._queue_field(actions, 4, self.tr("queue"), ttk.Entry(actions, textvariable=self.queue_group_var, width=12), col=2)
        self._queue_field(actions, 5, self.tr("priority"), ttk.Entry(actions, textvariable=self.queue_priority_var, width=12), col=0)
        self._queue_field(actions, 5, self.tr("conda_env"), ttk.Entry(actions, textvariable=self.queue_conda_env_var, width=16), col=2)
        ttk.Button(actions, text=self.tr("add_to_queue"), command=self.queue_add_job, style="Accent.TButton").grid(row=6, column=0, columnspan=4, sticky="ew", pady=(12, 0))

        daemon = tk.Frame(body, bg=SURFACE, bd=1, relief="solid", padx=12, pady=10)
        daemon.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=(0, 10))
        daemon.grid_columnconfigure(1, weight=1)
        tk.Label(daemon, text=self.tr("operations"), bg=SURFACE, fg=TEXT, font=("Microsoft YaHei UI", 12, "bold")).grid(row=0, column=0, columnspan=4, sticky="w")
        ttk.Button(daemon, text="Doctor", command=lambda: self.queue_run_simple(["doctor"])).grid(row=1, column=0, sticky="ew", pady=(12, 0), padx=(0, 6))
        ttk.Button(daemon, text=self.tr("daemon_status"), command=lambda: self.queue_run_simple(["daemon", "status"])).grid(row=1, column=1, sticky="ew", pady=(12, 0), padx=6)
        ttk.Button(daemon, text=self.tr("start_daemon"), command=lambda: self.queue_run_simple(["daemon", "start"])).grid(row=1, column=2, sticky="ew", pady=(12, 0), padx=6)
        ttk.Button(daemon, text=self.tr("stop_daemon"), command=lambda: self.queue_run_simple(["daemon", "stop"])).grid(row=1, column=3, sticky="ew", pady=(12, 0), padx=(6, 0))
        ttk.Button(daemon, text=self.tr("queue_list"), command=lambda: self.queue_run_simple(["list", "--all"])).grid(row=2, column=0, sticky="ew", pady=(8, 0), padx=(0, 6))
        ttk.Button(daemon, text="Status", command=lambda: self.queue_run_simple(["status", "--all"])).grid(row=2, column=1, sticky="ew", pady=(8, 0), padx=6)
        ttk.Button(daemon, text=self.tr("daemon_logs"), command=lambda: self.queue_run_simple(["daemon", "logs", "--lines", "120"])).grid(row=2, column=2, sticky="ew", pady=(8, 0), padx=6)
        self._queue_field(daemon, 3, self.tr("job_id"), ttk.Entry(daemon, textvariable=self.queue_job_id_var, width=10), col=0, pady=(14, 0))
        ttk.Button(daemon, text=self.tr("show"), command=lambda: self.queue_job_action("show")).grid(row=4, column=0, sticky="ew", pady=(8, 0), padx=(0, 6))
        ttk.Button(daemon, text=self.tr("logs"), command=lambda: self.queue_job_action("logs")).grid(row=4, column=1, sticky="ew", pady=(8, 0), padx=6)
        ttk.Button(daemon, text=self.tr("retry"), command=lambda: self.queue_job_action("retry")).grid(row=4, column=2, sticky="ew", pady=(8, 0), padx=6)
        ttk.Button(daemon, text=self.tr("cancel"), command=lambda: self.queue_job_action("cancel")).grid(row=4, column=3, sticky="ew", pady=(8, 0), padx=(6, 0))
        ttk.Label(daemon, textvariable=self.queue_status_var, style="CardMuted.TLabel").grid(row=5, column=0, columnspan=4, sticky="w", pady=(12, 0))

        log_panel = tk.Frame(body, bg=SURFACE, bd=1, relief="solid", padx=12, pady=12)
        log_panel.grid(row=2, column=0, columnspan=2, sticky="nsew")
        log_panel.grid_rowconfigure(1, weight=1)
        log_panel.grid_columnconfigure(0, weight=1)
        tk.Label(log_panel, text=self.tr("queue_output"), bg=SURFACE, fg=TEXT, font=("Microsoft YaHei UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Button(log_panel, text=self.tr("clear"), command=lambda: self.queue_log.delete("1.0", "end")).grid(row=0, column=1, sticky="e")
        self.queue_log = tk.Text(log_panel, height=18, wrap="word", font=("Consolas", 10), bg=DARK, fg="#d7e2ee", insertbackground="#d7e2ee", relief="flat")
        self.queue_log.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(10, 0))

    def _queue_field(self, parent: tk.Frame, row: int, label: str, widget: tk.Widget, col: int = 0, pady: tuple[int, int] = (8, 0)) -> None:
        tk.Label(parent, text=label, bg=SURFACE, fg=MUTED).grid(row=row, column=col, sticky="w", pady=pady, padx=(0, 8))
        widget.grid(row=row, column=col + 1, sticky="ew", pady=pady, padx=(0, 8))

    def _bind_preview_updates(self) -> None:
        for var in (
            self.source_server_var,
            self.target_server_var,
            self.source_conda_root_var,
            self.target_conda_root_var,
            self.env_name_var,
            self.target_env_name_var,
            self.shared_dir_var,
            self.target_shared_dir_var,
        ):
            var.trace_add("write", lambda *_: self._update_preview())

    def _update_preview(self) -> None:
        env = self.env_name_var.get().strip() or self.tr("source_env_placeholder")
        target_env = self.target_env_name_var.get().strip() or env
        src = self.source_server_var.get() or self.tr("source_server_placeholder")
        dst = self.target_server_var.get() or self.tr("target_server_placeholder")
        shared = self.shared_dir_var.get().strip() or DEFAULT_SHARED_DIR
        target_shared = self.target_shared_dir_var.get().strip() or shared
        self.preview_var.set(
            f"1. Pack {env} on {src}\n"
            f"2. Save archive to {shared}/conda-packs\n"
            f"3. Target {dst} reads from {target_shared}/conda-packs\n"
            f"4. Unpack as {target_env} and run conda-unpack"
        )

    def _auto_refresh_tick(self) -> None:
        if self.auto_refresh.get() and not self.refresh_running:
            now = time.monotonic()
            last = getattr(self, "_last_refresh_monotonic", 0.0)
            if now - last >= max(5, self.refresh_interval_s.get()):
                self.refresh_gpus()
        self.after(1000, self._auto_refresh_tick)

    def refresh_gpus(self) -> None:
        if self.refresh_running:
            return
        self.refresh_running = True
        self._last_refresh_monotonic = time.monotonic()
        self.summary_hint_var.set(self.tr("refreshing_gpu"))
        for server in self.servers:
            self.status_vars[server.alias]["count"].set(self.tr("connecting"))
            self.status_vars[server.alias]["status"].set(f"{self.tr('connecting')} {server.display_target}")
            self._render_loading(server)
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _render_loading(self, server: Server) -> None:
        frame = self.gpu_frames[server.alias]
        if not frame.winfo_children():
            tk.Label(frame, text="正在建立 SSH 连接并读取 nvidia-smi ...", bg=SURFACE, fg=MUTED).pack(anchor="w")

    def _refresh_worker(self) -> None:
        results: list[tuple[Server, list[GpuInfo], str]] = []
        threads: list[threading.Thread] = []
        lock = threading.Lock()

        def one(server: Server) -> None:
            try:
                gpus, error = query_gpus(server, self.ssh_pool)
            except Exception as exc:
                gpus, error = [], str(exc)
            with lock:
                results.append((server, gpus, error))

        for server in self.servers:
            thread = threading.Thread(target=one, args=(server,), daemon=True)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        self.result_queue.put(("gpu_results", results))

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self.result_queue.get_nowait()
                if kind == "gpu_results":
                    self._render_gpu_results(payload)  # type: ignore[arg-type]
                elif kind == "migration_log":
                    self._append_migration_log(str(payload))
                elif kind == "migration_state":
                    self.migration_step_var.set(str(payload))
                elif kind == "migration_done":
                    self._finish_migration(str(payload))
                elif kind == "queue_log":
                    self._append_queue_log(str(payload))
                elif kind == "queue_state":
                    self.queue_status_var.set(str(payload))
                elif kind == "queue_done":
                    self._finish_queue_command(str(payload))
        except queue.Empty:
            pass
        self.after(200, self._poll_queue)

    def _render_gpu_results(self, results: list[tuple[Server, list[GpuInfo], str]]) -> None:
        util_threshold = self.util_threshold.get()
        mem_threshold = self.mem_threshold_mb.get()
        total_gpus = 0
        total_free = 0
        online = 0

        for server, gpus, error in sorted(results, key=lambda item: parse_int(item[0].alias, 9999)):
            vars_for_server = self.status_vars[server.alias]
            frame = self.gpu_frames[server.alias]

            if error:
                vars_for_server["count"].set(self.tr("connection_failed"))
                vars_for_server["status"].set(error)
                self.count_labels[server.alias].configure(bg=RED_BG, fg=RED)
                self._show_server_error(server.alias, frame, "无法读取 nvidia-smi，请检查 SSH 免密、网络或服务器状态。")
                continue

            online += 1
            free_count = sum(1 for gpu in gpus if gpu.is_free(util_threshold, mem_threshold))
            total_gpus += len(gpus)
            total_free += free_count
            count_bg = GREEN_BG if free_count else RED_BG
            count_fg = GREEN if free_count else RED
            vars_for_server["count"].set(f"{self.tr('free_count')} {free_count}/{len(gpus)}")
            vars_for_server["status"].set(f"SSH: {server.display_target}")
            self.count_labels[server.alias].configure(bg=count_bg, fg=count_fg)
            self._gpu_grid(server.alias, frame, gpus, util_threshold, mem_threshold)

        busy = max(0, total_gpus - total_free)
        stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_refresh_at.set(f"{self.tr('last_refresh')}: {stamp}")
        self.summary_free_var.set(f"{total_free}/{total_gpus}")
        self.summary_online_var.set(f"{online}/{len(self.servers)}")
        self.summary_busy_var.set(str(busy))
        self.summary_hint_var.set(self.tr("idle_hint"))
        self.refresh_running = False

    def _error_panel(self, parent: tk.Frame, text: str) -> None:
        panel = tk.Frame(parent, bg=RED_BG, padx=12, pady=10)
        panel.pack(fill="x")
        tk.Label(panel, text=text, bg=RED_BG, fg=RED, font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")

    def _show_server_error(self, alias: str, parent: tk.Frame, text: str) -> None:
        if alias in self.gpu_widgets:
            for widgets in self.gpu_widgets[alias].values():
                card = widgets["card"]
                card.grid_remove()
            return
        for child in parent.winfo_children():
            child.destroy()
        self._error_panel(parent, text)

    def _gpu_grid(self, alias: str, parent: tk.Frame, gpus: list[GpuInfo], util_threshold: int, mem_threshold: int) -> None:
        if not gpus:
            if alias not in self.gpu_widgets:
                tk.Label(parent, text="no GPU data", bg=SURFACE, fg=MUTED).pack(anchor="w")
            return
        widgets_by_gpu = self.gpu_widgets.get(alias)
        if widgets_by_gpu is None:
            for child in parent.winfo_children():
                child.destroy()
            grid = tk.Frame(parent, bg=SURFACE)
            grid.pack(fill="x")
            widgets_by_gpu = {}
            self.gpu_widgets[alias] = widgets_by_gpu
        else:
            grid = parent.winfo_children()[0]

        seen = set()
        for idx, gpu in enumerate(gpus):
            seen.add(gpu.index)
            widgets = widgets_by_gpu.get(gpu.index)
            if widgets is None:
                widgets = self._create_gpu_chip(grid)
                widgets_by_gpu[gpu.index] = widgets
            self._update_gpu_chip(widgets, gpu, gpu.is_free(util_threshold, mem_threshold))
            card = widgets["card"]
            card.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 4, 0), pady=0)
            grid.grid_columnconfigure(idx, weight=1, uniform="gpu")
        for gpu_index, widgets in widgets_by_gpu.items():
            if gpu_index not in seen:
                widgets["card"].grid_remove()

    def _create_gpu_chip(self, parent: tk.Frame) -> dict[str, object]:
        chip = tk.Frame(parent, bg=SURFACE, padx=0, pady=0, width=104, height=34)
        chip.grid_propagate(False)
        title = tk.Label(chip, text="", bg=SURFACE, fg=TEXT, anchor="w", font=("Segoe UI", 7, "bold"))
        title.pack(fill="x")
        canvas = tk.Canvas(chip, height=18, highlightthickness=0, bg=SURFACE)
        canvas.pack(fill="x", pady=(1, 0))
        canvas.bind("<Configure>", lambda event, w=None: self._redraw_gpu_bar(canvas))
        return {"card": chip, "title": title, "canvas": canvas, "gpu": None, "is_free": True}

    def _update_gpu_chip(self, widgets: dict[str, object], gpu: GpuInfo, is_free: bool) -> None:
        widgets["gpu"] = gpu
        widgets["is_free"] = is_free
        used_gb = gpu.mem_used_mb / 1024
        total_gb = gpu.mem_total_mb / 1024
        widgets["title"].configure(text=f"G{gpu.index}  {gpu.name[:18]}", fg=GREEN if is_free else RED)
        canvas = widgets["canvas"]
        self._redraw_gpu_bar(canvas)

    def _redraw_gpu_bar(self, canvas: tk.Canvas) -> None:
        widgets = None
        for server_widgets in self.gpu_widgets.values():
            for candidate in server_widgets.values():
                if candidate.get("canvas") is canvas:
                    widgets = candidate
                    break
            if widgets is not None:
                break
        if widgets is None or widgets.get("gpu") is None:
            return
        gpu = widgets["gpu"]
        is_free = bool(widgets.get("is_free"))
        canvas.delete("all")
        width = max(1, canvas.winfo_width())
        height = max(1, canvas.winfo_height())
        bg = GREEN_BG if is_free else RED_BG
        fg = GREEN if is_free else RED
        fill_width = max(2, int(width * max(gpu.mem_percent, gpu.util_percent) / 100))
        canvas.create_rectangle(0, 0, width, height, fill=bg, outline=bg)
        canvas.create_rectangle(0, 0, fill_width, height, fill=fg, outline=fg)
        text = f"{gpu.util_percent}%  {gpu.mem_used_mb/1024:.1f}/{gpu.mem_total_mb/1024:.0f}G"
        canvas.create_text(width / 2, height / 2, text=text, fill="#ffffff" if not is_free else TEXT, font=("Segoe UI", 7, "bold"))

    def _append_migration_log(self, text: str) -> None:
        self.migration_log.insert("end", text)
        if not text.endswith("\n"):
            self.migration_log.insert("end", "\n")
        self.migration_log.see("end")

    def start_migration(self) -> None:
        if self.migration_running:
            return
        env_name = self.env_name_var.get().strip()
        if not env_name:
            messagebox.showerror("缺少环境名", "请填写源环境名。")
            return
        target_env_name = self.target_env_name_var.get().strip() or env_name
        source = self.server_by_label.get(self.source_server_var.get())
        target = self.server_by_label.get(self.target_server_var.get())
        if not source or not target:
            messagebox.showerror("服务器错误", "请选择源服务器和目标服务器。")
            return
        source_root = self.source_conda_root_var.get().strip()
        target_root = self.target_conda_root_var.get().strip()
        shared_dir = self.shared_dir_var.get().strip()
        target_shared_dir = self.target_shared_dir_var.get().strip() or shared_dir
        if not source_root or not target_root or not shared_dir:
            messagebox.showerror("路径错误", "请填写 miniconda 根目录和共享目录。")
            return
        if source == target and env_name == target_env_name and not self.overwrite_var.get():
            messagebox.showwarning("目标已存在风险", "源和目标相同且环境名相同。若要覆盖，请勾选覆盖选项。")
            return

        self.migration_running = True
        self.migrate_button.configure(state="disabled")
        self.migration_progress.start(12)
        self.migration_step_var.set("准备开始")
        self._append_migration_log("")
        self._append_migration_log(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] 开始迁移 {env_name}: {source.label} -> {target.label}")
        threading.Thread(
            target=self._migration_worker,
            args=(source, target, source_root, target_root, env_name, target_env_name, shared_dir, target_shared_dir, self.overwrite_var.get()),
            daemon=True,
        ).start()

    def _migration_worker(
        self,
        source: Server,
        target: Server,
        source_root: str,
        target_root: str,
        env_name: str,
        target_env_name: str,
        shared_dir: str,
        target_shared_dir: str,
        overwrite: bool,
    ) -> None:
        try:
            self.result_queue.put(("migration_state", "1/3 源机器正在 conda-pack 打包"))
            self.result_queue.put(("migration_log", f"源机器打包: {source.display_target}\n"))
            pack_proc = run_remote_script(source, pack_script(source_root, env_name, shared_dir), timeout_s=60 * 60 * 3)
            self.result_queue.put(("migration_log", pack_proc.stdout))
            if pack_proc.stderr:
                self.result_queue.put(("migration_log", pack_proc.stderr))
            if pack_proc.returncode != 0:
                self.result_queue.put(("migration_done", f"打包失败，退出码 {pack_proc.returncode}\n"))
                return

            archive = ""
            for line in pack_proc.stdout.splitlines():
                if line.startswith("__ARCHIVE__="):
                    archive = line.split("=", 1)[1].strip()
            if not archive:
                self.result_queue.put(("migration_done", "打包完成但没有解析到压缩包路径。\n"))
                return

            self.result_queue.put(("migration_state", "2/3 目标机器正在解压环境"))
            self.result_queue.put(("migration_log", f"目标机器解包: {target.display_target}\n压缩包: {archive}\n"))
            unpack_proc = run_remote_script(
                target,
                unpack_script(target_root, target_env_name, archive, overwrite, shared_dir, target_shared_dir),
                timeout_s=60 * 60 * 3,
            )
            self.result_queue.put(("migration_log", unpack_proc.stdout))
            if unpack_proc.stderr:
                self.result_queue.put(("migration_log", unpack_proc.stderr))
            if unpack_proc.returncode != 0:
                self.result_queue.put(("migration_done", f"解包失败，退出码 {unpack_proc.returncode}\n"))
                return

            dest = ""
            for line in unpack_proc.stdout.splitlines():
                if line.startswith("__DEST__="):
                    dest = line.split("=", 1)[1].strip()
            self.result_queue.put(("migration_state", "3/3 完成"))
            self.result_queue.put(("migration_done", f"迁移完成。目标环境: {dest or target_env_name}\n"))
        except subprocess.TimeoutExpired:
            self.result_queue.put(("migration_done", "操作超时。可以去源/目标服务器查看是否仍在执行。\n"))
        except Exception as exc:
            self.result_queue.put(("migration_done", f"迁移失败: {exc}\n"))

    def _finish_migration(self, message: str) -> None:
        self.migration_running = False
        self.migration_progress.stop()
        self.migrate_button.configure(state="normal")
        self.migration_step_var.set("已结束")
        self._append_migration_log(message)

    def _queue_server(self) -> Server | None:
        server = self.server_by_label.get(self.queue_server_var.get())
        if server is None:
            messagebox.showerror("Server Error", "Select a Queue Runner server.")
        return server

    def _queue_dir(self) -> str:
        return self.queue_dir_var.get().strip() or DEFAULT_QUEUE_RUNNER_DIR

    def _append_queue_log(self, text: str) -> None:
        self.queue_log.insert("end", text)
        if not text.endswith("\n"):
            self.queue_log.insert("end", "\n")
        self.queue_log.see("end")

    def _start_queue_thread(self, label: str, worker) -> None:
        if self.queue_running:
            return
        self.queue_running = True
        self.queue_status_var.set(label)
        self._append_queue_log(f"\n[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {label}")
        threading.Thread(target=worker, daemon=True).start()

    def _finish_queue_command(self, message: str) -> None:
        self.queue_running = False
        self.queue_status_var.set("Ready")
        if message:
            self._append_queue_log(message)

    def queue_install(self) -> None:
        server = self._queue_server()
        if server is None:
            return
        if not LOCAL_GPUQ_FILE.exists():
            messagebox.showerror("Missing gpuq", f"Cannot find local gpuq script:\n{LOCAL_GPUQ_FILE}")
            return
        remote_dir = self._queue_dir()

        def worker() -> None:
            try:
                payload = base64.b64encode(LOCAL_GPUQ_FILE.read_bytes()).decode("ascii")
                proc = run_remote_script(server, gpuq_install_script(remote_dir, payload), timeout_s=600)
                if proc.stdout:
                    self.result_queue.put(("queue_log", proc.stdout))
                if proc.stderr:
                    self.result_queue.put(("queue_log", proc.stderr))
                self.result_queue.put(("queue_done", f"Install finished with exit code {proc.returncode}\n"))
            except Exception as exc:
                self.result_queue.put(("queue_done", f"Install failed: {exc}\n"))

        self._start_queue_thread(f"Installing gpuq on {server.label}", worker)

    def queue_refresh(self) -> None:
        self.queue_run_simple(["status", "--all"])

    def queue_run_simple(self, args: list[str]) -> None:
        server = self._queue_server()
        if server is None:
            return
        remote_dir = self._queue_dir()

        def worker() -> None:
            try:
                proc = run_remote_script(server, gpuq_command_script(remote_dir, args), timeout_s=600)
                command = " ".join(args)
                self.result_queue.put(("queue_log", f"$ ./gpuq {command}\n"))
                if proc.stdout:
                    self.result_queue.put(("queue_log", proc.stdout))
                if proc.stderr:
                    self.result_queue.put(("queue_log", proc.stderr))
                self.result_queue.put(("queue_done", f"Command exit code: {proc.returncode}\n"))
            except Exception as exc:
                self.result_queue.put(("queue_done", f"Command failed: {exc}\n"))

        self._start_queue_thread(f"Running gpuq {' '.join(args)}", worker)

    def queue_add_job(self) -> None:
        name = self.queue_name_var.get().strip()
        cwd = self.queue_cwd_var.get().strip()
        command = self.queue_command_var.get().strip()
        gpus = self.queue_gpus_var.get().strip()
        queue_name = self.queue_group_var.get().strip()
        priority = self.queue_priority_var.get().strip()
        conda_env = self.queue_conda_env_var.get().strip()
        if not cwd or not command:
            messagebox.showerror("Missing Field", "CWD and Command are required.")
            return
        args = ["add", "--cwd", cwd, "--command", command]
        if name:
            args.extend(["--name", name])
        if gpus:
            args.extend(["--gpus", gpus])
        if queue_name:
            args.extend(["--queue", queue_name])
        if priority:
            args.extend(["--priority", priority])
        if conda_env:
            args.extend(["--conda-env", conda_env])
        self.queue_run_simple(args)

    def queue_job_action(self, action: str) -> None:
        job_id = self.queue_job_id_var.get().strip()
        if not job_id:
            messagebox.showerror("Missing Job ID", "Enter a job ID first.")
            return
        if action == "logs":
            self.queue_run_simple(["logs", job_id, "--lines", "120"])
        elif action == "cancel":
            self.queue_run_simple(["cancel", job_id, "--force"])
        else:
            self.queue_run_simple([action, job_id])


def main() -> int:
    try:
        app = App()
    except Exception as exc:
        messagebox.showerror("启动失败", str(exc))
        return 2
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
