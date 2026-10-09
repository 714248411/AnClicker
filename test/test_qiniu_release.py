"""Release integration checks; no network calls or publishing credentials required."""
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

_spec = importlib.util.spec_from_file_location(
    "anclicker_qiniu_publisher", Path(__file__).parents[1] / "packaging" / "发布Velopack.py")
publisher = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = publisher
_spec.loader.exec_module(publisher)


def asset(version="1.4.3"):
    return {"PackageId": "AnClicker", "Version": version, "Type": "Full",
            "FileName": f"AnClicker-{version}-win-x64-full.nupkg", "Size": 1,
            "SHA256": "A" * 64}


def test_default_configuration_matches_client(monkeypatch):
    for key in ("bucket_env", "region_env", "key_prefix_env", "public_base_url_env"):
        monkeypatch.delenv(publisher.UPDATE_CONFIG[key], raising=False)
    config = publisher.PublishConfig.from_environment()
    publisher.check_source(config)
    assert config.source_url == "https://updates.ytsoftware.cn/an-clicker/win-x64"


def test_historical_test_domain_cannot_replace_client_source(monkeypatch):
    monkeypatch.setenv("QINIU_PUBLIC_BASE_URL", "https://tm0gx0ycx.hd-bkt.clouddn.com")
    with pytest.raises(publisher.ReleaseError):
        publisher.check_source(publisher.PublishConfig.from_environment())


@pytest.mark.parametrize("version", ["1.4.3", "1.4.4"])
def test_same_or_newer_remote_version_blocks_release(version):
    with pytest.raises(publisher.ReleaseError):
        publisher.assert_newer("1.4.3", {"Assets": [asset(version)]})


def test_previous_production_version_allows_upgrade():
    publisher.assert_newer("1.4.3", {"Assets": [asset("1.3.4")]})


def test_remote_package_path_traversal_is_rejected():
    unsafe = asset()
    unsafe["FileName"] = "../other.nupkg"
    with pytest.raises(publisher.ReleaseError):
        publisher.current_assets({"Assets": [unsafe]})


@pytest.mark.parametrize("package_verified", [True, False])
def test_feed_is_published_only_after_package_verification(tmp_path, monkeypatch, package_verified):
    package = asset()
    package_path = tmp_path / package["FileName"]
    package_path.write_bytes(b"x")
    package["SHA256"] = publisher.digest(package_path)
    feed = {"Assets": [package]}
    feed_path = tmp_path / publisher.UPDATE_CONFIG["feed_name"]
    feed_path.write_text(json.dumps(feed), encoding="utf-8")
    events = []
    config = publisher.PublishConfig("ytsoftware-velopack", "z0",
                                     "https://updates.ytsoftware.cn", "an-clicker/win-x64")
    monkeypatch.setattr(publisher, "validate_local", lambda *args: (feed, [package]))
    remote = iter([{"Assets": []}, {"Assets": []}, feed])
    monkeypatch.setattr(publisher, "get_feed", lambda *args: next(remote))

    class Uploader:
        def __init__(self, config):
            pass

        def upload(self, path, overwrite=False):
            events.append("feed" if overwrite else "package")

        def refresh_feed(self):
            events.append("refresh")

    def verify(*args):
        events.append("verify")
        if not package_verified:
            raise RuntimeError("simulated package hash mismatch")

    monkeypatch.setattr(publisher, "QiniuUploader", Uploader)
    monkeypatch.setattr(publisher, "verify_public", verify)
    response = Mock()
    response.json.return_value = feed
    monkeypatch.setattr(publisher.requests, "get", lambda *args, **kwargs: response)
    if package_verified:
        publisher.publish(config, tmp_path, tmp_path)
        assert events == ["package", "verify", "feed", "refresh"]
    else:
        with pytest.raises(RuntimeError, match="hash mismatch"):
            publisher.publish(config, tmp_path, tmp_path)
        assert events == ["package", "verify"]
