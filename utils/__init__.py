

def cache_me(fun):
    _cache = {}
    def _f(an_arg):
        if an_arg not in _cache:
            _cache[an_arg] = fun(an_arg)
        return _cache[an_arg]
    return _f


@cache_me
def project_ordering_key(node):
    return int(node[2:])
