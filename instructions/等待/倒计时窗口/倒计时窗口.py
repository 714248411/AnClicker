"""倒计时窗口：独立参数编辑器与执行器。"""

from __future__ import annotations

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .倒计时窗口_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "倒计时窗口"
    DISPLAY_NAME = "倒计时窗口"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("标题", "窗口标题", "text", "倒计时"),
        FieldSpec("内容", "提示内容", "multiline", "请稍候"),
        FieldSpec("秒数", "倒计时秒数", "int", 5, minimum=0, maximum=86400),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "倒计时窗口"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"倒计时窗口执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        title_ = str(actions.parameter(command.parameters, "标题", default="倒计时"))
        content_ = str(actions.parameter(command.parameters, "内容", default="请稍候"))
        seconds_ = int(actions.parameter(command.parameters, "秒数", default=5))
        self._show_countdown(context, title_, content_, seconds_)
        return True

    @staticmethod
    def _show_countdown(
        context: ExecutionContext,
        title_: str,
        content_: str,
        seconds_: int,
    ) -> None:
        import tkinter as tk
        from tkinter import ttk

        root_ = tk.Tk()
        root_.title(title_)
        root_.geometry("300x200")
        root_.resizable(False, False)
        try:
            root_.attributes("-topmost", True)
            root_.attributes("-alpha", 0.9)
            root_.attributes("-toolwindow", True)
        except tk.TclError:
            pass

        tk.Label(root_, text=content_, font=("微软雅黑", 12), fg="blue").pack(pady=4)
        count_label_ = tk.Label(root_, text="", font=("微软雅黑", 50), fg="red")
        count_label_.pack(pady=1)
        state_ = {"remaining": max(0, int(seconds_)), "closed": False}

        def finish_() -> None:
            if state_["closed"]:
                return
            state_["closed"] = True
            context.emit("已结束等待窗口")
            root_.destroy()

        def update_() -> None:
            if state_["closed"]:
                return
            if context.stop_requested or state_["remaining"] < 1:
                finish_()
                return
            count_label_.configure(text=str(state_["remaining"]))
            context.emit(f"{title_}：{state_['remaining']}")
            state_["remaining"] -= 1
            root_.after(1000, update_)

        ttk.Button(root_, text="结束等待", command=finish_).pack(pady=4)
        root_.protocol("WM_DELETE_WINDOW", finish_)
        root_.update_idletasks()
        x_ = max(0, (root_.winfo_screenwidth() - root_.winfo_width()) // 2)
        y_ = max(0, (root_.winfo_screenheight() - root_.winfo_height()) // 2)
        root_.geometry(f"+{x_}+{y_}")
        if state_["remaining"] < 1:
            finish_()
            return
        update_()
        root_.mainloop()
