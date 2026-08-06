import logging,os
import traceback

from PySide6.QtCore import Qt
from qfluentwidgets_pro import QConfig,RangeConfigItem,OptionsConfigItem,BoolValidator,ConfigItem,qconfig,RangeValidator,InfoBar,InfoBarPosition

settings_file=f"C:/Users/{os.getlogin()}/AppData/Roaming/School-Timetable-Generator/settings.json"
class Settings(QConfig):
    morning_class_num=RangeConfigItem("table_style","morning_class_num",4,RangeValidator(1,10),restart=True)
    afternoon_class_num=RangeConfigItem("table_style","afternoon_class_num",2,RangeValidator(1,10),restart=True)
    show_teachers=OptionsConfigItem("table_style","show_teachers",True,BoolValidator(),restart=True)
    text_font=ConfigItem("table_style","text_font","宋体",restart=True)
    text_size=ConfigItem("table_style","text_size",9,restart=True)
    school_name=ConfigItem("table_style","school_name","学校名称",restart=True)
    lessons_time=ConfigItem("table_style","lessons_time",{},restart=True)

    subjects_info=ConfigItem("lessons_info","subjects_info",{},restart=True)
    lessons_info=ConfigItem("lessons_info","lessons_info",{},restart=True)
    teachers_info=ConfigItem("lessons_info","teachers_info",{},restart=True)
    grades_info=ConfigItem("lessons_info","grades_info",{},restart=True)

    activity_info=ConfigItem("activity_info","activity_info",{},restart=True)

    rules=ConfigItem("rules","rules",{})
    reduce_continue=OptionsConfigItem("rules","reduce_continue",True,BoolValidator())
    average_subjects=OptionsConfigItem("rules","average_subjects",True,BoolValidator())

    object_splitter_state=ConfigItem("ui","object_splitter_state",None)
    preview_splitter_state=ConfigItem("ui","preview_splitter_state",None)
    window_geometry=ConfigItem("ui","window_geometry",None)
    window_maximized=ConfigItem("ui","window_maximized",False)

def load_settings():
    cfg=Settings()
    qconfig.load(settings_file, cfg)
    return cfg
cfg=load_settings()

def save_settings():
    try:
        # 将内存配置写入文件
        cfg.save()
        logging.info("保存设置成功")
    except:
        e=traceback.format_exc()
        logging.error(f"保存设置时出错：\n{e}")

def settings_error(window,error):
    InfoBar.error(
        title='设置保存失败！',
        content=error,
        orient=Qt.Horizontal,
        isClosable=True,
        position=InfoBarPosition.TOP,
        duration=-1,
        parent=window
    )