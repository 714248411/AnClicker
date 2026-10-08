"""Application-wide public configuration. Never load publishing credentials here."""

APP_NAME = "An Clicker"
CURRENT_VERSION = "v1.3.2"
WINDOW_TITLE = f"{APP_NAME}    [{CURRENT_VERSION}]"
# Stable application identity: changing these can break data/update compatibility.
APP_ID = "AnClicker"
EXECUTABLE_NAME = f"{APP_ID}.exe"
MACOS_BUNDLE_ID = "com.yanyi.anclicker"
COMPANY_NAME = "YanYi and contributors"
COPYRIGHT = "Copyright © 2022–2026 YanYi and contributors"
VERSION = CURRENT_VERSION.removeprefix("v")
WINDOWS_VERSION = tuple(int(part) for part in VERSION.split(".")) + (0,)
SINGLETON_KEY_DEFAULT = f"FasterThanLight_{APP_NAME}_SingletonKey"
DATA_DIR_ENV = "ANCLICKER_DATA_DIR"
SINGLETON_ENV = "ANCLICKER_SINGLETON_KEY"

# All public updater/build/publisher settings live in this one dictionary.
# Credential entries name environment variables; never put AK/SK values here.
UPDATE_CONFIG = {
    "pack_id": APP_ID,
    "runtime": "win-x64",
    "project": "an-clicker",
    "public_base_url": "https://updates.ytsoftware.cn",
    "snapshot_name": "update-source.json",
    "launcher_name": f"{APP_NAME}.exe",
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
UPDATE_CONFIG["url"] = f"{UPDATE_CONFIG['public_base_url']}/{UPDATE_CONFIG['key_prefix']}"


def update_source_config():
    """Return a fresh public snapshot for build/publish verification."""
    return {"url": UPDATE_CONFIG["url"], "pack_id": UPDATE_CONFIG["pack_id"],
            "runtime": UPDATE_CONFIG["runtime"]}


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
