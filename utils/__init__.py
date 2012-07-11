

def cache_me(fun):
    _cache = {}
    def _f(an_arg):
        if an_arg not in _cache:
            _cache[an_arg] = fun(an_arg)
        return _cache[an_arg]
    return _f


@cache_me
def project_ordering_key(node):
    try:
        return int(node[2:])
    except ValueError:
        return node


def get_min_max(collection, key=lambda x: x):
    the_min = the_max = None
    for obj in collection:
        the_val = key(obj)
        if the_min is None or the_min > the_val:
            the_min = the_val
        if the_max is None or the_max < the_val:
            the_max = the_val
    return the_min, the_max
