# VS Code / Git 解密差异显示

用户提供文档的方法是：

```powershell
git config --global diff.decrypt.textconv cat.exe
git config --global core.attributesFile ~/.gitattributes
```

并在 `~/.gitattributes` 中加入 `*.c diff=decrypt`、`*.h diff=decrypt`。本机这两项配置和 Python 属性原本已存在；实测 Git 自带 cat.exe 仍输出 TSD 密文，导致历史版本无法显示。

## 本机处理

本次沿用 textconv 驱动和全局属性文件，驱动改用已获本机加密客户端授权的 Python 执行 `~/bin/git_decrypt_textconv.py`。它先正常读取文件；Git 提供扩展名不匹配的临时密文时，在临时目录创建 .py 源文件，再经本机透明解密读取。临时目录用后自动清理；读取不到明文时返回失败。

不自行实现密码算法，不保存明文缓存，不修改加密软件或 Git 的 clean / smudge 行为。原工作区和历史对象继续遵循已有加密策略。GitHub 网页没有本机解密客户端，历史密文仍需在本机查看。

复现设置（按本机实际授权的 Python 路径调整）：

```powershell
.\scripts\configure_git_diff.ps1 -PythonExecutable 'C:\Users\008915\AppData\Local\Programs\Python\Python310\python.exe'
git check-attr diff -- src/app_version.py
git show --textconv HEAD:src/app_version.py
git diff --textconv -- src/app_version.py
```

全局驱动脚本放在用户目录，移动工程后仍可使用；脚本源码在本项目 scripts/ 下。配置脚本补充 C / H / Python / spec / TOML / PowerShell / shell 属性，保留原有属性内容。

VS Code 内置 Git 已通过 `git show --textconv` 加载历史文件，无需添加不存在的 `git.useTextconv` 设置。重新打开原差异标签即可；若旧内容仍被缓存，运行「Developer: Reload Window」。

检查结果：本机历史 app_version.py 与当前工作区均显示为源码，输出不含 TSD 头，版本行差异可见。原全局配置备份保存在本工程忽略目录 `build/git-diff-check/original.gitconfig`。

参考：[Git textconv 文档](https://git-scm.com/docs/gitattributes#_performing_text_diffs_of_binary_files)、[VS Code 内置 Git 的历史文件加载实现](https://github.com/microsoft/vscode/blob/main/extensions/git/src/git.ts)。
