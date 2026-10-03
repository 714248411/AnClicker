"""数字验证码：独立参数编辑器与执行器。"""

from __future__ import annotations

import base64
import io

from instructions.common import FieldSpec, InstructionExecutorBase, SchemaInstructionEditor
from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from .数字验证码_ui import Ui_InstructionEditor


class InstructionEditor(SchemaInstructionEditor):
    TYPE_ID = "数字验证码"
    DISPLAY_NAME = "数字验证码"
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec("区域", "验证码区域 x,y,w,h", "text", "", required=True),
        FieldSpec("变量", "变量名称", "text", "验证码", required=True),
        FieldSpec(
            "验证码类型",
            "验证码类型",
            "choice",
            "通用数英1-4位",
            (
                "通用数英1-4位", "通用数英5-8位", "通用数英9~11位",
                "通用数英12位及以上", "通用数英1~6位plus",
                "定制-数英5位~qcs", "定制-纯数字4位",
                "通用中文字符1~2位", "通用中文字符3~5位",
                "通用中文字符6~8位", "通用中文字符9位及以上",
                "定制-XX西游苦行中文字符", "通用数字计算题", "通用中文计算题",
            ),
        ),
    )


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = "数字验证码"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"数字验证码执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if not delegated_:
            service_ = context.service("验证码识别")
            region_ = actions.region(actions.parameter(command.parameters, "区域"))
            code_type_ = str(actions.parameter(command.parameters, "验证码类型"))
            if service_ is not None:
                result_ = service_(region=region_, code_type=code_type_)
            else:
                result_ = self._recognize(context, region_, code_type_)
        actions.store_variable(context, command.parameters, result_)
        context.emit(f"数字验证码：{result_}")
        return result_

    @staticmethod
    def _recognize(context: ExecutionContext, region_, code_type_: str) -> str:
        type_ids_ = {
            "数字": 10110,
            "英文数字": 10110,
            "通用数英1-4位": 10110,
            "通用数英5-8位": 10111,
            "通用数英9~11位": 10112,
            "通用数英12位及以上": 10113,
            "通用数英1~6位plus": 10103,
            "定制-数英5位~qcs": 9001,
            "定制-纯数字4位": 193,
            "通用中文字符1~2位": 10114,
            "通用中文字符3~5位": 10115,
            "通用中文字符6~8位": 10116,
            "通用中文字符9位及以上": 10117,
            "定制-XX西游苦行中文字符": 10107,
            "通用数字计算题": 50100,
            "通用中文计算题": 50101,
        }
        if code_type_ not in type_ids_:
            raise ValueError(f"不支持的验证码类型：{code_type_}")
        database_ = context.metadata.get("database")
        token_ = database_.get_setting_value("云码Token") if database_ is not None else ""
        if not token_:
            raise RuntimeError("请先在设置中填写云码Token")

        image_ = actions.pyautogui_module().screenshot(region=region_)
        image_bytes_ = io.BytesIO()
        image_.save(image_bytes_, format="PNG")
        import requests

        response_ = requests.post(
            "http://api.jfbym.com/api/YmServer/customApi",
            json={
                "image": base64.b64encode(image_bytes_.getvalue()).decode("ascii"),
                "token": token_,
                "type": str(type_ids_[code_type_]),
            },
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response_.raise_for_status()
        payload_ = response_.json()
        if int(payload_.get("code", -1)) != 10000:
            raise RuntimeError(f"验证码识别失败：{payload_.get('msg') or payload_.get('code')}")
        return str((payload_.get("data") or {}).get("data") or "")
