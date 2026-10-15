"""File-header dependency declarations with explicit, deferred resolution.

Some application dependencies must stay unloaded until a platform branch or a
feature is used. Keep their declarations at the file header while resolving
the real objects at the existing call boundary. No proxy classes are exposed.
"""
import builtins
import sys


class DeferredImports:
    """Resolve header specs using Python's regular import hooks and cache.

    ``from`` specs contain (kind, module, names, level); ``import`` specs
    contain (kind, module, (), full_module_alias). Symbols are read afresh on
    each call, preserving monkeypatches, optional-dependency errors and class
    identity. The containing module's namespace supplies relative-import and
    binding-specific hook context.
    """

    def __init__(self, namespace, specifications):
        self.namespace = namespace
        self.specifications = specifications

    def load(self, key):
        kind, name, members, option = self.specifications[key]
        if kind == 'import':
            fromlist = ('__name__',) if option else ()
            return builtins.__import__(name, self.namespace, self.namespace, fromlist, 0)
        module = builtins.__import__(name, self.namespace, self.namespace, members, option)
        values = []
        for member in members:
            try:
                value = getattr(module, member)
            except AttributeError:
                # IMPORT_FROM also supports a partially initialized child
                # registered in sys.modules before its parent's attribute.
                child = module.__name__ + '.' + member
                if child not in sys.modules:
                    raise ImportError(f"cannot import name {member!r} from {module.__name__!r}") from None
                value = sys.modules[child]
            values.append(value)
        return values[0] if len(values) == 1 else tuple(values)
