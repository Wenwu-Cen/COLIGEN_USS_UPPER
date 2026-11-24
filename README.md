# COLIGEN USS UPPER

超声波上位机，当前版本 **v5.2.12**。支持实车采集、TXT / ASC / BLF 回放、点线和车位可视化，以及回灌比对。

## 下载与开始

1. 下载 `COLIGEN_USS_UPPER_v5.2.12.exe` 和 `SHA256SUMS.txt`。[GitHub Release](https://github.com/Wenwu-Cen/COLIGEN_USS_UPPER/releases/tag/v5.2.12) · [内网 Gitea Release](http://192.168.10.45:3000/Wenwu-Cen/COLIGEN_USS_UPPER/releases/tag/v5.2.12) · 内网 SVN `Algo/可视化工具/COLIGEN_USS_UPPER`。
2. 在 Windows x64 上运行 EXE。回看日志时点击「打开日志」。采集实车时在「设备与显示」选数据源、配置接口，再点「在线连接」。
3. 实车画面更新后，在「录制设置」选择项目、回灌输入来源和「仅采集」或「实时回灌比对」。停止后在状态栏查看保存目录。[录制操作](docs/RECORDING.md#开始录制)

## 按任务查文档

- **连接设备、回看日志、看地图或查字段**。[使用手册](docs/USER_GUIDE.md)
- **配置 S20、D4M3、E211 的输入和导出**。[录制与回灌手册](docs/RECORDING.md)
- **查 XCP 变量、报文格式、坐标或驱动**。[联调与参考索引](docs/README.md#设备与协议联调)
- **运行源码、构建或发布**。[开发维护](docs/maintenance/DEVELOPMENT.md) · [Ubuntu 使用与构建](docs/maintenance/UBUNTU_RELEASE.md) · [版本记录](docs/CHANGELOG.md)

下载并解压源码 ZIP 可离线查看完整文档。也可以直接打开 [v5.2.12 在线文档索引](https://github.com/Wenwu-Cen/COLIGEN_USS_UPPER/tree/v5.2.12/docs)。
