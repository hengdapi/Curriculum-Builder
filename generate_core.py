import random
import time

from locals import *


def check(clas: Class,time: Time,subject: Subject,failed_reasons=None,conflict_lessons=None) -> bool:
    if conflict_lessons is None:
        conflict_lessons=set()
    if failed_reasons is None:
        failed_reasons=set()
    try:
        reasons_num=len(failed_reasons)
        logging.debug(f"检查能否在 {clas} 的 {time} 安排 {subject}")
        teacher=clas.get_teacher(subject)
        teacher.check(time,subject,failed_reasons,conflict_lessons)
        if subject in clas.set_lessons:
            failed_reasons.add(f"规则冲突：{subject} 是固定课程")
        time=time.all_week
        for rule in lesson_info.rules:
            if clas not in rule.scope:
                continue
            if rule.type==Rule_type.set_time:
                if rule.time==time and rule.subject!=subject:
                    failed_reasons.add(f"规则冲突：{time} 必须排 {rule.subject}")
            # 不能排在指定时间
            elif rule.type==Rule_type.avoid_time:
                # 支持只写节次（如"上午第4节"）
                if rule.subject==subject and time==rule.time:
                    failed_reasons.add(f"规则冲突：{subject} 不能排在 {time} ")
            # 同一时间最多排几节课
            elif rule.type==Rule_type.set_num:
                if rule.subject==subject and subject.get_time_num(time)>=int(rule.number):
                    failed_reasons.add(f"规则冲突：{clas.name} 同一时间 最多排 {rule.number} 节课")
            # 学科不能与另一学科同一时间
            elif rule.type==Rule_type.avoid_subject:
                if subject==rule.subjectA and rule.subjectB.timetable.get(time):
                    failed_reasons.add(f"规则冲突：已经在 {", ".join([clas.name for clas in rule.subjectB.timetable.get(time)])} 的 {time} 安排了与 {subject} 冲突的 {rule.subjectB}")
                if subject==rule.subjectB and rule.subjectA.timetable.get(time):
                    failed_reasons.add(f"规则冲突：已经在 {", ".join([clas.name for clas in rule.subjectA.timetable.get(time)])} 的 {time} 安排了与 {subject} 冲突的 {rule.subjectA}")
            # 老师不能与另一老师同一时间有课
            elif rule.type==Rule_type.avoid_teacher:
                teacher=clas.get_teacher(subject)
                teacherA = rule.teacherA
                teacherB = rule.teacherB
                if teacher==teacherA and teacherB.timetable.get(time):
                    failed_reasons.add(f"规则冲突：{clas.name} {subject} 的教师 {teacherA.name} 和 {teacherB.name} 在 {time} 会冲突")
                elif teacher==teacherB and teacherA.timetable.get(time):
                    failed_reasons.add(f"规则冲突：{clas.name} {subject} 的教师 {teacherB.name} 和 {teacherA.name} 在 {time} 会冲突")
        if len(failed_reasons)>reasons_num:
            return False
        return True
    except:
        e=traceback.format_exc()
        logging.error(f"检查时出错：\n{e}")
        return False

