# Docker 实验性部署说明 (Experimental)

> [!WARNING]
> **状态声明**：本项目主线全力保障 **Windows 本地原生桌面环境** 的极致开箱即用体验。
> Docker 镜像部署目前作为**社区实验性目录**保留。在无图形界面的 Docker 容器内，由于无法直接弹出桌面窗口交互，首次登录需通过控制台扫码或导入已登录 Cookie；若遇强风控滑块验证码，可能需要配合 noVNC 或宿主机导入 Cookie 恢复。

### 使用方法

在项目根目录下执行：

```bash
docker compose -f experimental/docker/docker-compose.yml up -d
```

启动后访问 `http://<服务器IP>:9090/admin`，在管理控制台完成扫码登录或导入 Cookie。
