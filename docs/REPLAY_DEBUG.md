# PC 回灌 Debug 数据源

此数据源供 Replay_SourceFile 的 GDB / VS Code 单步调试使用。它读取 REPLAY_UPPER_SNAPSHOT 指定的 UPPER v1 / CRC32 二进制最新快照，与 C 进程分开运行。

推荐从回灌工程按 F5 启动 Replay: COLIGEN upper single-step。启动器会设置快照路径并自动连接本上位机的“回灌 Debug”。

也可以在“设备与显示”的 Hardware 选项中手动选择“回灌 Debug”，连接时选择回灌生成的快照文件。上一次选择在当前进程中保留。

断点停住时保留最后完整帧，状态显示“暂停 / 等待下一步”，可继续检查数组和操作视图。继续执行到下一个完整输出后刷新；读到截断、CRC 错误或暂时不存在的文件时重试，保持已有完整画面。此模式不输出实时 PDC 提示音，不把当前电脑时间标成原始采样日期。

回灌工程对应路径：
D:/Cenww_work/SF26195_Geely_KX21/replay/Replay_SourceFile/docs/REPLAY_UPPER_DEBUG.md

测试可设置 REPLAY_DEBUG_TEST_PACKET 指向真实 C 回灌输出的快照文件，然后执行：
python -m pytest -q tests/test_replay_debug.py
