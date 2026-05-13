# GPU Server Control

[English](README.md)

一个在 Windows 本机运行的远程 NVIDIA GPU 服务器管理工具。它通过 SSH 连接 Linux 服务器，提供 GPU 状态监控、conda 环境迁移和 GPU 任务排队管理。

## 功能

- **紧凑 GPU 看板**
  - 通过 SSH 调用多台服务器的 `nvidia-smi`。
  - 每台服务器一行，每张 GPU 用进度条展示。
  - 在进度条内显示利用率和显存占用。
  - 可配置空闲判断阈值。

- **持久 SSH 监控**
  - GPU 刷新复用 Paramiko SSH 连接，不需要每次刷新都重连。
  - 支持密钥登录和可选密码登录。
  - 支持自定义 SSH 端口。

- **Conda 环境迁移**
  - 在源服务器使用 `conda-pack` 打包环境。
  - 如果源 conda base 中缺少 `conda-pack`，会自动尝试安装。
  - 压缩包写入共享目录，例如 `/mnt/share/user/conda-packs`。
  - 在目标服务器解压到 `<目标 conda 根目录>/envs/<环境名>`。
  - 解压后自动运行 `conda-unpack`。
  - 支持源服务器和目标服务器共享盘挂载路径不同的情况。

- **任务队列集成**
  - 内置 `queue_runner/gpuq` 脚本。
  - 可以从 GUI 一键同步/安装到远端服务器。
  - 支持添加排队任务：运行目录、命令、GPU、队列、优先级、conda 环境。
  - 支持启动/停止远端 daemon。
  - 支持查看队列状态、任务详情和日志。

- **服务器管理界面**
  - 可以在界面中新增、修改、删除服务器。
  - 密码留空表示使用 SSH 密钥。
  - 填写密码则使用密码登录。

- **中英文界面**
  - 默认英文界面。
  - 可在 `Settings` 中切换中文。

## 运行要求

Windows 本机运行源码需要：

- Python 3.10+
- Tkinter，通常 Windows Python 或 Miniconda 自带
- `paramiko`

安装依赖：

```powershell
pip install -r requirements.txt
```

远端 Linux 服务器需要：

- `bash`
- `tar`
- `base64`
- NVIDIA 驱动和 `nvidia-smi`
- 用于环境迁移的 conda/miniconda
- 如果使用任务队列 daemon，需要 `screen`

## 快速开始

复制示例配置：

```powershell
copy servers.example.json servers.json
notepad servers.json
```

运行源码：

```powershell
python gpu_server_tool.py
```

或双击/运行：

```powershell
run_gpu_server_tool.bat
```

## 便携版 exe

构建独立 exe：

```powershell
build_exe.bat
```

生成文件：

```text
dist/GPU_Server_Control.exe
```

运行时请把 `servers.json` 放在 exe 同目录：

```text
dist/
  GPU_Server_Control.exe
  servers.json
```

打包后的 exe 内置 Python 和依赖，新 Windows 机器不需要安装 Python。

## 服务器配置

`servers.json` 示例：

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

字段说明：

- `alias`：显示名，必须唯一。
- `hostname`：IP 或域名。
- `user`：SSH 用户名。
- `port`：可选 SSH 端口，默认 `22`。
- `password`：可选。为空或省略时使用密钥登录。

默认密钥路径：

```text
%USERPROFILE%\.ssh\id_ed25519
```

## Conda 环境迁移

在 `Conda Migration` 页面选择：

- 源服务器
- 源 miniconda 根目录
- 环境名
- 目标服务器
- 目标 miniconda 根目录
- 目标环境名
- 源共享目录
- 可选目标共享目录

流程：

```text
1. SSH 到源服务器。
2. 检查 <源 conda 根目录>/envs/<环境名>。
3. 确保源 base 环境中有 conda-pack。
4. 打包到 <源共享目录>/conda-packs/*.tar.gz。
5. SSH 到目标服务器。
6. 如果共享盘挂载路径不同，自动重写压缩包路径。
7. 解压到 <目标 conda 根目录>/envs/<目标环境名>。
8. 运行 conda-unpack。
```

如果同一共享盘在不同服务器路径不同，例如：

```text
源共享目录: /mnt/share-a/user
目标共享目录: /mnt/share-b/user
```

请同时填写两个路径。

## Queue Runner

`Queue Runner` 页面封装了内置的 `gpuq` 调度器。

典型流程：

```text
1. 选择服务器。
2. 设置远端 gpuq 目录，例如 /mnt/share/user/gpu-queue-runner。
3. 点击 Install/Sync，同步 gpuq 并执行 init/doctor。
4. 从 GUI 添加任务。
5. 启动 daemon。
6. 刷新状态或查看日志。
```

任务支持：

- 运行目录
- 命令
- GPU，例如 `0,1,2,3` 或 `all`
- 队列名
- 优先级
- Conda 环境

`gpuq` 会在远端 `screen` 会话中启动任务，默认注入 `CUDA_VISIBLE_DEVICES`。

## 注意事项

- 不要提交真实 `servers.json`，其中可能包含内网 IP、用户名、密码或临时云主机地址。
- 建议优先使用 SSH 密钥，避免在配置文件里保存密码。
- 大型 conda 环境打包和解压可能耗时较久。
- `conda-pack` 对严重不一致的环境仍可能失败；本工具已使用 `--ignore-missing-files` 和 `--ignore-editable-packages` 尽量兼容科研环境。
- 目标 conda 根目录需要已经存在；本工具负责迁移环境，不负责安装 Miniconda。

## 常见问题

### `servers.json format error`

JSON 最后一项后面不能有逗号。建议用界面里的 `Manage Servers` 管理服务器，避免手写错误。

### `Cannot find conda executable`

请填写 conda 根目录，而不是 `bin` 目录：

```text
/data/user/miniconda3
```

程序会寻找：

```text
/data/user/miniconda3/bin/conda
```

### `Archive is not visible on target server`

目标服务器看不到源服务器生成的压缩包。常见原因：

- 源和目标不是同一个共享存储。
- 同一个共享存储在目标服务器路径不同。
- 目标用户没有读取权限。

路径不同请填写 `Target shared`。

## 开发

语法检查：

```powershell
python -m py_compile gpu_server_tool.py
```

构建 exe：

```powershell
build_exe.bat
```

## License

尚未选择开源许可证。发布前建议添加 LICENSE。
