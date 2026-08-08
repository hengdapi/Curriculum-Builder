# coding=utf-8
import webbrowser,time

from locals import project_url,check_update
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
        write(f"本程序是基于GPLv3协议的免费开源软件\ncopyright © 2026-{time.strftime("%Y", time.localtime())} Hengxiaopi",self,layout,10)
        self.project_link=button("打开项目地址",self,layout)
        self.project_link.setIcon(FluentIcon.LINK)
        self.project_link.setFixedSize(200, 40)
        self.project_link.clicked.connect(lambda:webbrowser.open(project_url))

        self.feedback_label=subheader("反馈",self,layout,10)

        self.email_label=write("如果发现bug或者有更好的建议，欢迎反馈",self,layout,10)

        self.feedback_layout=QHBoxLayout(self)
        layout.addLayout(self.feedback_layout)
        self.save_log=button("复制日志内容",self,self.feedback_layout,10)
        self.save_log.setIcon(FluentIcon.COPY)
        self.save_log.setFixedSize(170, 40)
        self.save_log.clicked.connect(self.copy_log)

        self.send_issue=button("创建议题",self,self.feedback_layout,10)
        self.send_issue.setIcon(FluentIcon.LINK)
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