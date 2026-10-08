import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pytest
from local_ocr import OcrSession, validated_rows
from instructions.models import ExecutionContext


@pytest.mark.skipif(sys.platform != 'win32' or not (Path(__file__).parents[1]/'ocr_models/wechat/WeChatOCR.exe').is_file(),
                    reason='User-supplied Windows OCR runtime required')
def test_real_extracted_wechat(tmp_path):
    picture = Image.new('RGB', (800, 180), 'white')
    ImageDraw.Draw(picture).text((30, 40), '开始运行 12345',
        font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 48), fill='black')
    path = tmp_path/'微信离线测试.png'
    picture.save(path)
    with OcrSession() as session:
        rows = validated_rows(session.recognize(path, '微信OCR', {}, ExecutionContext(), 30))
    text = ''.join(row['text'] for row in rows)
    assert '12345' in text and '开始运行' in text
    assert all(0 <= row['center'][0] < 800 for row in rows)
