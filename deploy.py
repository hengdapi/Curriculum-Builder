import os
import sys

if sys.platform == "win32":
    args = [
        sys.executable,  # 使用当前Python解释器
        "-m",
        "nuitka",
        "--standalone",
        # "--windows-uac-admin",
        "--windows-disable-console",
        "--plugin-enable=pyside6",
        # 关键：包含 imageformats 用于 SVG 渲染，platforms/styles 保底
        "--include-qt-plugins=all",
        # 确保深度追踪所有 import（尤其是 qfluentwidgets_pro 的复杂引用）
        "--follow-imports",
        "--assume-yes-for-downloads",
        "--mingw64",
        "--show-memory",
        "--show-progress",
        "--windows-icon-from-ico=logo.ico",  # 设置应用程序图标
        # ── 项目数据文件 ──
        "--include-data-dir=images=images",
        "--include-data-file=logo.ico=logo.ico",
        "--include-data-file=template.xlsx=template.xlsx",
        # ── qfluentwidgets_pro 资源文件（QSS / SVG / i18n 等）──
        "--include-data-dir=qfluentwidgets_pro/_rc=qfluentwidgets_pro/_rc",
        # ── 显式包含所有自定义包（防止 CI 环境路径差异导致遗漏）──
        "--include-package=pages",
        "--include-package=locals",
        "--include-package=style",
        "--include-package=wr_settings",
        "--include-package=save_core",
        "--include-package=generate_core",
        "--include-package=qfluentwidgets_pro",
        "--include-package=qfluentwidgets_pro.common",
        "--include-package=qfluentwidgets_pro.components",
        "--include-package=qfluentwidgets_pro.qframelesswindow",
        # 排除不必要的大型包以减小体积
        "--nofollow-import-to=pytest,unittest,test",
        "main.py",
    ]

elif sys.platform == "darwin":
    args = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--plugin-enable=pyside6",
        "--show-memory",
        "--show-progress",
        "--macos-create-app-bundle",
        "--assume-yes-for-download",
        "--macos-disable-console",
        "main.py",
    ]
else:
    args = [
        sys.executable,
        "-m",
        "pyinstaller",
        "-w",
        "main.py",
    ]


os.system(" ".join(args))
