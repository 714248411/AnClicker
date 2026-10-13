"""User-controlled update prompt and a visual route back to its entry."""
from qt_compat.QtCore import Qt, QRect, QRectF, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, Signal
from qt_compat.QtGui import QColor, QPainter, QPen
from qt_compat.QtWidgets import QDialog, QLabel, QPushButton, QProgressBar, QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect


class UpdateCheckDialog(QDialog):
    """可随时重新打开的更新进度；关闭窗口不打断下载。"""

    def __init__(self, window, current_version):
        super().__init__(window)
        self.setWindowTitle('检查更新')
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(False)
        self.setObjectName('updateCheckDialog')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        title_row = QHBoxLayout()
        title = QLabel('检查更新', self)
        title.setObjectName('updateCheckTitle')
        title_row.addWidget(title)
        title_row.addStretch()
        self.close_button = QPushButton('×', self)
        self.close_button.setObjectName('updateCheckClose')
        self.close_button.setAccessibleName('关闭检查更新窗口')
        self.close_button.setAutoDefault(False)
        self.close_button.setFixedSize(26, 26)
        self.close_button.clicked.connect(self.reject)
        title_row.addWidget(self.close_button)
        layout.addLayout(title_row)
        self.version_label = QLabel(f'当前版本 {current_version}', self)
        self.version_label.setObjectName('updateCheckHint')
        self.version_label.setTextFormat(Qt.PlainText)
        self.version_label.setWordWrap(True)
        layout.addWidget(self.version_label)
        status_row = QHBoxLayout()
        self.status_label = QLabel(self)
        self.status_label.setTextFormat(Qt.PlainText)
        self.status_label.setWordWrap(True)
        self.percent_label = QLabel(self)
        status_row.addWidget(self.status_label, 1)
        status_row.addWidget(self.percent_label)
        layout.addLayout(status_row)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        layout.addWidget(self.progress_bar)
        self.hint_label = QLabel(self)
        self.hint_label.setObjectName('updateCheckHint')
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)
        buttons = QHBoxLayout()
        buttons.addStretch()
        self.dismiss_button = QPushButton('关闭', self)
        self.dismiss_button.setAutoDefault(False)
        self.dismiss_button.clicked.connect(self.reject)
        buttons.addWidget(self.dismiss_button)
        layout.addLayout(buttons)
        self.setFixedWidth(min(460, max(300, window.width() - 40)))
        self.apply_theme(window)
        self.set_progress('正在检查更新…', -1)

    def apply_theme(self, window):
        workspace = getattr(window, 'view_workspace', None)
        dark = getattr(workspace, 'theme_mode', '') == 'dark'
        self._background, foreground, self._border, muted, track = (
            ('#202126', '#eef0f6', '#424650', '#b5bdcc', '#343843') if dark
            else ('#ffffff', '#202534', '#d9deea', '#647084', '#e9edf5')
        )
        self.setStyleSheet(f'''
            QDialog#updateCheckDialog {{ background: transparent; }}
            QLabel {{ color: {foreground}; background: transparent; font-size: 13px; }}
            QLabel#updateCheckTitle {{ font-size: 16px; font-weight: 600; }}
            QLabel#updateCheckHint {{ color: {muted}; }}
            QProgressBar {{ border: none; border-radius: 5px; background: {track}; }}
            QProgressBar::chunk {{ border-radius: 5px; background: #6378ed; }}
            QPushButton {{ padding: 6px 16px; border: 1px solid {self._border};
                border-radius: 6px; color: {foreground}; background: {self._background}; }}
            QPushButton:hover {{ background: {track}; }}
            QPushButton#updateCheckClose {{ padding: 0; border: none; }}
        ''')
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(self._background))
        painter.setPen(QPen(QColor(self._border), 1))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(.5, .5, -.5, -.5), 12, 12)

    def set_progress(self, text, value):
        self.status_label.setText(text)
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0 if value < 0 else 100)
        if value >= 0:
            self.progress_bar.setValue(value)
        self.percent_label.setText(f'{value}%' if value >= 0 else '')
        self.adjustSize()

    def set_error(self, text):
        self.status_label.setText(text)
        self.progress_bar.hide()
        self.percent_label.clear()
        self.hint_label.setText('可关闭此窗口，再从“检查更新”重试。')
        self.dismiss_button.setText('关闭')
        self.adjustSize()


