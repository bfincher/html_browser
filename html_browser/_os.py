def joinPaths(path, *paths):
    toReturn = path
    for p in paths:
        if toReturn.endswith('/') or p.endswith('/'):
            toReturn += p
        else:
            toReturn += "/%s" % p
    return toReturn
