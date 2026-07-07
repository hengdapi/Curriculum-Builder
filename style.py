from PySide6.QtGui import QFont
from PySide6.QtWidgets import *
from qfluentwidgets_pro import *

class fonts:
    title=QFont("Microsoft YaHei",30,QFont.Bold)
    biggersubheader=QFont("Microsoft YaHei",25,QFont.Bold)
    subheader=QFont("Microsoft YaHei",20,QFont.Bold)
    write=QFont("Microsoft YaHei",15)
    button=QFont("Microsoft YaHei",13)

def add_widget(widget,layout:QBoxLayout,spacing=20):
    layout.addWidget(widget)
    layout.addSpacing(spacing)

def label(text: str,label_type,font:QFont,window,layout:QBoxLayout,spacing=20):
    label = label_type(text, window)
    label.setFont(font)
    add_widget(label,layout,spacing)
    return label

def title(text: str,window,layout:QBoxLayout,spacing=20)->LargeTitleLabel:
    return label(text,LargeTitleLabel,fonts.title,window,layout,spacing)

def biggersubheader(text: str,window,layout:QBoxLayout,spacing=20)->SubtitleLabel:
    return label(text,SubtitleLabel,fonts.biggersubheader,window,layout,spacing)

def subheader(text: str,window,layout:QBoxLayout,spacing=20)->SubtitleLabel:
    return label(text,SubtitleLabel,fonts.subheader,window,layout,spacing)

def write(text: str,window,layout:QBoxLayout,spacing=20)->BodyLabel:
    return label(text,BodyLabel,fonts.write,window,layout,spacing)

def button(text: str,window,layout:QBoxLayout,spacing=20)->PushButton:
    return label(text,PushButton,fonts.button,window,layout,spacing)