class UpdatePrompt(QDialog):
    update_requested = Signal()
    deferred = Signal(object, object)

    def __init__(self, window, version, notes='', ready=False):
        super().__init__(window)
        self.setWindowTitle('发现新版本')
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setObjectName('updatePrompt')
        self.setModal(False)
        dark = getattr(getattr(window, 'view_workspace', None), 'theme_mode', '') == 'dark'
        bg, fg, border = ('#202126','#eef0f6','#424650') if dark else ('#ffffff','#202534','#d9deea')
        self.setStyleSheet(f'QDialog#updatePrompt {{background:{bg};border:1px solid {border};border-radius:12px;}} QLabel {{color:{fg};background:transparent;}} QPushButton {{padding:7px 18px;border:1px solid {border};border-radius:6px;color:{fg};background:{bg};}} QPushButton#updateNow {{background:#5266dc;color:white;border:none;}}')
        layout = QVBoxLayout(self);layout.setContentsMargins(20,18,20,18);layout.setSpacing(12)
        title=QLabel(f'发现新版本 {version or ""}',self);title.setStyleSheet('font-size:16px;font-weight:600;');layout.addWidget(title)
        text=QLabel('更新包已准备好，点击更新后安装并重启。' if ready else '点击更新后下载并安装；稍后更新可从标题栏的“新版本”继续。',self)
        text.setWordWrap(True);layout.addWidget(text)
        if notes:
            detail=QLabel(str(notes)[:900],self);detail.setWordWrap(True);detail.setTextFormat(Qt.PlainText)
            detail.setMaximumHeight(180);layout.addWidget(detail)
        row=QHBoxLayout();row.addStretch()
        self.later_button=QPushButton('稍后更新',self);self.later_button.clicked.connect(self.reject)
        self.update_button=QPushButton('更新',self);self.update_button.setObjectName('updateNow');self.update_button.clicked.connect(self.choose_update)
        self.later_button.setAutoDefault(False);self.update_button.setAutoDefault(False)
        row.addWidget(self.later_button);row.addWidget(self.update_button);layout.addLayout(row)
        self.setFixedWidth(min(460,max(280,window.width()-40)))
        self.adjustSize()

    def choose_update(self):
        self.accept();self.update_requested.emit()

    def reject(self):
        if self.isVisible():
            pixmap=self.grab();rect=QRect(self.geometry())
            rect.moveTopLeft(self.mapToGlobal(self.rect().topLeft()))
            super().reject();self.deferred.emit(pixmap,rect)
        else: super().reject()


def animate_to_entry(window, button, pixmap, global_rect):
    if not window.isVisible() or not button.isVisible(): return
    ghost=QLabel(window);ghost.setAttribute(Qt.WA_TransparentForMouseEvents)
    ghost.setScaledContents(True);ghost.setPixmap(pixmap)
    start=QRect(global_rect);start.moveTopLeft(window.mapFromGlobal(start.topLeft()))
    end=QRect(button.mapTo(window,button.rect().topLeft()),button.size())
    ghost.setGeometry(start);ghost.show();ghost.raise_()
    effect=QGraphicsOpacityEffect(ghost);ghost.setGraphicsEffect(effect)
    group=QParallelAnimationGroup(ghost)
    move=QPropertyAnimation(ghost,b'geometry',group);move.setDuration(650)
    move.setStartValue(start);move.setEndValue(end);move.setEasingCurve(QEasingCurve.InOutCubic)
    fade=QPropertyAnimation(effect,b'opacity',group);fade.setDuration(650);fade.setStartValue(1.0);fade.setEndValue(0.25)
    group.addAnimation(move);group.addAnimation(fade)
    def finish():
        ghost.deleteLater()
        button.pulse()
    group.finished.connect(finish)
    ghost._animation=group
    group.start()
    return ghost
