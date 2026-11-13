"""Local judge. Run `python server.py` and open http://localhost:8000"""
import inspect
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import problems as P

PORT = 8000
ROOT = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(ROOT, "runner.py")
SOLUTIONS = os.path.join(ROOT, "solutions")
PROGRESS = os.path.join(ROOT, "progress.json")
REVIEWS = os.path.join(ROOT, "reviews.json")  # id -> {"step": k, "due": "YYYY-MM-DD"}
NOTES = os.path.join(ROOT, "notes.json")  # id -> your note text
REVIEW_DAYS = [3, 7, 21, 60]  # spaced-repetition gaps after each successful re-solve
ALLOWED_HOSTS = {f"localhost:{PORT}", f"127.0.0.1:{PORT}"}
# python.exe (not pythonw.exe) so the runner's output pipe works when the server itself runs windowless
PYTHON = sys.executable.replace("pythonw.exe", "python.exe")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)  # don't flash a console window per run on Windows
_tests, _lock = {}, threading.Lock()


def tests(p):
    with _lock:
        if p.id not in _tests:
            _tests[p.id] = P.build_tests(p)
        return _tests[p.id]


def load_json(path):
    try:
        with open(path, encoding="utf-8-sig") as f:  # -sig: tolerate a byte-order mark (Notepad / PowerShell edits)
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)


def load_progress():
    return load_json(PROGRESS)


def ref_code(p):
    return "class Solution:\n" + inspect.getsource(p.ref).replace("    def ref(", f"    def {p.func}(self, ", 1)


def schedule_review(pid, accepted, first_solve):
    """Spaced repetition: first solve -> due in 3 days; each on-time re-solve pushes it further; a miss resets it."""
    today = date.today()
    reviews = load_json(REVIEWS)
    r = reviews.get(pid)
    note = ""
    if r is None:
        if accepted and first_solve:
            reviews[pid] = {"step": 0, "due": (today + timedelta(REVIEW_DAYS[0])).isoformat()}
            note = f"Added to your review queue: solve it again in {REVIEW_DAYS[0]} days."
    elif date.fromisoformat(r["due"]) <= today:
        if accepted:
            step = r["step"] + 1
            if step >= len(REVIEW_DAYS):
                del reviews[pid]
                note = "Review complete: this one is mastered."
            else:
                reviews[pid] = {"step": step, "due": (today + timedelta(REVIEW_DAYS[step])).isoformat()}
                note = f"Review done. Next review in {REVIEW_DAYS[step]} days."
        else:
            reviews[pid] = {"step": 0, "due": (today + timedelta(1)).isoformat()}
            note = "Review missed: it comes back tomorrow."
    save_json(REVIEWS, reviews)
    return note


def parse_custom_input(p, text):
    """One JSON value per line, in parameter order. Returns (args, error)."""
    if len(text) > 200_000:
        return None, "Input is too large for a custom test (200 KB max)."
    lines = [ln for ln in text.splitlines() if ln.strip()]
    names = P.params(p)
    if len(lines) != len(names):
        return None, f"Expected {len(names)} lines, one per parameter ({', '.join(names)}); got {len(lines)}."
    args = []
    for name, ln in zip(names, lines):
        try:
            args.append(json.loads(ln))
        except ValueError:
            return None, f"Line for '{name}' is not valid JSON: {ln[:80]}"
    return args, ""


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


