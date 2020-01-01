def join_paths(path, *paths):
    to_return = path
    for p in paths:
        if to_return.endswith('/') or p.endswith('/'):
            to_return += p
        else:
            to_return += "/%s" % p
    return to_return
