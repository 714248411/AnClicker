"""Display-only folding, resolved against persisted table step numbers."""
import re
import unicodedata

TYPE_ID = '折叠步骤'
THREAD_ID = '多线程启动'


def parse_ranges(text):
    text = unicodedata.normalize('NFKC', str(text)).translate(str.maketrans({'、': ',', '—': '-', '–': '-', '−': '-', '至': '-', '到': '-'}))
    ranges = []
    for part in text.split(';'):
        match = re.fullmatch(r'\s*([0-9]+)\s*(?:[-,]\s*([0-9]+)\s*)?', part)
        if not match:
            raise ValueError('范围格式不正确，请输入 7-9 或 7,9；多段用分号分隔。')
        start, end = int(match[1]), int(match[2] or match[1])
        if start < 1 or end < start:
            raise ValueError('步骤序号从 1 开始，结束序号不能小于开始序号。')
        ranges.append((start, end))
    return ranges


def validate_parameters(parameters):
    if not parameters.get('按条数', True) and not parameters.get('按范围', False):
        raise ValueError('请至少勾选一种折叠方法。')
    if parameters.get('按条数', True) and not 1 <= int(parameters.get('下方条数', 1)) <= 1000000:
        raise ValueError('下方条数必须在 1 到 1000000 之间。')
    if parameters.get('按范围', False) and parameters.get('动态范围', False):
        if not 1 <= int(parameters.get('终止步骤', 1)) <= 1000000:
            raise ValueError('终止步骤必须在 1 到 1000000 之间。')
    elif parameters.get('按范围', False):
        parse_ranges(parameters.get('步骤范围', ''))


def folding_groups(commands):
    ordered = sorted(commands, key=lambda c: (c.order, c.id or 0))
    groups = {}
    for index, command in enumerate(ordered):
        if command.type_id == THREAD_ID:
            p = command.parameters
            groups[command.id] = {'kind': THREAD_ID, 'name': str(p.get('线程名称', '')),
                'members': set(p.get('线程分组成员', ())) & {c.id for c in ordered},
                'collapsed': bool(p.get('已折叠', True)), 'locked': bool(p.get('整体锁定', True)),
                'depth': int(p.get('嵌套层级', 0))}
            continue
        if command.type_id != TYPE_ID:
            continue
        p = command.parameters
        members = set()
        try:
            validate_parameters(p)
            ranges = ([(index + 2, int(p.get('终止步骤', index + 1)))] if p.get('动态范围', False)
                      else parse_ranges(p.get('步骤范围', ''))) if p.get('按范围', False) else []
            count = int(p.get('下方条数', 1)) if p.get('按条数', True) else 0
            for j in range(index + 1, len(ordered)):
                if j <= index + count or any(start <= j + 1 <= end for start, end in ranges):
                    members.add(ordered[j].id)
        except (ValueError, TypeError):
            pass  # Invalid imported settings remain editable and hide nothing.
        groups[command.id] = {'number': 1 + sum(g.get('kind') != THREAD_ID for g in groups.values()), 'members': members,
                              'collapsed': bool(p.get('已折叠', True)), 'locked': bool(p.get('整体锁定', False))}
    return groups


def hidden_steps(groups):
    hidden = set()
    pending = [owner for owner, group in groups.items() if group['collapsed']]
    visited = set()
    while pending:
        owner = pending.pop()
        if owner in visited:
            continue
        visited.add(owner)
        members = groups[owner]['members']
        hidden.update(members)
        pending.extend(member for member in members if member in groups)
    return hidden


def group_title(group):
    if group.get('kind') == THREAD_ID:
        return f"{'▸' if group['collapsed'] else '▾'} 多线程 · {group['name']}（{len(group['members'])} 条）"
    return f"{'▸' if group['collapsed'] else '▾'} 折叠{group['number']}（{len(group['members'])} 条）"


