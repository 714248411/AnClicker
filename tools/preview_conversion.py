import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['QT_QPA_PLATFORM']='windows'
from qt_compat.QtWidgets import QApplication
from instruction_code import prepare_instruction_conversion
from instruction_conversion_dialog import InstructionConversionDialog
app=QApplication([])
dialog=InstructionConversionDialog(prepare_instruction_conversion('时间等待({"时长":\n打开网页({"url": "https://www.hao123.com"})'))
dialog.show();app.processEvents()
dialog.grab().save('validation/conversion-dialog.png')
dialog.close()
