# coding=utf-8
import sys,logging,time
from PySide6 import QtWidgets
from PySide6.QtGui import QIcon,QFont
from PySide6.QtCore import QLocale,QSize,QByteArray
from qfluentwidgets_pro import MSFluentWindow,SplashScreen,FluentTranslator,setThemeColor,setTheme,Theme
from qfluentwidgets_pro.common.icon import FluentIcon
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

        # ===== 恢复窗口位置/大小（取代原来的 resize + move）=====
        geom_b64 = cfg.window_geometry.value
        if geom_b64:
            try:
                data = QByteArray.fromBase64(geom_b64.encode())
                self.restoreGeometry(data)
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

        self.addSubInterface(home.Home(),FluentIcon.HOME,"主页")
        self.addSubInterface(settings.Settings(),FluentIcon.SETTING,"设置")
        self.addSubInterface(generate.Generate(),FluentIcon.BRUSH,"生成")
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
        """窗口关闭时保存 geometry 到配置"""
        try:
            state = self.saveGeometry()              # QByteArray
            cfg.window_geometry.value = bytes(state.toBase64()).decode()
            save_settings()
        except Exception:
            pass
        super().closeEvent(e)


if __name__ == '__main__':
    logging.info("\n\n" + "="*60)
    logging.info(f"程序开始启动，当前时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    
    # 详细的系统信息
    logging.info(f"操作系统平台：{sys.platform}")
    logging.info(f"系统架构：{sys.maxsize > 2**32 and '64位' or '32位'}")

    try:
        import platform
        logging.info(f"操作系统名称：{platform.system()} {platform.release()}")
        logging.info(f"操作系统版本：{platform.version()}")
        logging.info(f"处理器信息：{platform.processor()}")
        logging.info(f"机器类型：{platform.machine()}")
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