def check_exchange(clas:Class,time1:Time,time2:Time,failed_reasons:set,conflict_lessons:set)->bool:
    subjects1=clas.get_lessons(time1)
    subjects2=clas.get_lessons(time2)
    if not subjects1 or not subjects2:
        return False
    # 两个半周课程：检查能否拼接
    if len(subjects1)==1 and subjects1[0] in clas.half_subjects and len(subjects2)==1 and subjects2[0] in clas.half_subjects and check(clas,time2.dou_week,subjects1[0],failed_reasons):
        return True
    # 目标位置是空位：直接检查源课程能否放入
    if not subjects2:
        if len(subjects1)==1:
            return check(clas,time2,subjects1[0],failed_reasons,conflict_lessons)
        elif len(subjects1)==2:
            check1=check(clas,time2.sin_week,subjects1[0],failed_reasons,conflict_lessons)
            check2=check(clas,time2.dou_week,subjects1[1],failed_reasons,conflict_lessons)
            return check1 and check2
        return False
    # 源位置是空位：理论上不应该发生
    if not subjects1:
        return False
    if (time1,subjects1[0]) in clas.set_lessons.items():
        failed_reasons.add(f"规则冲突：{time1} 必须排 {subjects1[0]}")
        return False
    if (time2,subjects2[0]) in clas.set_lessons.items():
        failed_reasons.add(f"规则冲突：{time2} 必须排 {subjects2[0]}")
        return False
    clas.remove_lesson(time1)
    clas.remove_lesson(time2)
    if len(subjects2)==1:
        check1=check(clas,time1,subjects2[0],failed_reasons,conflict_lessons)
    else:
        check1=check(clas,time1.sin_week,subjects2[0],failed_reasons,conflict_lessons)
        check2=check(clas,time1.dou_week,subjects2[1],failed_reasons,conflict_lessons)
        check1=check1 and check2
    if len(subjects1)==1:
        check2=check(clas,time2,subjects1[0],failed_reasons,conflict_lessons)
    else:
        check2=check(clas,time2.sin_week,subjects1[0],failed_reasons,conflict_lessons)
        check3=check(clas,time2.dou_week,subjects1[1],failed_reasons,conflict_lessons)
        check2=check2 and check3
    for subject in subjects1:
        clas.add_lesson(time1,subject)
    for subject in subjects2:
        clas.add_lesson(time2,subject)

    clas.timetable[time1],clas.timetable[time2]=subjects2,subjects1
    check_continue=True
    for subject in subjects1:
        if subject.get_continue_times(clas)<clas.continue_num[subject]:
            check_continue=False
            failed_reasons.add(f"规则冲突：交换后 {subject} 只能连堂 {subject.get_continue_times(clas)} 次（规则要求连堂 {clas.continue_num[subject]} 次） ")
    for subject in subjects2:
        if subject.get_continue_times(clas)<clas.continue_num[subject]:
            check_continue=False
            failed_reasons.add(f"规则冲突：交换后 {subject} 只能连堂 {subject.get_continue_times(clas)} 次（规则要求连堂 {clas.continue_num[subject]} 次） ")
    clas.timetable[time1],clas.timetable[time2]=subjects1,subjects2
    return check1 and check2 and check_continue

