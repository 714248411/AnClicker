"""Offline DOCX question-bank matching; never calls a remote answer service."""
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
import re
import unicodedata
from xml.etree import ElementTree as ET
from zipfile import ZipFile

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def normalized(text):
    text = unicodedata.normalize('NFKC', str(text)).casefold()
    return re.sub(r'\s+', '', text).strip()

class QuestionBank(tuple):
    """Cached DOCX rows plus normalized questions and an exact-match index."""
    def __new__(cls, pairs):
        bank = super().__new__(cls, pairs)
        bank.normalized_rows = tuple((normalized(q), q, a) for q, a in bank)
        bank.exact = {}
        for text, question, answer in bank.normalized_rows:
            bank.exact.setdefault(text, []).append((question, answer))
        return bank


def _text(element):
    return ''.join(item.text or '' for item in element.findall('.//w:t', NS))

@lru_cache(maxsize=8)
def _read(path, modified, size):
    with ZipFile(path) as book:
        info = book.getinfo('word/document.xml')
        if info.file_size > 20_000_000:
            raise ValueError('题库内容过大，请拆分为较小的 Word 文档')
        body = ET.fromstring(book.read(info)).find('w:body', NS)
    if body is None:
        raise ValueError('Word 题库缺少正文，请检查文档后重新保存')
    pairs = []
    question, answer = [], []
    in_answer = False
    def flush():
        if question and answer:
            pairs.append(('\n'.join(question).strip(), '\n'.join(answer).strip()))
        question.clear()
        answer.clear()
    for child in body:
        if child.tag.endswith('}tbl'):
            flush()
            in_answer = False
            for row in child.findall('w:tr', NS):
                cells = [_text(cell).strip() for cell in row.findall('w:tc', NS)]
                if len(cells) >= 2 and cells[0] and cells[1]:
                    if cells[0] in ('题目', '问题') and cells[1] in ('答案', '参考答案'):
                        continue
                    pairs.append((cells[0], cells[1]))
            continue
        if not child.tag.endswith('}p'):
            continue
        text = _text(child).strip()
        if not text:
            continue
        q = re.match(r'^(?:题目|问题)\s*[:：]\s*(.*)$', text)
        a = re.match(r'^(?:参考答案|答案)\s*[:：]\s*(.*)$', text)
        if q:
            flush()
            in_answer = False
            question.append(q.group(1))
        elif a:
            in_answer = True
            answer.append(a.group(1))
        elif in_answer:
            answer.append(text)
        elif question:
            question.append(text)
    flush()
    pairs = tuple((q, a) for q, a in pairs if q and a)
    if not pairs:
        raise ValueError('题库中没有题目和答案；请使用题目/答案两列表格，或“题目：…”“答案：…”段落')
    return QuestionBank(pairs)

def load_bank(path):
    path = Path(path).expanduser().resolve()
    if path.suffix.lower() != '.docx':
        raise ValueError('请选择 .docx Word 题库；旧 .doc 文件请先另存为 .docx')
    stat = path.stat()
    return _read(str(path), stat.st_mtime_ns, stat.st_size)

def find_answer(pairs, question, mode='精准', threshold=.85):
    needle = normalized(question)
    if not needle:
        raise ValueError('待匹配题目不能为空')
    if mode not in ('精准', '包含', '模糊'):
        raise ValueError('请选择有效匹配方式')
    if not 0 < float(threshold) <= 1:
        raise ValueError('相似度必须在 0–1 之间')
    if isinstance(pairs, QuestionBank):
        exact = pairs.exact.get(needle)
        if exact:
            if len({answer for _, answer in exact}) != 1:
                raise ValueError('题库存在同等匹配但答案不同的题目，请补全题目或修正题库')
            return {'answer': exact[0][1], 'question': exact[0][0], 'score': 1.0}
        if mode == '精准':
            return None
        rows = pairs.normalized_rows
    else:
        rows = ((normalized(q), q, a) for q, a in pairs)
    scored = []
    for text, q, answer in rows:
        score = 0
        if needle == text:
            score = 1.0
        elif mode == '包含' and text in needle:
            score = len(text) / len(needle)
        elif mode == '模糊':
            matcher = SequenceMatcher(None, needle, text, autojunk=False)
            # Both bounds can only overestimate ratio(), preserving match results.
            if matcher.real_quick_ratio() < float(threshold) or matcher.quick_ratio() < float(threshold):
                continue
            score = matcher.ratio()
        if score and (mode != '模糊' or score >= float(threshold)):
            scored.append((score, answer, q))
    if not scored:
        return None
    scored.sort(key=lambda item: item[0], reverse=True)
    best = [item for item in scored if abs(item[0]-scored[0][0]) < 1e-9]
    if len({item[1] for item in best}) != 1:
        raise ValueError('题库存在同等匹配但答案不同的题目，请补全题目或修正题库')
    return {'answer': best[0][1], 'question': best[0][2], 'score': best[0][0]}
