from anclicker.domain.fields import FieldSpec as F
TYPE_ID = '多线程关闭'
FIELDS = (F('线程名称','线程名称',default='线程1'),
    F('关闭范围','关闭范围','choice','指定线程',('指定线程','全部线程')),
)
