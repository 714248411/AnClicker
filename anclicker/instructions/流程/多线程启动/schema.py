from anclicker.domain.fields import FieldSpec as F
TYPE_ID = '多线程启动'
FIELDS = (F('线程名称','线程名称',default='线程1',required=True),
    F('入口编号','分支入口编号（0 使用后续连线）','int',0,minimum=0,maximum=2147483647),
    F('运行方式','运行方式','choice','运行一次',('运行一次','循环运行')),
)
