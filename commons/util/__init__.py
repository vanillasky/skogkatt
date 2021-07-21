import importlib
import sys


def instantiate(class_name: str, kwargs: dict):
    try:
        name_parts = class_name.split(".")
        module_name = ".".join(name_parts[:-1])
        module = importlib.import_module(module_name)
        klass = getattr(module, name_parts[-1])
        # args = inspect.signature(klass.__init__)
        instance = klass(**kwargs)

        return instance
    except ImportError:
        e, tb = sys.exc_info()[1:]
        v = ValueError('Cannot resolve %r: %s' % (class_name, e))
        v.__cause__, v.__traceback__ = e, tb
        raise v
