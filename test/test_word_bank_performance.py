import random
from unittest.mock import patch
import pytest
from local_word_answers import QuestionBank, find_answer, load_bank
from test.test_requested_workflow_updates import bank, paragraph


def test_loaded_bank_reuses_exact_index_and_reports_conflicting_answers(tmp_path):
    path = bank(tmp_path, paragraph('题目：Ａ B C') + paragraph('答案：正确'))
    pairs = load_bank(path)
    assert load_bank(path) is pairs
    from local_word_answers import normalized
    with patch('local_word_answers.normalized', wraps=normalized) as normalize:
        assert find_answer(pairs, 'abc')['answer'] == '正确'
        assert normalize.call_count == 1  # Only the query, never every row again.
    for mode in ('精准', '包含', '模糊'):
        with pytest.raises(ValueError, match='答案不同'):
            find_answer(QuestionBank([('Ａ B C', 'one'), ('abc', 'two')]), 'abc', mode)


def test_question_bank_refreshes_when_document_changes(tmp_path):
    first = load_bank(bank(tmp_path, paragraph('题目：Q') + paragraph('答案：first')))
    second = load_bank(bank(tmp_path, paragraph('题目：Q') + paragraph('答案：second answer')))
    assert second is not first
    assert find_answer(second, 'Q')['answer'] == 'second answer'


def test_missing_word_body_has_clear_error(tmp_path):
    from zipfile import ZipFile
    path = tmp_path / 'broken.docx'
    with ZipFile(path, 'w') as archive:
        archive.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>')
    with pytest.raises(ValueError, match='缺少正文'):
        load_bank(path)


def reference(pairs, question, mode, threshold):
    from local_word_answers import normalized
    from difflib import SequenceMatcher
    needle = normalized(question)
    scored = []
    for q, answer in pairs:
        text = normalized(q)
        score = 1.0 if needle == text else (len(text)/len(needle) if mode == '包含' and text in needle else SequenceMatcher(None, needle, text, autojunk=False).ratio() if mode == '模糊' else 0)
        if score and (mode != '模糊' or score >= threshold):
            scored.append((score, answer, q))
    if not scored:
        return None
    scored.sort(key=lambda item: item[0], reverse=True)
    best = [item for item in scored if abs(item[0]-scored[0][0]) < 1e-9]
    if len({item[1] for item in best}) != 1:
        raise ValueError('conflict')
    return {'answer': best[0][1], 'question': best[0][2], 'score': best[0][0]}


@pytest.mark.parametrize('mode', ['精准', '包含', '模糊'])
def test_index_and_fuzzy_pruning_preserve_matching_and_ambiguity(mode):
    rng = random.Random(74)
    pairs = [(''.join(rng.choices('abcd中文题目', k=rng.randint(2,30))), str(i)) for i in range(100)]
    pairs += [('Ａ B C', 'x'), ('abc', 'y'), ('重复题', 'same'), ('重复题', 'same')]
    queries = [q for q, _ in pairs[::5]] + ['abc', 'xx重复题yy', '题目完全不同', '重复题']
    indexed = QuestionBank(pairs)
    for query in queries:
        for threshold in (.1, .5, .85, 1):
            try:
                expected = reference(pairs, query, mode, threshold)
            except ValueError:
                with pytest.raises(ValueError):
                    find_answer(indexed, query, mode, threshold)
                continue
            assert find_answer(indexed, query, mode, threshold) == expected
            assert find_answer(pairs, query, mode, threshold) == expected
