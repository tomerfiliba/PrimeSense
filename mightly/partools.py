import sys
from threading import Thread


def parallel_map(func, items):
    """
    >>> import time
    >>> def f(x):
    ...     time.sleep(3)
    ...     return x * 7
    ...
    >>> t0 = time.time()
    >>> parallel_map(f, [1, 4, 8, 12])
    [7, 28, 56, 84]
    >>> int(time.time() - t0)
    3
    """
    results = {}
    threads = []
    def run(i, item):
        try:
            res = func(item)
        except Exception:
            results[i] = (False, sys.exc_info())
        else:
            results[i] = (True, res)
    for i, item in enumerate(items):
        thd = Thread(target = run, args = (i, item))
        thd.start()
        threads.append(thd)
    for thd in threads:
        thd.join()
    seqres = [None] * len(results)
    for i, (succ, obj) in results.items():
        if not succ:
            raise obj[0], obj[1], obj[2]
        else:
            seqres[i] = obj
    return seqres


if __name__ == "__main__":
    import doctest
    doctest.testmod()




