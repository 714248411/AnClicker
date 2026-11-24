"""Stable one-step movement for selected instruction runs."""
from anclicker.domain.step_folding import locked_insertion_boundary


def move_selected_one_step(current, selected, groups, direction):
    if direction not in (-1, 1):
        raise ValueError('移动方向必须为上移或下移')
    selected = set(selected)
    runs = []
    continuing = False
    for item in current:
        if item in selected:
            if not runs or not continuing:
                runs.append([])
            runs[-1].append(item)
            continuing = True
        else:
            continuing = False
    ordered = list(current)
    for run in (runs if direction == -1 else reversed(runs)):
        start = ordered.index(run[0])
        end = start + len(run)
        if direction == -1:
            if start == 0:
                continue
            boundary = locked_insertion_boundary(ordered, groups, start - 1, 'above')
            neighbour = ordered[boundary:start]
            if not selected.intersection(neighbour):
                ordered[boundary:end] = run + neighbour
        else:
            if end == len(ordered):
                continue
            boundary = locked_insertion_boundary(ordered, groups, end + 1, 'below')
            neighbour = ordered[end:boundary]
            if not selected.intersection(neighbour):
                ordered[start:boundary] = neighbour + run
    return ordered
