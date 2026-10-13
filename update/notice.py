"""User-controlled update prompt and a visual route back to its entry."""
from qt_compat.QtCore import Qt, QRect, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, Signal
from qt_compat.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect


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
