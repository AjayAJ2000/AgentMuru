from importlib.metadata import PackageNotFoundError, version


def _detect_version() -> str:
    try:
        return version("brickflowui")
    except PackageNotFoundError:
        return "0.1.13"


__version__ = _detect_version()
