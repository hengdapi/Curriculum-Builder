# coding=utf-8
import sys,logging,time
from PySide6 import QtWidgets
from PySide6.QtGui import QIcon,QFont
from PySide6.QtCore import QLocale,QSize,QByteArray
from qfluentwidgets_pro import MSFluentWindow,SplashScreen,FluentTranslator,setThemeColor,setTheme,Theme
from qfluentwidgets_pro.common.icon import FluentIcon

from locals import lesson_info
from pages import home,settings,generate
from qframelesswindow.utils import getSystemAccentColor
from wr_settings import save_settings, cfg

class Window(MSFluentWindow):
    def __init__(self):
        super().__init__()
        logging.debug("初始化主窗口")
        if sys.platform in ["win32","darwin"]:
            setThemeColor(getSystemAccentColor(),save=False)
        setTheme(Theme.AUTO,save=False)
        self.setWindowTitle("课程表生成器")
        self.setWindowIcon(QIcon("logo.ico"))
        self.setFont(QFont("Microsoft YaHei", 20))

        # ===== 恢复窗口位置/大小 =====
        # 先恢复普通几何，不立即应用最大化；等窗口显示并布局完成后再最大化，
        # 避免无边框窗口在启动时内容区域计算错误（缩在左上角）
        geom_b64 = cfg.window_geometry.value
        if geom_b64:
            try:
                data = QByteArray.fromBase64(geom_b64.encode())
                self.restoreGeometry(data)
                # 兼容旧配置：如果 geometry 里仍带最大化状态，先恢复为普通尺寸，
                # 避免后续布局计算时内容区域异常
                if self.isMaximized():
                    self.showNormal()
                logging.debug("成功恢复窗口位置和大小")
            except Exception as e:
                logging.warning(f"恢复窗口位置失败，使用默认设置: {e}")
                self._default_geometry()
        else:
            self._default_geometry()
            logging.debug("使用默认窗口位置和大小")

        #启动页面
        splashScreen=SplashScreen(self.windowIcon(),self)
        splashScreen.setIconSize(QSize(150,150))
        self.show()

        # 布局稳定后再恢复最大化状态
        if cfg.window_maximized.value:
            self.showMaximized()
            logging.debug("恢复窗口最大化状态")
        self.home=home.Home()
        self.settings=settings.Settings()
        self.generate=generate.Generate()

        self.addSubInterface(self.home,FluentIcon.HOME,"主页")
        self.addSubInterface(self.settings,FluentIcon.SETTING,"设置")
        self.addSubInterface(self.generate,FluentIcon.BRUSH,"生成")
        logging.debug("已添加所有子页面")

        splashScreen.finish()
        logging.info("主窗口初始化完成")

    def _default_geometry(self):
        """没有记录时的默认尺寸和居中"""
        self.resize(1300, 700)
        screen = self.screen().availableGeometry()
        size = self.size()
        self.move(
            int((screen.width() - size.width()) / 2),
            int((screen.height() - size.height()) / 2)
        )

    def closeEvent(self, e):
        """窗口关闭时保存 geometry 和最大化状态到配置"""
        try:
            if not lesson_info.saved:
                reply=QtWidgets.QMessageBox.question(self,"方案未保存","您当前的方案未保存，是否前往保存？\n若不保存，即使您已经导出了Excel版课程表，也无法再恢复当前方案了",QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No|QtWidgets.QMessageBox.Cancel)
                if reply==QtWidgets.QMessageBox.Yes:
                    self.generate.save_plan()
                elif reply==QtWidgets.QMessageBox.Cancel:
                    e.ignore()
                    return

            is_max = self.isMaximized()
            cfg.window_maximized.value = is_max

            # 若当前处于最大化，先恢复为普通状态再保存 geometry，
            # 否则 saveGeometry 会保存最大化后的尺寸，导致下次启动异常
            if is_max:
                self.showNormal()

            state = self.saveGeometry()              # QByteArray
            cfg.window_geometry.value = bytes(state.toBase64()).decode()
            save_settings()
        except Exception:
            pass
        super().closeEvent(e)


if __name__ == '__main__':
    logging.info("\n\n" + "="*60)
    logging.info(f"程序开始启动，当前时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    try:
        import platform
        logging.info(f"操作系统名称：{platform.system()} {platform.release()}")
        logging.info(f"操作系统版本：{platform.version()}")
    except:
        pass
    
    app=QtWidgets.QApplication(sys.argv)
    translator=FluentTranslator(QLocale(QLocale.Chinese,QLocale.China))
    app.installTranslator(translator)
    ui=Window()
    ui.show()
    logging.info("主窗口已显示")
    exit_code = app.exec()
    logging.info(f"程序退出，退出码：{exit_code}")
    sys.exit(exit_code)