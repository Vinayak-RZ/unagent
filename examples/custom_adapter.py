# Illustrative custom adapter. Copy into your repo. Register via --adapter custom in this package.

from superdeterminism.models import Span, Trace


NAME = "custom"


def load(path_or_bytes) -> list[Trace]:
    from superdeterminism.adapters.custom import load as _load

    return _load(path_or_bytes)
