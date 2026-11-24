"""Application-wide public configuration. Never load publishing credentials here."""

APP_NAME = "AnClicker"
CURRENT_VERSION = "v1.9.3"
WINDOW_TITLE = f"{APP_NAME}    [{CURRENT_VERSION}]"
# Stable application identity: changing these can break data/update compatibility.
APP_ID = "AnClicker"
EXECUTABLE_NAME = f"{APP_ID}.exe"
MACOS_BUNDLE_ID = "com.yanyi.anclicker"
COMPANY_NAME = "YanYi and contributors"
COPYRIGHT = "Copyright © 2022–2026 YanYi and contributors"
VERSION = CURRENT_VERSION.removeprefix("v")
WINDOWS_VERSION = tuple(int(part) for part in VERSION.split(".")) + (0,)
# Keep the legacy process/update identities independent of the display name.
SINGLETON_KEY_DEFAULT = "FasterThanLight_An Clicker_SingletonKey"
DATA_DIR_ENV = "ANCLICKER_DATA_DIR"
SINGLETON_ENV = "ANCLICKER_SINGLETON_KEY"

# Public update identity and the legacy publishing route.
# Credential entries name environment variables; never put AK/SK values here.
UPDATE_CONFIG = {
    "pack_id": APP_ID,
    "runtime": "win-x64",
    "project": "an-clicker",
    "internal_api_base_url": "https://www.ytsoftware.cn",
    "public_base_url": "https://updates.ytsoftware.cn",
    "snapshot_name": "update-source.json",
    "launcher_name": "AnClicker.exe",
    "bucket": "ytsoftware-velopack",
    "region": "z0",
    "access_key_env": "QINIU_ACCESS_KEY",
    "secret_key_env": "QINIU_SECRET_KEY",
    "bucket_env": "QINIU_BUCKET",
    "region_env": "QINIU_REGION",
    "key_prefix_env": "QINIU_KEY_PREFIX",
    "public_base_url_env": "QINIU_PUBLIC_BASE_URL",
}
UPDATE_CONFIG.update({
    "feed_name": f"releases.{UPDATE_CONFIG['runtime']}.json",
    "assets_name": f"assets.{UPDATE_CONFIG['runtime']}.json",
    "portable_name": f"{UPDATE_CONFIG['pack_id']}-{UPDATE_CONFIG['runtime']}-Portable.zip",
    "key_prefix": f"{UPDATE_CONFIG['project']}/{UPDATE_CONFIG['runtime']}",
})
# Legacy URL used by historical release tools only.
UPDATE_CONFIG["url"] = f"{UPDATE_CONFIG['public_base_url']}/{UPDATE_CONFIG['key_prefix']}"
UPDATE_CHANNELS = ("stable", "beta")


def update_source_config(channel="stable"):
    """Return the public updater configuration for a distribution channel."""
    if channel not in UPDATE_CHANNELS:
        raise ValueError(f"Unknown update channel: {channel}")
    base_url = UPDATE_CONFIG["internal_api_base_url"]
    project = UPDATE_CONFIG["project"]
    return {"url": f"{base_url}/api/v1/internal-updates/{project}/{channel}/",
            "pack_id": UPDATE_CONFIG["pack_id"], "runtime": UPDATE_CONFIG["runtime"],
            "delivery_channel": channel}


QQ = "84284936"
QQ_GROUP = "http://qm.qq.com/cgi-bin/qm/qr?_wv=1027&k=XCOQZMwDVB3y-vIz4LXdMITq-7sqGP3A&authKey=6FPrdTF0o6JIfJoc58deZ1cEWvUURazs%2FDh%2BJOz1aJI2DS%2BMFr3jRIai2%2F7bbvwN&noverify=0&group_code=84284936"
QQ_OLD = "308994839"
QQ_GROUP_OLD = "https://qm.qq.com/q/3ih3PE16Mg"
QQ_CONTACTS = ("714248411", "2309636438")
EMAIL_CONTACTS = ("714248411@qq.com", "federalsadler@sohu.com")
CONTRIBUTORS = ("YanYi", "FasterThanLight")
MAIN_WEBSITE = "https://gitee.com/fasterthanlight/automatic_clicker_2"
GITEE_WEBSITE_SECOND = "https://gitee.com/YiZhiYanYi/AnClicker"
GITHUB_WEBSITE_OLD = "https://github.com/FsterThanLight/automatic_clicker_2"
Github_WEBSITE = "https://github.com/714248411/AnClicker"
ISSUE_WEBSITE = "https://gitee.com/fasterthanlight/automatic_clicker_2/issues"
ISSUE_WEBSITE_2 = "https://gitee.com/YiZhiYanYi/AnClicker/issues"
