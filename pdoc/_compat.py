def removesuffix(x: str, suffix: str):
    try:
        return x.removesuffix(suffix)
    except AttributeError:  # pragma: no cover
        if x.endswith(suffix):
            x = x[: -len(suffix)]
        return x
