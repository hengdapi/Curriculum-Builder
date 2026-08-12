# coding=utf-8
import webbrowser,time

from PySide6.QtGui import QIcon

from locals import project_url,check_update,app_version,github_url
from style import *
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame,QVBoxLayout

class IssueHelp(MessageBoxBase):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.title=SubtitleLabel("创建议题")
        add_widget(self.title,self.viewLayout)
        self.image=ImageLabel("images/issue_help.png")
        self.image.setFixedSize(700,230)
        add_widget(self.image,self.viewLayout)
        self.content_label=write("如果您不熟悉issue，请您详细阅读以上图片，了解如何创建议题。",self,self.viewLayout)
        self.content_label.setWordWrap(True)
        add_widget(self.content_label,self.viewLayout)
        self.yesButton.setText("打开议题页面")
        self.cancelButton.setText("关闭")

    def validate(self) -> bool:
        webbrowser.open(f"{project_url}/issues")
        return False

class Home(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.setObjectName("Home")
        layout=QVBoxLayout(self)
        layout.setContentsMargins(20,20,0,0)

        self.title = title("主页",self,layout)

        self.welcome_label=subheader("欢迎使用课程表生成器！😀",self,layout,10)

        self.introduce_label=write("此工具可以帮助你生成符合需求的课程表，现在请在设置页面上填写信息，生成一个课程表吧！",self,layout)

        subheader("关于",self,layout,10)
        write(f"本程序是基于GPLv3协议的免费开源软件\ncopyright © 2026-{time.strftime("%Y", time.localtime())} Hengxiaopi\n当前版本：{app_version}",self,layout,10)
        self.about_layout=QHBoxLayout(self)
        layout.addLayout(self.about_layout)
        self.project_link=DropDownPushButton(FluentIcon.GLOBE,"打开项目页面")
        self.project_link.setFixedSize(170, 40)
        project_menu=RoundMenu(parent=self.project_link)
        project_menu.addAction(Action(QIcon("images/gitcode.png"),"GitCode",triggered=lambda:webbrowser.open(project_url)))
        project_menu.addAction(Action(FluentIcon.GITHUB,"GitHub",triggered=lambda:webbrowser.open(github_url)))
        self.project_link.setMenu(project_menu)
        add_widget(self.project_link,self.about_layout,10)

        self.check_update_button=button("检查更新",self,self.about_layout)
        self.check_update_button.setIcon(FluentIcon.UPDATE)
        self.check_update_button.setFixedSize(130, 40)
        self.check_update_button.clicked.connect(lambda:check_update(self,True))
        self.about_layout.addStretch(1)
        layout.addSpacing(20)

        self.feedback_label=subheader("反馈",self,layout,10)

        self.email_label=write("如果发现bug或者有更好的建议，欢迎反馈",self,layout,10)

        self.feedback_layout=QHBoxLayout(self)
        layout.addLayout(self.feedback_layout)
        self.save_log=button("复制日志内容",self,self.feedback_layout,10)
        self.save_log.setIcon(FluentIcon.COPY)
        self.save_log.setFixedSize(170, 40)
        self.save_log.clicked.connect(self.copy_log)

        self.send_issue=button("创建议题",self,self.feedback_layout,10)
        self.send_issue.setIcon(FluentIcon.FEEDBACK)
        self.send_issue.setFixedSize(130, 40)
        self.send_issue.clicked.connect(self.on_send_issue)
        self.feedback_layout.addStretch(1)

        layout.addStretch(1)  # 添加一个可伸缩的空间，值越大伸缩性越强
        self.setLayout(layout)

        QTimer.singleShot(500, lambda: check_update(self))

    def on_send_issue(self):
        help_messagebox=IssueHelp(self.parent().parent().parent())
        help_messagebox.exec()

    def copy_log(self):
        with open("log.txt","r",encoding="utf-8") as f:
            log=f.read()
            QApplication.clipboard().setText(log)
        InfoBar.success("日志内容已复制到剪贴板","",parent=self,duration=2000)