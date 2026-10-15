"""Instruction execution implementation."""
from __future__ import annotations
from anclicker.instructions.common import actions
from anclicker.platform.services import play_system_tone
import sys
from anclicker.domain.instructions import CommandRecord
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.common import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'pyttsx4': ('import', 'pyttsx4', (), False),
    'winsound': ('import', 'winsound', (), False),
})


class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '提示音'

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f'提示音执行器不能执行{command.type_id}')
        (delegated_, result_) = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        p_ = command.parameters
        type_ = str(actions.parameter(p_, '类型', default='系统提示音'))
        count_ = int(actions.parameter(p_, '次数', default=1))
        if type_ in {'TTS', '播放语音'}:
            pyttsx4 = _module_imports.load('pyttsx4')
            engine_ = pyttsx4.init()
            engine_.setProperty('rate', int(actions.parameter(p_, '语速', default=200)))
            engine_.say(str(actions.parameter(p_, '内容', default='')))
            engine_.runAndWait()
        else:
            for index_ in range(count_):
                if type_ in {'蜂鸣', '音频信号'}:
                    play_system_tone(int(actions.parameter(p_, '频率', default=800)), int(actions.parameter(p_, '持续', default=300)))
                else:
                    sound_type_ = str(actions.parameter(p_, '提示类型', default='信息'))
                    if sys.platform == 'win32':
                        winsound = _module_imports.load('winsound')
                        sound_alias_ = {'警告': 'SystemAsterisk', '系统警告': 'SystemAsterisk', '错误': 'SystemExclamation', '系统错误': 'SystemExclamation', '询问': 'SystemQuestion', '系统询问': 'SystemQuestion', '信息': 'SystemHand', '系统信息': 'SystemHand', '系统启动': 'SystemStart', '系统关闭': 'SystemExit'}.get(sound_type_)
                        if sound_alias_:
                            winsound.PlaySound(sound_alias_, winsound.SND_ALIAS)
                        else:
                            winsound.MessageBeep()
                    else:
                        play_system_tone(500, 300)
                if index_ + 1 < count_:
                    actions.wait_seconds(float(actions.parameter(p_, '间隔', default=0.1)))
        context.emit('提示音播放完成')
        return True
