import hashlib
import io
import json
from pathlib import Path
import struct
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest

import background_component_auto as auto
import background_component_settings as settings


def pe_bytes(suffix):
    data = bytearray(128)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 0x3c, 64)
    data[64:68] = b'PE\0\0'
    struct.pack_into('<H', data, 68, 0x14c)
    return bytes(data) + suffix


@pytest.fixture
def installation(tmp_path, monkeypatch):
    base = tmp_path/'application/current/damo'
    cache = tmp_path/'data/damo/7.2424'
    monkeypatch.setenv('ANCLICKER_DM_CONFIG', str(base/'config.json'))
    monkeypatch.setattr(auto.sys, 'platform', 'win32')
    monkeypatch.setattr(auto, '__file__', str(tmp_path/'application/background_component_auto.py'))
    monkeypatch.setattr(auto, 'managed_directory', lambda: cache)
    contents = {'xd47243.dll': pe_bytes(b'main'), 'Go.dll': pe_bytes(b'helper')}
    keys = {'xd47243.dll': 'dll_sha256', 'Go.dll': 'helper_sha256'}
    hashes = {keys[name]: hashlib.sha256(data).hexdigest() for name, data in contents.items()}
    monkeypatch.setattr(auto, 'FILES', tuple((name, len(data), keys[name]) for name, data in contents.items()))
    monkeypatch.setattr(auto, '_hashes', lambda: hashes)
    requests = []

    def download(name, target, size, digest, emit, cancelled):
        auto._check_cancel(cancelled)
        requests.append(name)
        target.write_bytes(contents[name])

    monkeypatch.setattr(auto, '_download', download)
    return base, cache, contents, requests


def test_clean_install_automatically_configures_complete_pair(installation):
    base, cache, contents, requests = installation
    result = auto.resolved_config()
    assert result['backend'] == 'native-7.2424'
    assert Path(result['dll_path']) == cache/'xd47243.dll'
    assert Path(result['helper_path']) == cache/'Go.dll'
    assert requests == list(contents)
    assert (cache/'installed.json').is_file()
    assert not base.exists()
    assert not list(cache.glob('.install-*'))


def test_local_components_reused_offline_and_after_app_relocation(installation, monkeypatch):
    base, cache, contents, requests = installation
    base.mkdir(parents=True)
    for name, data in contents.items():
        (base/name).write_bytes(data)
    first = auto.resolved_config()
    assert not requests
    monkeypatch.setenv('ANCLICKER_DM_CONFIG', str(base.parent.parent.parent/'new/current/damo/config.json'))
    assert auto.resolved_config() == first
    assert not requests


def test_second_use_checks_files_without_download(installation):
    auto.resolved_config()
    installation[3].clear()
    messages = []
    auto.resolved_config(emit=messages.append)
    assert not installation[3] and not messages


def test_corrupt_managed_file_is_repaired(installation):
    _, cache, contents, requests = installation
    auto.resolved_config()
    (cache/'Go.dll').write_bytes(b'bad file')
    requests.clear()
    auto.resolved_config()
    assert requests == ['Go.dll']
    assert (cache/'Go.dll').read_bytes() == contents['Go.dll']


@pytest.mark.parametrize('failure', ['network', 'hash', 'cancel', 'bits'])
def test_partial_or_bad_pair_is_not_published(installation, monkeypatch, failure):
    _, cache, contents, _ = installation

    def download(name, target, *args):
        if name == 'Go.dll':
            if failure == 'network':
                raise RuntimeError('network unavailable')
            if failure == 'cancel':
                raise auto.ConfigurationCancelled('cancel')
            if failure == 'hash':
                target.write_bytes(b'bad')
                return
        target.write_bytes(contents[name])

    monkeypatch.setattr(auto, '_download', download)
    if failure == 'bits':
        monkeypatch.setattr('background_dm_worker.pe_bits', lambda path: 64)
    with pytest.raises(RuntimeError):
        auto.ensure_component()
    assert not (cache/'xd47243.dll').exists()
    assert not (cache/'Go.dll').exists()
    assert not (cache/'installed.json').exists()
    assert not list(cache.glob('.install-*'))


