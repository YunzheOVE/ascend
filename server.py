"""Local judge. Run `python server.py` and open http://localhost:8000"""
import inspect
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import problems as P

PORT = 8000
ROOT = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(ROOT, "runner.py")
SOLUTIONS = os.path.join(ROOT, "solutions")
PROGRESS = os.path.join(ROOT, "progress.json")
ALLOWED_HOSTS = {f"localhost:{PORT}", f"127.0.0.1:{PORT}"}
_tests, _lock = {}, threading.Lock()


def tests(p):
    with _lock:
        if p.id not in _tests:
            _tests[p.id] = P.build_tests(p)
        return _tests[p.id]


def load_progress():
    try:
        with open(PROGRESS) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def saved_code(p):
    try:
        with open(os.path.join(SOLUTIONS, p.id + ".py"), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return P.starter(p)


def show(v, limit=600):
    s = json.dumps(v)
    return s if len(s) <= limit else s[:limit] + f" ... ({len(s):,} chars)"


def case_view(p, args, exp, got, ms):
    return {"input": "\n".join(f"{k} = {show(a)}" for k, a in zip(P.params(p), args)),
            "expected": show(exp), "got": show(got), "ms": ms}


def same(p, got, exp, args):
    try:
        if hasattr(p, "check"):  # problems with several valid answers validate the output instead
            return p.check(args, got, exp) is True
        return json.dumps(p.norm(got)) == json.dumps(p.norm(exp))
    except Exception:  # malformed output (wrong shape) is just a wrong answer
        return False


def judge(code, p, cases, stop_on_wrong):
    res = {"verdict": "Accepted", "passed": 0, "total": len(cases), "ms": 0, "cases": [], "error": "", "stdout": ""}
    with tempfile.TemporaryDirectory() as tmp:
        inp, logp = os.path.join(tmp, "in.json"), os.path.join(tmp, "stdout.txt")
        with open(inp, "w") as f:
            json.dump({"code": code, "func": p.func, "tests": [a for a, _ in cases]}, f)
        with open(logp, "w") as log:
            proc = subprocess.Popen([sys.executable, "-I", RUNNER, inp], stdout=subprocess.PIPE, stderr=log, text=True)
            lines = queue.Queue()
            threading.Thread(target=lambda: [lines.put(l) for l in proc.stdout] + [lines.put(None)], daemon=True).start()

            def get(timeout):
                line = lines.get(timeout=timeout)
                return json.loads(line) if line else {"error": "Process crashed (stack overflow or out of memory?)"}

            try:
                msg = get(15)
                if "error" in msg:
                    res.update(verdict="Compile Error", error=msg["error"])
                for i, (args, exp) in enumerate(cases if "ready" in msg else []):
                    try:
                        msg = get(p.tl + 1)
                    except queue.Empty:
                        msg = {"ms": None}
                    if "error" in msg:
                        res.update(verdict="Runtime Error", error=msg["error"])
                        res["cases"].append(case_view(p, args, exp, None, None))
                        break
                    if msg["ms"] is None or msg["ms"] > p.tl * 1000:
                        res.update(verdict="Time Limit Exceeded",
                                   error=f"Test {i + 1} took longer than {p.tl:g}s (likely needs a better time complexity).")
                        res["cases"].append(case_view(p, args, exp, None, msg["ms"]))
                        break
                    ok = same(p, msg["out"], exp, args)
                    res["ms"] = max(res["ms"], msg["ms"])
                    res["passed"] += ok
                    if ok and stop_on_wrong:
                        continue
                    res["cases"].append(dict(case_view(p, args, exp, msg["out"], msg["ms"]), ok=ok))
                    if not ok and res["verdict"] == "Accepted":
                        res["verdict"] = "Wrong Answer"
                        if stop_on_wrong:
                            break
            except queue.Empty:
                res.update(verdict="Time Limit Exceeded", error="Your code took too long to load.")
            finally:
                proc.kill()
                proc.wait()
        with open(logp, errors="replace") as f:
            res["stdout"] = f.read(4000)
    return res


class Handler(BaseHTTPRequestHandler):
    def reply(self, code, body, ctype="application/json"):
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def problem(self, pid):
        p = P.BY_ID.get(pid)
        if not p:
            self.reply(404, {"error": "unknown problem"})
        return p

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
                return self.reply(200, f.read(), "text/html; charset=utf-8")
        if path == "/api/problems":
            prog = load_progress()
            return self.reply(200, [{"id": p.id, "title": p.title, "difficulty": p.difficulty, "status": prog.get(p.id, ""),
                                     "group": p.group, "division": p.hint["module"].split(":")[0],
                                     "starred": P.STARRED.get(p.id, "")}
                                    for p in P.PROBLEMS])
        if path == "/api/roadmap":
            return self.reply(200, P.ROADMAP)
        if path.startswith("/api/problems/"):
            if p := self.problem(path.rsplit("/", 1)[1]):
                exs = [case_view(p, a, e, None, None) for a, e in tests(p)[:len(p.examples)]]
                self.reply(200, {"id": p.id, "title": p.title, "difficulty": p.difficulty, "statement": p.statement,
                                 "examples": exs, "hint": p.hint, "code": saved_code(p), "starter": P.starter(p)})
            return
        if path.startswith("/api/solution/"):
            if p := self.problem(path.rsplit("/", 1)[1]):
                src = inspect.getsource(p.ref).replace("    def ref(", f"    def {p.func}(self, ", 1)
                self.reply(200, {"code": "class Solution:\n" + src})
            return
        self.reply(404, "not found", "text/plain")

    def do_POST(self):
        # Only our own page may submit code: blocks other websites from running code on this machine.
        origin = self.headers.get("Origin", "")
        if self.headers.get("Host") not in ALLOWED_HOSTS or (origin and origin.split("//")[-1] not in ALLOWED_HOSTS) \
                or self.headers.get("Content-Type") != "application/json":
            return self.reply(403, {"error": "forbidden"})
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        p = self.problem(body.get("id"))
        if not p:
            return
        code = str(body.get("code", ""))
        os.makedirs(SOLUTIONS, exist_ok=True)
        with open(os.path.join(SOLUTIONS, p.id + ".py"), "w", encoding="utf-8") as f:
            f.write(code)
        if self.path == "/api/run":
            return self.reply(200, judge(code, p, tests(p)[:len(p.examples)], stop_on_wrong=False))
        if self.path == "/api/submit":
            res = judge(code, p, tests(p), stop_on_wrong=True)
            with _lock:
                prog = load_progress()
                if prog.get(p.id) != "solved":
                    prog[p.id] = "solved" if res["verdict"] == "Accepted" else "attempted"
                    with open(PROGRESS, "w") as f:
                        json.dump(prog, f, indent=1)
            return self.reply(200, res)
        self.reply(404, {"error": "not found"})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"Judge running at http://localhost:{PORT}  (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
