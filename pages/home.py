# coding=utf-8
import os,time
from style import *
from PySide6.QtWidgets import QFrame,QVBoxLayout


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
        write(f"本程序是基于GPLv3协议的免费开源软件\ncopyright © 2026-{time.strftime("%Y", time.localtime())} Hengdapi",self,layout,10)
        self.project_link=button("打开项目地址",self,layout)
        self.project_link.setIcon(FluentIcon.GITHUB)
        self.project_link.setFixedSize(200, 40)
        self.project_link.clicked.connect(lambda:os.system("start https://github.com/hengdapi/School-Timetable-Generater"))

        self.feedback_label=subheader("反馈",self,layout,10)

        self.email_label=write("如果发现bug或者有更好的建议，欢迎反馈",self,layout,10)

        self.save_log=button("打开日志文件夹",self,layout,10)
        self.save_log.setIcon(FluentIcon.FOLDER)
        self.save_log.setFixedSize(200, 40)
        self.save_log.clicked.connect(lambda:os.system('start explorer /select,"log.txt"'))

        self.feedback_layout=QHBoxLayout(self)
        layout.addLayout(self.feedback_layout)
        self.send_issue=PrimaryPushButton()
        self.send_issue.setText("创建议题")
        add_widget(self.send_issue,self.feedback_layout)
        self.send_issue.setIcon(FluentIcon.GITHUB)
        self.send_issue.setFixedSize(130, 40)
        self.send_issue.clicked.connect(lambda:os.system("start https://github.com/hengdapi/School-Timetable-Generater/issues"))

        self.feedback_button=button("问卷反馈",self,self.feedback_layout)
        self.feedback_button.setIcon(FluentIcon.FEEDBACK)
        self.feedback_button.setFixedSize(130, 40)
        self.feedback_button.clicked.connect(lambda:os.system("start https://v.wjx.cn/vm/mLVfiDq.aspx#"))
        self.feedback_layout.addStretch(1)

        layout.addStretch(1)  # 添加一个可伸缩的空间，值越大伸缩性越强
        self.setLayout(layout)