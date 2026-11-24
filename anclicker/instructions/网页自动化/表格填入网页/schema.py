from anclicker.domain.fields import FieldSpec
TYPE_ID='表格填入网页'
FIELDS=(FieldSpec('range','表格区域（留空为当前工作表）','text',''),FieldSpec('mode','填入方式','choice','按表头对应',choices=('按表头对应','按顺序')),FieldSpec('header','首行内容','choice','首行表头',choices=('首行表头','无表头')))
