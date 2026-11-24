"""Read-only crawl preview and background workers for the native editor."""
import csv
import io
import json
from pathlib import Path
from anclicker.platform.qt_compat.QtCore import QThread, Qt, Signal
from anclicker.platform.qt_compat.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QPlainTextEdit, QPushButton, QApplication, QFileDialog, QMessageBox, QInputDialog)
from anclicker.domain.instructions import ExecutionContext
from anclicker.platform.crawl4ai_bridge import crawl_page


class CrawlPreviewWorker(QThread):
    def __init__(self, parent, request=None, bridges=()):
        super().__init__(parent)
        self.request = request
        self.bridges = bridges
        self.context = ExecutionContext()
        self.result = None
        self.error = None

    def run(self):
        try:
            if self.request is not None:
                self.result = crawl_page(context=self.context, **self.request)
                return
            tabs = []
            for bridge in self.bridges:
                if self.context.stop_requested:
                    raise InterruptedError('已停止')
                if not bridge.lock.acquire(blocking=False):
                    continue
                try:
                    if bridge.process is None or bridge.process.poll() is not None:
                        continue
                    response = bridge.execute({'id':'acInspect','params':{}}, timeout=5)
                    for tab in response.get('result', {}).get('tabs', []):
                        if str(tab.get('url', '')).startswith(('http://', 'https://')):
                            tabs.append(tab)
                finally:
                    bridge.lock.release()
            self.result = tabs
        except Exception as error:
            self.error = str(error)


class VideoDownloadWorker(QThread):
    def __init__(self, parent, url, path, referer):
        super().__init__(parent)
        self.url, self.path, self.referer = url, path, referer
        self.cancelled = False
        self.error = None

    def run(self):
        from anclicker.platform.video_download import download_video
        try:
            download_video(self.url, self.path, self.referer, lambda: self.cancelled)
        except Exception as error:
            self.error = str(error)


class ImageDownloadWorker(VideoDownloadWorker):
    progress = Signal(int, int)

    def run(self):
        from anclicker.platform.image_download import download_image
        try:
            self.path = str(download_image(self.url, self.path, self.referer,
                lambda: self.cancelled, self.progress.emit))
        except Exception as error:
            self.error = str(error)


