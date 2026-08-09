from __future__ import annotations

import requests,json,webbrowser
import sys,copy
from typing import Literal,Any
from threading import Thread
from packaging import version

import pandas as pd
from PySide6.QtWidgets import QTableWidgetItem,QTableWidget,QApplication
from PySide6.QtCore import QTimer
from qfluentwidgets_pro import TableWidget,PrimaryPushButton,PushButton,FluentIcon,TextEdit

from wr_settings import *
with open("app_version.txt","r",encoding="utf-8") as f:
    app_version=f.read()
logging.basicConfig(format="[%(levelname)s] %(asctime)s %(filename)s %(funcName)s %(lineno)d行:\t%(message)s",
                    level=logging.INFO,
                    filename=None,
                    encoding="utf-8")

file_handler = logging.FileHandler("log.txt", mode="a", encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s %(filename)s %(funcName)s %(lineno)d行:\t%(message)s"))
logging.getLogger().addHandler(file_handler)

appdata=os.path.join(os.environ["APPDATA"],"School-Timetable-Generator")

def check_update(window):
    try:
        url="https://api.gitcode.com/api/v5/repos/2603_96523924/School-Timetable-Generator/releases/latest"

        payload={}
        headers={
            'Accept':'application/json'
        }

        response=requests.get(url,headers=headers,data=payload).json()
        logging.debug(f"检查更新api返回内容：{response}")

        if version.parse(response["tag_name"])<=version.parse(app_version):
            return
        logging.info(f"发现新版本：{response['tag_name']}")
        window.update_msg=Toast.info("发现新版本",f"新版本 {response["tag_name"]} 现已发布，更新内容如下：",duration=-1,parent=window)
        change_log=TextEdit()
        change_log.setMarkdown(response["body"])
        change_log.setReadOnly(True)
        change_log.setFixedSize(280,response["body"].count("\n")*30)
        change_log.setStyleSheet("background-color:transparent; border: none;")
        window.update_msg.addWidget(change_log,alignment=Qt.AlignmentFlag.AlignLeft)
        view_update_button=PushButton()
        view_update_button.setIcon(FluentIcon.INFO)
        view_update_button.setText("查看详细信息")
        view_update_button.clicked.connect(lambda:webbrowser.open(f"{project_url}/releases/{response["tag_name"]}"))
        window.update_msg.addWidget(view_update_button, alignment=Qt.AlignmentFlag.AlignLeft)
        download_button=PrimaryPushButton()
        download_button.setIcon(FluentIcon.DOWNLOAD)
        download_button.setText("下载新版本")
        download_button.clicked.connect(lambda:download_update(window,response))
        window.update_msg.addWidget(download_button, alignment=Qt.AlignmentFlag.AlignLeft)
        window.update_msg.show()

    except Exception as err:
        e=traceback.format_exc()
        logging.critical(f"检查更新出错：\n{e}")
        show_error(window,err)

class UpdateThread(Thread):
    def __init__(self,response:dict):
        super().__init__()
        self.response=response

    def run(self):
        try:
            logging.info("开始下载更新")
            download_url=None
            for asset in self.response["assets"]:
                if asset["name"].endswith("Setup.exe"):
                    download_url:str=asset.get("browser_download_url")
                    break
            if download_url is None:
                logging.error("未找到安装包")
                return
            logging.info(f"找到最新版本，开始从 {download_url} 下载")

            r = requests.get(download_url,stream=True)
            with open("update.exe", "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            logging.info("下载完成，自动运行安装包update.exe")
            os.startfile("update.exe")
        except Exception as err:
            e=traceback.format_exc()
            logging.critical(f"下载更新出错：\n{e}")

def download_update(window,response:dict):
    try:
        window.update_msg.close()
        Toast.info("正在后台下载更新","下载完成后将为您自动运行安装包",duration=3000,parent=window)
        update_thread=UpdateThread(response)
        logging.debug("更新线程已创建")
        update_thread.start()
    except Exception as err:
        e=traceback.format_exc()
        logging.critical(f"下载更新出错：\n{e}")
        show_error(window,err)

def lesson2str(lesson):
    """
    根据课程节次生成时间描述

    :param lesson: 课程节次
    :return: 时间描述（如"上午第1节"）
    """
    # 判断课程是在上午还是下午
    if lesson<=cfg.morning_class_num.value:
        time="上午"
    else:
        time="下午"
        # 调整课程节次为下午的相对节次
        lesson-= cfg.morning_class_num.value

    return f"{time}第{lesson}节"

def str2subject(subject_name:str)->Subject:
    """
    去除前缀，查找 Subject 对象
    """
    clean_name=subject_name
    for prefix in ["【连】","【单】","【双】"]:
        if clean_name.startswith(prefix):
            clean_name=clean_name[len(prefix):]
            break
    return lesson_info.subjects[clean_name]

def show_error(page,error:Exception):
    Toast.error("发生错误",str(error)+"\n错误信息已存入日志，可通过首页按钮反馈",duration=-1,parent=page)

def restart_app(delay_ms=100):
    """重启程序"""
    logging.info(f'重启程序，sys.executable:{sys.executable}，sys.argv:{sys.argv}')

    def _restart():
        app=QApplication.instance()
        if app:
            app.quit()
            app.processEvents()
        os.execl(sys.executable,sys.executable,*sys.argv)

    QTimer.singleShot(delay_ms,_restart)

def is_special(subject:str):
    """
    判断给定的课程名称是否为特殊课程

    :param subject: 课程名称
    :return: 如果课程是特殊课程，则返回True；否则返回False
    """
    return subject.endswith("(0.5)") or subject.endswith("（0.5）")

# 定义工作日列表
days = ["","星期一", "星期二", "星期三", "星期四", "星期五"]

def display_df_in_table(table_widget: TableWidget|QTableWidget, df: pd.DataFrame):
    table_widget.clear()
    df.columns=df.columns.astype(str)
    # 设置行数和列数
    table_widget.setRowCount(df.shape[0])
    table_widget.setColumnCount(df.shape[1])

    # 设置表头
    table_widget.setHorizontalHeaderLabels(df.columns)
    table_widget.setVerticalHeaderLabels([str(idx) for idx in df.index])

    # 填充数据
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            if str(df.iat[i, j]) in ["nan","None"]:
                continue
            item = QTableWidgetItem(str(df.iat[i, j]))
            item.setTextAlignment(Qt.AlignCenter)
            table_widget.setItem(i, j, item)

def table_style(content=None)->pd.DataFrame:
    table_style={}
    for day in days[1:]:
        table_style[day]={}
        for lesson in range(1,cfg.morning_class_num.value+1):
            table_style[day][f"上午第{lesson}节"]=content
        for lesson in range(1,cfg.afternoon_class_num.value+1):
            table_style[day][f"下午第{lesson}节"]=content
    return pd.DataFrame(table_style)

def class_total_dataframe()->pd.DataFrame:
    data={}
    for clas in lesson_info.class_lst:
        data[clas.name]={}
        timetable=clas.timetable_dataframe.to_dict()
        for day,lessons in timetable.items():
            for time,lesson in lessons.items():
                data[clas.name][day+time]=lesson
    return pd.DataFrame(data).transpose()

def teacher_total_dataframe()->pd.DataFrame:
    data={}
    for teacher in lesson_info.teachers.values():
        data[teacher.name]={}
        timetable=teacher.timetable_dataframe.to_dict()
        for day,lessons in timetable.items():
            for time,lesson in lessons.items():
                data[teacher.name][day+time]=lesson
    dataframe=pd.DataFrame(data).transpose()
    dataframe=dataframe[[str(Time(day,lesson)) for day in range(1,6) for lesson in range(1,cfg.morning_class_num.value+cfg.afternoon_class_num.value+1)]]
    return dataframe

class Time:
    def __init__(self,day:int=0,lesson:int=0,week:Literal["sin","dou","all"]="all",string:str|None=None):
        if string:
            if "【单】" in string:
                self.week="sin"
                string=string.replace("【单】","")
            elif "【双】" in string:
                self.week="dou"
                string=string.replace("【双】","")
            else:
                self.week="all"
            self.day=days.index(string[:3])
            self.lesson=int(string[6:-1])
            if "下午" in string:
                self.lesson+=cfg.morning_class_num.value
        else:
            self.day=day
            self.lesson=lesson
            self.week=week
        self.sin=(self.week=="sin")
        self.dou=(self.week=="dou")
        self.all=(self.week=="all")
        self.half=not self.all
    def __eq__(self, other):
        if not isinstance(other,Time):
            return False
        return self.day==other.day and self.lesson==other.lesson and self.week==other.week
    def __hash__(self):
        return hash((self.day,self.lesson,self.week))
    def __str__(self):
        return {"sin":"【单】","dou":"【双】","all":""}[self.week]+days[self.day]+lesson2str(self.lesson)

    def to_str(self,day:bool,lesson:bool,week:bool=False):
        string=""
        if week:
            string+={"sin":"【单】","dou":"【双】","all":""}[self.week]
        if day:
            string+=days[self.day]
        if lesson:
            string+=lesson2str(self.lesson)
        return string

    @property
    def sin_week(self):
        return Time(self.day,self.lesson,"sin")
    @property
    def dou_week(self):
        return Time(self.day,self.lesson,"dou")
    @property
    def all_week(self):
        return Time(self.day,self.lesson,"all")

    @property
    def next(self):
        next_time=self.all_week
        if self.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
            if self.day==5:
                next_time.day=next_time.lesson=1
            else:
                next_time.day+=1
                next_time.lesson=1
        else:
            next_time.lesson+=1
        return next_time

    @property
    def prev(self):
        prev_time=self.all_week
        if self.lesson==1:
            if self.day==1:
                prev_time.day=5
                prev_time.lesson=cfg.morning_class_num.value+cfg.afternoon_class_num.value
            else:
                prev_time.day-=1
                prev_time.lesson=cfg.morning_class_num.value+cfg.afternoon_class_num.value
        else:
            prev_time.lesson-=1
        return prev_time

class Teacher:
    """
    教师类，用于管理教师的课程时间
    """
    def __init__(self, name:str):
        """
        初始化教师对象

        :param name: 教师姓名
        """
        self.name = name
        self.timetable:dict[Time,tuple[Class,Subject]]={}  # 记录教师已占用的课程时间

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if not isinstance(other, Teacher):
            return False
        return self.name==other.name

    def __hash__(self):
        return hash(self.name)

    def add_lesson(self,time:Time,clas:Class,subject:Subject):
        """
        添加教师的课程时间
        """
        self.timetable[time]=(clas,subject)

    def is_busy(self,time:Time):
        """
        检查教师在特定时间是否有课
        :return: 是否有课
        """
        if time.all:
            return time.dou_week in self.timetable or time.sin_week in self.timetable or time.all_week in self.timetable
        elif time.sin:
            return time.sin_week in self.timetable or time.all_week in self.timetable
        else:
            return time.dou_week in self.timetable or time.all_week in self.timetable

    def remove_lesson(self,time:Time):
        """
        移除教师在特定时间上的课程
        """
        self.timetable.pop(time)

    @property
    def timetable_dataframe(self)->pd.DataFrame:
        data=copy.deepcopy(table_style())
        for time,lesson in self.timetable.items():
            if data.loc[time.to_str(False,True),time.to_str(True,False)]:
                lines=data.loc[time.to_str(False,True),time.to_str(True,False)].split("\n")
                lines[0]+=f"/{lesson[0]}"
                lines[1]+=f"/{time.to_str(False,False,True)}{lesson[1]}"
                data.loc[time.to_str(False,True),time.to_str(True,False)]="\n".join(lines)
            else:
                data.loc[time.to_str(False,True),time.to_str(True,False)]=f"{lesson[0]}\n{time.to_str(False,False,True)}{lesson[1]}"
        return data

class Subject:
    def __init__(self, name:str):
        """
        初始化课程对象

        :param name: 课程名称
        """
        self.name = name
        self.continuous=False
        self.continue_times:dict[Class,int]={}
        self.time_list:dict[Time,int]={Time(day,lesson):0 for day in range(1,6) for lesson in range(1,cfg.morning_class_num.value+cfg.afternoon_class_num.value+1)}
        self.timetable:dict[Time,list[Class]]={Time(day,lesson):[] for day in range(1,6) for lesson in range(1,cfg.morning_class_num.value+cfg.afternoon_class_num.value+1)}

    def __str__(self):
        if self.continuous:
            return f"【连】{self.name}"
        return self.name

    def __eq__(self, other):
        if not isinstance(other,Subject):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def get_time_num(self,time:Time):
        return self.time_list[time]

    def add_lesson(self,clas:Class,time:Time):
        self.time_list[time]+=1
        self.timetable[time].append(clas)

    def remove_lesson(self,clas:Class,time:Time):
        self.time_list[time]-=1
        self.timetable[time].remove(clas)

    def to_continuous_lesson(self):
        subject2=copy.copy(self)
        subject2.continuous=True
        return subject2

    def to_normal_lesson(self):
        subject2=copy.copy(self)
        subject2.continuous=False
        return subject2

class Class:
    def __init__(self,name,teachers:dict[str,Teacher]):
        """
        初始化班级对象

        :param name: 班级名称
        :param teachers: 班级任课教师列表({学科:老师})
        """
        self.name=name
        self.teachers=teachers
        self.timetable:dict[Time,list[Subject]]={Time(day,lesson):[] for day in range(1,6) for lesson in range(1,cfg.morning_class_num.value+cfg.afternoon_class_num.value+1)}
        self.left_subjects:list[Subject]=[]

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __json__(self):
        timetable={}
        for time,subjects in self.timetable.items():
            timetable[str(time)]=[subject.name for subject in subjects]
        return timetable

    def get_teacher(self,subject:Subject):
        return self.teachers[subject.name]

    def get_subject_num(self,subject:Subject)->int:
        return self.left_subjects.count(subject)

    def add_lesson(self,time:Time,subject:Subject):
        if subject in half_subjects and time.all:
            if not self.get_lessons(time):
                time=time.sin_week
            else:
                time=time.dou_week
        logging.debug(f"在 {self.name} 的 {time} 安排 {subject}")
        self.get_teacher(subject).add_lesson(time,self,subject)
        time=time.all_week
        if time in self.timetable:
            self.timetable[time].append(subject)
        else:
            self.timetable[time]=[subject]
        if subject.continuous:
            if self not in lesson_info.subjects[subject.name].continue_times:
                lesson_info.subjects[subject.name].continue_times[self]=0
            lesson_info.subjects[subject.name].continue_times[self]+=0.5
        subject.add_lesson(self,time)
        self.left_subjects.remove(subject)

    def remove_lesson(self,time:Time):
        subjects=self.get_lessons(time)
        if subjects:
            if time.all and len(subjects)==2:
                self.remove_lesson(time.dou_week)
                self.remove_lesson(time.sin_week)
                return
            if len(subjects)==1 and subjects[0] in half_subjects:
                time=time.sin_week
            if time.sin or time.all:
                subject=subjects[0]
            elif len(subjects)==2:
                subject=subjects[1]
            else:
                return
            logging.debug(f"删除 {self} {time} 的 {subject}")
            self.get_teacher(subject).remove_lesson(time)
            time=time.all_week
            self.timetable[time].remove(subject)
            if subject.continuous:
                lesson_info.subjects[subject.name].continue_times[self]-=0.5
            subject.remove_lesson(self,time)
            self.left_subjects.append(subject)

    def get_lessons(self,time:Time)->list[Subject]|None:
        return copy.copy(self.timetable.get(time.all_week))

    @property
    def timetable_dataframe(self)->pd.DataFrame:
        data=copy.deepcopy(table_style())
        for time,subjects in self.timetable.items():
            if len(subjects)==1:
                subject=subjects[0]
                data.loc[time.to_str(False,True),time.to_str(True,False)]=str(subject)
                if cfg.show_teachers.value:
                    data.loc[time.to_str(False,True),time.to_str(True,False)]+=f"\n{self.get_teacher(subject)}"
            elif len(subjects)==2:
                data.loc[time.to_str(False,True),time.to_str(True,False)]=f"【单】{subjects[0]}/"
                data.loc[time.to_str(False,True),time.to_str(True,False)]+=f"【双】{subjects[1]}"
                if cfg.show_teachers.value:
                    data.loc[time.to_str(False,True),time.to_str(True,False)]+=f"\n【单】{self.get_teacher(subjects[0])}/"
                    data.loc[time.to_str(False,True),time.to_str(True,False)]+=f"【双】{self.get_teacher(subjects[1])}"
        return data

class LessonInfoEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if hasattr(o, "__json__"):
            return o.__json__()
        return super().default(o)

class Rule_type:
    set_time="set_time"
    avoid_time="avoid_time"
    priority_time="priority_time"
    set_num="set_num"
    avoid_subject="avoid_subject"
    avoid_teacher="avoid_teacher"
    set_continue="set_continue"
    half_num="half_num"

rule_types={
    "set_time": "{subject}|学科必须排在|{time}",
    "avoid_time": "{subject}|学科不能排在|{time}",
    "priority_time": "{subject}|学科优先排在|{time}",
    "set_num": "{subject}|学科同一时间最多排|{number}|节课",
    "avoid_subject": "{subjectA}|学科与|{subjectB}|学科不能排在同一时间",
    "avoid_teacher": "{teacherA}|老师与|{teacherB}|老师不能在同一时间有课",
    "set_continue": "{subject}|学科每周连堂|{number}|次",
    "half_num": "{subject}|学科两周排一次课（即单双周）"
}

class Rule:
    def __init__(self,**kwargs):
        self.type=kwargs["type"]
        self.time=self.subject=self.number=self.subjectA=self.subjectB=self.teacherA=self.teacherB=None
        if self.type in [Rule_type.set_time,Rule_type.avoid_time,Rule_type.priority_time]:
            self.time=Time(string=kwargs["time"])
        if self.type in [Rule_type.set_time,Rule_type.avoid_time,Rule_type.priority_time,Rule_type.set_num,Rule_type.set_continue,Rule_type.half_num]:
            self.subject=lesson_info.subjects.get(kwargs["subject"])
        if self.type in [Rule_type.set_num,Rule_type.set_continue]:
            self.number=kwargs["number"]
        if self.type==Rule_type.avoid_subject:
            self.subjectA=lesson_info.subjects.get(kwargs["subjectA"])
            self.subjectB=lesson_info.subjects.get(kwargs["subjectB"])
        if self.type==Rule_type.avoid_teacher:
            self.teacherA=lesson_info.teachers.get(kwargs["teacherA"])
            self.teacherB=lesson_info.teachers.get(kwargs["teacherB"])

    def __str__(self):
        ans=rule_types[self.type].replace("|","").replace("{"," ").replace("}"," ")
        for string in self.__dict__:
            if string=="type" or self.__dict__[string] is None:
                continue
            ans=ans.replace(string,str(self.__dict__[string]))
        return ans

    def to_dict(self)->dict:
        ans={}
        for string in self.__dict__:
            if self.__dict__[string] is None:
                continue
            ans[str(string)]=str(self.__dict__[string])
        return ans

    def __eq__(self, other):
        if not isinstance(other,Rule):
            return False
        return self.type==other.type and self.__dict__==other.__dict__

# 解析课程信息
class LessonInfo:
    def __init__(self):
        self.teachers: dict[str,Teacher]={}
        self.subjects: dict[str,Subject]={}
        self.classes: dict[str,Class]={}
        self.class_names:list[str]=[]
        self.class_lst:list[Class]=[]
        self.saved=True
        logging.info("正在解析课程信息...")
        
        lessons=cfg.lessons_info.value
        subjects_str=cfg.subjects_info.value
        teachers_str=cfg.teachers_info.value
        
        logging.debug(f"课程信息：{len(lessons)}个班级，{len(subjects_str)}个科目，{len(teachers_str)}个老师")
        
        for subject in subjects_str:
            self.subjects[subject]=Subject(subject)
        logging.debug(f"已创建 {len(self.subjects)} 个科目对象")
        
        for teacher in teachers_str:
            self.teachers[teacher]=Teacher(teacher)
        logging.debug(f"已创建 {len(self.teachers)} 个教师对象")
        
        for idx, clas in enumerate(lessons):
            class_name=clas["班级"]
            self.classes[class_name]=Class(class_name,{})
            self.class_names=list(self.classes.keys())
            self.class_lst=[self.classes[clas_name] for clas_name in self.class_names]
            total_lessons=0
            for subject in subjects_str:
                if clas[subject+" - 任课老师"]:
                    self.classes[class_name].teachers[subject]=self.teachers[clas[subject+" - 任课老师"]]
                    lesson_count=int(clas[subject+" - 课时"])
                    for i in range(lesson_count):
                        self.classes[class_name].left_subjects.append(self.subjects[subject])
                    total_lessons+=lesson_count
            logging.debug(f"解析班级 {idx+1}/{len(lessons)}：{len(self.classes[class_name].teachers)} 位任课老师，{total_lessons} 节课")
        
        for subject in self.subjects.values():
            subject.continue_times={clas:0 for clas in self.class_lst}

        self.rules: list[Rule]=[]
        sys.setrecursionlimit(max(len(self.classes)*5*(cfg.morning_class_num.value+cfg.afternoon_class_num.value)*2,1000))
        logging.info("课程信息解析完成")
lesson_info=LessonInfo()

priority_subjects:dict[Time,list[Subject]]={}
half_subjects:set[Subject]=set()
continue_num:dict[Subject,int]={}
set_lessons:list[tuple[Time,Subject]]=[]

for rule in cfg.rules.value:
    rule=Rule(**rule)
    lesson_info.rules.append(rule)
    if rule.type==Rule_type.set_time:
        set_lessons.append((rule.time,rule.subject))
    elif rule.type==Rule_type.priority_time:
        if rule.time not in priority_subjects:
            priority_subjects[rule.time]=[rule.subject]
        else:
            priority_subjects[rule.time].append(rule.subject)
    elif rule.type==Rule_type.half_num:
        half_subjects.add(rule.subject)
    elif rule.type==Rule_type.set_continue:
        continue_num[rule.subject]=int(rule.number)

logging.info("课程信息解析完毕，生成初始化完成")

def diff_cfg(new_classes:list,new_teachers:list,new_subjects:list)->tuple[set,set,set]:
    old_classes=set(lesson_info.class_names)
    diff_classes=old_classes-set(new_classes)
    diff_teachers=set(lesson_info.teachers)-set(new_teachers)
    diff_subjects=set(lesson_info.subjects)-set(new_subjects)
    return diff_classes,diff_teachers,diff_subjects

def del_cfg_diff(diff_classes:set,diff_teachers:set,diff_subjects:set)->None:
    for grade,classes in cfg.grades_info.value.items():
        cfg.grades_info.value[grade]=list(set(classes)-diff_classes)
        cfg.grades_info.value[grade].sort(key=lambda clas:lesson_info.class_names.index(clas))
    new_rules=copy.copy(cfg.rules.value)
    for rule in cfg.rules.value:
        if rule.get("subject") in diff_subjects or rule.get("subjectA") in diff_subjects or rule.get("subjectB") in diff_subjects or rule.get("teacherA") in diff_teachers or rule.get("teacherB") in diff_teachers:
            new_rules.remove(rule)
    cfg.rules.value=new_rules

project_url="https://gitcode.com/2603_96523924/School-Timetable-Generator"