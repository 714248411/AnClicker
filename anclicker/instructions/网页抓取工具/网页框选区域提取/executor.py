import json
from anclicker.instructions.common import InstructionExecutorBase
from anclicker.platform.rpa_bridge import get_bridge

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID='网页框选区域提取'
    def execute_once(self,context,command):
        context.metadata.pop('last_web_extraction',None)
        bridge=get_bridge()
        if bridge.process is None or bridge.process.poll() is not None:
            raise ValueError('请先在 AnClicker 内打开并定位到框选网页')
        try: region=json.loads(command.parameters.get('区域',''))
        except (ValueError,TypeError):raise ValueError('请先框选网页区域')
        response=bridge.execute({'id':'acRegion','params':{'action':'extract','region':region,'maxChars':int(command.parameters.get('最大字符数',20000))}},context=context,timeout=60)
        result=response['result']
        context.metadata['last_web_extraction']=result
        context.emit('网页区域提取完成：'+str(len(result.get('text','')))+' 字符'+('（已达到上限）' if result.get('truncated') else ''))
        return result