def test_retry_after_interrupted_download(installation, monkeypatch):
    _, cache, contents, requests = installation
    original = auto._download
    monkeypatch.setattr(auto, '_download', Mock(side_effect=RuntimeError('offline')))
    with pytest.raises(RuntimeError):
        auto.resolved_config()
    monkeypatch.setattr(auto, '_download', original)
    auto.resolved_config()
    assert (cache/'Go.dll').read_bytes() == contents['Go.dll']


def test_concurrent_requests_install_once(installation, monkeypatch):
    original = auto._download

    def slow(*args):
        time.sleep(.02)
        original(*args)

    monkeypatch.setattr(auto, '_download', slow)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda _: auto.resolved_config(), range(3)))
    assert results[0] == results[1] == results[2]
    assert len(installation[3]) == 2


def test_waiting_for_installer_is_cancellable(installation):
    auto._install_lock.acquire()
    try:
        count = 0
        def cancelled():
            nonlocal count
            count += 1
            return count > 1
        with pytest.raises(auto.ConfigurationCancelled):
            auto.ensure_component(cancelled=cancelled)
    finally:
        auto._install_lock.release()
    assert not installation[1].exists()


def test_manual_configuration_and_authorization_are_preserved(installation, monkeypatch):
    base, _, _, requests = installation
    base.mkdir(parents=True)
    source = {'backend': 'com', 'dll_path': 'custom.dll', 'reg_code': 'local-only-code'}
    (base/'config.json').write_text(json.dumps(source), encoding='utf8')
    original = (base/'config.json').read_bytes()
    result = auto.resolved_config()
    assert result['dll_path'] == str((base/'custom.dll').resolve())
    assert result['reg_code'] == 'local-only-code'
    assert (base/'config.json').read_bytes() == original and not requests


def test_automatic_mode_ignores_old_manual_paths_without_erasing_them(installation):
    base, _, _, requests = installation
    base.mkdir(parents=True)
    source = {'mode': 'auto', 'backend': 'com', 'dll_path': 'old.dll'}
    (base/'config.json').write_text(json.dumps(source), encoding='utf8')
    result = auto.resolved_config()
    assert result['backend'] == 'native-7.2424' and len(requests) == 2
    assert json.loads((base/'config.json').read_text()) == source


def test_unconfigured_explicit_worker_does_not_download(installation):
    assert auto.resolved_config(automatic=False) == {}
    assert not installation[1].exists()


def test_legacy_dm_dll_keeps_com_loading(installation):
    base, _, _, requests = installation
    base.mkdir(parents=True)
    (base/'dm.dll').write_bytes(b'legacy')
    assert auto.resolved_config() == {'backend': 'com', 'dll_path': str((base/'dm.dll').resolve())}
    assert not requests


def test_invalid_manual_json_is_reported_without_overwriting(installation):
    base, _, _, requests = installation
    base.mkdir(parents=True)
    (base/'config.json').write_text('{broken', encoding='utf8')
    with pytest.raises(ValueError):
        auto.resolved_config()
    assert (base/'config.json').read_text() == '{broken'
    assert not requests


def test_non_windows_does_not_install(installation, monkeypatch):
    monkeypatch.setattr(auto.sys, 'platform', 'linux')
    with pytest.raises(RuntimeError, match='Windows'):
        auto.ensure_component()
    assert not installation[1].exists()


def test_storage_survives_velopack_update(tmp_path, monkeypatch):
    install = tmp_path/'portable/current'
    install.mkdir(parents=True)
    (install/'sq.version').write_text('version')
    (install.parent/'Update.exe').write_bytes(b'updater')
    monkeypatch.delenv('ANCLICKER_DATA_DIR', raising=False)
    monkeypatch.setattr(auto.sys, 'frozen', True, raising=False)
    monkeypatch.setattr(auto.sys, 'platform', 'win32')
    monkeypatch.setattr(auto.sys, 'executable', str(install/'AnClicker.exe'))
    assert auto.managed_directory() == install.parent/'data/damo/7.2424'


class Response(io.BytesIO):
    def geturl(self):
        return auto.SOURCE + 'test.dll'


@pytest.mark.parametrize('content,expected_error', [
    (b'good', None), (b'evil', '校验失败'), (b'huge data', '文件大小不符'), (b'', '校验失败')])