class GenerateThread(QThread):
    finished_signal=Signal(set)  # 生成成功
    progress_signal=Signal(tuple)  # 进度信息

    def __init__(self,class_lst:list[Class],parent=None):
        super().__init__(parent)
        self.class_lst=class_lst
        self.last_progress_time=0  # 记录上次发送进度的时间
        self.progress_interval=0.8  # 进度更新间隔（秒）
        self.skipped_lessons:set[tuple[Class,Time]]=set()
        self.tried_times:dict[Class,dict[Time,int]]={clas:{Time(day,lesson):0 for day in range(1,6) for lesson in range(1,cfg.day_class_num+1)} for clas in class_lst}
        logging.debug("创建GenerateThread实例")

    def run(self):
        # 执行耗时的课程表生成逻辑
        try:
            logging.info("开始生成课程表...")
            start_time = time.time()
            
            logging.debug("重新初始化班级")
            for clas in self.class_lst:
                clas.reset()

            logging.debug(f"开始DFS分配剩余课程，共{len(self.class_lst)}个班级")
            self.finish=False
            self.dfs(self.class_lst[0],Time(1,1))
            
            elapsed_time = time.time() - start_time
            logging.info(f"课程表生成完成，耗时{elapsed_time:.2f}秒")
        except:
            e=traceback.format_exc()
            logging.critical(f"生成课程表时错误：\n{e}")
        self.finish=True
        self.finished_signal.emit(self.skipped_lessons)

    def should_emit_progress(self):
        """判断是否应该发送进度信号"""
        current_time=time.time()
        if current_time-self.last_progress_time>=self.progress_interval:
            self.last_progress_time=current_time
            return True
        return False

    def dfs(self,clas: Class,curr_time: Time):
        try:
            if self.finish:
                return
            if self.should_emit_progress():
                percentage=round(self.class_lst.index(clas)/len(self.class_lst)*100)
                self.progress_signal.emit((clas,curr_time,percentage))
            last=False
            if curr_time.day==5 and curr_time.lesson==cfg.day_class_num:
                if self.class_lst[-1]==clas:
                    last=True

            next_time=curr_time.next
            logging.debug(f"当前时间：{curr_time}")
            self.tried_times[clas][curr_time]+=1
            if self.tried_times[clas][curr_time]>self.max_tries:

                logging.debug(f"{curr_time} 尝试次数过多，跳过")
            elif curr_time in clas.set_lessons:
                logging.debug(f"{curr_time}存在固定课程")
                clas.add_lesson(curr_time,clas.set_lessons[curr_time])
            elif clas.get_lessons(curr_time):
                logging.debug(f"{curr_time}存在已排课程")
            else:
                if curr_time in clas.priority_subjects:
                    curr_priority=clas.priority_subjects[curr_time]
                else:
                    curr_priority=[]
                logging.debug(f"当前优先课程：{[i.name for i in curr_priority]}")

                curr_subjects=list(set(clas.left_subjects))
                random.shuffle(curr_subjects)

                if cfg.average_subjects.value:
                    for lesson in range(cfg.day_class_num,0,-1):
                        lessons=clas.get_lessons(Time(curr_time.day,lesson))
                        if lessons:
                            if lessons[0] in curr_subjects:
                                curr_subjects.remove(lessons[0])
                                curr_subjects.append(lessons[0])
                            if len(lessons)>1 and lessons[1] in curr_subjects:
                                curr_subjects.remove(lessons[1])
                                curr_subjects.append(lessons[1])

                for subject in curr_subjects:
                    if cfg.reduce_continue.value and clas.get_teacher(subject).is_busy(curr_time.prev):
                        curr_subjects.remove(subject)
                        curr_subjects.append(subject)
                    elif cfg.average_subjects.value and (subject in curr_priority or clas.left_subjects.count(subject)>5-curr_time.day+1):
                        curr_subjects.remove(subject)
                        curr_subjects.insert(0,subject)

                logging.debug(f"当前课程：{[i.name for i in curr_subjects]}")

                for subject in curr_subjects:
                    if subject not in clas.left_subjects:
                        continue
                    # 单双周
                    if subject in clas.half_subjects and check(clas, curr_time.sin_week, subject):
                        clas.add_lesson(curr_time.sin_week,subject)
                        for subject2 in clas.half_subjects&set(clas.left_subjects):
                            if not check(clas, curr_time.dou_week, subject2):
                                continue
                            clas.add_lesson(curr_time.dou_week,subject2)
                            if not last:
                                if curr_time.day==5 and curr_time.lesson==cfg.day_class_num:
                                    self.dfs(self.class_lst[self.class_lst.index(clas)+1],Time(1,1))
                                else:
                                    self.dfs(clas,next_time)
                                if self.finish:
                                    return
                                clas.remove_lesson(curr_time.dou_week)
                        clas.remove_lesson(curr_time.sin_week)
                    elif subject not in clas.half_subjects and check(clas, curr_time, subject):
                        # 连堂
                        add_continue=False
                        if subject.get_continue_times(clas)<clas.continue_num[subject] and clas.left_subjects.count(subject)>=2:
                            if clas.continue_num[subject]-subject.get_continue_times(clas)==clas.left_subjects.count(subject)/2:
                                if check(clas,next_time,subject) and (cfg.allow_noon_continuous.value or curr_time.lesson!=cfg.morning_class_num.value) and curr_time.lesson!=cfg.day_class_num:
                                    add_continue=True
                                else:
                                    continue
                            elif check(clas,next_time,subject) and (cfg.allow_noon_continuous.value or curr_time.lesson!=cfg.morning_class_num.value) and curr_time.lesson!=cfg.day_class_num:
                                add_continue=random.choice([True,False])
                            if add_continue:
                                clas.add_lesson(next_time,subject)
                            else:
                                continue
                        clas.add_lesson(curr_time,subject)
                        if not last:
                            if curr_time.day==5 and curr_time.lesson==cfg.day_class_num:
                                self.dfs(self.class_lst[self.class_lst.index(clas)+1],Time(1,1))
                            else:
                                self.dfs(clas,next_time)
                            if self.finish:
                                return
                            clas.remove_lesson(curr_time)
                            if add_continue:
                                clas.remove_lesson(next_time)
                return
            if not last:
                if curr_time.day==5 and curr_time.lesson==cfg.day_class_num:
                    self.dfs(self.class_lst[self.class_lst.index(clas)+1],Time(1,1))
                else:
                    self.dfs(clas,next_time)
            if last:
                self.finish=True
        except:
            e=traceback.format_exc()
            logging.critical(f"生成课程表出错：{clas} {curr_time}\n{e}")