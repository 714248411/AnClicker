"""Theme-aware About and donation presentation without changing link targets or QR data."""
from anclicker.platform.qt_compat.QtCore import Qt,QSize,QRectF
from anclicker.platform.qt_compat.QtGui import QColor,QPalette,QIcon,QPixmap,QPainter
from anclicker.platform.qt_compat.QtWidgets import QDialog,QVBoxLayout,QLabel,QScrollArea,QWidget,QFrame,QSizePolicy
from anclicker.ui.theme import THEMES
from anclicker.ui.window_chrome import ChromeControlButton, toggleMaxState
from qframelesswindow import FramelessDialog, StandardTitleBar


def information_theme(parent=None, mode=None):
    mode=mode or getattr(parent,'_theme_mode',None) or getattr(getattr(parent,'view_workspace',None),'theme_mode','light')
    return THEMES.get(mode,THEMES['light'])



class InformationTitleBar(StandardTitleBar):
    """Use the application chrome for small information windows, including older Windows."""
    def __init__(self, window):
        super().__init__(window)
        self.setObjectName('informationTitleBar')
        self.setAttribute(Qt.WA_StyledBackground,True)
        self.setFixedHeight(34)
        self.hBoxLayout.setContentsMargins(0,0,4,0)
        self.hBoxLayout.setSpacing(2)
        for name,kind,text in (('minBtn','minimize','最小化'),
                               ('maxBtn','maximize','最大化/还原'),('closeBtn','close','关闭')):
            old=getattr(self,name)
            index=self.hBoxLayout.indexOf(old)
            self.hBoxLayout.removeWidget(old);old.hide();old.deleteLater()
            button=ChromeControlButton(kind,self);button.setFixedSize(28,28)
            button.setToolTip(text);button.setAccessibleName(text)
            self.hBoxLayout.insertWidget(index,button)
            setattr(self,name,button)
        self.minBtn.clicked.connect(window.showMinimized)
        self.maxBtn.clicked.connect(lambda: toggleMaxState(window))
        self.closeBtn.clicked.connect(window.close)
        self.setTitle(window.windowTitle());self.setIcon(window.windowIcon())
        for label in (self.titleLabel,self.iconLabel):
            label.setAttribute(Qt.WA_TransparentForMouseEvents)

    def apply_theme(self, colors):
        c=colors
        self.setStyleSheet(f"QWidget#informationTitleBar {{background:{c['surface']};}}")
        self.titleLabel.setStyleSheet(f"background:transparent;color:{c['text']};padding:0 4px;font:13px 'Microsoft YaHei UI';")
        for button in (self.minBtn,self.maxBtn,self.closeBtn):
            button.setNormalColor(QColor(c['text']))
            button.setNormalBackgroundColor(QColor(Qt.transparent))
            button.setHoverColor(QColor(c['text']));button.setPressedColor(QColor(c['text']))
            button.setHoverBackgroundColor(QColor(c['surface3']))
            button.setPressedBackgroundColor(QColor(c['line']))
        self.closeBtn.setHoverColor(QColor('white'));self.closeBtn.setPressedColor(QColor('white'))
        self.closeBtn.setHoverBackgroundColor(QColor('#dc3545'))
        self.closeBtn.setPressedBackgroundColor(QColor('#b42332'))


class _InformationOutline(QWidget):
    def __init__(self,parent,color):
        super().__init__(parent)
        self.color=QColor(color)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
    def paintEvent(self,event):
        painter=QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color=QColor(self.color);color.setAlpha(110)
        painter.setPen(color)
        rect=QRectF(self.rect()).adjusted(.5,.5,-.5,-.5)
        if self.window().isMaximized():painter.drawRect(rect)
        else:painter.drawRoundedRect(rect,8,8)


