"""Exercise bundled OCR models and its isolated worker without desktop input."""
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image, ImageDraw, ImageFont
from local_ocr import OcrSession, validated_rows
from instructions.models import ExecutionContext


def validate_offline_ocr():
    with TemporaryDirectory(prefix='ocr-smoke-') as folder:
        path = Path(folder) / 'offline.png'
        image = Image.new('RGB', (700, 140), 'white')
        ImageDraw.Draw(image).text((20, 35), 'An Clicker 12345',
                                   font=ImageFont.load_default(size=48), fill='black')
        image.save(path)
        with OcrSession() as session:
            rows = validated_rows(session.recognize(path, 'RapidOCR', {}, ExecutionContext(), 45))
        if '12345' not in ''.join(row['text'] for row in rows):
            raise RuntimeError('Bundled offline OCR recognition failed')
        return {'rapidocr': True, 'isolated_worker': True, 'synthetic_image': True}
