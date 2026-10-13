from types import SimpleNamespace
from qt_compat.QtTest import QTest
from qt_compat.QtCore import Qt
from test.test_hidden_stop import host
import update.自动更新接入 as module


def prepare(host, monkeypatch):
    manager=host.auto_update
    monkeypatch.setattr(module,'update_target_details',lambda info:('9.9.9','测试更新说明'))
    return manager,object()


def test_found_update_waits_for_consent_and_later_animates_to_entry(host,monkeypatch):
    m,info=prepare(host,monkeypatch);downloads=[]
    monkeypatch.setattr(m,'start_download',lambda *a,**kw:downloads.append((a,kw)))
    m.handle_update_info(info);QTest.qWait(30)
    prompt=m._update_prompt
    assert prompt.isVisible() and not downloads
    assert prompt.update_button.text()=='更新' and prompt.later_button.text()=='稍后更新'
    prompt.later_button.click();QTest.qWait(100)
    assert not downloads and m.ready_update_info is None
    ghost=m._defer_animation
    assert ghost.isVisible() and ghost._animation.duration()==650
    QTest.qWait(800)
    button=host.view_workspace.title_bar.updateButton
    assert button.isVisible() and button._pulse_animation is not None
    button.click();QTest.qWait(20)
    assert m._update_prompt.isVisible() and not downloads
    m._update_prompt.update_button.click()
    assert len(downloads)==1 and downloads[0][1]['is_manual'] is True
    assert m._install_after_download


def test_previously_downloaded_update_still_requires_choice(host,monkeypatch):
    m,info=prepare(host,monkeypatch);applied=[]
    monkeypatch.setattr(m,'apply_ready_update',lambda:applied.append(True))
    m.handle_pending_update(info);QTest.qWait(25)
    assert m._update_prompt.isVisible() and not applied
    m._update_prompt.later_button.click();QTest.qWait(25)
    assert not applied
    host.view_workspace.title_bar.updateButton.click()
    assert applied==[True]


def test_install_only_after_consented_download_finishes(host,monkeypatch):
    m,info=prepare(host,monkeypatch);applied=[]
    monkeypatch.setattr(m,'apply_ready_update',lambda:applied.append(True))
    m.mark_update_ready(info);m.on_download_thread_finished();QTest.qWait(20)
    assert not applied
    m._install_after_download=True
    m.on_download_thread_finished();QTest.qWait(20)
    assert applied==[True]
    m._install_after_download=True;m.download_was_manual=False
    m.handle_download_failure('模拟失败')
    assert not m._install_after_download


def test_escape_defers_without_downloading(host,monkeypatch):
    m,info=prepare(host,monkeypatch);downloads=[]
    monkeypatch.setattr(m,'start_download',lambda *a,**kw:downloads.append(True))
    m.handle_update_info(info);QTest.qWait(20)
    QTest.keyClick(m._update_prompt,Qt.Key_Escape)
    assert not downloads and m._update_prompt is None


def test_prompt_layout_in_light_and_dark_themes(host,monkeypatch):
    m,info=prepare(host,monkeypatch)
    for theme in ('light','dark'):
        host.view_workspace.theme_mode=theme;host.view_workspace._apply_theme()
        m.handle_update_info(info);QTest.qWait(30)
        prompt=m._update_prompt
        for button in (prompt.later_button,prompt.update_button):
            assert prompt.rect().contains(button.geometry()) and button.isVisible()
        prompt.grab().save('validation/update-prompt-'+theme+'.png')
        prompt.accept();QTest.qWait(20)
