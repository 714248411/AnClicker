from anclicker.domain.fields import FieldSpec
FIELDS = (FieldSpec('points','点击坐标','text',''), FieldSpec('clickType','点击方式','choice','单击',choices=('单击','双击','右键')), FieldSpec('interval','每点间隔（秒）','float',1,minimum=0,maximum=3600),)
