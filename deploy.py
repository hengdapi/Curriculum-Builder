import subprocess
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
        "--include-qt-plugins=sensible,sqldrivers",
        "--assume-yes-for-downloads",
        "--mingw64",
        "--show-memory",
        "--show-progress",
        "--windows-icon-from-ico=logo.ico",  # 设置应用程序图标
        "--output-filename=School-Timetable-Generator.exe",  # 指定输出主程序文件名
        # ── 项目数据文件 ──
        "--include-data-dir=images=images",
        "--include-data-file=logo.ico=logo.ico",
        "--include-data-file=template.xlsx=template.xlsx",
        "--include-data-file=app_version.txt=app_version.txt",
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


subprocess.run(" ".join(args))