def locked_move_ids(commands, selected_ids):
    """Dragging any member of a locked group moves its complete outer group."""
    groups = folding_groups(commands)
    selected = set(selected_ids)
    changed = True
    while changed:
        changed = False
        for owner, group in groups.items():
            whole = {owner} | group['members']
            if group['locked'] and selected & whole and not whole <= selected:
                selected.update(whole)
                changed = True
    return selected


def locked_insertion_boundary(ordered_ids, groups, boundary, placement=None):
    """Snap an interior gap to a group edge, including enclosing locked groups."""
    positions = {cid: i for i, cid in enumerate(ordered_ids)}
    boundary = max(0, min(boundary, len(ordered_ids)))
    while True:
        spans = [(positions[owner], max(positions[cid] for cid in group['members'] if cid in positions) + 1)
                 for owner, group in groups.items()
                 if group['locked'] and owner in positions and any(cid in positions for cid in group['members'])]
        blocked = [(start, end) for start, end in spans if start < boundary < end]
        if not blocked:
            return boundary
        start = min(a for a, b in blocked)
        end = max(b for a, b in blocked)
        boundary = (start if placement == 'above' else end if placement == 'below'
                    else start if boundary - start < end - boundary else end)
        # Once a direction is chosen, keep it through overlapping/nested groups.
        placement = 'above' if boundary == start else 'below'


def relocated_locked_parameters(commands, ordered_ids, *, enforce_boundaries=False):
    """Keep locked membership after a move, including absolute/disjoint ranges."""
    groups = folding_groups(commands)
    positions = {cid: index + 1 for index, cid in enumerate(ordered_ids)}
    updates = {}
    for command in commands:
        group = groups.get(command.id)
        if not group or not group['locked'] or command.id not in positions:
            continue
        owner = positions[command.id]
        if enforce_boundaries:
            expected = [c.id for c in sorted(commands, key=lambda c: (c.order, c.id or 0))
                        if c.id == command.id or c.id in group['members']]
            actual = ordered_ids[owner - 1:owner - 1 + len(expected)]
            if actual != expected:
                raise ValueError('折叠区域已加锁，只能在整组上方或下方插入，请先解锁。')
        members = sorted(positions[cid] for cid in group['members'] if cid in positions)
        if any(position <= owner for position in members):
            raise ValueError('锁定分组必须保持折叠步骤在成员前面，请整体移动。')
        if command.type_id == THREAD_ID:
            continue
        p = dict(command.parameters)
        if p.get('动态范围', False):
            p.update({'按条数': False, '按范围': True, '终止步骤': max(members, default=owner)})
            updates[command.id] = p
            continue
        if members and members == list(range(owner + 1, owner + 1 + len(members))) and not p.get('按范围', False):
            p['按条数'], p['下方条数'] = True, len(members)
        else:
            # Compress positions into ranges, retaining a representable empty group.
            spans = []
            for position in members or [owner]:
                if spans and position == spans[-1][1] + 1:
                    spans[-1][1] = position
                else:
                    spans.append([position, position])
            p['按条数'], p['按范围'] = False, True
            p['步骤范围'] = ';'.join(str(a) if a == b else f'{a}-{b}' for a, b in spans)
        updates[command.id] = p
    return updates


def sync_dynamic_folds(before, after):
    """Keep an Excel-style interval attached to its surviving end row."""
    groups = folding_groups(before)
    old = {c.id: c for c in before}
    positions = {c.id: i + 1 for i, c in enumerate(after)}
    updates = {}
    for command in after:
        previous = old.get(command.id)
        if (previous is None or command.type_id != TYPE_ID
                or not command.parameters.get('动态范围', False)
                or command.parameters != previous.parameters):
            continue  # New/edited settings explicitly choose a new interval.
        owner = positions[command.id]
        survivors = [positions[cid] for cid in groups[command.id]['members']
                     if cid in positions and positions[cid] > owner]
        end = max(survivors, default=owner)
        p = dict(command.parameters)
        # An empty interval is represented by its own header's row number.
        if p.get('按条数', True) and not p.get('按范围', False) and end > owner:
            p['下方条数'] = end - owner
        else:
            p.update({'按条数': False, '按范围': True, '终止步骤': end})
        if p != command.parameters:
            updates[command.id] = p
    return updates


