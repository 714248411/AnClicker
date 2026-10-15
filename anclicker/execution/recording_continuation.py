"""Insert a new recording segment below the selected preview step."""
from dataclasses import replace
import uuid
from anclicker.platform.qt_compat.QtWidgets import QMessageBox


def begin_continuation(view):
    if view.busy or view.written or not view.drafts:
        return
    row = view.preview.currentRow()
    if row < 0 or row not in {index.row() for index in view.preview.selectedIndexes()}:
        QMessageBox.information(view, '接续录制', '请先选中一个步骤，新录制内容会插入该步骤下方。')
        return
    view._continuation = (list(view.drafts), row + 1)
    try:
        view.begin(continuation=True)
    finally:
        if not view.busy and getattr(view, '_continuation', None) is not None:
            finish_continuation(view, [])
            view.render_preview()
            view.update_buttons()


def finish_continuation(view, recorded, *, web=False):
    pending = getattr(view, '_continuation', None)
    if pending is None:
        view.drafts = recorded
        return
    original, position = pending
    view._continuation = None
    if web and recorded and recorded[0].type_id == '打开网页':
        # The recording session's setup page is not an additional workflow step.
        recorded = recorded[1:]
    if not recorded:
        view.drafts = original
        return
    suffix = original[position:]
    if suffix and position:
        anchor = original[position - 1].parameters
        group = anchor.get('录制批次')
        baseline = float(anchor.get('录制时间', 0))
        if group:
            # Resume the original segment relative to the insertion point,
            # rather than waiting its entire original offset again.
            new_group = uuid.uuid4().hex
            adjusted = []
            for draft in suffix:
                if draft.parameters.get('录制批次') != group:
                    adjusted.extend(suffix[len(adjusted):])
                    break
                parameters = dict(draft.parameters)
                parameters['录制批次'] = new_group
                parameters['录制时间'] = max(0, float(parameters.get('录制时间', 0)) - baseline)
                adjusted.append(replace(draft, parameters=parameters))
            suffix = adjusted
    view.drafts = original[:position] + recorded + suffix
