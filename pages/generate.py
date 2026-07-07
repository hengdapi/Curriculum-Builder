from style import *
from generate_core import *
from save_core import SaveThread
from PySide6.QtCore import Qt,QByteArray
from PySide6 import QtGui
import time

class Generate(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.setObjectName("Generate")
        main_layout = QVBoxLayout(self)

        # === 创建内容容器 ===
        view=QWidget()
        view.setStyleSheet("QWidget{background: transparent}")
        self.layout = QVBoxLayout(view)

        self.title = title("生成",self,self.layout,10)
        self.title.setFixedHeight(60)
        # 读取配置文件
        self.cfg=load_settings()
        # 检查是否已配置课程信息
        if not self.cfg.lessons_info.value:
            settings_error(self,"请先在设置中配置课程信息")

        self.operation_layout=QHBoxLayout()
        self.layout.addLayout(self.operation_layout)
        # 生成课程表按钮
        self.generate_button=PrimaryPushButton()
        self.generate_button.setText("生成课程表")
        self.generate_button.setIcon(FluentIcon.BRUSH)
        self.generate_button.setFixedSize(160,40)
        self.generate_button.clicked.connect(self.generate_timetable)
        add_widget(self.generate_button,self.operation_layout)

        self.save_button=PrimaryPushButton()
        self.save_button.setText("保存课程表")
        self.save_button.setIcon(FluentIcon.SAVE)
        self.save_button.setFixedSize(160,40)
        self.save_button.clicked.connect(self.save_timetable)
        add_widget(self.save_button,self.operation_layout)
        self.operation_layout.addStretch(1)

        self.progress_bar=ProgressBar()
        self.progress_bar.hide()
        add_widget(self.progress_bar,self.layout,0)

        self.log_label:BodyLabel=write("",self,self.layout)
        self.log_label.hide()
        add_widget(self.log_label,self.layout,0)

        # 课程表预览
        self.preview_splitter=Splitter(Qt.Horizontal)
        add_widget(self.preview_splitter,self.layout,0)

        self.object_pane=QWidget()
        self.object_layout=QVBoxLayout(self.object_pane)
        self.object_search=SearchLineEdit()
        add_widget(self.object_search,self.object_layout)
        search_items=[]
        for grade,classes in self.cfg.grades_info.value.items():
            search_items.append(grade)
            search_items.extend(classes)
        search_items.extend(self.cfg.teachers_info.value)
        self.search_completer=QCompleter(search_items,self.object_search)
        self.search_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_completer.setFilterMode(Qt.MatchContains)
        self.object_search.setCompleter(self.search_completer)

        self.object_tree=TreeWidget(self)
        self.object_tree.setHeaderHidden(True)
        self.show_object_tree()
        self.object_tree.clicked.connect(self.show_timetable)
        add_widget(self.object_tree,self.object_layout,0)
        self.object_search.textChanged.connect(self.filter_object_tree)
        self.preview_splitter.addWidget(self.object_pane)

        self.timetable_pane=QWidget()
        self.timetable_layout=QVBoxLayout(self.timetable_pane)
        self.timetable_subheader=subheader("班级课程表",self,self.timetable_layout,10)
        self.timetable_preview=TableWidget()
        self.timetable_preview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.timetable_preview.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.timetable_preview.clicked.connect(self.on_timetable_preview_clicked)
        self.timetable_preview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.timetable_preview.customContextMenuRequested.connect(self.select_target)
        add_widget(self.timetable_preview,self.timetable_layout,0)
        self.preview_splitter.addWidget(self.timetable_pane)

        self.teacher_timetable_pane=QWidget()
        self.teacher_timetable_pane.hide()
        self.teacher_timetable_layout=QVBoxLayout(self.teacher_timetable_pane)
        self.teacher_timetable_subheader=subheader("教师课程表",self,self.teacher_timetable_layout,10)
        self.teacher_timetable_preview=TableWidget()
        self.teacher_timetable_preview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.teacher_timetable_preview.verticalHeader().setVisible(False)
        add_widget(self.teacher_timetable_preview,self.teacher_timetable_layout,0)

        self.preview_splitter.addWidget(self.teacher_timetable_pane)
        self.preview_splitter.splitterMoved.connect(self.save_splitter_state)
        state_b64=self.cfg.preview_splitter_state.value
        if state_b64:
            byte_array=QByteArray.fromBase64(state_b64.encode())
            self.preview_splitter.restoreState(byte_array)
        else:
            self.preview_splitter.setStretchFactor(0,2)
            self.preview_splitter.setStretchFactor(1,7)
            self.preview_splitter.setStretchFactor(2,6)

        self.exchange_layout=QHBoxLayout()
        self.layout.addLayout(self.exchange_layout)
        self.exchange_label=write("调整课程：",self,self.exchange_layout,10)
        self.source_lesson=LineEdit()
        self.source_lesson.setReadOnly(True)
        self.source_lesson.setPlaceholderText("左键点击表格中对应课程即可")
        add_widget(self.source_lesson,self.exchange_layout,0)

        self.exchange_button=PrimaryPushButton()
        self.exchange_button.setText("交换课程")
        self.exchange_button.setIcon(FluentIcon.SCROLL)
        self.exchange_button.setEnabled(False)
        self.exchange_button.clicked.connect(self.exchange_lesson)
        add_widget(self.exchange_button,self.exchange_layout,0)

        self.target_lesson=ComboBox()
        add_widget(self.target_lesson,self.exchange_layout,0)

        self.hidden_widgets=[self.save_button,self.exchange_label,self.target_lesson,self.exchange_button,self.source_lesson,self.preview_splitter]
        self.hide_widgets()
        # === 设置滚动区域内容 ===
        self.layout.addStretch(1)
        main_layout.addWidget(view)

    def hide_widgets(self):
        for widget in self.hidden_widgets:
            widget.hide()

    def show_widgets(self):
        for widget in self.hidden_widgets:
            widget.show()

    def show_object_tree(self):
        self.object_tree.clear()
        self.classes_top_item=QTreeWidgetItem(["班级课表"])
        for grade,classes in self.cfg.grades_info.value.items():
            grade_item=QTreeWidgetItem([grade])
            for clas in classes:
                grade_item.addChild(QTreeWidgetItem([clas]))
            self.classes_top_item.addChild(grade_item)
        self.object_tree.addTopLevelItem(self.classes_top_item)

        self.teachers_top_item=QTreeWidgetItem(["教师课表"])
        for teacher in self.cfg.teachers_info.value:
            self.teachers_top_item.addChild(QTreeWidgetItem([teacher]))
        self.object_tree.addTopLevelItem(self.teachers_top_item)
        self.class_total_item=QTreeWidgetItem(["班级总表"])
        self.teacher_total_item=QTreeWidgetItem(["教师总表"])
        self.object_tree.addTopLevelItems([self.class_total_item,self.teacher_total_item])

    def filter_object_tree(self,keyword:str):
        keyword=str(keyword).strip().lower()
        # 班级课表：匹配班级或年级名称
        grade_matches_any=False
        for g in range(self.classes_top_item.childCount()):
            grade_item=self.classes_top_item.child(g)
            grade_match=keyword in grade_item.text(0).lower()
            class_any_match=False
            for c in range(grade_item.childCount()):
                class_item=grade_item.child(c)
                class_match=keyword in class_item.text(0).lower() or grade_match
                class_item.setHidden(not class_match)
                if class_match:
                    class_any_match=True
            grade_item.setHidden(not class_any_match and not grade_match)
            if not grade_item.isHidden():
                grade_matches_any=True
        self.classes_top_item.setHidden(False)

        # 教师课表：匹配教师姓名
        teacher_matches_any=False
        for t in range(self.teachers_top_item.childCount()):
            teacher_item=self.teachers_top_item.child(t)
            match=keyword in teacher_item.text(0).lower()
            teacher_item.setHidden(not match)
            if match:
                teacher_matches_any=True

        # 总表项目：在搜索时总是显示，便于快速查看
        self.class_total_item.setHidden(False)
        self.teacher_total_item.setHidden(False)

        # 如果有关键字，自动展开匹配项，否则保持默认
        if keyword:
            self.classes_top_item.setExpanded(grade_matches_any)
            for g in range(self.classes_top_item.childCount()):
                grade_item=self.classes_top_item.child(g)
                if not grade_item.isHidden():
                    grade_item.setExpanded(True)
            self.teachers_top_item.setExpanded(teacher_matches_any)
        else:
            self.classes_top_item.setExpanded(False)
            for g in range(self.classes_top_item.childCount()):
                self.classes_top_item.child(g).setExpanded(False)
            self.teachers_top_item.setExpanded(False)

    def save_splitter_state(self):
        state=self.preview_splitter.saveState()  # QByteArray
        state_base64=bytes(state.toBase64()).decode()  # 转为普通字符串（Base64）
        self.cfg.preview_splitter_state.value=state_base64
        save_settings()

    def select_target(self,pos):
        # 获取点击位置的行列
        item=self.timetable_preview.itemAt(pos)
        if not item:
            return
        curr_text=f"{Time(item.column()+1,item.row()+1)} {item.text().split("\n")[0]}"
        self.target_lesson.setCurrentText(curr_text)
        if self.target_lesson.currentText()==curr_text:
            self.exchange_lesson()

    def generate_timetable(self):
        try:
            logging.info("生成按钮被点击")
            # 禁用生成按钮防止重复点击
            self.generate_button.setEnabled(False)
            self.progress_bar.show()
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(len(lesson_info.class_names))
            self.log_label.show()
            self.hide_widgets()

            # 创建并启动线程
            self.generate_start_time=time.time()
            self.generate_thread=GenerateThread()
            self.generate_thread.finished_signal.connect(self.on_generation_finished)
            self.generate_thread.progress_signal.connect(self.on_progress_update)
            self.generate_thread.start()
        except Exception as error:
            e=traceback.format_exc()
            logging.critical(f"生成课程表出错：\n{e}")
            show_error(self,error)

    def on_timetable_preview_clicked(self):
        try:
            if self.preview_mode!=0:
                return
            self.target_lesson.clear()
            self.source_lesson.clear()
            self.exchange_button.setEnabled(False)
            if self.timetable_preview.currentItem().background()==QColor(255,255,200):
                for j in range(self.timetable_preview.columnCount()):
                    for i in range(self.timetable_preview.rowCount()):
                        item=self.timetable_preview.item(i,j)
                        if not item:
                            continue
                        item.setBackground(QtGui.QBrush(Qt.NoBrush))
                        item.setToolTip("")
                self.teacher_timetable_pane.hide()
                return
            curr_item=self.timetable_preview.currentItem()
            clas=lesson_info.classes[self.preview_object]
            curr_time=Time(curr_item.column()+1,curr_item.row()+1)
            source_subjects=clas.get_lessons(curr_time)
            teacher=clas.get_teacher(source_subjects[0])
            self.source_lesson.setText(f"{curr_time} {curr_item.text().split("\n")[0]}")
            for j in range(self.timetable_preview.columnCount()):
                for i in range(self.timetable_preview.rowCount()):
                    item=self.timetable_preview.item(i,j)
                    if not item:
                        continue
                    time=Time(item.column()+1,item.row()+1)
                    target_subjects=clas.get_lessons(time)
                    exchangeable=False

                    item.setBackground(QColor(255,150,150))
                    item.setToolTip("不可交换")
                    if target_subjects[0] in [lesson[1] for lesson in set_lessons] or source_subjects[0] in [lesson[1] for lesson in set_lessons]:
                        continue
                    if not source_subjects[0].continuous and not target_subjects[0].continuous:
                        if (len(target_subjects)==1 and check(clas,curr_time,target_subjects[0]) or
                        len(target_subjects)==2 and check(clas,curr_time,target_subjects[0]) and check(clas,curr_time,target_subjects[1])) and\
                        (len(source_subjects)==1 and check(clas,time,source_subjects[0]) or
                         len(source_subjects)==2 and check(clas,time,source_subjects[0]) and check(clas,time,source_subjects[1])):
                            exchangeable=True
                    elif source_subjects[0].continuous:
                        if clas.get_lessons(curr_time.prev)==source_subjects[0] and clas.get_lessons(curr_time.prev)[0].continuous:
                            source_subjects2=copy.copy(source_subjects)
                            source_subjects=clas.get_lessons(curr_time.prev)
                        else:
                            source_subjects2=clas.get_lessons(curr_time.next)
                        target_subjects2=clas.get_lessons(time.next)
                        if (len(target_subjects)==1 and check(clas,curr_time,target_subjects[0]) or
                            len(target_subjects)==2 and check(clas,curr_time,target_subjects[0]) and check(clas,curr_time,target_subjects[1])) and\
                            (len(source_subjects)==1 and check(clas,time,source_subjects[0]) or
                             len(source_subjects)==2 and check(clas,time,source_subjects[0]) and check(clas,time,source_subjects[1])) and\
                            ((len(target_subjects2)==1 and check(clas,curr_time,target_subjects2[0]) or
                            len(target_subjects2)==2 and check(clas,curr_time,target_subjects2[0]) and check(clas,curr_time,target_subjects2[1])) and
                            check(clas,time.next,source_subjects2[0])):
                            exchangeable=True

                    if exchangeable:
                        item.setBackground(QColor(150,255,150))
                        item.setToolTip("右键点击可交换")
                        self.target_lesson.addItem(f"{time} {item.text().split("\n")[0]}",userData=(time,copy.copy(target_subjects)))
                        self.exchange_button.setEnabled(True)

            curr_item.setBackground(QColor(255,255,200))
            curr_item.setToolTip("当前选中（再次点击可取消）")

            display_df_in_table(self.teacher_timetable_preview,teacher.timetable_dataframe)
            self.teacher_timetable_subheader.setText(f"任课教师 {teacher.name} 课程表")
            teacher_item=self.teacher_timetable_preview.item(curr_time.lesson-1,curr_time.day-1)
            teacher_item.setBackground(QColor(255,255,200))
            # 手动设置行高
            for row in range(self.teacher_timetable_preview.rowCount()):
                self.teacher_timetable_preview.setRowHeight(row, 60)
            # 手动设置列宽
            for col in range(self.teacher_timetable_preview.columnCount()):
                self.teacher_timetable_preview.setColumnWidth(col, 100)
            self.teacher_timetable_pane.show()
        except Exception as error:
            e=traceback.format_exc()
            logging.critical(f"点击课程表出错：\n{e}")
            show_error(self,error)

    def exchange_lesson(self):
        try:
            curr_item=self.timetable_preview.currentItem()
            clas=lesson_info.classes[self.preview_object]
            curr_time=Time(curr_item.column()+1,curr_item.row()+1)
            curr_subjects=copy.copy(clas.get_lessons(curr_time))
            target_time,target_subjects=self.target_lesson.currentData()
            if len(curr_subjects)==1:
                clas.remove_lesson(curr_time,curr_subjects[0])
            else:
                clas.remove_lesson(curr_time.sin_week,curr_subjects[0])
                clas.remove_lesson(curr_time.dou_week,curr_subjects[1])
            if len(target_subjects)==1:
                clas.remove_lesson(target_time,target_subjects[0])
            else:
                clas.remove_lesson(target_time.sin_week,target_subjects[0])
                clas.remove_lesson(target_time.dou_week,target_subjects[1])
            if len(curr_subjects)==1:
                clas.add_lesson(target_time,curr_subjects[0])
            else:
                clas.add_lesson(target_time.sin_week,curr_subjects[0])
                clas.add_lesson(target_time.dou_week,curr_subjects[1])
            if len(target_subjects)==1:
                clas.add_lesson(curr_time,target_subjects[0])
            else:
                clas.add_lesson(curr_time.sin_week,target_subjects[0])
                clas.add_lesson(curr_time.dou_week,target_subjects[1])
            self.show_timetable()
        except Exception as error:
            e=traceback.format_exc()
            logging.critical(f"交换课程出错：\n{e}")
            show_error(self,error)

    def show_timetable(self):
        self.source_lesson.clear()
        self.target_lesson.clear()
        self.exchange_button.setEnabled(False)

        object_item=self.object_tree.currentItem()
        if not object_item:
            return
        try:
            self.teacher_timetable_pane.hide()
            self.timetable_pane.show()
            if object_item.text(0)=="班级总表":
                self.preview_mode=2
                self.timetable_subheader.setText("班级总表")
                display_df_in_table(self.timetable_preview,class_total_dataframe())
                self.exchange_label.hide()
                self.source_lesson.hide()
                self.target_lesson.hide()
                self.exchange_button.hide()
            elif object_item.text(0)=="教师总表":
                self.preview_mode=3
                self.timetable_subheader.setText("教师总表")
                display_df_in_table(self.timetable_preview,teacher_total_dataframe())
                self.exchange_label.hide()
                self.source_lesson.hide()
                self.target_lesson.hide()
                self.exchange_button.hide()
            elif object_item.parent() is not None and object_item.parent().text(0) =="教师课表":
                self.preview_mode=1
                self.preview_object=object_item.text(0)
                self.timetable_subheader.setText(f"{self.preview_object} 课程表")
                display_df_in_table(self.timetable_preview,lesson_info.teachers[self.preview_object].timetable_dataframe)
                self.exchange_label.hide()
                self.source_lesson.hide()
                self.target_lesson.hide()
                self.exchange_button.hide()
            elif object_item.parent().parent() is not None and object_item.parent().parent().text(0) =="班级课表":
                self.preview_mode=0
                self.preview_object=object_item.text(0)
                self.timetable_subheader.setText(f"{self.preview_object} 课程表")
                display_df_in_table(self.timetable_preview,lesson_info.classes[self.preview_object].timetable_dataframe)
                self.exchange_label.show()
                self.source_lesson.show()
                self.target_lesson.show()
                self.exchange_button.show()
            else:
                raise ValueError("未知的课程表类型")
        except:
            self.timetable_pane.hide()
            return
        # 手动设置行高
        for row in range(self.timetable_preview.rowCount()):
            self.timetable_preview.setRowHeight(row, 60)
        # 手动设置列宽
        for col in range(self.timetable_preview.columnCount()):
            self.timetable_preview.setColumnWidth(col, 110)

    def on_generation_finished(self):
        logging.info("排课已完成")
        self.generate_button.setEnabled(True)
        self.generate_button.setText("重新生成")
        self.log_label.hide()
        self.progress_bar.hide()
        self.show_widgets()
        self.show_timetable()
        self.layout.takeAt(self.layout.count()-1)

    def on_progress_update(self,progress:tuple[Class,Time]):
        try:
            used_time=round(time.time()-self.generate_start_time)
            percentage=round(lesson_info.class_names.index(progress[0].name)/len(lesson_info.class_names)*100)
            self.log_label.setText(f"当前进度：{percentage}%%，班级：{progress[0].name}，课时：{progress[1]}，已用时间：%02d:%02d"%(used_time//60,used_time%60))
            self.progress_bar.setValue(lesson_info.class_names.index(progress[0].name))
        except Exception as error:
            e=traceback.format_exc()
            logging.critical(f"生成课程表出错：\n{e}")
            show_error(self,error)

    def save_timetable(self):
        filename,_=QFileDialog.getSaveFileName(self,"保存课程表","","Microsoft Excel 工作表(*.xlsx);;Microsoft Excel 97-2003 工作表(*.xls)")
        if not filename:
            return
        logging.info(f"保存课程表文件名：{filename}")

        self.save_infobar=InfoBar(InfoBarIcon.INFORMATION,"正在保存课程表，请稍候...","",parent=self,duration=-1)
        self.save_progress=IndeterminateProgressBar()
        self.save_infobar.addWidget(self.save_progress)
        self.save_infobar.show()

        name,ext=os.path.splitext(filename)
        save_thread=SaveThread(name,ext,self)
        save_thread.success.connect(self.on_save_success)
        save_thread.error.connect(self.on_save_error)
        save_thread.start()

    def on_save_success(self):
        self.save_infobar.close()
        InfoBar.success("课程表保存成功！","",parent=self,duration=-1)

    def on_save_error(self,error):
        self.save_infobar.close()
        InfoBar.error("课程表保存失败！",error,parent=self,duration=-1)