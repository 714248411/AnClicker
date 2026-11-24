from anclicker.instructions.网页抓取工具.Crawl4AI网页抓取.executor import InstructionExecutor as BaseExecutor

class InstructionExecutor(BaseExecutor):
    TYPE_ID = '网页标题提取'
    OUTPUT_FORMAT = '标题'
