from anclicker.domain.fields import FieldSpec
TYPE_ID = '窗口位置与大小'
OPERATIONS = ('设置位置和大小','仅移动位置','仅调整大小','记录位置和大小','恢复位置和大小')
FIELDS = (FieldSpec('操作','操作','choice',OPERATIONS[0],OPERATIONS),
          FieldSpec('窗口','目标窗口','text',''),
          FieldSpec('X','屏幕 X','int',0),FieldSpec('Y','屏幕 Y','int',0),
          FieldSpec('宽度','窗口宽度','int',800,minimum=1,maximum=100000),
          FieldSpec('高度','窗口高度','int',600,minimum=1,maximum=100000),
          FieldSpec('记录名称','记录变量','text','窗口位置记录'))
