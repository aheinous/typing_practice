
_logf = open('log', 'w')

def dbg(*vargs, **kwargs):
    print(*vargs,**kwargs,file=_logf)
    _logf.flush()