"""Inspect centralized imports without executing the inspected application."""
import argparse
import ast
from importlib.machinery import PathFinder
from importlib.util import resolve_name
from pathlib import Path
import sys

SOURCE_DIRECTORIES = ('anclicker', 'legacy', 'tools', 'examples', 'archive')


def python_files(root):
    root = Path(root)
    return [root / 'main.py', root / 'info.py',
            *(p for folder in SOURCE_DIRECTORIES for p in (root / folder).rglob('*.py'))]


def dependency_specs(tree):
    constructors = {alias.asname or alias.name for node in tree.body
                    if isinstance(node, ast.ImportFrom) and node.module == 'anclicker._imports'
                    for alias in node.names if alias.name == 'DeferredImports'}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Name) and call.func.id in constructors:
                yield from ast.literal_eval(call.args[1]).values()


def declared_modules(path, root):
    path, root = Path(path), Path(root)
    parts = path.relative_to(root).parts
    if parts[0] == 'legacy':
        parts = parts[1:]
    package = '.'.join(parts[:-1])
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    modules = [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
    modules += [resolve_name('.' * node.level + (node.module or ''), package)
                if node.level else node.module or ''
                for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    for kind, name, members, option in dependency_specs(tree):
        modules.append(resolve_name('.' * option + name, package)
                       if kind == 'from' and option else name)
    return tuple(name for name in modules if name)


def find_spec_without_importing(name):
    search_path = None
    spec = None
    for index, part in enumerate(name.split('.')):
        prefix = '.'.join(name.split('.')[:index + 1])
        try:
            spec = PathFinder.find_spec(prefix, search_path)
        except (ImportError, AttributeError, ValueError):
            return None
        if spec is None:
            return None
        search_path = spec.submodule_search_locations
        if search_path is None and index < len(name.split('.')) - 1:
            return None
    return spec


def hidden_imports(root, excluded=()):
    """Include deferred dependencies and real from-list submodules in PYZ."""
    root = Path(root)
    modules = set()
    sources = [root / 'main.py', *(root / 'anclicker').rglob('*.py'), *(root / 'legacy').rglob('*.py')]
    for path in sources:
        parts = path.relative_to(root).parts
        if parts[0] == 'legacy':
            parts = parts[1:]
        module_parts = parts[:-1] if parts[-1] == '__init__.py' else (*parts[:-1], Path(parts[-1]).stem)
        module_name = '.'.join(module_parts)
        if any(module_name == name or module_name.startswith(name + '.') for name in excluded):
            continue
        package = '.'.join(parts[:-1])
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        for kind, name, members, option in dependency_specs(tree):
            name = resolve_name('.' * option + name, package) if kind == 'from' and option else name
            if name in sys.builtin_module_names or find_spec_without_importing(name) is not None:
                modules.add(name)
            for member in members:
                child = name + '.' + member
                if find_spec_without_importing(child) is not None:
                    modules.add(child)
    return tuple(sorted(modules))


def violations(path):
    tree = ast.parse(Path(path).read_text(encoding='utf-8-sig'))
    system_names = {alias.asname or alias.name for node in tree.body if isinstance(node, ast.Import)
                    for alias in node.names if alias.name == 'sys'}
    header = set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)) or (
                isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            header.add(node)
            continue
        # Directly executed tools need their source root on sys.path before
        # importing application helpers. This pure header bootstrap is allowed.
        bootstrap = isinstance(node, ast.If) and not node.orelse and all(
            isinstance(item, ast.Expr) and isinstance(item.value, ast.Call)
            and isinstance(item.value.func, ast.Attribute) and item.value.func.attr == 'insert'
            and isinstance(item.value.func.value, ast.Attribute) and item.value.func.value.attr == 'path'
            and isinstance(item.value.func.value.value, ast.Name)
            and item.value.func.value.value.id in system_names for item in node.body)
        if bootstrap:
            header.add(node)
            continue
        break
    return [node.lineno for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
            and node not in header]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    files = python_files(args.root)
    failures = [(str(path.relative_to(args.root)), line) for path in files for line in violations(path)]
    for name, line in failures:
        print(f'{name}:{line}: import must be in the module header')
    print(f'Import policy: {len(files)} files checked; {len(failures)} violations')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
