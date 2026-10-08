from unittest.mock import Mock, patch
import pytest
from ocr_pool import OcrPool
from instructions.models import ExecutionContext


def test_prewarm_reuses_worker_and_close_releases_it():
    with patch('ocr_pool.OcrSession') as factory:
        factory.return_value.recognize.return_value = []
        pool = OcrPool()
        pool.prewarm('RapidOCR', {})
        pool._entries['RapidOCR']['thread'].join(2)
        for _ in range(3):
            pool.recognize('image.png', 'RapidOCR', {}, ExecutionContext(), 5)
        pool.prewarm('RapidOCR', {})
        assert factory.call_count == 1
        assert factory.return_value.recognize.call_count == 4
        factory.return_value.close.assert_not_called()
        pool.close()
        factory.return_value.close.assert_called_once()


def test_timeout_discards_worker_and_engines_are_isolated():
    with patch('ocr_pool.OcrSession') as factory:
        first, second, third = Mock(), Mock(), Mock()
        first.recognize.side_effect = TimeoutError()
        factory.side_effect = [first, second, third]
        pool = OcrPool()
        with pytest.raises(TimeoutError):
            pool.recognize('image', 'RapidOCR', {}, ExecutionContext(), 1)
        first.close.assert_called_once()
        pool.recognize('image', 'RapidOCR', {}, ExecutionContext(), 1)
        pool.recognize('image', '微信OCR', {}, ExecutionContext(), 1)
        assert factory.call_count == 3
        pool.close()
        second.close.assert_called_once()
        third.close.assert_called_once()


def test_real_rapid_worker_warms_once_and_reuses_process(tmp_path):
    from PIL import Image, ImageDraw
    image = Image.new('RGB', (300, 120), 'white')
    ImageDraw.Draw(image).text((20, 40), '12345', fill='black', font_size=32)
    path = tmp_path/'text.png'
    image.save(path)
    pool = OcrPool()
    try:
        pool.prewarm('RapidOCR', {})
        thread = pool._entries['RapidOCR']['thread']
        thread.join(30)
        assert not thread.is_alive()
        session = pool._entries['RapidOCR']['session']
        assert session is not None
        process = session.process
        for _ in range(3):
            rows = pool.recognize(path, 'RapidOCR', {}, ExecutionContext(), 15)
            assert any('12345' in row['text'] for row in rows)
            assert pool._entries['RapidOCR']['session'].process.pid == process.pid
    finally:
        pool.close()
    assert process.poll() is not None
