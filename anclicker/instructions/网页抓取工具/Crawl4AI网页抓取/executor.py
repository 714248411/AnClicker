"""Run Crawl4AI through AnClicker's cancellable subprocess bridge."""
from anclicker.instructions.common import InstructionExecutorBase, actions
from anclicker.platform.crawl4ai_bridge import crawl_page

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = 'Crawl4AI网页抓取'
    OUTPUT_FORMAT = None

    def execute_once(self, context, command):
        context.metadata.pop('last_web_extraction', None)
        delegated, result = actions.delegated(context, self.TYPE_ID, command)
        if delegated:
            return result
        p = command.parameters
        resolve = lambda key: actions.substitute_variables(context, str(p.get(key, '')))
        name = str(p.get('变量', '网页抓取结果')).strip()
        if not name:
            raise ValueError('请填写保存结果的变量名称')
        kind = self.OUTPUT_FORMAT or p.get('格式', 'Markdown')
        if kind not in ('Markdown', '正文', '链接', '图片', '视频', '表格', '标题', '完整结果'):
            raise ValueError('不支持的抓取格式')
        context.emit('Crawl4AI：正在抓取网页…')
        result = crawl_page(resolve('网址'), context, selector=resolve('选择器'),
                            wait_for=resolve('等待元素'), timeout=int(p.get('超时', 60)),
                            max_chars=int(p.get('最大字符数', 20000)))
        value = result if kind == '完整结果' else result[{'Markdown':'markdown', '正文':'text', '链接':'links', '图片':'images', '视频':'videos', '表格':'tables', '标题':'titles'}[kind]]
        context.set_variable(name, value)
        context.metadata['last_web_extraction'] = value
        context.emit('Crawl4AI：抓取完成，已保存到变量 ' + name + ('（结果已截断）' if result['truncated'] else ''))
        return value