def copy_group_drafts(commands, selected_ids, snapshot=None):
    """Copy locked groups in table order with destination-independent ranges."""
    ordered = sorted(commands, key=lambda c: (c.order, c.id or 0))
    groups = folding_groups(ordered)
    selected = locked_move_ids(ordered, selected_ids)
    drafts = []
    for command in ordered:
        if command.id not in selected:
            continue
        draft = command.to_draft()
        if command.type_id == THREAD_ID:
            draft.parameters.pop('线程分组成员', None)
        if command.id in groups and command.type_id == TYPE_ID:
            members = groups[command.id]['members'] & selected
            p = dict(draft.parameters)
            # Copied rows are contiguous in the payload. Relative counts keep
            # the copied header attached to its own rows at any paste position.
            p.update({'动态范围': True, '按条数': bool(members),
                      '下方条数': max(1, len(members)), '按范围': not bool(members), '终止步骤': 1})
            draft.parameters = p
        drafts.append(draft)
    if snapshot is not None and any(d.type_id == THREAD_ID for d in drafts):
        copied = [c for c in ordered if c.id in selected]
        positions = {c.id: i for i, c in enumerate(copied)}
        node_positions = {n.node_id: positions[n.command_id] for n in snapshot.nodes if n.command_id in positions}
        edges = [[node_positions[e.source], node_positions.get(e.target, -1), e.kind]
                 for e in snapshot.edges if e.source in node_positions
                 and (e.target in node_positions or e.target == 'end')]
        entries = [[i, positions[int(c.parameters.get('入口编号', 0) or 0)]]
                   for i, c in enumerate(copied) if c.type_id == THREAD_ID
                   and int(c.parameters.get('入口编号', 0) or 0) in positions]
        drafts[0].parameters['_线程复制'] = {'edges': edges, 'entries': entries}
        depths = [int(d.parameters.get('嵌套层级', 0)) for d in drafts if d.type_id == THREAD_ID]
        for draft in drafts:
            if draft.type_id == THREAD_ID:
                draft.parameters['嵌套层级'] = int(draft.parameters.get('嵌套层级', 0)) - min(depths)
    return drafts


def drag_fold_parameters(before, after, moved_ids, target_ids):
    """Use the marker's explicit parent collection, even at an unchanged row gap."""
    groups = folding_groups(before)
    positions = {c.id: i + 1 for i, c in enumerate(after)}
    moved, targets = set(moved_ids), set(target_ids)
    updates = {}
    for command in before:
        if command.type_id != TYPE_ID or command.id not in positions:
            continue
        members = set(groups[command.id]['members'])
        if command.id not in moved:
            members.difference_update(moved)
            if command.id in targets:
                members.update(moved)
        owner = positions[command.id]
        rows = sorted(positions[cid] for cid in members if cid in positions and positions[cid] > owner)
        p = dict(command.parameters)
        contiguous = rows == list(range(owner + 1, (rows[-1] if rows else owner) + 1))
        if contiguous and rows and p.get('按条数', True) and not p.get('按范围', False):
            p['下方条数'] = len(rows)
        elif contiguous and p.get('动态范围', False):
            p.update({'按条数': False, '按范围': True, '终止步骤': rows[-1] if rows else owner})
        else:
            spans = []
            for row in rows or [owner]:
                if spans and row == spans[-1][1] + 1:
                    spans[-1][1] = row
                else:
                    spans.append([row, row])
            p.update({'按条数': False, '按范围': True, '动态范围': False,
                      '步骤范围': ';'.join(str(a) if a == b else f'{a}-{b}' for a, b in spans)})
        updates[command.id] = p
    return updates
