"""
Inno Setup 安装脚本生成器
由 GitHub Actions 在打包时调用，根据环境变量 APP_VERSION 动态生成 installer.iss
"""
import os

VERSION = os.environ.get("APP_VERSION", "0.0.0")

ISS_TEMPLATE = f'''#define MyAppName "课程表生成器"
#define MyAppVersion "v{VERSION}"
#define MyAppPublisher "Hengxiaopi"
#define MyAppURL "https://school-timetable-generator.hengxiaopi.dpdns.org/"
#define MyAppExeName "School-Timetable-Generator.exe"

[Setup]
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
;AppVerName={{#MyAppName}} {{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\School-Timetable-Generator
DisableProgramGroupPage=yes
; [Icons] 的“quicklaunchicon”条目使用 {{userappdata}}，而其 [Tasks] 条目具有适合 IsAdminInstallMode 的检查。
UsedUserAreasWarning=no
LicenseFile=LICENSE
; 移除以下行，以在管理安装模式下运行（为所有用户安装）。
PrivilegesRequired=lowest
OutputDir=.
OutputBaseFilename=School-Timetable-Generator-v{VERSION}-Windows-x86_64-Setup
SetupIconFile=logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{{cm:CreateQuickLaunchIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "main.dist\\main.exe"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "main.dist\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs
; 注意: 不要在任何共享系统文件上使用“Flags: ignoreversion”

[Icons]
Name: "{{autoprograms}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: quicklaunchicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
'''

def main():
    output_path = os.path.join(os.path.dirname(__file__), '..', 'installer.iss')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ISS_TEMPLATE)
    print(f"[OK] installer.iss generated (version={VERSION})")
    print(f"     Output: {os.path.abspath(output_path)}")


if __name__ == '__main__':
    main()