class InformationDialog(FramelessDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        if parent is not None and not parent.windowIcon().isNull():
            self.setWindowIcon(parent.windowIcon())
        bar=InformationTitleBar(self)
        self.setTitleBar(bar)
        self.setContentsMargins(1,bar.height()+1,1,1)
        bar.setGeometry(1,1,self.width()-2,bar.height())
        colors=information_theme(parent)
        bar.apply_theme(colors)
        self.outline=_InformationOutline(self,colors['line'])
        self.outline.setGeometry(self.rect());self.outline.raise_()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.titleBar.setGeometry(1,1,self.width()-2,self.titleBar.height())
        if hasattr(self,'outline'):
            self.outline.setGeometry(self.rect());self.outline.raise_()


def apply_information_theme(dialog, colors):
    c=colors
    if isinstance(dialog.titleBar,InformationTitleBar):
        dialog.titleBar.apply_theme(c)
    dialog.outline.color=QColor(c['line'])
    dialog.outline.update()
    palette=dialog.palette()
    for role,value in ((QPalette.Window,c['bg']),(QPalette.Base,c['surface']),
                       (QPalette.WindowText,c['text']),(QPalette.Text,c['text']),
                       (QPalette.Button,c['surface2']),(QPalette.ButtonText,c['text']),
                       (QPalette.Link,c['accent'])):
        palette.setColor(role,QColor(value))
    dialog.setPalette(palette)
    dialog.setStyleSheet(f'''
        QDialog {{background:{c['bg']};color:{c['text']};}}
        QWidget#informationBody {{background:{c['bg']};color:{c['text']};}}
        QScrollArea {{background:{c['bg']};border:none;}}
        QLabel {{background:transparent;color:{c['text']};font-family:'Microsoft YaHei UI';font-size:13px;}}
        QLabel#label_5, QLabel#informationTitle {{font-size:18px;font-weight:600;}}
        QLabel#label_2, QLabel#informationHint {{color:{c['dim']};font-size:12px;}}
        QPushButton,QToolButton {{background:{c['surface2']};color:{c['text']};border:1px solid {c['line']};
            border-radius:7px;padding:7px 12px;font-family:'Microsoft YaHei UI';font-size:13px;}}
        QPushButton:hover,QToolButton:hover {{background:{c['surface3']};border-color:{c['accent']};}}
        QPushButton:focus,QToolButton:focus {{border-color:{c['accent']};}}
        QPushButton#pushButton_2 {{background:{c['accent2']};color:{c['accent_text']};border-color:{c['accent2']};}}
        QPushButton#pushButton_2:hover {{background:{c['accent']};}}
        QToolButton[repositoryLink="true"] {{padding:8px 6px;}}
        QScrollBar:vertical {{background:transparent;width:8px;margin:0;}}
        QScrollBar::handle:vertical {{background:{c['line']};border-radius:4px;min-height:24px;}}
        QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{height:0;}}
        QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical {{background:transparent;}}
    ''')


def fit_information_dialog(dialog):
    screen=dialog.screen()
    if screen:
        area=screen.availableGeometry()
        dialog.resize(min(dialog.width(),max(280,area.width()-40)),min(dialog.height(),max(260,area.height()-60)))


def style_about_dialog(about, parent=None):
    c=information_theme(parent)
    about.pushButton_2.setStyleSheet('')
    for label in (about.label_7,about.label_9):
        label.setStyleSheet('')
        label.setText(label.text().replace('<font color="red">',f'<font color="{c["accent"]}">'))
    about.label_4.setText(about.label_4.text().replace('<a href=',f'<a style="color:{c["accent"]}" href='))
    about.label_2.setText(about.label_2.text().replace('<a href=',f'<a style="color:{c["accent"]}" href='))
    about.label.setMaximumSize(QSize(64,64))
    about.label.setFixedSize(64,64)
    about.verticalLayout.setAlignment(about.label,Qt.AlignHCenter)
    about.gridLayout_2.setColumnStretch(0,1)
    about.gridLayout_2.setColumnStretch(2,1)
    about.verticalLayout.setSpacing(6)
    about.verticalLayout_2.setContentsMargins(20,16,20,16)
    about.verticalLayout_2.setSpacing(12)
    about.horizontalLayout_3.setSpacing(8)
    for button in (about.gitee,about.gitee_3,about.gitee_2,about.gitee_4):
        button.setProperty('repositoryLink',True)
        button.setIconSize(QSize(32,32))
        button.setMinimumSize(70,68)
        button.setCursor(Qt.PointingHandCursor)
    if c is THEMES['dark']:
        for button in (about.gitee_2,about.gitee_4):
            pixmap=button.icon().pixmap(64,64)
            painter=QPainter(pixmap);painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(),QColor(c['text']));painter.end()
            button.setIcon(QIcon(pixmap))
    body=QWidget();body.setObjectName('informationBody');body.setLayout(about.verticalLayout_2)
    about.content_scroll=QScrollArea(about);about.content_scroll.setWidgetResizable(True)
    about.content_scroll.setFrameShape(QFrame.NoFrame);about.content_scroll.setWidget(body)
    root=QVBoxLayout(about);root.setContentsMargins(0,0,0,0);root.addWidget(about.content_scroll)
    about.setMinimumSize(350,300)
    apply_information_theme(about,c)
    fit_information_dialog(about)


class _DonationQrLabel(QLabel):
    def __init__(self,pixmap,parent=None):
        super().__init__(parent)
        self.original=pixmap
    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.fit_image()
    def fit_image(self):
        ratio=self.devicePixelRatioF()
        target=QSize(round(min(435,max(1,self.width()))*ratio),round(max(1,self.height())*ratio))
        image=self.original.scaled(target,Qt.KeepAspectRatio,Qt.FastTransformation)
        image.setDevicePixelRatio(ratio)
        self.setPixmap(image)


class DonationDialog(InformationDialog):
    def __init__(self,pixmap,parent=None,mode=None):
        super().__init__(parent)
        self.setObjectName('donationDialog');self.setWindowTitle('捐赠');self.setModal(True)
        self.resize(490,540);self.setMinimumSize(300,280)
        root=QVBoxLayout(self);root.setContentsMargins(16,16,16,14);root.setSpacing(12)
        scroll=QScrollArea(self);scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.NoFrame)
        body=QWidget();body.setObjectName('informationBody');layout=QVBoxLayout(body)
        layout.setContentsMargins(8,4,8,8);layout.setSpacing(12)
        title=QLabel('感谢支持 AnClicker');title.setObjectName('informationTitle');title.setAlignment(Qt.AlignCenter);title.setWordWrap(True)
        hint=QLabel('自愿捐赠 · 感谢你的支持');hint.setObjectName('informationHint');hint.setAlignment(Qt.AlignCenter);hint.setWordWrap(True)
        layout.addWidget(title)
        self.image=_DonationQrLabel(pixmap,body);self.image.setObjectName('donationQrCode');self.image.setAlignment(Qt.AlignCenter)
        self.image.setMinimumSize(0,120);self.image.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Ignored)
        self.original=pixmap
        layout.addWidget(self.image,1);layout.addWidget(hint)
        scroll.setWidget(body);root.addWidget(scroll,1)
        self.content_scroll=scroll
        apply_information_theme(self,information_theme(parent,mode));fit_information_dialog(self)
        self._fit_image()
    def _fit_image(self):
        self.image.fit_image()
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'image'):self._fit_image()
