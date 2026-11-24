from anclicker.instructions.网页抓取工具.Crawl4AI网页抓取.executor import InstructionExecutor as BaseExecutor

class InstructionExecutor(BaseExecutor):
    TYPE_ID = '网页正文提取'
    OUTPUT_FORMAT = '正文'
