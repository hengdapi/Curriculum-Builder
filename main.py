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
            except Exception:
                self._default_geometry()
        else:
            self._default_geometry()

        #启动页面
        splashScreen=SplashScreen(self.windowIcon(),self)
        splashScreen.setIconSize(QSize(150,150))
        self.show()

        self.addSubInterface(home.Home(),FluentIcon.HOME,"主页")
        self.addSubInterface(settings.Settings(),FluentIcon.SETTING,"设置")
        self.addSubInterface(generate.Generate(),FluentIcon.BRUSH,"生成")

        splashScreen.finish()

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
    logging.info("\n\n程序开始启动，当前时间："+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    app=QtWidgets.QApplication(sys.argv)
    translator=FluentTranslator(QLocale(QLocale.Chinese,QLocale.China))
    app.installTranslator(translator)
    ui=Window()
    ui.show()
    sys.exit(app.exec())