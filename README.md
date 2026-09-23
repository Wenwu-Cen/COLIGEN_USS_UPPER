# COLIGEN USS UPPER CAN

## 目录结构说明

```text
src/         Python运行代码以及CAN/GUI适配模块
tests/       Pytest测试用例以及旧版自测试程序
scripts/     PowerShell运行和构建脚本，以及CS+桥接工具
config/      运行时TOML配置文件
assets/      应用程序图标以及打包所需静态资源
docs/        集成文档、架构说明以及项目状态文档
recordings/  ASC/TXT回放文件
build/       PyInstaller构建中间文件（自动生成）
dist/        打包后的EXE输出目录（自动生成）
library/     第三方厂商运行库存放目录
```

`CAN_S20/` 是项目外部的同级目录，用于存放 DBC 文件以及（可用时）报文回放源文件。

该目录不会被复制到当前项目中。

当前软件版本：`3.4.3`（周立功等实时源下，拖动画布和滚轮缩放改为停手/停轮后再整帧重绘，减轻卡顿。S20 车位可视化不变：冲突 ID 默认按车位，关闭画布 SLOT 后按点云/PDC）。发版时同步修改 `src/app_version.py` 的 `APP_VERSION` 和 `pyproject.toml` 的 `version`；窗口标题与打包 EXE 名会自动带上该版本号。

---

## 快速开始

### 安装或更新 uv 环境

```powershell
uv sync
```

---

### 从源码运行GUI程序

```powershell
.\scripts\run_can_upper.ps1
```

---

### 运行测试

```powershell
uv run pytest -q
```

---

### 构建Windows可执行程序

```powershell
.\scripts\build_can_upper.ps1
```

生成的可执行文件路径：

```text
dist/COLIGEN_USS_UPPER_CAN_v3.4.3.exe
```

---

## 推荐优先阅读文件

1. `docs/CAN_INTEGRATION_README.md`

   用于了解：

   - CAN通信集成
   - ASC/BLF报文回放
   - 软件部署方式
2. `docs/COORDINATE_SYSTEMS.md`

   画布 / TXT（泊车3.txt）/ ASC 的点和线坐标系对照。
3. `src/VehUpperDemo_CAN.py`

   应用程序入口文件。
4. `src/CanOnlinePort.py`

   主要负责：

   - ASC文件解析
   - DBC报文解析
   - CAN Frame组装
5. `src/VehUpperDemo.py`

   GUI界面以及画布渲染相关代码。
6. `config/can_upper_config.toml`

   CAN设备以及回放参数配置文件。

---

## 注意事项

以下目录不要手动修改：

```text
build/
dist/
.venv/
__pycache__/
```

这些目录属于：

- 自动生成文件
- 编译输出文件
- Python环境缓存文件

修改可能导致构建或运行异常。
