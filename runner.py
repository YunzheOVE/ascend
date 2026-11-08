"""Runs a user's Solution against test inputs in a separate process.
Usage: python -I runner.py <input.json>. Writes one JSON line per event to stdout."""
import json
import sys
import threading
import time
import traceback

# What LeetCode's Python 3 environment pre-imports, so solutions paste over unchanged.
PRELUDE = """from typing import *
import collections, heapq, bisect, math, itertools, functools, string, re, random
from collections import *
from heapq import *
from bisect import *
from functools import *
from itertools import *
from math import inf, gcd, sqrt, ceil, floor, log2, comb, isqrt
"""


def user_traceback():
    etype, e, tb = sys.exc_info()
    while tb and tb.tb_frame.f_code.co_filename != "solution.py":  # hide runner frames
        tb = tb.tb_next
    return "".join(traceback.format_exception(etype, e, tb))


def main():
    out = sys.stdout
    sys.stdout = sys.stderr  # user print() goes to the log file, not the protocol

    def send(**msg):
        out.write(json.dumps(msg) + "\n")
        out.flush()

    with open(sys.argv[1]) as f:
        data = json.load(f)
    ns = {}
    exec(PRELUDE, ns)
    try:
        exec(compile(data["code"], "solution.py", "exec"), ns)
        fn = getattr(ns["Solution"](), data["func"])
    except BaseException:
        return send(error=user_traceback() or traceback.format_exc())
    send(ready=True)
    for args in data["tests"]:
        start = time.perf_counter()
        try:
            res = fn(*args)
        except BaseException:
            return send(error=user_traceback())
        ms = round((time.perf_counter() - start) * 1000, 1)
        try:
            send(out=res, ms=ms)
        except (TypeError, ValueError):
            return send(error=f"Return value of type {type(res).__name__} is not a list/int/str/bool.")


sys.setrecursionlimit(10**6)
threading.stack_size(255 * 1024 * 1024)  # deep recursive DFS shouldn't crash; Windows caps this below 256MB
t = threading.Thread(target=main)
t.start()
t.join()
