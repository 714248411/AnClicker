"""Configured desktop notifications and window restoration."""
import time
from anclicker.platform.services import play_system_tone, show_window

class ConfiguredSystemServices:
    def __init__(self, settings):
        self.settings = settings

    def get_bool_setting(self, name):
        return self.settings.get_bool_setting(name)

    def system_prompt_tone(self, judge: str) -> None:
        if not self.get_bool_setting("系统提示音"):
            return
        if judge == "线程结束":
            for _ in range(3):
                play_system_tone(500, 300)
        elif judge == "全局快捷键":
            play_system_tone(500, 300)
        elif judge == "执行异常":
            play_system_tone(1000, 1000)

    def show_normal_window_with_specified_title(self, title: str) -> None:
        if not self.get_bool_setting("任务完成后显示主窗口"):
            return
        time.sleep(0.5)
        show_window(title)
