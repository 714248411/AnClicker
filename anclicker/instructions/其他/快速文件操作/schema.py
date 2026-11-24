from anclicker.domain.fields import FieldSpec
TYPE_ID='快速文件操作'
FIELDS=(FieldSpec('操作','操作','choice','复制',('打开','复制')), FieldSpec('源路径','源文件或文件夹','path','',required=True), FieldSpec('目标路径','复制目标完整路径或现有文件夹','path'), FieldSpec('覆盖','覆盖已有目标','bool',False), FieldSpec('预期文字','核验文字（多项用 | 分隔）'), FieldSpec('窗口标题','核验目标窗口完整标题'), FieldSpec('区域','核验区域 x,y,w,h'),)