def judge(code, p, cases, stop_on_wrong, outs=None):
    """Run code on cases. If `outs` is a list, each raw output is appended to it (used to get reference answers)."""
    res = {"verdict": "Accepted", "passed": 0, "total": len(cases), "ms": 0, "cases": [], "error": "", "stdout": ""}
    with tempfile.TemporaryDirectory() as tmp:
        inp, logp = os.path.join(tmp, "in.json"), os.path.join(tmp, "stdout.txt")
        with open(inp, "w") as f:
            json.dump({"code": code, "func": p.func, "tests": [a for a, _ in cases]}, f)
        with open(logp, "w") as log:
            proc = subprocess.Popen([PYTHON, "-I", RUNNER, inp], stdout=subprocess.PIPE, stderr=log, text=True,
                                    creationflags=NO_WINDOW)
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
                    if outs is not None:
                        outs.append(msg["out"])
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
            prog, reviews, notes = load_progress(), load_json(REVIEWS), load_json(NOTES)
            return self.reply(200, [{"id": p.id, "title": p.title, "difficulty": p.difficulty, "status": prog.get(p.id, ""),
                                     "group": p.group, "division": p.hint["module"].split(":")[0],
                                     "module": P.module_of(p), "moduleName": p.hint["module"], "starred": P.STARRED.get(p.id, ""), "due": reviews.get(p.id, {}).get("due", ""),
                                     "hasNote": bool(notes.get(p.id, "").strip())}
                                    for p in P.PROBLEMS])
        if path == "/api/roadmap":
            return self.reply(200, P.ROADMAP)
        if path == "/api/tree":
            return self.reply(200, P.TREE)
        if path == "/api/notes":
            notes = load_json(NOTES)
            return self.reply(200, [{"id": p.id, "title": p.title, "group": p.group, "note": notes[p.id]}
                                    for p in P.PROBLEMS if notes.get(p.id, "").strip()])
        if path.startswith("/api/problems/"):
            if p := self.problem(path.rsplit("/", 1)[1]):
                exs = [case_view(p, a, e, None, None) for a, e in tests(p)[:len(p.examples)]]
                sample = "\n".join(json.dumps(a) for a in tests(p)[0][0])  # first example, in custom-input format
                self.reply(200, {"id": p.id, "title": p.title, "difficulty": p.difficulty, "statement": p.statement,
                                 "examples": exs, "hint": p.hint, "code": saved_code(p), "starter": P.starter(p),
                                 "params": P.params(p), "sample": sample, "note": load_json(NOTES).get(p.id, ""),
                                 "due": load_json(REVIEWS).get(p.id, {}).get("due", "")})
            return
        if path.startswith("/api/solution/"):
            if p := self.problem(path.rsplit("/", 1)[1]):
                self.reply(200, {"code": ref_code(p)})
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
        if self.path == "/api/notes":  # notes don't touch the saved code
            with _lock:
                notes = load_json(NOTES)
                text = str(body.get("note", ""))[:20_000]
                if text.strip():
                    notes[p.id] = text
                else:
                    notes.pop(p.id, None)
                save_json(NOTES, notes)
            return self.reply(200, {"ok": True})
        code = str(body.get("code", ""))
        os.makedirs(SOLUTIONS, exist_ok=True)
        with open(os.path.join(SOLUTIONS, p.id + ".py"), "w", encoding="utf-8") as f:
            f.write(code)
        if self.path == "/api/run":
            return self.reply(200, judge(code, p, tests(p)[:len(p.examples)], stop_on_wrong=False))
        if self.path == "/api/custom":
            args, err = parse_custom_input(p, str(body.get("input", "")))
            if err:
                return self.reply(200, {"verdict": "Invalid Input", "error": err, "passed": 0, "total": 1, "ms": 0,
                                        "cases": [], "stdout": ""})
            expected = []
            ref = judge(ref_code(p), p, [(args, None)], stop_on_wrong=False, outs=expected)
            if not expected:  # the reference couldn't handle it, so the input breaks the problem's rules
                return self.reply(200, {"verdict": "Invalid Input", "passed": 0, "total": 1, "ms": 0, "cases": [], "stdout": "",
                                        "error": "This input doesn't fit the problem's constraints (the reference solution "
                                                 "failed on it).\n\n" + (ref["error"] or "")})
            return self.reply(200, judge(code, p, [(args, expected[0])], stop_on_wrong=False))
        if self.path == "/api/submit":
            res = judge(code, p, tests(p), stop_on_wrong=True)
            accepted = res["verdict"] == "Accepted"
            with _lock:
                prog = load_progress()
                first_solve = accepted and prog.get(p.id) != "solved"
                if prog.get(p.id) != "solved":
                    prog[p.id] = "solved" if accepted else "attempted"
                    save_json(PROGRESS, prog)
                res["review"] = schedule_review(p.id, accepted, first_solve)
            return self.reply(200, res)
        self.reply(404, {"error": "not found"})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"Judge running at http://localhost:{PORT}  (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
