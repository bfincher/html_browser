def join_paths(path: str, *paths: str) -> str:
    to_return = path
    for p in paths:
        if to_return.endswith('/') or p.endswith('/'):
            to_return += p
        else:
            to_return += f"/{p}"
    return to_return
