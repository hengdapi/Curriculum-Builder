"""
Inno Setup 安装脚本生成器
由 GitHub Actions 在打包时调用，根据环境变量 APP_VERSION 动态生成 installer.iss
"""
import os

VERSION = os.environ.get("APP_VERSION", "0.0.0")

ISS_TEMPLATE = f'''; ─── 课程表生成器 - Inno Setup 安装脚本（自动生成）─────────────────
#define MyAppName "课程表生成器"
#define MyAppVersion "{VERSION}"
#define MyAppPublisher "School Timetable Generator"
#define MyAppURL "https://gitcode.com/2603_96523924/School-Timetable-Generator"
#define MyAppExeName "main.exe"

[Setup]
AppId={{{{B8F5A3D2-7C1E-4A9D-B6F2-E8D4C1A5F9B3}}}}
AppName={{{{#MyAppName}}}}
AppVersion={{{{#MyAppVersion}}}}
AppPublisher={{{{#MyAppPublisher}}}}
AppPublisherURL={{{{#MyAppURL}}}}
AppSupportURL={{{{#MyAppURL}}}}
AppUpdatesURL={{{{#MyAppURL}}}}
DefaultDirName={{autopf}}\\School-Timetable-Generator
; 不允许用户修改安装目录，统一管理
DisableDirPage=yes
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=School-Timetable-Generator-v{VERSION}-Setup
SetupIconFile=logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; 要求管理员权限（写入 Program Files）
PrivilegesRequired=admin
UninstallDisplayIcon={{app}}\\{{#MyAppExeName}}

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

[Files]
Source: "main.dist\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{autoprograms}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent

[Code]
; 安装前检查是否已存在旧版本并提示卸载
function InitializeSetup: Boolean;
var
  UninstallKey: String;
  UninstallPath: String;
  ResultCode: Integer;
begin
  Result := True;
  UninstallKey := 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{{{{B8F5A3D2-7C1E-4A9D-B6F2-E8D4C1A5F9B3}}}}_is1';
  
  if RegQueryStringValue(HKLM, UninstallKey, 'UninstallString', UninstallPath) then
  begin
    if MsgBox('检测到已安装旧版本，是否先卸载再继续？', mbConfirmation, MB_YESNO) = IDYES then
    begin
      if not ShellExec('', UninstallPath, '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
      begin
        MsgBox('卸载失败，请手动卸载后重试。', mbError, MB_OK);
        Result := False;
      end;
    end
    else
      Result := False;
  end;
end;
'''

def main():
    output_path = os.path.join(os.path.dirname(__file__), '..', 'installer.iss')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ISS_TEMPLATE)
    print(f"[OK] installer.iss generated (version={VERSION})")
    print(f"     Output: {os.path.abspath(output_path)}")


if __name__ == '__main__':
    main()