def test_download_validates_actual_bytes(tmp_path, monkeypatch, content, expected_error):
    # Exercise the real network reader without downloading third-party code in unit tests.
    monkeypatch.setattr(auto, 'urlopen', lambda request, timeout: Response(content))
    emit = Mock()
    args = ('test.dll', tmp_path/'download', 4, hashlib.sha256(b'good').hexdigest(), emit, lambda: False)
    if expected_error:
        with pytest.raises(RuntimeError, match=expected_error):
            auto._download(*args)
    else:
        auto._download(*args)
        assert (tmp_path/'download').read_bytes() == b'good'
        assert '100%' in emit.call_args[0][0]


def test_timeout_after_cancellation_reports_cancelled(tmp_path, monkeypatch):
    cancelled = [False]
    def connect(*args, **kwargs):
        cancelled[0] = True
        raise TimeoutError()
    monkeypatch.setattr(auto, 'urlopen', connect)
    with pytest.raises(auto.ConfigurationCancelled):
        auto._download('test', tmp_path/'download', 4, '', lambda msg: None, lambda: cancelled[0])


def test_settings_new_install_defaults_to_auto_and_saves_without_paths(installation):
    from qt_compat.QtWidgets import QApplication, QCheckBox, QDialogButtonBox
    app = QApplication.instance() or QApplication([])
    dialog = settings.ComponentSettings(None)
    try:
        assert dialog.findChild(QCheckBox, 'automaticBackgroundComponent').isChecked()
        buttons = dialog.findChild(QDialogButtonBox)
        buttons.button(QDialogButtonBox.Save).click()
        assert settings.read_config() == {'mode': 'auto'}
    finally:
        dialog.deleteLater()
        app.processEvents()


def test_setup_progress_keeps_ui_responsive_and_can_cancel(installation, monkeypatch):
    from qt_compat.QtWidgets import QApplication
    from qt_compat.QtCore import QTimer
    app = QApplication.instance() or QApplication([])
    ticks, started = [], threading.Event()
    def slow(**kwargs):
        started.set()
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            auto._check_cancel(kwargs['cancelled'])
            time.sleep(.01)
        raise AssertionError('UI did not process cancel during component setup')
    monkeypatch.setattr(auto, 'ensure_component', slow)
    timer = QTimer()
    timer.setInterval(10)
    def heartbeat():
        if not started.is_set():
            return
        ticks.append(1)
        if len(ticks) == 3:
            active = app.activeModalWidget()
            assert active is not None
            active.reject()
    timer.timeout.connect(heartbeat)
    timer.start()
    try:
        with pytest.raises(auto.ConfigurationCancelled):
            settings.configure_automatically()
        assert len(ticks) >= 3
    finally:
        timer.stop()
        app.processEvents()


def test_setup_progress_completes_with_configuration(installation):
    from qt_compat.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    result = settings.configure_automatically()
    assert result['backend'] == 'native-7.2424'
    app.processEvents()


def test_download_uses_pinned_backup_when_primary_is_unavailable(tmp_path, monkeypatch):
    calls = []
    def connect(request, timeout):
        calls.append(request.full_url)
        if len(calls) == 1:
            raise TimeoutError()
        return Response(b'good')
    monkeypatch.setattr(auto, 'urlopen', connect)
    auto._download('test.dll', tmp_path/'result', 4, hashlib.sha256(b'good').hexdigest(), lambda msg: None, lambda: False)
    assert len(calls) == 2
    assert auto.COMMIT in calls[0] and auto.COMMIT in calls[1]
    assert calls[1].startswith('https://api.github.com/')
    assert (tmp_path/'result').read_bytes() == b'good'


def test_settings_switch_to_auto_keeps_existing_authorization(installation):
    from qt_compat.QtWidgets import QApplication, QCheckBox, QDialogButtonBox
    app = QApplication.instance() or QApplication([])
    settings.write_config({'backend': 'com', 'dll_path': 'manual.dll', 'reg_code': 'secret-kept-local'})
    dialog = settings.ComponentSettings(None)
    try:
        checkbox = dialog.findChild(QCheckBox, 'automaticBackgroundComponent')
        assert not checkbox.isChecked()
        checkbox.setChecked(True)
        dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.Save).click()
        config = settings.read_config()
        assert config['mode'] == 'auto'
        assert config['dll_path'] == 'manual.dll'
        assert config['reg_code'] == 'secret-kept-local'
        assert 'secret-kept-local' not in settings.config_path().read_text()
    finally:
        dialog.deleteLater()
        app.processEvents()
