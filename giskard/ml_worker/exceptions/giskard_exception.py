from typing import Optional, Tuple
import platform


class GiskardException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class GiskardPythonEnvException(GiskardException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class GiskardPythonVerException(GiskardPythonEnvException):
    def __init__(self, cls_name, e, required_py_ver, *args: object) -> None:
        super().__init__(
            f"Failed to load '{cls_name}' due to {e.__class__.__name__}.\n"
            f"Make sure you are loading it in the environment with matched Python version (required {required_py_ver}, loading with {platform.python_version()}).",
            *args,
        )


class GiskardPythonDepException(GiskardPythonEnvException):
    def __init__(self, cls_name, e, *args: object) -> None:
        super().__init__(
            f"Failed to load '{cls_name}' due to {e.__class__.__name__}.\n"
            "Make sure you are loading it in the environment with matched dependencies.",
            *args,
        )


def python_env_exception_helper(cls_name, e: Exception, required_py_ver: Optional[Tuple[str, str, str]] = None):
    if required_py_ver is not None and required_py_ver[:2] != platform.python_version_tuple[:2]:
        # Python major and minor versions are not matched
        return GiskardPythonVerException(cls_name, e, required_py_ver=required_py_ver)
    elif isinstance(e, TypeError):
        # Try to infer Python version issues from exceptions
        # Python 3.9: code() takes at most 16 arguments (18 given)
        # Python 3.10: code expected at most 16 arguments, got 18
        # Python 3.11: code() argument 13 must be str, not int
        if "at most 16 arguments" in e.args[0] or "code() argument 13 must be str, not int" in e.args[0]:
            # Python 3.11 introduces `co_qualname` in code
            # See code in Python 3.10: https://docs.python.org/3.10/library/inspect.html#types-and-members
            # and code in Python 3.11: https://docs.python.org/3.11/library/inspect.html#types-and-members
            return GiskardPythonVerException(cls_name, e, required_py_ver=required_py_ver)
    # We assume the other cases as the dependency issues
    return GiskardPythonDepException(cls_name, e)
