"""Settings names and migration defaults."""
SETTING_TYPE_BASIC = "基础设置"
SETTING_TYPE_THIRD_PARTY = "三方接口"
SETTING_TYPE_SHORTCUT = "全局快捷键"
SETTING_TYPE_ACTIVATION = "激活信息"

ACTIVATION_SETTING_ITEMS = frozenset({"激活月份", "激活状态", "激活校验日期"})
THIRD_PARTY_SETTING_ITEMS = frozenset({"appId", "apiKey", "secretKey", "云码Token"})


def get_setting_type(setting_item: str) -> str:
    """根据设置项名称返回统一的中文分类。"""
    if setting_item in ACTIVATION_SETTING_ITEMS:
        return SETTING_TYPE_ACTIVATION
    if setting_item in THIRD_PARTY_SETTING_ITEMS:
        return SETTING_TYPE_THIRD_PARTY
    if setting_item.startswith("快捷键-"):
        return SETTING_TYPE_SHORTCUT
    return SETTING_TYPE_BASIC

DEFAULT_SETTINGS = {
    "图像匹配精度": "0.8",
    "退出提醒清空指令": "False",
    "系统提示音": "False",
    "显示工具栏": "True",
    "界面主题": "light",
    "任务完成后显示主窗口": "False",
    "当前文件路径": "None",
    "运行重复次数": "1",
    "执行中隐藏主窗口": "False",
    "appId": "",
    "apiKey": "",
    "secretKey": "",
    "云码Token": "",
    "快捷键-开始运行": "f10",
    "快捷键-结束运行": "f11",
    "快捷键-暂停和恢复": "alt+f11",
}

REMOVED_SETTING_ITEMS = (
    "模式",
    "时间间隔",
    "持续时间",
    "暂停时间",
    "启动检查更新",
    "高DPI自适应",
)

LEGACY_WINDOW_SETTING_KEYS = (
    "Clicker",
    "设置",
    "全局参数",
    "关于",
    "选择变量",
    "指令参数",
)