class CrawlResultDialog(QDialog):
    def __init__(self, result, parent=None, selected='Markdown'):
        super().__init__(parent)
        self.setWindowTitle('网页抓取结果')
        self.resize(820, 620)
        root = QVBoxLayout(self)
        title = QLabel(str(result.get('title') or '网页抓取结果'))
        title.setTextFormat(Qt.PlainText)
        title.setWordWrap(True)
        root.addWidget(title)
        address = QLabel(str(result.get('url', '')))
        address.setTextFormat(Qt.PlainText)
        address.setWordWrap(True)
        root.addWidget(address)
        summary = QLabel(f"正文 {len(result.get('text', ''))} 字符 · 链接 {len(result.get('links', []))} 条" +
                         (' · 达到上限，结果已截断；可在高级设置增加字符数' if result.get('truncated') else ''))
        summary.setWordWrap(True)
        root.addWidget(summary)
        self.result = result
        self.video_worker = None
        self.download_report = []
        self.pending_close = None
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        buffer = io.StringIO(newline='')
        writer = csv.writer(buffer)
        writer.writerow(['文字', '网址'])
        # Spreadsheet exports treat site-provided text as data, never formulas.
        for item in result.get('links', []):
            values = [str(item.get('text', '')), str(item.get('url', ''))]
            writer.writerow(["'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value for value in values])
        self.outputs = [
            ('Markdown', str(result.get('markdown', '')), 'md', 'Markdown (*.md)'),
            ('正文', str(result.get('text', '')), 'txt', '文本 (*.txt)'),
            ('链接', buffer.getvalue(), 'csv', 'CSV (*.csv)'),
            ('图片', json.dumps(result.get('images', []), ensure_ascii=False, indent=2), 'json', 'JSON (*.json)'),
            ('表格', json.dumps(result.get('tables', []), ensure_ascii=False, indent=2), 'json', 'JSON (*.json)'),
            ('标题', json.dumps(result.get('titles', {}), ensure_ascii=False, indent=2), 'json', 'JSON (*.json)'),
            ('视频', json.dumps(result.get('videos', []), ensure_ascii=False, indent=2), 'json', 'JSON (*.json)'),
            ('完整结果', json.dumps(result, ensure_ascii=False, indent=2), 'json', 'JSON (*.json)'),
        ]
        for label, text, extension, file_filter in self.outputs:
            edit = QPlainTextEdit()
            edit.setReadOnly(True)
            edit.setPlainText(text)
            self.tabs.addTab(edit, label)
        self.tabs.setCurrentIndex(next((i for i, row in enumerate(self.outputs) if row[0] == selected), 0))
        actions = QHBoxLayout()
        self.copy_button = QPushButton('复制当前内容')
        self.save_button = QPushButton('保存当前内容…')
        close_button = QPushButton('关闭')
        self.copy_button.clicked.connect(self.copy_current)
        self.save_button.clicked.connect(self.save_current)
        close_button.clicked.connect(self.accept)
        actions.addWidget(self.copy_button)
        actions.addWidget(self.save_button)
        actions.addStretch()
        actions.addWidget(close_button)
        root.addLayout(actions)
        export_actions = QHBoxLayout()
        export_actions.addWidget(QLabel('当前内容另存为'))
        for kind in ('Word', 'Excel', 'TXT'):
            button = QPushButton(kind)
            button.clicked.connect(lambda checked=False, kind=kind: self.save_converted(kind))
            export_actions.addWidget(button)
        export_actions.addStretch()
        root.addLayout(export_actions)
        video_actions = QHBoxLayout()
        self.image_save = QPushButton('图片另存为…')
        self.image_save.setEnabled(bool(result.get('images')))
        self.image_save.clicked.connect(self.save_image)
        video_actions.addWidget(self.image_save)
        self.video_save = QPushButton('视频另存为…')
        self.video_save.setEnabled(bool(result.get('videos')))
        self.video_save.clicked.connect(self.save_video)
        self.video_cancel = QPushButton('取消下载')
        self.video_cancel.setEnabled(False)
        self.video_cancel.clicked.connect(self.cancel_video)
        self.video_status = QLabel('')
        self.video_status.setWordWrap(True)
        self.video_status.setTextFormat(Qt.PlainText)
        video_actions.addWidget(self.video_save)
        video_actions.addWidget(self.video_cancel)
        self.report_button = QPushButton('查看下载结果')
        self.report_button.setVisible(False)
        self.report_button.clicked.connect(self.show_download_report)
        video_actions.addWidget(self.report_button)
        video_actions.addWidget(self.video_status, 1)
        root.addLayout(video_actions)

    def save_converted(self, kind):
        from anclicker.platform.extraction_export import export_extracted, EXTENSIONS
        keys = ['markdown', 'text', 'links', 'images', 'tables', 'titles', 'videos', None]
        key = keys[self.tabs.currentIndex()]
        value = self.result if key is None else self.result.get(key, '')
        if kind == 'Excel' and self.result.get('layout') and key in (None, 'text', 'markdown'):
            value = self.result
        suffix = EXTENSIONS[kind]
        name, _ = QFileDialog.getSaveFileName(self, '另存为 ' + kind, '网页提取结果' + suffix, kind + ' (*' + suffix + ')')
        if not name:
            return
        target = Path(name)
        if target.suffix.lower() != suffix:
            target = target.with_suffix(suffix)
        try:
            export_extracted(value, target, kind, '覆盖')
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, '保存失败', str(error))

    def copy_current(self):
        QApplication.clipboard().setText(self.outputs[self.tabs.currentIndex()][1])
        self.copy_button.setText('已复制')

    def save_current(self):
        label, text, extension, file_filter = self.outputs[self.tabs.currentIndex()]
        name, _ = QFileDialog.getSaveFileName(self, '保存' + label, '网页抓取结果.' + extension, file_filter)
        if not name:
            return
        path = Path(name)
        if not path.suffix:
            path = path.with_suffix('.' + extension)
        try:
            path.write_text(text, encoding='utf-8-sig' if extension == 'csv' else 'utf-8')
        except OSError as error:
            QMessageBox.warning(self, '保存失败', str(error))

    def save_image(self):
        from urllib.parse import urlsplit, unquote
        import re
        if self.video_worker is not None:return
        images = [item for item in self.result.get('images', []) if isinstance(item, dict) and item.get('url')]
        if not images:return
        from .image_save_range import ImageSaveRangeDialog, BatchImageDownloadWorker
        selection = ImageSaveRangeDialog(images, self)
        try:
            if selection.exec() != QDialog.Accepted:return
            indices = selection.indices()
            single = selection.single.isChecked()
        finally:selection.deleteLater()
        if not single:
            folder = QFileDialog.getExistingDirectory(self, '选择图片保存文件夹')
            if not folder:return
            worker = BatchImageDownloadWorker(self, images, indices, folder, self.result.get('url', ''))
            worker.progress.connect(lambda text: self.video_status.setText(text) if not worker.cancelled else None)
            self.video_worker = worker
            self.download_report = [];self.report_button.hide()
            worker.finished.connect(self.video_finished)
            self.image_save.setEnabled(False);self.video_save.setEnabled(False)
            self.video_cancel.setEnabled(True);self.video_status.setText('正在准备保存图片…')
            worker.start()
            return
        url = images[indices[0]]['url']
        if url.startswith('blob:'):
            QMessageBox.information(self, '无法直接另存', '此图片使用临时地址，请在浏览器中保存。')
            return
        filename = re.sub(r'[<>:"/\\|?*]', '_', unquote(urlsplit(url).path.rsplit('/', 1)[-1]))[:120] if not url.startswith('data:') else ''
        if Path(filename).suffix.lower() not in ('.png','.jpg','.jpeg','.gif','.webp','.bmp','.tif','.tiff','.ico','.avif','.svg'):
            filename = '网页图片'
        path, _ = QFileDialog.getSaveFileName(self, '图片另存为', filename, '图片文件 (*.png *.jpg *.jpeg *.gif *.webp *.bmp *.tif *.tiff *.ico *.avif *.svg);;所有文件 (*)')
        if not path:return
        worker = ImageDownloadWorker(self, url, path, self.result.get('url', ''))
        worker.progress.connect(lambda done,total: self.video_status.setText(
            ('正在下载图片：'+str(done*100//total)+'%') if total else ('正在下载图片：'+str(done//1024)+' KB')) if not worker.cancelled else None)
        self.video_worker = worker
        worker.finished.connect(self.video_finished)
        self.image_save.setEnabled(False);self.video_save.setEnabled(False)
        self.video_cancel.setEnabled(True);self.video_status.setText('正在下载图片…')
        worker.start()

    def save_video(self):
        from urllib.parse import urlsplit, unquote
        import re
        videos = self.result.get('videos', [])
        choices = [str(i + 1) + '. ' + (v.get('name') or v['url']) for i, v in enumerate(videos)]
        choice, accepted = QInputDialog.getItem(self, '选择视频', '要另存的视频', choices, 0, False)
        if not accepted:
            return
        video = videos[choices.index(choice)]
        url = video['url']
        if url.startswith('blob:') or urlsplit(url).path.lower().endswith(('.m3u8', '.mpd')):
            QMessageBox.information(self, '无法直接另存', '此视频使用临时地址或分段流，暂不支持直接保存。')
            return
        filename = re.sub(r'[<>:"/\\|?*]', '_', unquote(urlsplit(url).path.rsplit('/', 1)[-1]))[:120] or '网页视频'
        if Path(filename).suffix.lower() not in ('.mp4', '.webm', '.mov', '.m4v', '.ogv', '.avi', '.flv'):
            filename += '.mp4'
        path, _ = QFileDialog.getSaveFileName(self, '视频另存为', filename, '视频文件 (*.mp4 *.webm *.mov *.m4v *.ogv *.avi *.flv);;所有文件 (*)')
        if not path:
            return
        self.video_worker = VideoDownloadWorker(self, url, path, self.result.get('url', ''))
        self.video_worker.finished.connect(self.video_finished)
        self.video_save.setEnabled(False)
        self.image_save.setEnabled(False)
        self.video_cancel.setEnabled(True)
        self.video_status.setText('正在下载…')
        self.video_worker.start()

    def show_download_report(self):
        dialog = QDialog(self);dialog.setWindowTitle('图片下载结果');dialog.resize(620,400)
        layout = QVBoxLayout(dialog);text = QPlainTextEdit();text.setReadOnly(True)
        text.setPlainText('\n'.join(self.download_report));layout.addWidget(text)
        close = QPushButton('关闭');close.clicked.connect(dialog.accept);layout.addWidget(close)
        dialog.exec();dialog.deleteLater()

    def cancel_video(self):
        if self.video_worker:
            self.video_worker.cancelled = True
            self.video_cancel.setEnabled(False)
            self.video_status.setText('正在取消…')

    def video_finished(self):
        worker, self.video_worker = self.video_worker, None
        self.download_report = getattr(worker, 'report', [])
        self.report_button.setVisible(bool(self.download_report))
        self.video_status.setText(getattr(worker, 'summary', '') or worker.error or ('已保存：' + worker.path))
        self.video_save.setEnabled(bool(self.result.get('videos')))
        self.image_save.setEnabled(bool(self.result.get('images')))
        self.video_cancel.setEnabled(False)
        worker.deleteLater()
        if self.pending_close is not None:
            super().done(self.pending_close)

    def done(self, code):
        if self.video_worker is not None:
            self.pending_close = code
            self.cancel_video()
            return
        super().done(code)

    def accept(self):
        self.done(QDialog.Accepted)

    def reject(self):
        self.done(QDialog.Rejected)

    def closeEvent(self, event):
        if self.video_worker is not None:
            self.reject()
            event.ignore()
            return
        super().closeEvent(event)
