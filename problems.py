"""Problem bank. Each problem has a reference solution, an independent brute force,
and a random test generator. Run `python problems.py` to cross-check them."""
import inspect
import json
import random
import time
from bisect import bisect_left
from collections import Counter, defaultdict, deque
from functools import lru_cache
from heapq import heapify, heappop, heappush
from itertools import combinations
from typing import List

MOD = 10**9 + 7
PROBLEMS = []


def problem(cls):
    cls.id = cls.__name__
    cls.tl = getattr(cls, "tl", 2.0)  # seconds per test
    if not hasattr(cls, "norm"):  # how outputs are canonicalized before comparing
        cls.norm = staticmethod(lambda x: x)
    cls.big = getattr(cls, "big", 2)
    PROBLEMS.append(cls)
    return cls


def starter(p):
    sig = str(inspect.signature(p.ref))
    return f"class Solution:\n    def {p.func}(self, {sig[1:]}:\n        pass\n"


def params(p):
    return list(inspect.signature(p.ref).parameters)


def build_tests(p):
    """[(args, expected)] — examples, edge cases, small randoms, then large randoms."""
    rng = random.Random(p.id)
    cases = list(p.examples) + list(getattr(p, "edges", []))
    cases += [p.gen(rng, False) for _ in range(25)]
    cases += [p.gen(rng, True) for _ in range(p.big)]
    # JSON round-trip so expected values have exactly the shape the user's output will have
    return [(json.loads(json.dumps(a)), json.loads(json.dumps(p.ref(*json.loads(json.dumps(a)))))) for a in cases]


# ---------------------------------------------------------------- 1
@problem
class RectangleSums:
    title = "Orchard Rectangles"
    difficulty = "Medium"
    func = "rectangleSums"
    statement = """
<p>An orchard is an <code>m x n</code> grid where <code>grid[r][c]</code> is the net yield of one tree (it can be negative).
You get many queries <code>[r1, c1, r2, c2]</code>, each asking for the total yield of the rectangle with top-left
<code>(r1, c1)</code> and bottom-right <code>(r2, c2)</code>, inclusive.</p>
<p>Return the answers in query order.</p>
<ul><li><code>1 &lt;= m, n &lt;= 300</code></li><li><code>-1000 &lt;= grid[r][c] &lt;= 1000</code></li>
<li><code>1 &lt;= queries.length &lt;= 10^5</code></li><li><code>0 &lt;= r1 &lt;= r2 &lt; m</code>, <code>0 &lt;= c1 &lt;= c2 &lt; n</code></li></ul>"""
    hint = dict(pattern="2D prefix sums (inclusion-exclusion)", module="Silver: Introduction to Prefix Sums",
                url="https://usaco.guide/silver/prefix-sums", similar="LeetCode 304")
    examples = [([[3, 0, 1], [5, 6, 3], [1, 2, 0]], [[0, 0, 1, 1], [1, 1, 2, 2], [0, 0, 2, 2]])]
    edges = [([[5]], [[0, 0, 0, 0]]), ([[1, -2, 3]], [[0, 0, 0, 2], [0, 1, 0, 1]])]

    def ref(grid: List[List[int]], queries: List[List[int]]) -> List[int]:
        m, n = len(grid), len(grid[0])
        P = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m):
            for j in range(n):
                P[i + 1][j + 1] = grid[i][j] + P[i][j + 1] + P[i + 1][j] - P[i][j]
        return [P[r2 + 1][c2 + 1] - P[r1][c2 + 1] - P[r2 + 1][c1] + P[r1][c1] for r1, c1, r2, c2 in queries]

    def brute(grid, queries):
        return [sum(grid[r][c] for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)) for r1, c1, r2, c2 in queries]

    def gen(rng, big):
        m, n, q = (300, 300, 100000) if big else (rng.randint(1, 6), rng.randint(1, 6), rng.randint(1, 8))
        grid = [[rng.randint(-1000, 1000) for _ in range(n)] for _ in range(m)]
        qs = []
        for _ in range(q):
            r1, r2 = sorted((rng.randrange(m), rng.randrange(m)))
            c1, c2 = sorted((rng.randrange(n), rng.randrange(n)))
            qs.append([r1, c1, r2, c2])
        return grid, qs


# ---------------------------------------------------------------- 2
@problem
class CountSubarrays:
    title = "Balanced Ledger Windows"
    difficulty = "Medium"
    func = "countSubarrays"
    statement = """
<p>A ledger records daily balance changes <code>nums</code> (positive or negative). Count how many
<b>contiguous</b> stretches of days have a total change of exactly <code>k</code>.</p>
<ul><li><code>1 &lt;= nums.length &lt;= 10^5</code></li><li><code>-1000 &lt;= nums[i] &lt;= 1000</code></li>
<li><code>-10^7 &lt;= k &lt;= 10^7</code></li></ul>"""
    hint = dict(pattern="Prefix sums + hash map of counts (negatives break sliding window)",
                module="Silver: More on Prefix Sums", url="https://usaco.guide/silver/more-prefix-sums", similar="LeetCode 560")
    examples = [([1, 1, 1], 2), ([1, 2, 3], 3), ([1, -1, 0], 0)]
    edges = [([0, 0, 0], 0), ([5], 3), ([-2], -2)]

    def ref(nums: List[int], k: int) -> int:
        seen = Counter({0: 1})
        s = ans = 0
        for x in nums:
            s += x
            ans += seen[s - k]
            seen[s] += 1
        return ans

    def brute(nums, k):
        return sum(sum(nums[i:j]) == k for i in range(len(nums)) for j in range(i + 1, len(nums) + 1))

    def gen(rng, big):
        if big:
            return [rng.randint(-5, 5) for _ in range(100000)], rng.randint(-10, 10)
        return [rng.randint(-3, 3) for _ in range(rng.randint(1, 10))], rng.randint(-4, 4)


# ---------------------------------------------------------------- 3
@problem
class Attendance:
    title = "Venue Attendance"
    difficulty = "Medium"
    func = "dailyAttendance"
    statement = """
<p>A venue is open for <code>n</code> days (day <code>0</code> to <code>n - 1</code>). Each booking
<code>[start, end, people]</code> means <code>people</code> guests attend every day from <code>start</code> to <code>end</code>, inclusive.</p>
<p>Return an array of length <code>n</code> with the total attendance on each day.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li><code>0 &lt;= bookings.length &lt;= 10^5</code></li>
<li><code>0 &lt;= start &lt;= end &lt; n</code>, <code>1 &lt;= people &lt;= 10^4</code></li></ul>"""
    hint = dict(pattern="Difference array: +x at start, -x after end, then prefix sum",
                module="Silver: More on Prefix Sums", url="https://usaco.guide/silver/more-prefix-sums", similar="LeetCode 1109 / 1094")
    examples = [(5, [[0, 2, 10], [1, 3, 20], [1, 1, 25]]), (3, [[0, 2, 1], [2, 2, 4]])]
    edges = [(1, []), (4, [[3, 3, 7]])]

    def ref(n: int, bookings: List[List[int]]) -> List[int]:
        diff = [0] * (n + 1)
        for l, r, x in bookings:
            diff[l] += x
            diff[r + 1] -= x
        out, s = [], 0
        for i in range(n):
            s += diff[i]
            out.append(s)
        return out

    def brute(n, bookings):
        out = [0] * n
        for l, r, x in bookings:
            for i in range(l, r + 1):
                out[i] += x
        return out

    def gen(rng, big):
        n, u = (100000, 100000) if big else (rng.randint(1, 8), rng.randint(0, 6))
        b = []
        for _ in range(u):
            l, r = sorted((rng.randrange(n), rng.randrange(n)))
            b.append([l, r, rng.randint(1, 10**4)])
        return n, b


# ---------------------------------------------------------------- 4
@problem
class ReadingPlan:
    title = "Reading Plan"
    difficulty = "Medium"
    func = "minDailyPages"
    statement = """
<p>A book has chapters with <code>pages[i]</code> pages, which must be read in order. You must finish within
<code>days</code> days, reading one or more <b>whole consecutive chapters</b> per day (a day may also be empty).</p>
<p>Return the smallest possible value of the largest number of pages read on any single day.</p>
<ul><li><code>1 &lt;= days &lt;= pages.length &lt;= 10^5</code></li><li><code>1 &lt;= pages[i] &lt;= 10^4</code></li></ul>"""
    hint = dict(pattern="Binary search on the answer + greedy feasibility check (minimize the maximum)",
                module="Silver: Binary Search", url="https://usaco.guide/silver/binary-search", similar="LeetCode 1011 / 410 (cousin of Koko)")
    examples = [([7, 2, 5, 10, 8], 2), ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5)]
    edges = [([5], 1), ([3, 3, 3], 3), ([1, 1, 100], 1)]

    def ref(pages: List[int], days: int) -> int:
        def fits(cap):
            used, cur = 1, 0
            for p in pages:
                if cur + p > cap:
                    used, cur = used + 1, 0
                cur += p
            return used <= days

        lo, hi = max(pages), sum(pages)
        while lo < hi:
            mid = (lo + hi) // 2
            if fits(mid):
                hi = mid
            else:
                lo = mid + 1
        return lo

    def brute(pages, days):
        n, INF = len(pages), float("inf")
        f = [[INF] * (days + 1) for _ in range(n + 1)]
        f[0][0] = 0
        for i in range(1, n + 1):
            for d in range(1, days + 1):
                for k in range(i):
                    f[i][d] = min(f[i][d], max(f[k][d - 1], sum(pages[k:i])))
        return min(f[n][1:])

    def gen(rng, big):
        n = 100000 if big else rng.randint(1, 8)
        pages = [rng.randint(1, 10**4 if big else 10) for _ in range(n)]
        return pages, rng.randint(1, n)


# ---------------------------------------------------------------- 5
@problem
class Deadlines:
    title = "Freelancer Deadlines"
    difficulty = "Hard"
    func = "maxTasks"
    statement = """
<p>You are a freelancer starting at time <code>0</code>. Each task <code>[duration, deadline]</code> takes
<code>duration</code> units of uninterrupted work and only counts if finished at or before <code>deadline</code>.
You work on one task at a time and may skip any task.</p>
<p>Return the maximum number of tasks you can complete.</p>
<ul><li><code>1 &lt;= tasks.length &lt;= 10^5</code></li><li><code>1 &lt;= duration &lt;= 10^4</code></li>
<li><code>1 &lt;= deadline &lt;= 3 * 10^8</code></li></ul>"""
    hint = dict(pattern="Greedy: sort by deadline, keep a max-heap of durations, drop the longest when you overrun",
                module="Silver: Greedy with Sorting + Priority Queues", url="https://usaco.guide/silver/priority-queues", similar="LeetCode 630")
    examples = [([[3, 5], [2, 4], [4, 9], [5, 8]],), ([[5, 5], [1, 2], [1, 2], [1, 2]],)]
    edges = [([[5, 3]],), ([[1, 1], [1, 1]],)]

    def ref(tasks: List[List[int]]) -> int:
        heap, t = [], 0
        for d, dl in sorted(tasks, key=lambda x: x[1]):
            heappush(heap, -d)
            t += d
            if t > dl:
                t += heappop(heap)  # removes the longest task taken so far
        return len(heap)

    def brute(tasks):
        best, n = 0, len(tasks)
        for mask in range(1 << n):
            chosen = sorted((tasks[i] for i in range(n) if mask >> i & 1), key=lambda x: x[1])
            t, ok = 0, True
            for d, dl in chosen:  # earliest-deadline-first is optimal for a fixed subset
                t += d
                ok &= t <= dl
            if ok:
                best = max(best, len(chosen))
        return best

    def gen(rng, big):
        if big:
            return ([[rng.randint(1, 10**4), rng.randint(1, 3 * 10**8)] for _ in range(100000)],)
        return ([[rng.randint(1, 5), rng.randint(1, 15)] for _ in range(rng.randint(1, 8))],)


# ---------------------------------------------------------------- 6
@problem
class IceRegions:
    title = "Ice Survey"
    difficulty = "Medium"
    func = "iceStats"
    statement = """
<p>A satellite image is a grid of strings; <code>'#'</code> is ice and <code>'.'</code> is water. Ice cells
connected up/down/left/right form one <b>sheet</b>. The <b>perimeter</b> of a sheet is the number of edges of its cells
that touch water or the image border (holes inside a sheet count too).</p>
<p>Return <code>[number of sheets, largest sheet area, largest sheet perimeter]</code>. The two maximums are taken
independently and are <code>0</code> when there is no ice.</p>
<ul><li><code>1 &lt;= rows, cols &lt;= 500</code></li></ul>"""
    hint = dict(pattern="Flood fill (iterative BFS/DFS) collecting per-component stats",
                module="Silver: Flood Fill", url="https://usaco.guide/silver/flood-fill", similar="LeetCode 200 / 463 / 695 combined")
    examples = [(["##..", "#..#", "..##", "...."],), (["###", "#.#", "###"],)]
    edges = [(["."],), (["#"],), (["#.#.#"],)]

    def ref(grid: List[str]) -> List[int]:
        m, n = len(grid), len(grid[0])
        seen = [[False] * n for _ in range(m)]
        sheets = best_area = best_per = 0
        for si in range(m):
            for sj in range(n):
                if grid[si][sj] != "#" or seen[si][sj]:
                    continue
                sheets += 1
                seen[si][sj] = True
                stack, area, per = [(si, sj)], 0, 0
                while stack:
                    i, j = stack.pop()
                    area += 1
                    for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                        if not (0 <= a < m and 0 <= b < n) or grid[a][b] != "#":
                            per += 1
                        elif not seen[a][b]:
                            seen[a][b] = True
                            stack.append((a, b))
                best_area, best_per = max(best_area, area), max(best_per, per)
        return [sheets, best_area, best_per]

    def brute(grid):
        m, n = len(grid), len(grid[0])
        par = list(range(m * n))

        def find(x):
            while par[x] != x:
                x = par[x]
            return x

        ice = lambda i, j: 0 <= i < m and 0 <= j < n and grid[i][j] == "#"
        for i in range(m):
            for j in range(n):
                if ice(i, j) and ice(i + 1, j):
                    par[find(i * n + j)] = find((i + 1) * n + j)
                if ice(i, j) and ice(i, j + 1):
                    par[find(i * n + j)] = find(i * n + j + 1)
        area, per = Counter(), Counter()
        for i in range(m):
            for j in range(n):
                if ice(i, j):
                    r = find(i * n + j)
                    area[r] += 1
                    per[r] += sum(not ice(a, b) for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)))
        return [len(area), max(area.values(), default=0), max(per.values(), default=0)]

    def gen(rng, big):
        m, n = (500, 500) if big else (rng.randint(1, 6), rng.randint(1, 6))
        dens = rng.choice([0.3, 0.5, 0.6, 0.8])
        return (["".join("#" if rng.random() < dens else "." for _ in range(n)) for _ in range(m)],)


# ---------------------------------------------------------------- 7
@problem
class TwoTeams:
    title = "Two Teams"
    difficulty = "Medium"
    func = "canSplit"
    statement = """
<p><code>n</code> students (numbered <code>0</code> to <code>n - 1</code>) must be split into two teams (a team may be empty).
Each pair <code>[a, b]</code> in <code>conflicts</code> means <code>a</code> and <code>b</code> refuse to be on the same team.</p>
<p>Return <code>true</code> if a valid split exists, otherwise <code>false</code>.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li><code>0 &lt;= conflicts.length &lt;= 2 * 10^5</code></li>
<li><code>a != b</code>; the graph may be disconnected and may contain repeated pairs</li></ul>"""
    hint = dict(pattern="Bipartite check: 2-color each component with BFS/DFS",
                module="Silver: Graph Traversal", url="https://usaco.guide/silver/graph-traversal", similar="LeetCode 785 / 886")
    examples = [(4, [[0, 1], [1, 2], [2, 3]]), (3, [[0, 1], [1, 2], [0, 2]])]
    edges = [(1, []), (5, [[0, 1], [2, 3], [3, 4], [4, 2]]), (2, [[0, 1], [1, 0]])]

    def ref(n: int, conflicts: List[List[int]]) -> bool:
        adj = [[] for _ in range(n)]
        for a, b in conflicts:
            adj[a].append(b)
            adj[b].append(a)
        color = [-1] * n
        for s in range(n):
            if color[s] != -1:
                continue
            color[s] = 0
            q = deque([s])
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if color[v] == -1:
                        color[v] = color[u] ^ 1
                        q.append(v)
                    elif color[v] == color[u]:
                        return False
        return True

    def brute(n, conflicts):
        return any(all((m >> a & 1) != (m >> b & 1) for a, b in conflicts) for m in range(1 << n))

    def gen(rng, big):
        n, e = (100000, 200000) if big else (rng.randint(1, 9), rng.randint(0, 10))
        side = [rng.randint(0, 1) for _ in range(n)]
        edges = []
        while len(edges) < e and n > 1:
            a, b = rng.randrange(n), rng.randrange(n)
            if a != b and (side[a] != side[b] or rng.random() < (0.00002 if big else 0.15)):
                edges.append([a, b])
        return n, edges


# ---------------------------------------------------------------- 8
@problem
class MergeAccounts:
    title = "Merge Customer Profiles"
    difficulty = "Medium"
    func = "mergeProfiles"
    statement = """
<p>Each profile is <code>[name, email1, email2, ...]</code>. Two profiles belong to the same person if they share
<b>any</b> email, directly or through a chain of other profiles. Different people may have the same name, but an
email always belongs to exactly one person.</p>
<p>Return the merged profiles as <code>[name, ...all of that person's distinct emails]</code>. Profiles and the
emails inside them may be in any order.</p>
<ul><li><code>1 &lt;= profiles.length &lt;= 2 * 10^4</code></li><li>each profile has 1 to 10 emails</li></ul>"""
    hint = dict(pattern="Disjoint Set Union over emails (or DFS on the email graph)",
                module="Gold: Disjoint Set Union", url="https://usaco.guide/gold/dsu", similar="LeetCode 721")
    examples = [([["ana", "ana@x.com", "ana.w@x.com"], ["bo", "bo@x.com"], ["ana", "ana.w@x.com", "ana99@x.com"], ["ana", "other.ana@x.com"]],)]
    edges = [([["kim", "k@x.com"], ["kim", "k@x.com"]],), ([["a", "1@x"], ["b", "2@x"], ["a", "3@x", "1@x"], ["b", "2@x", "4@x"], ["a", "3@x"]],)]

    @staticmethod
    def norm(out):
        return sorted([a[0]] + sorted(set(a[1:])) for a in out)

    def ref(profiles: List[List[str]]) -> List[List[str]]:
        parent, owner = {}, {}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for name, *emails in profiles:
            for e in emails:
                parent.setdefault(e, e)
                owner[e] = name
            for e in emails[1:]:
                parent[find(e)] = find(emails[0])
        groups = defaultdict(list)
        for e in parent:
            groups[find(e)].append(e)
        return [[owner[r]] + sorted(es) for r, es in groups.items()]

    def brute(profiles):
        adj, owner = defaultdict(set), {}
        for name, *emails in profiles:
            for e in emails:
                owner[e] = name
                adj[e] |= set(emails)
        seen, out = set(), []
        for e in owner:
            if e in seen:
                continue
            comp, q = [], [e]
            seen.add(e)
            while q:
                x = q.pop()
                comp.append(x)
                for y in adj[x] - seen:
                    seen.add(y)
                    q.append(y)
            out.append([owner[e]] + comp)
        return out

    def gen(rng, big):
        people, count, names = (6000, 20000, ["n%d" % i for i in range(500)]) if big else (rng.randint(1, 4), rng.randint(1, 6), ["ana", "bo", "kim"])
        mails = [[f"p{p}_{j}@mail.com" for j in range(4)] for p in range(people)]
        pname = [rng.choice(names) for _ in range(people)]
        out = []
        for _ in range(count):
            p = rng.randrange(people)
            out.append([pname[p]] + rng.sample(mails[p], rng.randint(1, 3 if not big else 2)))
        return (out,)


# ---------------------------------------------------------------- 9
@problem
class ProjectTime:
    title = "Build Pipeline"
    difficulty = "Hard"
    func = "minFinishTime"
    statement = """
<p>A build has <code>n</code> jobs; job <code>i</code> takes <code>durations[i]</code> minutes. Each pair
<code>[a, b]</code> in <code>deps</code> means job <code>a</code> must finish before job <code>b</code> can start. Any number
of jobs can run in parallel.</p>
<p>Return the minimum total time to finish every job, or <code>-1</code> if the dependencies contain a cycle.</p>
<ul><li><code>1 &lt;= n &lt;= 5 * 10^4</code></li><li><code>0 &lt;= deps.length &lt;= 10^5</code></li>
<li><code>1 &lt;= durations[i] &lt;= 10^4</code>, <code>a != b</code></li></ul>"""
    hint = dict(pattern="Topological sort (Kahn's) + DP along the order (longest path in a DAG)",
                module="Gold: Topological Sort", url="https://usaco.guide/gold/toposort", similar="LeetCode 2050 (Course Schedule + DP)")
    examples = [(3, [3, 2, 5], [[0, 2], [1, 2]]), (5, [1, 2, 3, 4, 5], [[0, 4], [1, 4], [2, 4], [3, 4]]), (2, [1, 1], [[0, 1], [1, 0]])]
    edges = [(1, [7], []), (3, [1, 1, 1], [[0, 1], [1, 2], [2, 1]])]

    def ref(n: int, durations: List[int], deps: List[List[int]]) -> int:
        adj, indeg = [[] for _ in range(n)], [0] * n
        for a, b in deps:
            adj[a].append(b)
            indeg[b] += 1
        start = [0] * n
        q = deque(i for i in range(n) if indeg[i] == 0)
        done = best = 0
        while q:
            u = q.popleft()
            done += 1
            fin = start[u] + durations[u]
            best = max(best, fin)
            for v in adj[u]:
                start[v] = max(start[v], fin)
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)
        return best if done == n else -1

    def brute(n, durations, deps):
        preds = defaultdict(list)
        for a, b in deps:
            preds[b].append(a)
        step = lambda f: [durations[i] + max((f[a] for a in preds[i]), default=0) for i in range(n)]
        f = durations[:]
        for _ in range(n):
            f = step(f)
        return -1 if step(f) != f else max(f)

    def gen(rng, big):
        n, m = (50000, 100000) if big else (rng.randint(1, 8), rng.randint(0, 10))
        order = list(range(n))
        rng.shuffle(order)
        deps = []
        for _ in range(m if n > 1 else 0):
            i, j = sorted(rng.sample(range(n), 2))
            deps.append([order[i], order[j]])
        if not big and n > 1 and rng.random() < 0.25:
            deps.append(rng.sample(range(n), 2))
        return n, [rng.randint(1, 10**4 if big else 9) for _ in range(n)], deps


# ---------------------------------------------------------------- 10
@problem
class FastestRoutes:
    title = "Counting Fastest Routes"
    difficulty = "Medium"
    func = "countFastestRoutes"
    statement = """
<p>A city has <code>n</code> intersections and two-way roads <code>[u, v, minutes]</code>. No two roads connect the same
pair of intersections. Return the number of <b>different fastest routes</b> from intersection <code>0</code> to
<code>n - 1</code>, modulo <code>10^9 + 7</code>. Return <code>0</code> if <code>n - 1</code> is unreachable.</p>
<ul><li><code>2 &lt;= n &lt;= 5 * 10^4</code></li><li><code>0 &lt;= roads.length &lt;= 10^5</code></li>
<li><code>1 &lt;= minutes &lt;= 10^4</code></li></ul>"""
    hint = dict(pattern="Dijkstra that also carries a path count (ties add, improvements reset)",
                module="Gold: Shortest Paths with Non-Negative Edge Weights", url="https://usaco.guide/gold/shortest-paths", similar="LeetCode 1976")
    examples = [(4, [[0, 1, 1], [0, 2, 1], [1, 3, 1], [2, 3, 1]]), (3, [[0, 1, 5]]),
                (5, [[0, 1, 2], [1, 4, 2], [0, 2, 1], [2, 3, 1], [3, 4, 2], [0, 4, 4]])]
    edges = [(2, [[0, 1, 3]]), (2, [])]

    def ref(n: int, roads: List[List[int]]) -> int:
        adj = [[] for _ in range(n)]
        for u, v, w in roads:
            adj[u].append((v, w))
            adj[v].append((u, w))
        dist, ways = [float("inf")] * n, [0] * n
        dist[0], ways[0] = 0, 1
        heap = [(0, 0)]
        while heap:
            d, u = heappop(heap)
            if d > dist[u]:
                continue
            for v, w in adj[u]:
                if d + w < dist[v]:
                    dist[v], ways[v] = d + w, ways[u]
                    heappush(heap, (d + w, v))
                elif d + w == dist[v]:
                    ways[v] = (ways[v] + ways[u]) % (10**9 + 7)
        return ways[n - 1]

    def brute(n, roads):
        adj = defaultdict(list)
        for u, v, w in roads:
            adj[u].append((v, w))
            adj[v].append((u, w))
        found = Counter()

        def dfs(u, cost, used):
            if u == n - 1:
                found[cost] += 1
                return
            for v, w in adj[u]:
                if v not in used:
                    dfs(v, cost + w, used | {v})

        dfs(0, 0, {0})
        return found[min(found)] % MOD if found else 0

    def gen(rng, big):
        n, m = (50000, 100000) if big else (rng.randint(2, 7), rng.randint(0, 12))
        m = min(m, n * (n - 1) // 2)
        pairs = {(i, i + 1) for i in range(n - 1)} if big else set()  # chain keeps the far end reachable
        while len(pairs) < m:
            u, v = sorted(rng.sample(range(n), 2))
            pairs.add((u, v))
        roads = [[u, v, rng.randint(1, 3)] for u, v in pairs]
        rng.shuffle(roads)
        return n, roads


# ---------------------------------------------------------------- 11
@problem
class BreakWalls:
    title = "Demolition Path"
    difficulty = "Hard"
    func = "minWallsToBreak"
    statement = """
<p>A grid has <code>0</code> (open floor) and <code>1</code> (wall). You start at the top-left cell and want to reach the
bottom-right cell, moving up/down/left/right. You may demolish walls to pass through them.</p>
<p>Return the minimum number of walls you must demolish. Both corners are always open.</p>
<ul><li><code>1 &lt;= rows * cols &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="0-1 BFS: deque, push 0-cost moves to the front and 1-cost moves to the back",
                module="Gold: Shortest Paths with Unweighted Edges", url="https://usaco.guide/gold/unweighted-shortest-paths", similar="LeetCode 2290")
    examples = [([[0, 1, 1], [1, 1, 0], [1, 1, 0]],), ([[0, 1, 0, 0, 0], [0, 1, 0, 1, 0], [0, 0, 0, 1, 0]],)]
    edges = [([[0]],), ([[0, 1, 1, 1, 0]],)]

    def ref(grid: List[List[int]]) -> int:
        m, n = len(grid), len(grid[0])
        dist = [[float("inf")] * n for _ in range(m)]
        dist[0][0] = 0
        dq = deque([(0, 0)])
        while dq:
            i, j = dq.popleft()
            d = dist[i][j]
            for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                if 0 <= a < m and 0 <= b < n and d + grid[a][b] < dist[a][b]:
                    dist[a][b] = d + grid[a][b]
                    (dq.append if grid[a][b] else dq.appendleft)((a, b))
        return dist[m - 1][n - 1]

    def brute(grid):
        m, n = len(grid), len(grid[0])
        dist = [[float("inf")] * n for _ in range(m)]
        dist[0][0] = 0
        changed = True
        while changed:
            changed = False
            for i in range(m):
                for j in range(n):
                    for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                        if 0 <= a < m and 0 <= b < n and dist[i][j] + grid[a][b] < dist[a][b]:
                            dist[a][b] = dist[i][j] + grid[a][b]
                            changed = True
        return dist[m - 1][n - 1]

    def gen(rng, big):
        m, n = (300, 333) if big else (rng.randint(1, 5), rng.randint(1, 5))
        g = [[int(rng.random() < 0.5) for _ in range(n)] for _ in range(m)]
        g[0][0] = g[m - 1][n - 1] = 0
        return (g,)


# ---------------------------------------------------------------- 12
@problem
class SumOfMinimums:
    title = "Weakest Link Total"
    difficulty = "Medium"
    func = "sumOfMinimums"
    statement = """
<p>A chain has links with strengths <code>arr</code>. For every contiguous segment of the chain, its strength is the
strength of its weakest link. Return the sum of strengths over all contiguous segments, modulo <code>10^9 + 7</code>.</p>
<ul><li><code>1 &lt;= arr.length &lt;= 10^5</code></li><li><code>1 &lt;= arr[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Monotonic stack: count how many subarrays each element is the min of (watch duplicates)",
                module="Gold: Stacks", url="https://usaco.guide/gold/stacks", similar="LeetCode 907")
    examples = [([4, 2, 5, 3],), ([3, 1, 2, 4],)]
    edges = [([5],), ([2, 2, 2],), ([1, 2, 3, 4, 5],)]

    def ref(arr: List[int]) -> int:
        n = len(arr)
        prev, nxt, st = [-1] * n, [n] * n, []
        for i in range(n):  # previous strictly smaller
            while st and arr[st[-1]] >= arr[i]:
                st.pop()
            prev[i] = st[-1] if st else -1
            st.append(i)
        st = []
        for i in range(n - 1, -1, -1):  # next smaller-or-equal, so ties are counted once
            while st and arr[st[-1]] > arr[i]:
                st.pop()
            nxt[i] = st[-1] if st else n
            st.append(i)
        return sum(arr[i] * (i - prev[i]) * (nxt[i] - i) for i in range(n)) % (10**9 + 7)

    def brute(arr):
        total = 0
        for i in range(len(arr)):
            lo = arr[i]
            for j in range(i, len(arr)):
                lo = min(lo, arr[j])
                total += lo
        return total % MOD

    def gen(rng, big):
        if big:
            return ([rng.randint(1, 10**9) for _ in range(100000)],)
        return ([rng.randint(1, 3) for _ in range(rng.randint(1, 9))],)


# ---------------------------------------------------------------- 13
@problem
class NestingBoxes:
    title = "Nesting Boxes"
    difficulty = "Hard"
    func = "maxNesting"
    statement = """
<p>Each box is <code>[width, height]</code>. Box A fits inside box B only if A is <b>strictly</b> smaller in both width and
height. Boxes cannot be rotated. Return the maximum number of boxes you can nest one inside another.</p>
<ul><li><code>1 &lt;= boxes.length &lt;= 10^5</code></li><li><code>1 &lt;= width, height &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="Custom sort (width asc, height desc) then O(n log n) LIS on heights",
                module="Gold: Longest Increasing Subsequence", url="https://usaco.guide/gold/lis", similar="LeetCode 354")
    examples = [([[3, 3], [1, 2], [4, 5], [2, 2], [4, 3]],), ([[2, 8], [3, 4], [3, 9], [1, 1]],)]
    edges = [([[1, 1], [1, 1], [1, 1]],), ([[7, 7]],)]

    def ref(boxes: List[List[int]]) -> int:
        tails = []
        for _, h in sorted(boxes, key=lambda b: (b[0], -b[1])):
            i = bisect_left(tails, h)
            if i == len(tails):
                tails.append(h)
            else:
                tails[i] = h
        return len(tails)

    def brute(boxes):
        b = sorted(boxes)
        dp = [1] * len(b)
        for i in range(len(b)):
            for j in range(i):
                if b[j][0] < b[i][0] and b[j][1] < b[i][1]:
                    dp[i] = max(dp[i], dp[j] + 1)
        return max(dp)

    def gen(rng, big):
        n, v = (100000, 10**5) if big else (rng.randint(1, 9), 5)
        return ([[rng.randint(1, v), rng.randint(1, v)] for _ in range(n)],)


# ---------------------------------------------------------------- 14
@problem
class SmallerAfter:
    title = "Later Underdogs"
    difficulty = "Hard"
    func = "countSmallerAfter"
    statement = """
<p>Given scores <code>nums</code> in the order players entered a tournament, return an array where
<code>answer[i]</code> is how many players who entered <b>after</b> player <code>i</code> have a strictly smaller score.</p>
<ul><li><code>1 &lt;= nums.length &lt;= 10^5</code></li><li><code>-10^9 &lt;= nums[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Coordinate compression + Fenwick tree (BIT), scanning right to left (or merge sort)",
                module="Gold: Point Update Range Sum (+ Silver: Coordinate Compression)", url="https://usaco.guide/gold/PURS", similar="LeetCode 315")
    examples = [([4, 1, 3, 1, 2],), ([-1, -1],)]
    edges = [([7],), ([5, 4, 3, 2, 1],), ([1000000000, -1000000000, 0],)]

    def ref(nums: List[int]) -> List[int]:
        rank = {v: i + 1 for i, v in enumerate(sorted(set(nums)))}
        m, n = len(rank), len(nums)
        bit, out = [0] * (m + 1), [0] * n
        for i in range(n - 1, -1, -1):
            r, s, j = rank[nums[i]], 0, rank[nums[i]] - 1
            while j > 0:
                s += bit[j]
                j -= j & -j
            out[i] = s
            while r <= m:
                bit[r] += 1
                r += r & -r
        return out

    def brute(nums):
        return [sum(nums[j] < nums[i] for j in range(i + 1, len(nums))) for i in range(len(nums))]

    def gen(rng, big):
        if big:
            return ([rng.randint(-10**9, 10**9) for _ in range(100000)],)
        return ([rng.randint(-3, 3) for _ in range(rng.randint(1, 9))],)


# ---------------------------------------------------------------- 15
@problem
class SumDistances:
    title = "Total Commute in a Tree Network"
    difficulty = "Hard"
    func = "sumOfDistances"
    statement = """
<p>A network of <code>n</code> offices (numbered <code>0</code> to <code>n - 1</code>) is connected by <code>n - 1</code> two-way
cables <code>edges</code> forming a tree; each cable has length 1. For every office <code>i</code>, return the sum of its
distances to all other offices.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li>The tree may be very deep (a long path), so watch your recursion.</li></ul>"""
    hint = dict(pattern="Tree DP with rerooting: subtree sizes + answer[child] = answer[parent] - size + (n - size)",
                module="Gold: DP on Trees - Solving For All Roots", url="https://usaco.guide/gold/all-roots", similar="LeetCode 834")
    examples = [(5, [[0, 1], [1, 2], [1, 3], [3, 4]]), (3, [[0, 2], [2, 1]])]
    edges = [(1, []), (2, [[1, 0]])]

    def ref(n: int, edges: List[List[int]]) -> List[int]:
        adj = [[] for _ in range(n)]
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        parent, order, stack = [-1] * n, [], [0]
        parent[0] = 0
        while stack:
            u = stack.pop()
            order.append(u)
            for v in adj[u]:
                if parent[v] == -1 and v != 0:
                    parent[v] = u
                    stack.append(v)
        size, down = [1] * n, [0] * n
        for u in reversed(order[1:]):
            p = parent[u]
            size[p] += size[u]
            down[p] += down[u] + size[u]
        ans = [0] * n
        ans[0] = down[0]
        for u in order[1:]:
            ans[u] = ans[parent[u]] - size[u] + (n - size[u])
        return ans

    def brute(n, edges):
        adj = defaultdict(list)
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        out = []
        for s in range(n):
            dist, q = {s: 0}, deque([s])
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if v not in dist:
                        dist[v] = dist[u] + 1
                        q.append(v)
            out.append(sum(dist.values()))
        return out

    def gen(rng, big):
        n = 100000 if big else rng.randint(1, 10)
        path = big and rng.random() < 0.5
        label = list(range(n))
        rng.shuffle(label)
        edges = [[label[i - 1 if path else rng.randrange(i)], label[i]] for i in range(1, n)]
        for e in edges:
            rng.shuffle(e)
        rng.shuffle(edges)
        return n, edges


# ================================================================ batch 2
# Modeled on the CSES / AtCoder / LeetCode classics that usaco.guide modules link to (statements are original).

@problem
class FerrisWheel:
    title = "Gondola Rides"
    difficulty = "Easy"
    func = "minGondolas"
    statement = """
<p>Children with weights <code>weights</code> are queuing for a Ferris wheel. Each gondola carries <b>at most two</b>
children, and their total weight must not exceed <code>limit</code>. Return the minimum number of gondolas needed so
everyone gets a ride.</p>
<ul><li><code>1 &lt;= weights.length &lt;= 10^5</code></li><li><code>1 &lt;= weights[i] &lt;= limit &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Sort, then two pointers: the heaviest child rides with the lightest one if they fit, otherwise alone",
                module="Silver: Two Pointers", url="https://usaco.guide/silver/two-pointers", similar="CSES Ferris Wheel · LeetCode 881")
    examples = [([2, 3, 7, 9], 10), ([5, 5, 5, 5, 5], 10)]
    edges = [([4], 4), ([1, 1, 1], 3), ([3, 5, 3, 4], 5)]

    def ref(weights: List[int], limit: int) -> int:
        w = sorted(weights)
        i, j, rides = 0, len(w) - 1, 0
        while i <= j:
            if w[i] + w[j] <= limit:
                i += 1
            j -= 1
            rides += 1
        return rides

    def brute(weights, limit):
        n = len(weights)

        @lru_cache(None)
        def f(mask):  # min gondolas for the children in mask
            if not mask:
                return 0
            i = (mask & -mask).bit_length() - 1
            rest = mask & ~(1 << i)
            best = 1 + f(rest)
            for j in range(n):
                if rest >> j & 1 and weights[i] + weights[j] <= limit:
                    best = min(best, 1 + f(rest & ~(1 << j)))
            return best

        return f((1 << n) - 1)

    def gen(rng, big):
        n, lim = (100000, 10**9) if big else (rng.randint(1, 9), rng.randint(3, 12))
        return [rng.randint(1, lim) for _ in range(n)], lim


@problem
class GenreStretch:
    title = "Playlist Variety"
    difficulty = "Medium"
    func = "longestStretch"
    statement = """
<p>A radio log lists the genre id of every song played, in order: <code>genres</code>. Return the length of the longest
run of <b>consecutive</b> songs that uses at most <code>k</code> different genres.</p>
<ul><li><code>1 &lt;= k &lt;= genres.length &lt;= 10^5</code></li><li><code>0 &lt;= genres[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Variable-size sliding window with a count map; shrink from the left while it has more than k genres",
                module="Gold: Sliding Window", url="https://usaco.guide/gold/sliding-window", similar="CSES Playlist · LeetCode 340 / 904")
    examples = [([1, 2, 1, 3, 4, 3, 3], 2), ([5, 5, 5], 1)]
    edges = [([7], 1), ([1, 2, 3], 3), ([1, 2, 3, 4], 1)]

    def ref(genres: List[int], k: int) -> int:
        count, left, best = {}, 0, 0
        for right, g in enumerate(genres):
            count[g] = count.get(g, 0) + 1
            while len(count) > k:
                out = genres[left]
                count[out] -= 1
                if not count[out]:
                    del count[out]
                left += 1
            best = max(best, right - left + 1)
        return best

    def brute(genres, k):
        n = len(genres)
        return max(j - i for i in range(n) for j in range(i + 1, n + 1) if len(set(genres[i:j])) <= k)

    def gen(rng, big):
        if big:
            ids = [rng.randint(0, 10**9) for _ in range(60)]
            return [rng.choice(ids) for _ in range(100000)], rng.randint(1, 25)
        n = rng.randint(1, 10)
        return [rng.randint(0, 3) for _ in range(n)], rng.randint(1, n)


@problem
class StableReadings:
    title = "Stable Readings"
    difficulty = "Medium"
    func = "longestStable"
    statement = """
<p>A sensor logs <code>readings</code> once a minute. A stretch of consecutive readings is <b>stable</b> if its highest
and lowest values differ by at most <code>limit</code>. Return the length of the longest stable stretch.</p>
<ul><li><code>1 &lt;= readings.length &lt;= 10^5</code></li><li><code>-10^9 &lt;= readings[i] &lt;= 10^9</code></li>
<li><code>0 &lt;= limit &lt;= 2 * 10^9</code></li></ul>"""
    hint = dict(pattern="Sliding window that keeps two monotonic deques: one for the window max, one for the window min",
                module="Gold: Sliding Window", url="https://usaco.guide/gold/sliding-window",
                similar="LeetCode 1438 (CSES Sliding Window Minimum is the building block)")
    examples = [([8, 2, 4, 7], 4), ([10, 1, 2, 4, 7, 2], 5)]
    edges = [([3], 0), ([5, 5, 5], 0), ([1, 9, 1, 9], 7)]

    def ref(readings: List[int], limit: int) -> int:
        hi, lo = deque(), deque()  # indices; readings decreasing in hi, increasing in lo
        left = best = 0
        for right, x in enumerate(readings):
            while hi and readings[hi[-1]] <= x:
                hi.pop()
            hi.append(right)
            while lo and readings[lo[-1]] >= x:
                lo.pop()
            lo.append(right)
            while readings[hi[0]] - readings[lo[0]] > limit:
                left += 1
                if hi[0] < left:
                    hi.popleft()
                if lo[0] < left:
                    lo.popleft()
            best = max(best, right - left + 1)
        return best

    def brute(readings, limit):
        n = len(readings)
        return max(j - i + 1 for i in range(n) for j in range(i, n) if max(readings[i:j + 1]) - min(readings[i:j + 1]) <= limit)

    def gen(rng, big):
        if big:
            return [rng.randint(-10**9, 10**9) for _ in range(100000)], rng.randint(0, 2 * 10**9)
        return [rng.randint(-5, 5) for _ in range(rng.randint(1, 10))], rng.randint(0, 6)


@problem
class PeakOccupancy:
    title = "Peak Occupancy"
    difficulty = "Medium"
    func = "maxOverlap"
    statement = """
<p>Each reservation <code>[start, end]</code> uses a meeting room from time <code>start</code> up to, but not including,
<code>end</code>. A room freed at time <code>t</code> can be reused by a reservation starting at <code>t</code>.
Return the minimum number of rooms needed, which is the largest number of reservations active at the same moment.</p>
<ul><li><code>1 &lt;= reservations.length &lt;= 10^5</code></li><li><code>0 &lt;= start &lt; end &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Sweep line: +1 at each start, -1 at each end, sorted by time with ends before starts on ties",
                module="Silver: Custom Comparators and Coordinate Compression", url="https://usaco.guide/silver/sorting-custom",
                similar="CSES Restaurant Customers · LeetCode 253 (Meeting Rooms II)")
    examples = [([[0, 30], [5, 10], [15, 20]],), ([[1, 5], [5, 8], [2, 3]],)]
    edges = [([[4, 9]],), ([[1, 2], [1, 2], [1, 2]],), ([[0, 1], [1, 2], [2, 3]],)]

    def ref(reservations: List[List[int]]) -> int:
        events = sorted([(s, 1) for s, _ in reservations] + [(e, -1) for _, e in reservations])  # (t, -1) sorts before (t, 1)
        cur = best = 0
        for _, d in events:
            cur += d
            best = max(best, cur)
        return best

    def brute(reservations):
        return max(sum(s <= t < e for s, e in reservations) for t, _ in reservations)

    def gen(rng, big):
        n, T = (100000, 10**9) if big else (rng.randint(1, 8), 10)
        out = []
        for _ in range(n):
            s = rng.randint(0, T - 1)
            out.append([s, rng.randint(s + 1, min(T, s + (T // 50 if big else T)))])
        return (out,)


@problem
class OrderedChange:
    title = "Ordered Change"
    difficulty = "Medium"
    func = "countOrders"
    statement = """
<p>A vending machine pays out change one coin at a time. It has unlimited coins of each distinct value in
<code>coins</code>. Count the different <b>ordered</b> sequences of coins that add up to exactly <code>target</code>
(paying 2 then 1 is different from paying 1 then 2). Return the count modulo <code>10^9 + 7</code>.</p>
<ul><li><code>1 &lt;= coins.length &lt;= 100</code>, values distinct</li><li><code>1 &lt;= coins[i] &lt;= 10^4</code></li>
<li><code>1 &lt;= target &lt;= 10^4</code></li></ul>"""
    hint = dict(pattern="1D DP over the amount with the coin loop inside (put the coin loop outside and you count unordered combinations instead)",
                module="Gold: Knapsack DP", url="https://usaco.guide/gold/knapsack",
                similar="CSES Coin Combinations I · LeetCode 377 (compare CSES Coin Combinations II / LeetCode 518)")
    examples = [([1, 2, 3], 4), ([9], 3)]
    edges = [([1], 1), ([2, 5], 7), ([1], 40)]

    def ref(coins: List[int], target: int) -> int:
        ways = [1] + [0] * target
        for s in range(1, target + 1):
            ways[s] = sum(ways[s - c] for c in coins if c <= s) % (10**9 + 7)
        return ways[target]

    def brute(coins, target):
        def f(s):
            return 1 if s == 0 else sum(f(s - c) for c in coins if c <= s)
        return f(target) % MOD

    def gen(rng, big):
        if big:
            return [1] + rng.sample(range(2, 10**4 + 1), 99), 10**4
        return rng.sample(range(1, 7), rng.randint(1, 3)), rng.randint(1, 12)


@problem
class TugOfWar:
    title = "Tug of War"
    difficulty = "Medium"
    func = "minDifference"
    statement = """
<p>Split everyone, with weights <code>weights</code>, into two tug-of-war teams (a team may be empty). Return the
smallest possible difference between the two teams' total weights.</p>
<ul><li><code>1 &lt;= weights.length &lt;= 100</code></li><li><code>1 &lt;= weights[i] &lt;= 1000</code></li></ul>"""
    hint = dict(pattern="Subset-sum knapsack: find every reachable team total (boolean DP or a bitset), pick the one closest to half",
                module="Gold: Knapsack DP", url="https://usaco.guide/gold/knapsack",
                similar="CSES Apple Division (larger n here, so no brute force) · LeetCode 1049")
    examples = [([3, 2, 7, 4, 1],), ([10, 10, 1],)]
    edges = [([5],), ([6, 6],), ([1000, 1, 1, 1],)]

    def ref(weights: List[int]) -> int:
        reach = 1  # bit s is set when some team can total exactly s
        for w in weights:
            reach |= reach << w
        total = sum(weights)
        return min(total - 2 * s for s in range(total // 2 + 1) if reach >> s & 1)

    def brute(weights):
        total, n = sum(weights), len(weights)
        return min(abs(total - 2 * sum(weights[i] for i in range(n) if m >> i & 1)) for m in range(1 << n))

    def gen(rng, big):
        if big:
            return ([rng.randint(1, 1000) for _ in range(100)],)
        return ([rng.randint(1, 20) for _ in range(rng.randint(1, 11))],)


@problem
class Bookshop:
    title = "Bookshop Budget"
    difficulty = "Medium"
    func = "maxPages"
    statement = """
<p>A bookshop has one copy of each book: book <code>i</code> costs <code>prices[i]</code> and has
<code>pages[i]</code> pages. With at most <code>budget</code> to spend, return the largest total number of pages you
can buy.</p>
<ul><li><code>1 &lt;= prices.length == pages.length &lt;= 100</code></li><li><code>1 &lt;= prices[i], budget &lt;= 10^4</code></li>
<li><code>1 &lt;= pages[i] &lt;= 1000</code></li></ul>"""
    hint = dict(pattern="0/1 knapsack: best[b] = most pages for budget b; loop b downward so each book is bought once",
                module="Gold: Knapsack DP", url="https://usaco.guide/gold/knapsack", similar="CSES Book Shop · classic 0/1 knapsack")
    examples = [([4, 8, 5, 3], [5, 12, 8, 1], 10), ([7], [100], 6)]
    edges = [([1], [1], 1), ([5, 5, 5], [3, 3, 3], 15)]

    def ref(prices: List[int], pages: List[int], budget: int) -> int:
        best = [0] * (budget + 1)
        for p, v in zip(prices, pages):
            for b in range(budget, p - 1, -1):
                if best[b - p] + v > best[b]:
                    best[b] = best[b - p] + v
        return best[budget]

    def brute(prices, pages, budget):
        n = len(prices)
        return max(sum(pages[i] for i in range(n) if m >> i & 1) for m in range(1 << n)
                   if sum(prices[i] for i in range(n) if m >> i & 1) <= budget)

    def gen(rng, big):
        n, P, B = (100, 10**4, 10**4) if big else (rng.randint(1, 10), 10, 30)
        return [rng.randint(1, P) for _ in range(n)], [rng.randint(1, 1000 if big else 20) for _ in range(n)], rng.randint(1, B)


@problem
class TreasureWalk:
    title = "Treasure Walk"
    difficulty = "Medium"
    func = "maxTreasure"
    statement = """
<p>A cave map is a grid: <code>grid[r][c] = -1</code> is solid rock, and any other value is the gold in that cell.
You start at the top-left cell, finish at the bottom-right cell, and may only move <b>right</b> or <b>down</b>
through cells that are not rock. Return the most gold you can collect (counting the start and end cells), or
<code>-1</code> if there is no such path.</p>
<ul><li><code>1 &lt;= rows, cols &lt;= 500</code></li><li><code>grid[r][c] == -1</code> or <code>0 &lt;= grid[r][c] &lt;= 1000</code></li></ul>"""
    hint = dict(pattern="Grid DP: best[r][c] = gold[r][c] + max(best above, best to the left), with rock unreachable",
                module="Gold: Paths on Grids", url="https://usaco.guide/gold/paths-grids", similar="CSES Grid Paths · LeetCode 63 / 64")
    examples = [([[1, 3, 1], [1, -1, 1], [4, 2, 1]],), ([[0, -1], [-1, 0]],)]
    edges = [([[5]],), ([[-1]],), ([[1, 2, 3, 4]],)]

    def ref(grid: List[List[int]]) -> int:
        m, n = len(grid), len(grid[0])
        best = [[-1] * n for _ in range(m)]  # -1 = unreachable
        for i in range(m):
            for j in range(n):
                if grid[i][j] == -1:
                    continue
                if i == j == 0:
                    best[i][j] = grid[i][j]
                    continue
                prev = max(best[i - 1][j] if i else -1, best[i][j - 1] if j else -1)
                if prev >= 0:
                    best[i][j] = prev + grid[i][j]
        return best[m - 1][n - 1]

    def brute(grid):
        m, n = len(grid), len(grid[0])

        def walk(i, j):
            if i >= m or j >= n or grid[i][j] == -1:
                return -1
            if (i, j) == (m - 1, n - 1):
                return grid[i][j]
            rest = max(walk(i + 1, j), walk(i, j + 1))
            return -1 if rest < 0 else rest + grid[i][j]

        return walk(0, 0)

    def gen(rng, big):
        m, n = (500, 500) if big else (rng.randint(1, 5), rng.randint(1, 5))
        rock = 0.12 if big else 0.25
        return ([[-1 if rng.random() < rock else rng.randint(0, 1000 if big else 9) for _ in range(n)] for _ in range(m)],)


@problem
class CableNetwork:
    title = "Cable Network"
    difficulty = "Medium"
    func = "minCableCost"
    statement = """
<p>A company has <code>n</code> offices numbered <code>0</code> to <code>n - 1</code>. Each candidate cable
<code>[u, v, cost]</code> would link offices <code>u</code> and <code>v</code> both ways. Choose cables so that every
office can reach every other office (directly or through others) at the lowest total cost. Return that cost, or
<code>-1</code> if it is impossible.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li><code>0 &lt;= cables.length &lt;= 2 * 10^5</code></li>
<li><code>u != v</code>, <code>1 &lt;= cost &lt;= 10^9</code>; the same pair may appear more than once</li></ul>"""
    hint = dict(pattern="Minimum spanning tree: Kruskal (sort cables by cost, union-find skips ones that close a cycle) or Prim",
                module="Gold: Minimum Spanning Trees", url="https://usaco.guide/gold/mst", similar="CSES Road Reparation · LeetCode 1135 / 1584")
    examples = [(4, [[0, 1, 3], [1, 2, 1], [0, 2, 2], [2, 3, 5]]), (3, [[0, 1, 4]])]
    edges = [(1, []), (2, [[0, 1, 7], [1, 0, 2]])]

    def ref(n: int, cables: List[List[int]]) -> int:
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        total, used = 0, 0
        for u, v, c in sorted(cables, key=lambda e: e[2]):
            ru, rv = find(u), find(v)
            if ru != rv:
                parent[ru] = rv
                total += c
                used += 1
        return total if used == n - 1 else -1

    def brute(n, cables):
        def connected(es):
            adj = defaultdict(list)
            for u, v, _ in es:
                adj[u].append(v)
                adj[v].append(u)
            seen, stack = {0}, [0]
            while stack:
                for v in adj[stack.pop()]:
                    if v not in seen:
                        seen.add(v)
                        stack.append(v)
            return len(seen) == n

        costs = [sum(c for _, _, c in es) for es in combinations(cables, n - 1) if connected(es)]
        return min(costs) if costs else -1

    def gen(rng, big):
        n, m, C = (100000, 200000, 10**9) if big else (rng.randint(1, 6), rng.randint(0, 9), 9)
        cables = []
        if big and rng.random() < 0.8:  # usually connected via a random spanning tree
            cables = [[rng.randrange(i), i, rng.randint(1, C)] for i in range(1, n)]
        while len(cables) < m and n > 1:
            u, v = rng.sample(range(n), 2)
            cables.append([u, v, rng.randint(1, C)])
        rng.shuffle(cables)
        return n, cables


@problem
class OfficeParty:
    title = "Office Party"
    difficulty = "Medium"
    func = "maxFun"
    statement = """
<p>A company's <code>n</code> employees form a tree: each pair in <code>edges</code> is a direct reporting line.
Inviting employee <code>i</code> adds <code>fun[i]</code> to the party, but two employees joined by a reporting line
must not <b>both</b> be invited. Return the largest total fun possible.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code>, <code>edges.length == n - 1</code></li><li><code>0 &lt;= fun[i] &lt;= 10^4</code></li>
<li>The tree may be very deep (a long chain), so watch your recursion.</li></ul>"""
    hint = dict(pattern="Tree DP with two values per node: best with it invited, best without it (post-order, iterative for deep trees)",
                module="Gold: DP on Trees - Introduction", url="https://usaco.guide/gold/dp-trees",
                similar="AtCoder DP Contest P (Independent Set) · LeetCode 337 generalized")
    examples = [(5, [3, 2, 1, 10, 1], [[0, 1], [0, 2], [1, 3], [1, 4]]), (3, [5, 9, 5], [[0, 1], [1, 2]])]
    edges = [(1, [7], []), (2, [4, 4], [[1, 0]])]

    def ref(n: int, fun: List[int], edges: List[List[int]]) -> int:
        adj = [[] for _ in range(n)]
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        parent, order, stack = [-1] * n, [], [0]
        parent[0] = 0
        while stack:
            u = stack.pop()
            order.append(u)
            for v in adj[u]:
                if parent[v] == -1 and v != 0:
                    parent[v] = u
                    stack.append(v)
        take, skip = fun[:], [0] * n
        for u in reversed(order[1:]):
            p = parent[u]
            take[p] += skip[u]
            skip[p] += max(take[u], skip[u])
        return max(take[0], skip[0])

    def brute(n, fun, edges):
        return max(sum(fun[i] for i in range(n) if m >> i & 1) for m in range(1 << n)
                   if not any(m >> a & 1 and m >> b & 1 for a, b in edges))

    def gen(rng, big):
        n = 100000 if big else rng.randint(1, 11)
        path = big and rng.random() < 0.5
        label = list(range(n))
        rng.shuffle(label)
        edges = [[label[i - 1 if path else rng.randrange(i)], label[i]] for i in range(1, n)]
        rng.shuffle(edges)
        return n, [rng.randint(0, 10**4 if big else 9) for _ in range(n)], edges


# ================================================================ batch 3

@problem
class DivisibleStreaks:
    title = "Divisible Streaks"
    difficulty = "Medium"
    func = "countDivisible"
    statement = """
<p>A warehouse logs the net change in stock each hour as <code>changes</code> (values can be negative). Pallets hold
exactly <code>k</code> items. Count the <b>contiguous</b> stretches of hours whose total change is a multiple of
<code>k</code> (zero counts as a multiple).</p>
<ul><li><code>1 &lt;= changes.length &lt;= 10^5</code></li><li><code>-10^4 &lt;= changes[i] &lt;= 10^4</code></li>
<li><code>1 &lt;= k &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Prefix sums mod k + a hash map of how often each remainder has appeared (normalize negative remainders)",
                module="Silver: More on Prefix Sums", url="https://usaco.guide/silver/more-prefix-sums",
                similar="CSES Subarray Divisibility · LeetCode 974")
    examples = [([4, 5, 0, -2, -3, 1], 5), ([3], 9)]
    edges = [([0], 1), ([-1, -1, -1], 3), ([7, 7], 7)]

    def ref(changes: List[int], k: int) -> int:
        seen, s, total = Counter({0: 1}), 0, 0
        for x in changes:
            s = (s + x) % k  # Python's % is never negative for k > 0
            total += seen[s]
            seen[s] += 1
        return total

    def brute(changes, k):
        n = len(changes)
        return sum(sum(changes[i:j]) % k == 0 for i in range(n) for j in range(i + 1, n + 1))

    def gen(rng, big):
        if big:
            return [rng.randint(-10**4, 10**4) for _ in range(100000)], rng.choice([2, 7, 1000, 99991, 10**9])
        return [rng.randint(-6, 6) for _ in range(rng.randint(1, 10))], rng.randint(1, 6)


@problem
class BakeryOvens:
    title = "Bakery Ovens"
    difficulty = "Medium"
    func = "minTime"
    statement = """
<p>A bakery has several ovens; oven <code>i</code> bakes one loaf every <code>ovens[i]</code> minutes, and all ovens
work at the same time. Return the minimum number of minutes needed to bake at least <code>loaves</code> loaves.</p>
<ul><li><code>1 &lt;= ovens.length &lt;= 10^5</code></li><li><code>1 &lt;= ovens[i], loaves &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Binary search on the answer: in T minutes the ovens bake sum(T // t) loaves; the upper bound can reach 10^18",
                module="Silver: Binary Search", url="https://usaco.guide/silver/binary-search", similar="CSES Factory Machines · LeetCode 2187")
    examples = [([3, 2, 5], 7), ([10], 3)]
    edges = [([1], 1), ([10**9], 10**9), ([4, 4, 4], 3)]

    def ref(ovens: List[int], loaves: int) -> int:
        lo, hi = 1, min(ovens) * loaves
        while lo < hi:
            mid = (lo + hi) // 2
            made = 0
            for t in ovens:
                made += mid // t
                if made >= loaves:
                    break
            if made >= loaves:
                hi = mid
            else:
                lo = mid + 1
        return lo

    def brute(ovens, loaves):
        heap = [(t, t) for t in ovens]  # (time the next loaf is done, oven speed)
        heapify(heap)
        for _ in range(loaves):
            done, t = heappop(heap)
            heappush(heap, (done + t, t))
        return done

    def gen(rng, big):
        if big:
            return [rng.randint(1, 10**9) for _ in range(100000)], 10**9
        return [rng.randint(1, 9) for _ in range(rng.randint(1, 5))], rng.randint(1, 20)


@problem
class HotelDesk:
    title = "Hotel Desk"
    difficulty = "Medium"
    func = "assignRooms"
    statement = """
<p>Guest <code>i</code> stays from day <code>stays[i][0]</code> to day <code>stays[i][1]</code>, inclusive. A room
can take a new guest the day after its previous guest leaves. Assign every guest a room numbered
<code>1</code> to <code>k</code> using the <b>fewest rooms possible</b>, and return the room number of each guest in input order.</p>
<p>Any valid assignment with the minimum number of rooms is accepted.</p>
<ul><li><code>1 &lt;= stays.length &lt;= 10^5</code></li><li><code>1 &lt;= arrive &lt;= leave &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Sort guests by arrival; a min-heap of (leave day, room) tells you whether the earliest-free room is free yet",
                module="Silver: Priority Queues", url="https://usaco.guide/silver/priority-queues",
                similar="CSES Room Allocation · LeetCode 2402 (Meeting Rooms III)")
    examples = [([[1, 2], [2, 4], [4, 4]],), ([[5, 9], [1, 3], [4, 6]],)]
    edges = [([[1, 1]],), ([[3, 3], [3, 3], [3, 3]],), ([[1, 10], [2, 3], [4, 5], [6, 7]],)]

    def ref(stays: List[List[int]]) -> List[int]:
        out, heap, rooms = [0] * len(stays), [], 0
        for i in sorted(range(len(stays)), key=lambda i: stays[i][0]):
            arrive, leave = stays[i]
            if heap and heap[0][0] < arrive:
                room = heappop(heap)[1]
            else:
                rooms += 1
                room = rooms
            out[i] = room
            heappush(heap, (leave, room))
        return out

    def brute(stays):
        last, out = {}, [0] * len(stays)  # room -> leave day of its latest guest
        for i in sorted(range(len(stays)), key=lambda i: stays[i][0]):
            a, b = stays[i]
            room = next((r for r in sorted(last) if last[r] < a), len(last) + 1)
            last[room] = b
            out[i] = room
        return out

    def check(args, out, expected):
        stays, k = args[0], max(expected)
        if not isinstance(out, list) or len(out) != len(stays) or not all(type(r) is int and 1 <= r <= k for r in out):
            return False
        by_room = defaultdict(list)
        for stay, r in zip(stays, out):
            by_room[r].append(stay)
        return all(a[1] < b[0] for iv in by_room.values() for a, b in zip(sorted(iv), sorted(iv)[1:]))

    def gen(rng, big):
        n, T = (100000, 10**9) if big else (rng.randint(1, 8), 12)
        out = []
        for _ in range(n):
            a = rng.randint(1, T)
            out.append([a, min(T, a + rng.randint(0, T // 40 if big else 4))])
        return (out,)


@problem
class Rewiring:
    title = "Rewiring the Lab"
    difficulty = "Medium"
    func = "minMoves"
    statement = """
<p>A lab has <code>n</code> computers and some network cables <code>[a, b]</code>. In one move you can unplug any
cable and plug it between any two computers. Return the minimum number of moves needed so every computer can
reach every other one, or <code>-1</code> if there are not enough cables.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li><code>0 &lt;= cables.length &lt;= 2 * 10^5</code></li>
<li><code>a != b</code>; there may be repeated cables</li></ul>"""
    hint = dict(pattern="Count connected components (DFS/BFS or union-find); any spare cable can join two components",
                module="Silver: Graph Traversal", url="https://usaco.guide/silver/graph-traversal", similar="CSES Building Roads · LeetCode 1319")
    examples = [(4, [[0, 1], [0, 2], [1, 2]]), (6, [[0, 1], [0, 2], [0, 3], [1, 2]])]
    edges = [(1, []), (3, [[0, 1], [1, 0]]), (2, [[0, 1], [0, 1]])]

    def ref(n: int, cables: List[List[int]]) -> int:
        if len(cables) < n - 1:
            return -1
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        comps = n
        for a, b in cables:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
                comps -= 1
        return comps - 1

    def brute(n, cables):
        adj = defaultdict(list)
        for a, b in cables:
            adj[a].append(b)
            adj[b].append(a)
        seen, comps = set(), 0
        for s in range(n):
            if s not in seen:
                comps += 1
                stack = [s]
                seen.add(s)
                while stack:
                    for v in adj[stack.pop()]:
                        if v not in seen:
                            seen.add(v)
                            stack.append(v)
        return comps - 1 if len(cables) >= n - 1 else -1

    def gen(rng, big):
        n, m = (100000, rng.choice([99999, 150000])) if big else (rng.randint(1, 8), rng.randint(0, 9))
        return n, [rng.sample(range(n), 2) for _ in range(m)] if n > 1 else []


@problem
class PacketRoute:
    title = "Packet Route"
    difficulty = "Medium"
    func = "shortestRoute"
    statement = """
<p>A network has <code>n</code> routers and two-way <code>links</code>. Return the routers on a route from router
<code>0</code> to router <code>n - 1</code> that uses the <b>fewest links</b>, starting with <code>0</code> and ending with
<code>n - 1</code>. If no route exists, return an empty list. Any shortest route is accepted.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li><code>0 &lt;= links.length &lt;= 2 * 10^5</code></li></ul>"""
    hint = dict(pattern="BFS from router 0 that records each router's parent, then walk parents back from n - 1",
                module="Gold: Shortest Paths with Unweighted Edges", url="https://usaco.guide/gold/unweighted-shortest-paths",
                similar="CSES Message Route")
    examples = [(5, [[0, 1], [0, 2], [0, 3], [1, 4], [2, 3]]), (3, [[0, 1]])]
    edges = [(1, []), (2, [[1, 0]]), (4, [[0, 1], [1, 2], [2, 3], [0, 3]])]

    def ref(n: int, links: List[List[int]]) -> List[int]:
        adj = [[] for _ in range(n)]
        for a, b in links:
            adj[a].append(b)
            adj[b].append(a)
        parent = [-1] * n
        parent[0] = 0
        q = deque([0])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if parent[v] == -1:
                    parent[v] = u
                    q.append(v)
        if parent[n - 1] == -1:
            return []
        path = [n - 1]
        while path[-1] != 0:
            path.append(parent[path[-1]])
        return path[::-1]

    def brute(n, links):
        adj = defaultdict(set)
        for a, b in links:
            adj[a].add(b)
            adj[b].add(a)
        best = None

        def dfs(path):
            nonlocal best
            if path[-1] == n - 1:
                if best is None or len(path) < len(best):
                    best = path[:]
                return
            for v in adj[path[-1]]:
                if v not in path:
                    path.append(v)
                    dfs(path)
                    path.pop()

        dfs([0])
        return best or []

    def check(args, out, expected):
        n, links = args
        if not expected:
            return out == []
        linked = {(a, b) for a, b in links} | {(b, a) for a, b in links}
        return (isinstance(out, list) and len(out) == len(expected) and out[0] == 0 and out[-1] == n - 1
                and all((a, b) in linked for a, b in zip(out, out[1:])))

    def gen(rng, big):
        n, m = (100000, 200000) if big else (rng.randint(1, 8), rng.randint(0, 10))
        return n, [rng.sample(range(n), 2) for _ in range(m)] if n > 1 else []


@problem
class NearestCharger:
    title = "Nearest Charger"
    difficulty = "Medium"
    func = "chargerDistances"
    statement = """
<p>A parking garage map is a list of strings: <code>'C'</code> is a charging spot, <code>'.'</code> is open floor and
<code>'#'</code> is a wall. Cars move up/down/left/right, one cell per step, and cannot enter walls. Return a grid of
the same size where each cell holds the number of steps to the <b>nearest</b> charger, or <code>-1</code> for walls and
cells that cannot reach any charger.</p>
<ul><li><code>1 &lt;= rows * cols &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="Multi-source BFS: start the queue with every charger at distance 0, not one BFS per charger",
                module="Gold: Shortest Paths with Unweighted Edges", url="https://usaco.guide/gold/unweighted-shortest-paths",
                similar="LeetCode 542 (01 Matrix) / 1162 / 286 (Walls and Gates)")
    examples = [(["C..", ".#.", "..C"],), (["C#.", "##.", "..."],)]
    edges = [(["C"],), (["."],), (["#"],), (["C.C.C"],)]

    def ref(grid: List[str]) -> List[List[int]]:
        m, n = len(grid), len(grid[0])
        dist = [[-1] * n for _ in range(m)]
        q = deque()
        for i in range(m):
            for j in range(n):
                if grid[i][j] == "C":
                    dist[i][j] = 0
                    q.append((i, j))
        while q:
            i, j = q.popleft()
            for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                if 0 <= a < m and 0 <= b < n and grid[a][b] != "#" and dist[a][b] == -1:
                    dist[a][b] = dist[i][j] + 1
                    q.append((a, b))
        return dist

    def brute(grid):
        m, n = len(grid), len(grid[0])
        best = [[-1] * n for _ in range(m)]
        for si in range(m):
            for sj in range(n):
                if grid[si][sj] != "C":
                    continue
                d, q = {(si, sj): 0}, deque([(si, sj)])
                while q:
                    i, j = q.popleft()
                    for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                        if 0 <= a < m and 0 <= b < n and grid[a][b] != "#" and (a, b) not in d:
                            d[(a, b)] = d[(i, j)] + 1
                            q.append((a, b))
                for (i, j), v in d.items():
                    if best[i][j] == -1 or v < best[i][j]:
                        best[i][j] = v
        return best

    def gen(rng, big):
        m, n = (300, 333) if big else (rng.randint(1, 5), rng.randint(1, 5))
        pc = 0.002 if big else 0.15
        return (["".join("C" if (r := rng.random()) < pc else "#" if r < 0.3 else "." for _ in range(n)) for _ in range(m)],)


@problem
class GrowingKingdom:
    title = "Growing Kingdom"
    difficulty = "Medium"
    func = "afterEachRoad"
    statement = """
<p>A kingdom has <code>n</code> towns and no roads. Roads <code>[a, b]</code> are built one at a time in the given
order. After <b>each</b> road is built, report <code>[number of separate regions, size of the largest region]</code>,
where a region is a group of towns connected by roads.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li><code>1 &lt;= roads.length &lt;= 2 * 10^5</code></li>
<li><code>a != b</code>; a road may repeat</li></ul>"""
    hint = dict(pattern="Union-find with union by size: each new road merges at most two regions, and sizes only grow",
                module="Gold: Disjoint Set Union", url="https://usaco.guide/gold/dsu", similar="CSES Road Construction")
    examples = [(5, [[0, 1], [1, 2], [3, 4], [0, 2]]), (3, [[2, 0], [1, 2]])]
    edges = [(2, [[0, 1]]), (4, [[0, 1], [0, 1], [2, 3], [1, 3]])]

    def ref(n: int, roads: List[List[int]]) -> List[List[int]]:
        parent, size = list(range(n)), [1] * n

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        regions, largest, out = n, 1, []
        for a, b in roads:
            ra, rb = find(a), find(b)
            if ra != rb:
                if size[ra] < size[rb]:
                    ra, rb = rb, ra
                parent[rb] = ra
                size[ra] += size[rb]
                regions -= 1
                largest = max(largest, size[ra])
            out.append([regions, largest])
        return out

    def brute(n, roads):
        out, adj = [], defaultdict(set)
        for a, b in roads:
            adj[a].add(b)
            adj[b].add(a)
            seen, sizes = set(), []
            for s in range(n):
                if s in seen:
                    continue
                stack, cnt = [s], 0
                seen.add(s)
                while stack:
                    cnt += 1
                    for v in adj[stack.pop()]:
                        if v not in seen:
                            seen.add(v)
                            stack.append(v)
                sizes.append(cnt)
            out.append([len(sizes), max(sizes)])
        return out

    def gen(rng, big):
        n, m = (100000, 200000) if big else (rng.randint(2, 7), rng.randint(1, 8))
        return n, [rng.sample(range(n), 2) for _ in range(m)]


@problem
class TravelVoucher:
    title = "Travel Voucher"
    difficulty = "Hard"
    tl = 3.0  # Dijkstra over 2n states with heapq is ~0.7s in Python at full size
    func = "cheapestTrip"
    statement = """
<p>There are <code>n</code> cities and one-way <code>flights</code> <code>[from, to, price]</code>. You hold one
voucher that halves the price of a <b>single</b> flight (rounded down). Return the cheapest total price to travel from
city <code>0</code> to city <code>n - 1</code>, or <code>-1</code> if it cannot be reached.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li><code>0 &lt;= flights.length &lt;= 2 * 10^5</code></li>
<li><code>1 &lt;= price &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Dijkstra on an expanded state graph: (city, voucher used?) — two copies of every city",
                module="Gold: Shortest Paths with Non-Negative Edge Weights", url="https://usaco.guide/gold/shortest-paths",
                similar="CSES Flight Discount · LeetCode 787 (state-augmented shortest path)")
    examples = [(3, [[0, 1, 3], [1, 2, 3], [0, 2, 7]]), (4, [[0, 1, 10], [1, 3, 1], [0, 2, 2], [2, 3, 15]])]
    edges = [(1, []), (2, [[1, 0, 5]]), (2, [[0, 1, 1]])]

    def ref(n: int, flights: List[List[int]]) -> int:
        adj = [[] for _ in range(n)]
        for u, v, c in flights:
            adj[u].append((v, c))
        INF = float("inf")
        dist = [[INF] * n, [INF] * n]  # dist[used][city]
        dist[0][0] = 0
        heap = [(0, 0, 0)]
        while heap:
            d, u, used = heappop(heap)
            if d > dist[used][u]:
                continue
            for v, c in adj[u]:
                if d + c < dist[used][v]:
                    dist[used][v] = d + c
                    heappush(heap, (d + c, v, used))
                if not used and d + c // 2 < dist[1][v]:
                    dist[1][v] = d + c // 2
                    heappush(heap, (d + c // 2, v, 1))
        best = min(dist[0][n - 1], dist[1][n - 1])
        return -1 if best == INF else best

    def brute(n, flights):
        def bellman(prices):
            d = [float("inf")] * n
            d[0] = 0
            for _ in range(n):
                for (u, v, _), c in zip(flights, prices):
                    d[v] = min(d[v], d[u] + c)
            return d[n - 1]

        base = [c for _, _, c in flights]
        options = [bellman(base)] + [bellman(base[:i] + [base[i] // 2] + base[i + 1:]) for i in range(len(flights))]
        best = min(options)
        return -1 if best == float("inf") else best

    def gen(rng, big):
        n, m, C = (100000, 200000, 10**9) if big else (rng.randint(1, 6), rng.randint(0, 9), 20)
        flights = [[*rng.sample(range(n), 2), rng.randint(1, C)] for _ in range(m)] if n > 1 else []
        if big:  # a long expensive chain so the far city is usually reachable
            flights += [[i, i + 1, rng.randint(1, C)] for i in range(0, n - 1, 1)]
            rng.shuffle(flights)
        return n, flights


@problem
class CoinLineDuel:
    title = "Coin Line Duel"
    difficulty = "Medium"
    func = "firstPlayerTotal"
    statement = """
<p>Coins with values <code>coins</code> lie in a line. Two players take turns; on each turn a player takes the coin at
<b>either end</b> of the line. Both play to maximize their own total. Return the total the first player collects.</p>
<ul><li><code>1 &lt;= coins.length &lt;= 1000</code></li><li><code>1 &lt;= coins[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Interval DP on the score difference: best[i][j] = max(coins[i] - best[i+1][j], coins[j] - best[i][j-1])",
                module="Gold: Range DP", url="https://usaco.guide/gold/dp-ranges", similar="CSES Removal Game · LeetCode 486 / 877")
    examples = [([4, 5, 1, 3],), ([2, 9, 3],)]
    edges = [([7],), ([1, 1],), ([5, 3, 7, 10],)]

    def ref(coins: List[int]) -> int:
        n = len(coins)
        diff = coins[:]  # diff[i]: best (mover - other) on coins[i .. i+len-1]
        for length in range(2, n + 1):
            for i in range(n - length + 1):
                j = i + length - 1
                diff[i] = max(coins[i] - diff[i + 1], coins[j] - diff[i])
        return (sum(coins) + diff[0]) // 2

    def brute(coins):
        def play(i, j):  # (mover's total, other's total)
            if i > j:
                return 0, 0
            a_other, a_me = play(i + 1, j)
            b_other, b_me = play(i, j - 1)
            return max((coins[i] + a_me, a_other), (coins[j] + b_me, b_other))

        return play(0, len(coins) - 1)[0]

    def gen(rng, big):
        if big:
            return ([rng.randint(1, 10**9) for _ in range(1000)],)
        return ([rng.randint(1, 9) for _ in range(rng.randint(1, 10))],)


@problem
class ContractPicker:
    title = "Contract Picker"
    difficulty = "Hard"
    func = "maxReward"
    statement = """
<p>A freelancer can choose from contracts <code>[start, end, reward]</code>, each occupying the days from
<code>start</code> to <code>end</code> inclusive. They can work on only one contract per day, and a new contract may begin
the day after the previous one ends. Return the largest total reward they can earn.</p>
<ul><li><code>1 &lt;= contracts.length &lt;= 10^5</code></li><li><code>1 &lt;= start &lt;= end &lt;= 10^9</code></li>
<li><code>1 &lt;= reward &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Weighted interval scheduling: sort by end day; best[i] = max(skip it, reward + best up to the last contract ending before it starts), found by binary search",
                module="Gold: Introduction to DP (with Silver: Binary Search)", url="https://usaco.guide/gold/intro-dp",
                similar="CSES Projects · LeetCode 1235")
    examples = [([[2, 4, 4], [3, 6, 6], [6, 8, 2], [5, 7, 3]],), ([[1, 2, 5], [3, 4, 5], [1, 4, 9]],)]
    edges = [([[1, 1, 7]],), ([[1, 5, 3], [5, 9, 4]],), ([[1, 3, 2], [1, 3, 5], [4, 4, 1]],)]

    def ref(contracts: List[List[int]]) -> int:
        cs = sorted(contracts, key=lambda c: c[1])
        ends = [c[1] for c in cs]
        best = [0] * (len(cs) + 1)  # best[i]: most reward using only the first i contracts by end day
        for i, (s, e, r) in enumerate(cs):
            j = bisect_left(ends, s)  # contracts that end strictly before day s
            best[i + 1] = max(best[i], best[j] + r)
        return best[-1]

    def brute(contracts):
        n, top = len(contracts), 0
        for m in range(1 << n):
            pick = [contracts[i] for i in range(n) if m >> i & 1]
            if all(a[1] < b[0] or b[1] < a[0] for a, b in combinations(pick, 2)):
                top = max(top, sum(c[2] for c in pick))
        return top

    def gen(rng, big):
        n, T = (100000, 10**9) if big else (rng.randint(1, 9), 15)
        out = []
        for _ in range(n):
            s = rng.randint(1, T)
            out.append([s, min(T, s + rng.randint(0, T // 1000 if big else 5)), rng.randint(1, 10**9 if big else 10)])
        return (out,)


# ================================================================ batch 4: warm-ups for the Hard problems

@problem
class CoursePlanner:
    title = "Course Planner"
    difficulty = "Medium"
    func = "courseOrder"
    statement = """
<p>There are <code>n</code> courses numbered <code>0</code> to <code>n - 1</code>. Each pair <code>[a, b]</code> in
<code>prereqs</code> means course <code>a</code> must be taken before course <code>b</code>. Return an order in which to take
all <code>n</code> courses, or an empty list if no order works. Any valid order is accepted.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li><code>0 &lt;= prereqs.length &lt;= 2 * 10^5</code>, <code>a != b</code></li></ul>"""
    hint = dict(pattern="Topological sort: Kahn's algorithm (queue of courses with no remaining prerequisites) or DFS post-order",
                module="Gold: Topological Sort", url="https://usaco.guide/gold/toposort", similar="CSES Course Schedule ★ · LeetCode 210")
    examples = [(4, [[0, 1], [1, 2], [0, 3]]), (2, [[0, 1], [1, 0]])]
    edges = [(1, []), (3, []), (3, [[2, 1], [1, 0]])]

    def ref(n: int, prereqs: List[List[int]]) -> List[int]:
        adj, indeg = [[] for _ in range(n)], [0] * n
        for a, b in prereqs:
            adj[a].append(b)
            indeg[b] += 1
        order = [i for i in range(n) if indeg[i] == 0]
        for u in order:  # the list grows while we iterate: it doubles as the queue
            for v in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    order.append(v)
        return order if len(order) == n else []

    def brute(n, prereqs):
        from itertools import permutations
        for perm in permutations(range(n)):
            pos = {c: i for i, c in enumerate(perm)}
            if all(pos[a] < pos[b] for a, b in prereqs):
                return list(perm)
        return []

    def check(args, out, expected):
        n, prereqs = args
        if not expected:
            return out == []
        if not isinstance(out, list) or sorted(out) != list(range(n)):
            return False
        pos = {c: i for i, c in enumerate(out)}
        return all(pos[a] < pos[b] for a, b in prereqs)

    def gen(rng, big):
        n, m = (100000, 200000) if big else (rng.randint(1, 6), rng.randint(0, 8))
        order = list(range(n))
        rng.shuffle(order)
        pairs = []
        for _ in range(m if n > 1 else 0):
            i, j = sorted(rng.sample(range(n), 2))
            pairs.append([order[i], order[j]])
        if n > 1 and rng.random() < (0.5 if big else 0.25):
            pairs.append(rng.sample(range(n), 2))  # may close a cycle
        return n, pairs


@problem
class RisingPrices:
    title = "Rising Prices"
    difficulty = "Medium"
    func = "longestRise"
    statement = """
<p>Given daily stock prices <code>prices</code>, choose some of the days (keeping their order) so that the chosen prices
are <b>strictly increasing</b>. Return the largest number of days you can choose.</p>
<ul><li><code>1 &lt;= prices.length &lt;= 10^5</code></li><li><code>1 &lt;= prices[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Longest increasing subsequence in O(n log n): keep the smallest possible tail for each length, update with bisect",
                module="Gold: Longest Increasing Subsequence", url="https://usaco.guide/gold/lis",
                similar="CSES Increasing Subsequence · LeetCode 300 (warm-up for Nesting Boxes)")
    examples = [([7, 3, 5, 3, 6, 2, 9, 8],), ([5, 4, 3],)]
    edges = [([1],), ([2, 2, 2],), ([1, 2, 3, 4, 5],)]

    def ref(prices: List[int]) -> int:
        tails = []
        for x in prices:
            i = bisect_left(tails, x)
            if i == len(tails):
                tails.append(x)
            else:
                tails[i] = x
        return len(tails)

    def brute(prices):
        best = [1] * len(prices)
        for i in range(len(prices)):
            for j in range(i):
                if prices[j] < prices[i]:
                    best[i] = max(best[i], best[j] + 1)
        return max(best)

    def gen(rng, big):
        if big:
            return ([rng.randint(1, 10**9) for _ in range(100000)],)
        return ([rng.randint(1, 6) for _ in range(rng.randint(1, 10))],)


@problem
class FilmFestival:
    title = "Film Festival"
    difficulty = "Easy"
    func = "maxMovies"
    statement = """
<p>A festival shows movies <code>[start, end]</code>. You can watch a movie only from start to end, and you may begin a
new movie at the exact moment the previous one ends. Return the most movies you can watch in full.</p>
<ul><li><code>1 &lt;= movies.length &lt;= 10^5</code></li><li><code>0 &lt;= start &lt; end &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Interval scheduling greedy: sort by end time and take every movie that starts after the last one you took ends",
                module="Silver: Greedy Algorithms with Sorting", url="https://usaco.guide/silver/greedy-sorting",
                similar="CSES Movie Festival · LeetCode 435 (warm-up for Freelancer Deadlines)")
    examples = [([[3, 5], [4, 9], [5, 8]],), ([[1, 10], [2, 3], [3, 4], [4, 5]],)]
    edges = [([[0, 1]],), ([[1, 2], [1, 2]],)]

    def ref(movies: List[List[int]]) -> int:
        count, free_at = 0, -1
        for s, e in sorted(movies, key=lambda m: m[1]):
            if s >= free_at:
                count += 1
                free_at = e
        return count

    def brute(movies):
        n, best = len(movies), 0
        for m in range(1 << n):
            pick = sorted(movies[i] for i in range(n) if m >> i & 1)
            if all(a[1] <= b[0] for a, b in zip(pick, pick[1:])):
                best = max(best, len(pick))
        return best

    def gen(rng, big):
        n, T = (100000, 10**9) if big else (rng.randint(1, 9), 12)
        out = []
        for _ in range(n):
            s = rng.randint(0, T - 1)
            out.append([s, rng.randint(s + 1, min(T, s + (T // 1000 if big else 6)))])
        return (out,)


@problem
class LiveScoreboard:
    title = "Live Scoreboard"
    difficulty = "Medium"
    func = "processQueries"
    tl = 3.0
    statement = """
<p>A scoreboard holds <code>scores</code>. Process <code>queries</code> in order:</p>
<ul><li><code>[1, i, v]</code>: set <code>scores[i] = v</code>.</li>
<li><code>[2, l, r]</code>: report the sum of <code>scores[l..r]</code>, inclusive.</li></ul>
<p>Return the answers to all type-2 queries, in order.</p>
<ul><li><code>1 &lt;= scores.length, queries.length &lt;= 10^5</code></li><li><code>-10^9 &lt;= scores[i], v &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Fenwick tree (binary indexed tree): an update adds (v - old) at i; a range sum is prefix(r) - prefix(l - 1)",
                module="Gold: Point Update Range Sum", url="https://usaco.guide/gold/PURS",
                similar="CSES Dynamic Range Sum Queries · LeetCode 307 (warm-up for Later Underdogs)")
    examples = [([3, 2, 4, 5, 1, 1, 5, 3], [[2, 1, 4], [2, 5, 6], [1, 2, 9], [2, 0, 7]]),]
    edges = [([5], [[2, 0, 0], [1, 0, -3], [2, 0, 0]]), ([1, 2], [[1, 0, 1]])]

    def ref(scores: List[int], queries: List[List[int]]) -> List[int]:
        n = len(scores)
        tree, cur = [0] * (n + 1), scores[:]
        for i, x in enumerate(scores):  # O(n) build
            j = i + 1
            tree[j] += x
            if j + (j & -j) <= n:
                tree[j + (j & -j)] += tree[j]

        def prefix(i):  # sum of scores[0..i-1]
            s = 0
            while i > 0:
                s += tree[i]
                i -= i & -i
            return s

        out = []
        for t, a, b in queries:
            if t == 1:
                delta, cur[a] = b - cur[a], b
                i = a + 1
                while i <= n:
                    tree[i] += delta
                    i += i & -i
            else:
                out.append(prefix(b + 1) - prefix(a))
        return out

    def brute(scores, queries):
        s, out = scores[:], []
        for t, a, b in queries:
            if t == 1:
                s[a] = b
            else:
                out.append(sum(s[a:b + 1]))
        return out

    def gen(rng, big):
        n, q, V = (100000, 100000, 10**9) if big else (rng.randint(1, 6), rng.randint(1, 8), 9)
        qs = []
        for _ in range(q):
            if rng.random() < 0.5:
                qs.append([1, rng.randrange(n), rng.randint(-V, V)])
            else:
                l, r = sorted((rng.randrange(n), rng.randrange(n)))
                qs.append([2, l, r])
        return [rng.randint(-V, V) for _ in range(n)], qs


@problem
class OrgChart:
    title = "Org Chart"
    difficulty = "Easy"
    func = "countReports"
    statement = """
<p>A company has <code>n</code> employees; employee <code>0</code> is the CEO. For every other employee
<code>i</code> (<code>1 &lt;= i &lt; n</code>), <code>boss[i - 1]</code> is their direct boss. For each employee, return how
many people work under them, directly or indirectly.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li>The chain of bosses can be very long, so watch your recursion.</li></ul>"""
    hint = dict(pattern="Subtree sizes: process employees children-first (reverse BFS order, or post-order DFS) and add each size to the boss",
                module="Silver: Introduction to Tree Algorithms", url="https://usaco.guide/silver/intro-tree",
                similar="CSES Subordinates (warm-up for Total Commute)")
    examples = [(5, [0, 0, 1, 1]), (3, [2, 0])]
    edges = [(1, []), (2, [0])]

    def ref(n: int, boss: List[int]) -> List[int]:
        kids = [[] for _ in range(n)]
        for i, b in enumerate(boss, start=1):
            kids[b].append(i)
        order = [0]
        for u in order:
            order.extend(kids[u])
        under = [0] * n
        for u in reversed(order[1:]):
            under[boss[u - 1]] += under[u] + 1
        return under

    def brute(n, boss):
        under = [0] * n
        for i in range(1, n):
            b = boss[i - 1]
            while True:
                under[b] += 1
                if b == 0:
                    break
                b = boss[b - 1]
        return under

    def gen(rng, big):
        n = 100000 if big else rng.randint(1, 10)
        label = [0] + rng.sample(range(1, n), n - 1)  # CEO stays 0, others shuffled
        parent_of = {}
        for k in range(1, n):  # node at position k hangs under an earlier position (or the previous one: a chain)
            p = k - 1 if big and rng.random() < 0.5 else rng.randrange(k)
            parent_of[label[k]] = label[p]
        return n, [parent_of[i] for i in range(1, n)]


@problem
class MazeRunner:
    title = "Maze Runner"
    difficulty = "Medium"
    func = "escapePath"
    statement = """
<p>A maze is a list of strings: <code>'A'</code> is where you start, <code>'B'</code> is the exit, <code>'#'</code> is a
wall and <code>'.'</code> is open floor. Return a <b>shortest</b> route from A to B as a string of moves
<code>'L'</code>, <code>'R'</code>, <code>'U'</code>, <code>'D'</code>, or an empty string if B cannot be reached.
Any shortest route is accepted.</p>
<ul><li><code>1 &lt;= rows * cols &lt;= 10^5</code></li><li>Exactly one <code>'A'</code> and one <code>'B'</code>.</li></ul>"""
    hint = dict(pattern="Grid BFS from A that remembers the move used to enter each cell; walk back from B and reverse",
                module="Gold: Shortest Paths with Unweighted Edges", url="https://usaco.guide/gold/unweighted-shortest-paths",
                similar="CSES Labyrinth ★ (warm-up for Demolition Path)")
    examples = [(["#######", "#A#...#", "#.#.#.#", "#.....B", "#######"],), (["A#B"],)]
    edges = [(["AB"],), (["B", ".", "A"],)]
    MOVES = {"L": (0, -1), "R": (0, 1), "U": (-1, 0), "D": (1, 0)}

    def ref(grid: List[str]) -> str:
        m, n = len(grid), len(grid[0])
        start = next((i, j) for i in range(m) for j in range(n) if grid[i][j] == "A")
        came = {start: None}
        q = deque([start])
        while q:
            i, j = q.popleft()
            if grid[i][j] == "B":
                path = []
                while came[(i, j)]:
                    d = came[(i, j)]
                    path.append(d)
                    di, dj = {"L": (0, -1), "R": (0, 1), "U": (-1, 0), "D": (1, 0)}[d]
                    i, j = i - di, j - dj
                return "".join(reversed(path))
            for d, (di, dj) in (("L", (0, -1)), ("R", (0, 1)), ("U", (-1, 0)), ("D", (1, 0))):
                a, b = i + di, j + dj
                if 0 <= a < m and 0 <= b < n and grid[a][b] != "#" and (a, b) not in came:
                    came[(a, b)] = d
                    q.append((a, b))
        return ""

    def brute(grid):
        m, n = len(grid), len(grid[0])
        start = next((i, j) for i in range(m) for j in range(n) if grid[i][j] == "A")

        def dfs(cell, depth, seen):  # iterative deepening: first depth that works is shortest
            i, j = cell
            if grid[i][j] == "B":
                return ""
            if depth == 0:
                return None
            for d, (di, dj) in MazeRunner.MOVES.items():
                a, b = i + di, j + dj
                if 0 <= a < m and 0 <= b < n and grid[a][b] != "#" and (a, b) not in seen:
                    rest = dfs((a, b), depth - 1, seen | {(a, b)})
                    if rest is not None:
                        return d + rest
            return None

        for depth in range(m * n):
            found = dfs(start, depth, {start})
            if found is not None:
                return found
        return ""

    def check(args, out, expected):
        grid = args[0]
        if not expected:
            return out == ""
        if not isinstance(out, str) or len(out) != len(expected):
            return False
        m, n = len(grid), len(grid[0])
        i, j = next((i, j) for i in range(m) for j in range(n) if grid[i][j] == "A")
        for d in out:
            if d not in MazeRunner.MOVES:
                return False
            i, j = i + MazeRunner.MOVES[d][0], j + MazeRunner.MOVES[d][1]
            if not (0 <= i < m and 0 <= j < n) or grid[i][j] == "#":
                return False
        return grid[i][j] == "B"

    def gen(rng, big):
        m, n = (300, 333) if big else (rng.randint(1, 4), rng.randint(2, 4))
        cells = [["#" if rng.random() < (0.2 if big else 0.3) else "." for _ in range(n)] for _ in range(m)]
        a, b = rng.sample(range(m * n), 2)
        cells[a // n][a % n], cells[b // n][b % n] = "A", "B"
        return (["".join(r) for r in cells],)


# ================================================================ batch 6: focus problems not covered elsewhere

@problem
class LayeredUpdates:
    title = "Layered Updates"
    difficulty = "Medium"
    func = "applyBatches"
    statement = """
<p>You have an array <code>nums</code> and a list of operations, where <code>ops[i] = [l, r, d]</code> adds
<code>d</code> to every element of <code>nums[l..r]</code>. Then come <code>batches</code>: each <code>[x, y]</code> means
"apply operations <code>x</code> through <code>y</code> (inclusive) once each". Apply every batch and return the final array.</p>
<ul><li><code>1 &lt;= nums.length, ops.length, batches.length &lt;= 10^5</code></li><li><code>0 &lt;= nums[i], d &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="Two difference arrays: first count how many times each operation runs, then apply the operations to nums with a second difference array",
                module="Silver: More on Prefix Sums", url="https://usaco.guide/silver/more-prefix-sums", similar="CF Greg and Array (focus problem)")
    examples = [([1, 2, 3], [[0, 1, 1], [0, 2, 2], [1, 2, 3]], [[0, 1], [0, 2], [1, 2]]), ([1], [[0, 0, 1]], [[0, 0]])]
    edges = [([0, 0], [[0, 1, 5]], [[0, 0], [0, 0], [0, 0]]), ([4, 4], [[0, 0, 1], [1, 1, 1]], [[1, 1]])]

    def ref(nums: List[int], ops: List[List[int]], batches: List[List[int]]) -> List[int]:
        times = [0] * (len(ops) + 1)
        for x, y in batches:
            times[x] += 1
            times[y + 1] -= 1
        add, run = [0] * (len(nums) + 1), 0
        for i, (l, r, d) in enumerate(ops):
            run += times[i]
            add[l] += d * run
            add[r + 1] -= d * run
        out, cur = [], 0
        for i, x in enumerate(nums):
            cur += add[i]
            out.append(x + cur)
        return out

    def brute(nums, ops, batches):
        a = nums[:]
        for x, y in batches:
            for l, r, d in ops[x:y + 1]:
                for i in range(l, r + 1):
                    a[i] += d
        return a

    def gen(rng, big):
        n, m, k = (100000, 100000, 100000) if big else (rng.randint(1, 5), rng.randint(1, 4), rng.randint(1, 4))
        V = 10**5 if big else 5
        ops = []
        for _ in range(m):
            l, r = sorted((rng.randrange(n), rng.randrange(n)))
            ops.append([l, r, rng.randint(0, V)])
        return ([rng.randint(0, V) for _ in range(n)], ops,
                [sorted((rng.randrange(m), rng.randrange(m))) for _ in range(k)])


@problem
class LampPosts:
    title = "Lamp Posts"
    difficulty = "Easy"
    func = "countInRanges"
    statement = """
<p>Lamp posts stand along a road at mile markers <code>posts</code> (in no particular order). For each query
<code>[a, b]</code>, report how many lamp posts stand at markers from <code>a</code> to <code>b</code>, inclusive.</p>
<ul><li><code>1 &lt;= posts.length, queries.length &lt;= 10^5</code></li><li><code>0 &lt;= posts[i], a &lt;= b &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Sort once, then each query is bisect_right(b) - bisect_left(a)",
                module="Silver: Binary Search on a Sorted Array", url="https://usaco.guide/silver/binary-search-sorted-array",
                similar="USACO Counting Haybales (focus problem)")
    examples = [([3, 2, 7, 5], [[2, 3], [2, 4], [2, 5], [2, 7], [4, 6]]),]
    edges = [([5], [[0, 4], [5, 5], [6, 9]]), ([1, 1, 1], [[1, 1]])]

    def ref(posts: List[int], queries: List[List[int]]) -> List[int]:
        from bisect import bisect_right
        s = sorted(posts)
        return [bisect_right(s, b) - bisect_left(s, a) for a, b in queries]

    def brute(posts, queries):
        return [sum(a <= p <= b for p in posts) for a, b in queries]

    def gen(rng, big):
        n, q, V = (100000, 100000, 10**9) if big else (rng.randint(1, 8), rng.randint(1, 6), 10)
        return [rng.randint(0, V) for _ in range(n)], [sorted((rng.randint(0, V), rng.randint(0, V))) for _ in range(q)]


@problem
class MedianBoost:
    title = "Median Boost"
    difficulty = "Medium"
    func = "maxMedian"
    statement = """
<p>You have an odd-length list of test scores <code>scores</code> and <code>k</code> bonus points. Each bonus point adds
1 to any single score. Using at most <code>k</code> points, return the largest possible <b>median</b> score.</p>
<ul><li><code>1 &lt;= scores.length &lt;= 10^5</code>, length is odd</li><li><code>1 &lt;= scores[i], k &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Binary search on the answer: reaching median x costs sum(max(0, x - s)) over the upper half of the sorted scores",
                module="Silver: Binary Search", url="https://usaco.guide/silver/binary-search", similar="CF Maximum Median (focus problem)")
    examples = [([1, 3, 5], 2), ([1, 2, 1, 1, 1], 5)]
    edges = [([4], 6), ([5, 5, 5], 1)]

    def ref(scores: List[int], k: int) -> int:
        upper = sorted(scores)[len(scores) // 2:]

        def cost(x):
            c = 0
            for s in upper:
                if s >= x:
                    break  # upper half is sorted: nothing further needs points
                c += x - s
            return c

        lo, hi = upper[0], upper[0] + k
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if cost(mid) <= k:
                lo = mid
            else:
                hi = mid - 1
        return lo

    def brute(scores, k):
        s = sorted(scores)
        for _ in range(k):  # greedily raise the current median, which is always optimal
            s[len(s) // 2] += 1
            s.sort()
        return s[len(s) // 2]

    def gen(rng, big):
        if big:
            return [rng.randint(1, 10**9) for _ in range(99999)], rng.randint(1, 10**9)
        return [rng.randint(1, 8) for _ in range(rng.choice([1, 3, 5, 7]))], rng.randint(1, 12)


@problem
class RoundTrip:
    title = "Round Trip"
    difficulty = "Medium"
    func = "findLoop"
    statement = """
<p>There are <code>n</code> cities and one-way flights <code>[a, b]</code>. Find a trip that starts and ends in the same
city, uses at least one flight, and visits no other city twice. Return it as the list of cities in order, with the
first city repeated at the end (for example <code>[2, 5, 1, 2]</code>), or an empty list if no such trip exists.
Any valid trip is accepted.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li><code>0 &lt;= flights.length &lt;= 2 * 10^5</code>, <code>a != b</code></li></ul>"""
    hint = dict(pattern="DFS with three colors: an edge into a node that is still on the stack closes a cycle; walk parents back to print it",
                module="Gold: Topological Sort", url="https://usaco.guide/gold/toposort", similar="CSES Round Trip II (focus problem)")
    examples = [(4, [[0, 1], [1, 2], [2, 0], [2, 3]]), (3, [[0, 1], [1, 2], [0, 2]])]
    edges = [(1, []), (2, [[0, 1], [1, 0]])]

    def ref(n: int, flights: List[List[int]]) -> List[int]:
        adj = [[] for _ in range(n)]
        for a, b in flights:
            adj[a].append(b)
        state, parent = [0] * n, [-1] * n  # 0 unvisited, 1 on stack, 2 done
        for s in range(n):
            if state[s]:
                continue
            state[s] = 1
            stack = [(s, iter(adj[s]))]
            while stack:
                u, it = stack[-1]
                for v in it:
                    if state[v] == 1:  # back edge u -> v closes a cycle
                        cycle = [v, u]
                        while cycle[-1] != v:
                            cycle.append(parent[cycle[-1]])
                        return cycle[::-1]
                    if state[v] == 0:
                        state[v], parent[v] = 1, u
                        stack.append((v, iter(adj[v])))
                        break
                else:
                    state[u] = 2
                    stack.pop()
        return []

    def brute(n, flights):
        adj = defaultdict(set)
        for a, b in flights:
            adj[a].add(b)
        for s in range(n):  # BFS from s's successors back to s
            prev, q = {}, deque()
            for v in adj[s]:
                if v not in prev:
                    prev[v] = s
                    q.append(v)
            while q:
                u = q.popleft()
                if u == s:
                    path = [s]
                    while True:
                        path.append(prev[path[-1]])
                        if path[-1] == s:
                            return path[::-1]
                for v in adj[u]:
                    if v not in prev:
                        prev[v] = u
                        q.append(v)
        return []

    def check(args, out, expected):
        n, flights = args
        if not expected:
            return out == []
        edges = {(a, b) for a, b in flights}
        return (isinstance(out, list) and len(out) >= 3 and out[0] == out[-1] and len(set(out[:-1])) == len(out) - 1
                and all(type(c) is int and 0 <= c < n for c in out) and all((a, b) in edges for a, b in zip(out, out[1:])))

    def gen(rng, big):
        n, m = (100000, 100000) if big else (rng.randint(1, 6), rng.randint(0, 7))
        order = list(range(n))
        rng.shuffle(order)
        flights = []
        for _ in range(m if n > 1 else 0):  # mostly forward edges in a random order (a DAG)...
            i, j = sorted(rng.sample(range(n), 2))
            flights.append([order[i], order[j]])
        if n > 1 and rng.random() < 0.5:  # ...sometimes one backward edge that may close a long cycle
            i, j = sorted(rng.sample(range(n), 2))
            flights.append([order[j], order[i]])
        rng.shuffle(flights)
        return n, flights


@problem
class PriceTracker:
    title = "Price Tracker"
    difficulty = "Medium"
    func = "processQueries"
    tl = 3.0
    statement = """
<p>A tracker holds the current prices <code>prices</code>. Process <code>queries</code> in order:</p>
<ul><li><code>[1, i, v]</code>: set <code>prices[i] = v</code>.</li>
<li><code>[2, l, r]</code>: report the <b>lowest</b> price in <code>prices[l..r]</code>, inclusive.</li></ul>
<p>Return the answers to all type-2 queries, in order.</p>
<ul><li><code>1 &lt;= prices.length, queries.length &lt;= 10^5</code></li><li><code>1 &lt;= prices[i], v &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Segment tree: each node stores the min of its range; update a leaf and its ancestors, query with O(log n) nodes (a Fenwick tree can't undo a min)",
                module="Gold: Point Update Range Sum", url="https://usaco.guide/gold/PURS", similar="CSES Dynamic Range Minimum Queries (focus problem)")
    examples = [([3, 1, 4, 1, 5], [[2, 0, 2], [1, 1, 9], [2, 0, 2], [2, 2, 4]]),]
    edges = [([7], [[2, 0, 0], [1, 0, 2], [2, 0, 0]]), ([2, 2], [[1, 0, 1]])]

    def ref(prices: List[int], queries: List[List[int]]) -> List[int]:
        n = len(prices)
        tree = [0] * n + prices[:]  # iterative segment tree: leaves at n..2n-1
        for i in range(n - 1, 0, -1):
            tree[i] = min(tree[2 * i], tree[2 * i + 1])
        out = []
        for t, a, b in queries:
            if t == 1:
                i = a + n
                tree[i] = b
                while i > 1:
                    i //= 2
                    tree[i] = min(tree[2 * i], tree[2 * i + 1])
            else:
                lo, hi, best = a + n, b + n + 1, float("inf")
                while lo < hi:
                    if lo & 1:
                        best = min(best, tree[lo])
                        lo += 1
                    if hi & 1:
                        hi -= 1
                        best = min(best, tree[hi])
                    lo //= 2
                    hi //= 2
                out.append(best)
        return out

    def brute(prices, queries):
        p, out = prices[:], []
        for t, a, b in queries:
            if t == 1:
                p[a] = b
            else:
                out.append(min(p[a:b + 1]))
        return out

    def gen(rng, big):
        n, q, V = (100000, 100000, 10**9) if big else (rng.randint(1, 6), rng.randint(1, 8), 9)
        qs = []
        for _ in range(q):
            if rng.random() < 0.5:
                qs.append([1, rng.randrange(n), rng.randint(1, V)])
            else:
                l, r = sorted((rng.randrange(n), rng.randrange(n)))
                qs.append([2, l, r])
        return [rng.randint(1, V) for _ in range(n)], qs


@problem
class GrandTour:
    title = "Grand Tour"
    difficulty = "Hard"
    func = "countTours"
    tl = 3.0
    statement = """
<p>There are <code>n</code> cities and one-way <code>flights</code> <code>[a, b]</code> (the same flight can be listed
more than once; each listing is a different flight). Count the routes that start in city <code>0</code>, end in city
<code>n - 1</code>, and visit <b>every</b> city exactly once. Return the count modulo <code>10^9 + 7</code>.</p>
<ul><li><code>2 &lt;= n &lt;= 13</code></li><li><code>0 &lt;= flights.length &lt;= 300</code>, <code>a != b</code></li></ul>"""
    hint = dict(pattern="Bitmask DP: ways[mask][v] = routes from 0 that visited exactly the cities in mask and stand at v",
                module="Gold: Bitmask DP", url="https://usaco.guide/gold/dp-bitmasks", similar="CSES Hamiltonian Flights (focus problem)")
    examples = [(4, [[0, 1], [0, 2], [1, 2], [1, 3], [2, 1], [2, 3]]), (3, [[0, 2], [2, 1]])]
    edges = [(2, [[0, 1], [0, 1]]), (2, [[1, 0]])]

    def ref(n: int, flights: List[List[int]]) -> int:
        MOD = 10**9 + 7
        into = [[] for _ in range(n)]  # into[v]: list of a with a flight a -> v (repeats kept)
        for a, b in flights:
            into[b].append(a)
        ways = [[0] * n for _ in range(1 << n)]
        ways[1][0] = 1
        last = 1 << (n - 1)
        for mask in range(1, 1 << n):
            if not mask & 1 or (mask & last and mask != (1 << n) - 1):
                continue  # routes start at 0, and reach n-1 only as the final city
            row = ways[mask]
            for v in range(1, n):
                if mask >> v & 1:
                    prev = ways[mask ^ (1 << v)]
                    total = 0
                    for a in into[v]:
                        total += prev[a]
                    row[v] = total % MOD
        return ways[(1 << n) - 1][n - 1]

    def brute(n, flights):
        from itertools import permutations
        cnt = Counter((a, b) for a, b in flights)
        total = 0
        for mid in permutations(range(1, n - 1)):
            route = (0, *mid, n - 1)
            ways = 1
            for a, b in zip(route, route[1:]):
                ways *= cnt[(a, b)]
            total += ways
        return total % MOD

    def gen(rng, big):
        n = 13 if big else rng.randint(2, 7)
        m = 300 if big else rng.randint(0, 14)
        return n, [rng.sample(range(n), 2) for _ in range(m)]


@problem
class CourierDistances:
    title = "Courier Distances"
    difficulty = "Medium"
    func = "distances"
    tl = 3.0
    statement = """
<p>A city's <code>n</code> depots are connected by <code>n - 1</code> two-way roads <code>edges</code> forming a tree,
each one block long. For each query <code>[u, v]</code>, return the number of blocks between depots <code>u</code> and
<code>v</code>.</p>
<ul><li><code>1 &lt;= n, queries.length &lt;= 10^5</code></li><li>The tree may be very deep.</li></ul>"""
    hint = dict(pattern="Lowest common ancestor by binary lifting: dist(u, v) = depth[u] + depth[v] - 2 * depth[lca(u, v)]",
                module="Gold: LCA with Euler Tour", url="https://usaco.guide/gold/lca-euler", similar="CSES Distance Queries (focus problem)")
    examples = [(5, [[0, 1], [0, 2], [2, 3], [2, 4]], [[0, 3], [1, 4], [3, 4], [2, 2]]),]
    edges = [(1, [], [[0, 0]]), (2, [[1, 0]], [[0, 1], [1, 0]])]

    def ref(n: int, edges: List[List[int]], queries: List[List[int]]) -> List[int]:
        adj = [[] for _ in range(n)]
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        LOG = max(1, n.bit_length())
        up = [[0] * n for _ in range(LOG)]  # up[k][v]: 2^k-th ancestor (root points to itself)
        depth, seen, order = [0] * n, [False] * n, [0]
        seen[0] = True
        for u in order:
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    up[0][v], depth[v] = u, depth[u] + 1
                    order.append(v)
        for k in range(1, LOG):
            prev, cur = up[k - 1], up[k]
            for v in range(n):
                cur[v] = prev[prev[v]]

        def lca(u, v):
            if depth[u] < depth[v]:
                u, v = v, u
            diff, k = depth[u] - depth[v], 0
            while diff:
                if diff & 1:
                    u = up[k][u]
                diff >>= 1
                k += 1
            if u == v:
                return u
            for k in range(LOG - 1, -1, -1):
                if up[k][u] != up[k][v]:
                    u, v = up[k][u], up[k][v]
            return up[0][u]

        return [depth[u] + depth[v] - 2 * depth[lca(u, v)] for u, v in queries]

    def brute(n, edges, queries):
        adj = defaultdict(list)
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        out = []
        for u, v in queries:
            dist, q = {u: 0}, deque([u])
            while q:
                x = q.popleft()
                for y in adj[x]:
                    if y not in dist:
                        dist[y] = dist[x] + 1
                        q.append(y)
            out.append(dist[v])
        return out

    def gen(rng, big):
        n, q = (100000, 100000) if big else (rng.randint(1, 9), rng.randint(1, 5))
        path = big and rng.random() < 0.5
        label = list(range(n))
        rng.shuffle(label)
        edges = [[label[i - 1 if path else rng.randrange(i)], label[i]] for i in range(1, n)]
        rng.shuffle(edges)
        return n, edges, [[rng.randrange(n), rng.randrange(n)] for _ in range(q)]


# ================================================================ starred: arrays, prefix sums, two pointers

@problem
class RangeSums:
    title = "Range Sums"
    difficulty = "Easy"
    func = "rangeSums"
    statement = """
<p>Given an array <code>nums</code> and queries <code>[l, r]</code>, return the sum of <code>nums[l..r]</code>
(inclusive) for each query.</p>
<ul><li><code>1 &lt;= nums.length, queries.length &lt;= 10^5</code></li><li><code>-10^9 &lt;= nums[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Prefix sums: prefix[i] = sum of the first i numbers; a range sum is prefix[r + 1] - prefix[l]",
                module="Silver: Introduction to Prefix Sums", url="https://usaco.guide/silver/prefix-sums",
                similar="Yosupo Static Range Sum (focus problem) · LeetCode 303")
    examples = [([1, 3, 2, 7, 4], [[0, 4], [1, 3], [2, 2]]),]
    edges = [([5], [[0, 0]]), ([-1, 1], [[0, 1], [1, 1]])]

    def ref(nums: List[int], queries: List[List[int]]) -> List[int]:
        prefix = [0]
        for x in nums:
            prefix.append(prefix[-1] + x)
        return [prefix[r + 1] - prefix[l] for l, r in queries]

    def brute(nums, queries):
        return [sum(nums[l:r + 1]) for l, r in queries]

    def gen(rng, big):
        n, q, V = (100000, 100000, 10**9) if big else (rng.randint(1, 8), rng.randint(1, 5), 9)
        return [rng.randint(-V, V) for _ in range(n)], [sorted((rng.randrange(n), rng.randrange(n))) for _ in range(q)]


@problem
class BestStreak:
    title = "Best Streak"
    difficulty = "Easy"
    func = "bestStreak"
    statement = """
<p>A trader logs daily profit and loss as <code>days</code>. Return the largest total of any <b>non-empty</b> run of
consecutive days.</p>
<ul><li><code>1 &lt;= days.length &lt;= 10^5</code></li><li><code>-10^9 &lt;= days[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Kadane's algorithm, or: best = max over r of prefix[r] - (smallest prefix before r)",
                module="Silver: More on Prefix Sums", url="https://usaco.guide/silver/more-prefix-sums",
                similar="CSES Maximum Subarray Sum (focus problem) · LeetCode 53")
    examples = [([-1, 3, -2, 5, 3, -5, 2, 2],), ([-4, -2, -7],)]
    edges = [([5],), ([0, 0],)]

    def ref(days: List[int]) -> int:
        best, cur = days[0], 0
        for x in days:
            cur = max(x, cur + x)
            best = max(best, cur)
        return best

    def brute(days):
        return max(sum(days[i:j]) for i in range(len(days)) for j in range(i + 1, len(days) + 1))

    def gen(rng, big):
        if big:
            return ([rng.randint(-10**9, 10**9) for _ in range(100000)],)
        return ([rng.randint(-6, 6) for _ in range(rng.randint(1, 9))],)


@problem
class FairStretches:
    title = "Fair Stretches"
    difficulty = "Medium"
    func = "countFair"
    statement = """
<p>A string <code>digits</code> contains only characters <code>'0'</code> to <code>'9'</code>. A substring is
<b>fair</b> if the sum of its digits equals its length. Count the fair substrings (substrings at different positions
are counted separately).</p>
<ul><li><code>1 &lt;= digits.length &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="Subtract 1 from every digit: a fair substring then sums to 0, so count equal prefix sums with a hash map",
                module="Silver: Introduction to Prefix Sums", url="https://usaco.guide/silver/prefix-sums", similar="CF Good Subarrays ★")
    examples = [("120",), ("11011",), ("600005",)]
    edges = [("1",), ("0",), ("111",)]

    def ref(digits: str) -> int:
        seen, s, total = Counter({0: 1}), 0, 0
        for ch in digits:
            s += int(ch) - 1
            total += seen[s]
            seen[s] += 1
        return total

    def brute(digits):
        n = len(digits)
        return sum(sum(map(int, digits[i:j])) == j - i for i in range(n) for j in range(i + 1, n + 1))

    def gen(rng, big):
        if big:
            return ("".join(rng.choice("0112") for _ in range(100000)),)
        return ("".join(rng.choice("0123") for _ in range(rng.randint(1, 10))),)


@problem
class ScenicRun:
    title = "Scenic Run"
    difficulty = "Medium"
    func = "bestRun"
    statement = """
<p>Sights along a road are one mile apart; sight <code>i</code> has beauty <code>beauty[i]</code>. You run from sight
<code>l</code> to sight <code>r</code> (<code>l &lt; r</code>) and visit the <b>three</b> most beautiful sights on that
stretch. Your score is the sum of those three beauties minus the distance <code>r - l</code>. Return the best score.</p>
<ul><li><code>3 &lt;= beauty.length &lt;= 10^5</code></li><li><code>1 &lt;= beauty[i] &lt;= 10^8</code></li></ul>"""
    hint = dict(pattern="The run starts and ends at chosen sights i < j < k: score = (b[i] + i) + b[j] + (b[k] - k); fix j, use prefix/suffix maxima",
                module="Silver: Introduction to Prefix Sums", url="https://usaco.guide/silver/prefix-sums", similar="CF Running Miles ★")
    examples = [([5, 1, 4, 2, 3],), ([1, 1, 1],)]
    edges = [([9, 9, 9],), ([1, 100, 1, 1, 100, 1, 100],)]

    def ref(beauty: List[int]) -> int:
        n = len(beauty)
        left, best_left = [0] * n, float("-inf")
        for i in range(n):
            left[i] = best_left  # best b[a] + a with a < i
            best_left = max(best_left, beauty[i] + i)
        best, best_right = float("-inf"), float("-inf")
        for j in range(n - 1, -1, -1):
            if 0 < j < n - 1:
                best = max(best, left[j] + beauty[j] + best_right)
            best_right = max(best_right, beauty[j] - j)  # best b[c] - c with c > j (for the next j)
        return best

    def brute(beauty):
        n = len(beauty)
        return max(beauty[i] + beauty[j] + beauty[k] - (k - i) for i in range(n) for j in range(i + 1, n) for k in range(j + 1, n))

    def gen(rng, big):
        if big:
            return ([rng.randint(1, 10**8) for _ in range(100000)],)
        return ([rng.randint(1, 9) for _ in range(rng.randint(3, 9))],)


@problem
class EvenDigits:
    title = "Even Digits"
    difficulty = "Medium"
    func = "countEven"
    statement = """
<p>A string <code>s</code> contains only digits. Count its substrings in which <b>every</b> digit occurs an even number
of times (zero counts as even). Substrings at different positions are counted separately.</p>
<ul><li><code>1 &lt;= s.length &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="Prefix XOR of a 10-bit parity mask: a substring works exactly when its two prefix masks are equal",
                module="Silver: Intro to Bitwise Operators", url="https://usaco.guide/silver/intro-bitwise", similar="AtCoder Three Days Ago ★")
    examples = [("20230322",), ("0112",)]
    edges = [("7",), ("77",), ("1212",)]

    def ref(s: str) -> int:
        seen, mask, total = Counter({0: 1}), 0, 0
        for ch in s:
            mask ^= 1 << (ord(ch) - 48)
            total += seen[mask]
            seen[mask] += 1
        return total

    def brute(s):
        n = len(s)
        return sum(all(v % 2 == 0 for v in Counter(s[i:j]).values()) for i in range(n) for j in range(i + 1, n + 1))

    def gen(rng, big):
        if big:
            return ("".join(rng.choice("0123456789") for _ in range(100000)),)
        return ("".join(rng.choice("012") for _ in range(rng.randint(1, 10))),)


@problem
class PaintLayers:
    title = "Paint Layers"
    difficulty = "Medium"
    func = "areaWithCoats"
    statement = """
<p>A wall is a grid of unit squares. Each painted rectangle <code>[x1, y1, x2, y2]</code> adds one coat of paint to
every unit square with <code>x1 &lt;= x &lt; x2</code> and <code>y1 &lt;= y &lt; y2</code>. Return the total area that ends up with
<b>exactly</b> <code>k</code> coats.</p>
<ul><li><code>1 &lt;= rects.length &lt;= 10^5</code></li><li><code>0 &lt;= x1 &lt; x2 &lt;= 500</code>, <code>0 &lt;= y1 &lt; y2 &lt;= 500</code></li>
<li><code>1 &lt;= k &lt;= rects.length</code></li></ul>"""
    hint = dict(pattern="2-D difference array: +1 at (x1, y1) and (x2, y2), -1 at (x1, y2) and (x2, y1), then a 2-D prefix sum",
                module="Silver: More on Prefix Sums", url="https://usaco.guide/silver/more-prefix-sums", similar="USACO Painting the Barn ★")
    examples = [([[1, 1, 5, 5], [4, 4, 7, 6], [3, 3, 8, 7]], 2),]
    edges = [([[0, 0, 1, 1]], 1), ([[0, 0, 2, 2], [0, 0, 2, 2]], 1)]

    def ref(rects: List[List[int]], k: int) -> int:
        W = 501
        diff = [[0] * (W + 1) for _ in range(W + 1)]
        for x1, y1, x2, y2 in rects:
            diff[x1][y1] += 1
            diff[x1][y2] -= 1
            diff[x2][y1] -= 1
            diff[x2][y2] += 1
        area = 0
        for x in range(W):
            row, above = diff[x], diff[x - 1] if x else None
            for y in range(W):
                v = row[y] + (above[y] if above else 0) + (row[y - 1] if y else 0) - (above[y - 1] if above and y else 0)
                row[y] = v
                area += v == k
        return area

    def brute(rects, k):
        coats = Counter()
        for x1, y1, x2, y2 in rects:
            for x in range(x1, x2):
                for y in range(y1, y2):
                    coats[(x, y)] += 1
        return sum(v == k for v in coats.values())

    def gen(rng, big):
        n, C = (100000, 500) if big else (rng.randint(1, 5), 6)
        rects = []
        for _ in range(n):
            x1, x2 = sorted(rng.sample(range(C + 1), 2))
            y1, y2 = sorted(rng.sample(range(C + 1), 2))
            rects.append([x1, y1, x2, y2])
        return rects, rng.randint(1, n if not big else 50)


@problem
class TwoGifts:
    title = "Two Gifts"
    difficulty = "Easy"
    func = "twoGifts"
    statement = """
<p>A shop lists gift prices <code>prices</code>. Return the indices of two <b>different</b> gifts whose prices add up to
exactly <code>budget</code> (in any order), or an empty list if there are none. Any valid pair is accepted.</p>
<ul><li><code>1 &lt;= prices.length &lt;= 10^5</code></li><li><code>1 &lt;= prices[i], budget &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Sort indices by price and move two pointers inward (or use a hash map of seen prices)",
                module="Silver: Two Pointers", url="https://usaco.guide/silver/two-pointers",
                similar="CSES Sum of Two Values (focus problem) · LeetCode 1 / 167")
    examples = [([2, 7, 5, 1], 8), ([4, 4], 9)]
    edges = [([5], 10), ([5, 5], 10)]

    def ref(prices: List[int], budget: int) -> List[int]:
        seen = {}
        for i, p in enumerate(prices):
            if budget - p in seen:
                return [seen[budget - p], i]
            seen.setdefault(p, i)
        return []

    def brute(prices, budget):
        return next(([i, j] for i, j in combinations(range(len(prices)), 2) if prices[i] + prices[j] == budget), [])

    def check(args, out, expected):
        prices, budget = args
        if not expected:
            return out == []
        return (isinstance(out, list) and len(out) == 2 and all(type(i) is int and 0 <= i < len(prices) for i in out)
                and out[0] != out[1] and prices[out[0]] + prices[out[1]] == budget)

    def gen(rng, big):
        n, V = (100000, 10**9) if big else (rng.randint(1, 7), 9)
        prices = [rng.randint(1, V) for _ in range(n)]
        budget = prices[0] + prices[-1] if n > 1 and rng.random() < 0.5 else rng.randint(1, 2 * V)
        return prices, budget


@problem
class ReadingMarathon:
    title = "Reading Marathon"
    difficulty = "Easy"
    func = "maxBooks"
    statement = """
<p>Books on a shelf take <code>minutes[i]</code> minutes each to read. You have <code>free</code> minutes. Starting at any
book, you read books one after another along the shelf, and only count books you finish. Return the most books you can
finish.</p>
<ul><li><code>1 &lt;= minutes.length &lt;= 10^5</code></li><li><code>1 &lt;= minutes[i] &lt;= 10^4</code>, <code>1 &lt;= free &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Sliding window over positive numbers: extend right, shrink left while the window's total exceeds the time",
                module="Silver: Two Pointers", url="https://usaco.guide/silver/two-pointers", similar="CF Books (focus problem) · LeetCode 209")
    examples = [([3, 1, 2, 1], 5), ([2, 2, 3], 1)]
    edges = [([4], 4), ([1, 1, 1], 100)]

    def ref(minutes: List[int], free: int) -> int:
        left = total = best = 0
        for right, m in enumerate(minutes):
            total += m
            while total > free:
                total -= minutes[left]
                left += 1
            best = max(best, right - left + 1)
        return best

    def brute(minutes, free):
        n = len(minutes)
        return max([j - i for i in range(n) for j in range(i, n + 1) if sum(minutes[i:j]) <= free])

    def gen(rng, big):
        if big:
            return [rng.randint(1, 10**4) for _ in range(100000)], rng.randint(1, 10**8)
        return [rng.randint(1, 5) for _ in range(rng.randint(1, 8))], rng.randint(1, 12)


@problem
class ThreeGifts:
    title = "Three Gifts"
    difficulty = "Medium"
    func = "threeGifts"
    statement = """
<p>A shop lists gift prices <code>prices</code>. Return the indices of three <b>different</b> gifts whose prices add up
to exactly <code>budget</code> (in any order), or an empty list if there are none. Any valid triple is accepted.</p>
<ul><li><code>1 &lt;= prices.length &lt;= 1500</code></li><li><code>1 &lt;= prices[i], budget &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Sort indices by price; fix the first gift, then two pointers on the rest: O(n^2)",
                module="Silver: Two Pointers", url="https://usaco.guide/silver/two-pointers", similar="CSES Sum of Three Values ★ · LeetCode 15")
    examples = [([2, 7, 5, 1], 8), ([1, 2, 3], 7)]
    edges = [([3, 3], 9), ([3, 3, 3], 9)]

    def ref(prices: List[int], budget: int) -> List[int]:
        idx = sorted(range(len(prices)), key=prices.__getitem__)
        p = [prices[i] for i in idx]
        n = len(p)
        for a in range(n - 2):
            need, lo, hi = budget - p[a], a + 1, n - 1
            while lo < hi:
                s = p[lo] + p[hi]
                if s == need:
                    return [idx[a], idx[lo], idx[hi]]
                if s < need:
                    lo += 1
                else:
                    hi -= 1
        return []

    def brute(prices, budget):
        return next((list(t) for t in combinations(range(len(prices)), 3) if sum(prices[i] for i in t) == budget), [])

    def check(args, out, expected):
        prices, budget = args
        if not expected:
            return out == []
        return (isinstance(out, list) and len(out) == 3 and len(set(out)) == 3
                and all(type(i) is int and 0 <= i < len(prices) for i in out) and sum(prices[i] for i in out) == budget)

    def gen(rng, big):
        n, V = (1500, 10**9) if big else (rng.randint(1, 7), 9)
        prices = [rng.randint(1, V) for _ in range(n)]
        budget = rng.randint(3, 3 * V) if big and rng.random() < 0.5 else (sum(rng.sample(prices, 3)) if n >= 3 and rng.random() < 0.5 else rng.randint(1, 3 * V))
        return prices, budget


@problem
class TwoShowcases:
    title = "Two Showcases"
    difficulty = "Medium"
    func = "maxDiamonds"
    statement = """
<p>A jeweler has diamonds with sizes <code>sizes</code> and two display cases. Within one case, the largest and smallest
diamond may differ in size by at most <code>k</code>. Each diamond goes in at most one case. Return the most diamonds
that can be displayed.</p>
<ul><li><code>1 &lt;= sizes.length &lt;= 10^5</code></li><li><code>0 &lt;= sizes[i], k &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Sort; two pointers give the best window ending at or before i and starting at or after i+1; combine prefix and suffix maxima",
                module="Silver: Two Pointers", url="https://usaco.guide/silver/two-pointers", similar="USACO Diamond Collector ★")
    examples = [([1, 6, 4, 3, 1], 3), ([10, 1, 20], 0)]
    edges = [([5], 0), ([1, 1, 1, 1], 0)]

    def ref(sizes: List[int], k: int) -> int:
        s, n = sorted(sizes), len(sizes)
        best_upto, left = [0] * n, 0  # best_upto[i]: largest window inside s[0..i]
        for i in range(n):
            while s[i] - s[left] > k:
                left += 1
            best_upto[i] = max(i - left + 1, best_upto[i - 1] if i else 0)
        best, from_right, right = best_upto[-1], 0, n - 1
        for i in range(n - 1, 0, -1):  # window starting at i, combined with the best one before i
            while s[right] - s[i] > k:
                right -= 1
            from_right = max(from_right, right - i + 1)
            best = max(best, best_upto[i - 1] + from_right)
        return best

    def brute(sizes, k):
        from itertools import product
        best = 0
        for put in product(range(3), repeat=len(sizes)):  # 0 = not shown, 1 / 2 = case
            ok = all(max(c) - min(c) <= k for c in ([x for x, w in zip(sizes, put) if w == j] for j in (1, 2)) if c)
            if ok:
                best = max(best, sum(w > 0 for w in put))
        return best

    def gen(rng, big):
        if big:
            return [rng.randint(0, 10**9) for _ in range(100000)], rng.randint(0, 10**7)
        return [rng.randint(0, 9) for _ in range(rng.randint(1, 7))], rng.randint(0, 4)


@problem
class WindowPeaks:
    title = "Window Peaks"
    difficulty = "Medium"
    func = "windowMax"
    statement = """
<p>Given readings <code>nums</code> and a window size <code>k</code>, return the maximum of every window of
<code>k</code> consecutive readings, from left to right.</p>
<ul><li><code>1 &lt;= k &lt;= nums.length &lt;= 10^5</code></li><li><code>-10^9 &lt;= nums[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Monotonic deque of indices with decreasing values; the front is the window max",
                module="Gold: Sliding Window", url="https://usaco.guide/gold/sliding-window",
                similar="LeetCode 239 Sliding Window Maximum (focus problem)")
    examples = [([1, 3, -1, -3, 5, 3, 6, 7], 3), ([4, 2], 1)]
    edges = [([9], 1), ([1, 2, 3], 3)]

    def ref(nums: List[int], k: int) -> List[int]:
        dq, out = deque(), []
        for i, x in enumerate(nums):
            while dq and nums[dq[-1]] <= x:
                dq.pop()
            dq.append(i)
            if dq[0] <= i - k:
                dq.popleft()
            if i >= k - 1:
                out.append(nums[dq[0]])
        return out

    def brute(nums, k):
        return [max(nums[i:i + k]) for i in range(len(nums) - k + 1)]

    def gen(rng, big):
        n = 100000 if big else rng.randint(1, 9)
        V = 10**9 if big else 9
        return [rng.randint(-V, V) for _ in range(n)], rng.randint(1, n if not big else 5000)


# ================================================================ starred: sorting, greedy, priority queues, sorted sets

@problem
class StudyPlan:
    title = "Study Plan"
    difficulty = "Easy"
    func = "maxTopics"
    statement = """
<p>Topic <code>i</code> takes <code>hours[i]</code> hours to learn, and you have <code>budget</code> hours. Return the
largest number of topics you can learn.</p>
<ul><li><code>1 &lt;= hours.length &lt;= 10^5</code></li><li><code>1 &lt;= hours[i], budget &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Greedy: learn the quickest topics first (sort, then take while the total fits)",
                module="Silver: Greedy Algorithms with Sorting", url="https://usaco.guide/silver/greedy-sorting",
                similar="CF Studying Algorithms (focus problem)")
    examples = [([4, 3, 1, 4], 8), ([10], 5)]
    edges = [([5], 5), ([1, 1, 1], 100)]

    def ref(hours: List[int], budget: int) -> int:
        count = 0
        for h in sorted(hours):
            if h > budget:
                break
            budget -= h
            count += 1
        return count

    def brute(hours, budget):
        n = len(hours)
        return max(bin(m).count("1") for m in range(1 << n) if sum(hours[i] for i in range(n) if m >> i & 1) <= budget)

    def gen(rng, big):
        if big:
            return [rng.randint(1, 10**9) for _ in range(100000)], rng.randint(1, 10**12 // 20)
        return [rng.randint(1, 6) for _ in range(rng.randint(1, 8))], rng.randint(1, 15)


@problem
class AssignmentRush:
    title = "Assignment Rush"
    difficulty = "Easy"
    func = "maxScore"
    statement = """
<p>You must finish every assignment, one at a time, starting at time 0. Assignment <code>[duration, deadline]</code>
scores <code>deadline - finish_time</code> points (negative if late). Choose the order that maximizes your total
score and return it.</p>
<ul><li><code>1 &lt;= tasks.length &lt;= 10^5</code></li><li><code>1 &lt;= duration, deadline &lt;= 10^6</code></li></ul>"""
    hint = dict(pattern="Deadlines add up the same in any order; minimize the sum of finish times by doing the shortest tasks first",
                module="Silver: Greedy Algorithms with Sorting", url="https://usaco.guide/silver/greedy-sorting", similar="CSES Tasks & Deadlines ★")
    examples = [([[6, 10], [8, 15], [5, 12]],), ([[3, 1]],)]
    edges = [([[1, 1], [1, 1]],)]

    def ref(tasks: List[List[int]]) -> int:
        t = score = 0
        for d, dl in sorted(tasks):
            t += d
            score += dl - t
        return score

    def brute(tasks):
        from itertools import permutations
        best = None
        for order in permutations(tasks):
            t = s = 0
            for d, dl in order:
                t += d
                s += dl - t
            best = s if best is None else max(best, s)
        return best

    def gen(rng, big):
        n, V = (100000, 10**6) if big else (rng.randint(1, 6), 9)
        return ([[rng.randint(1, V), rng.randint(1, V)] for _ in range(n)],)


@problem
class SkylineTowers:
    title = "Block Towers"
    difficulty = "Medium"
    func = "minTowers"
    statement = """
<p>Blocks arrive one at a time with sizes <code>blocks</code>. Each block must go either on top of an existing tower
whose top block is <b>strictly larger</b>, or on the floor to start a new tower. Return the fewest towers possible.</p>
<ul><li><code>1 &lt;= blocks.length &lt;= 10^5</code></li><li><code>1 &lt;= blocks[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Keep tower tops in a sorted list; put each block on the tower with the smallest top that is larger (bisect_right)",
                module="Gold: More Operations on Sorted Sets", url="https://usaco.guide/gold/intro-sorted-sets", similar="CSES Towers ★")
    examples = [([3, 8, 2, 1, 5],), ([2, 2, 2],)]
    edges = [([7],), ([1, 2, 3],), ([3, 2, 1],)]

    def ref(blocks: List[int]) -> int:
        from bisect import bisect_right
        tops = []  # stays sorted: replacing tops[i] by a smaller-or-equal block keeps the order
        for b in blocks:
            i = bisect_right(tops, b)
            if i == len(tops):
                tops.append(b)
            else:
                tops[i] = b
        return len(tops)

    def brute(blocks):
        n = len(blocks)  # = longest non-decreasing subsequence (no two of them can share a tower)
        best = [1] * n
        for i in range(n):
            for j in range(i):
                if blocks[j] <= blocks[i]:
                    best[i] = max(best[i], best[j] + 1)
        return max(best)

    def gen(rng, big):
        if big:
            return ([rng.randint(1, 10**9) for _ in range(100000)],)
        return ([rng.randint(1, 5) for _ in range(rng.randint(1, 9))],)


@problem
class MountainSkyline:
    title = "Mountain Skyline"
    difficulty = "Medium"
    func = "visiblePeaks"
    statement = """
<p>Each mountain is a triangle with its peak at <code>[x, y]</code> and sides sloping down at 45 degrees to the ground,
so its base runs from <code>x - y</code> to <code>x + y</code>. A peak is <b>hidden</b> if it lies inside or on the edge
of another mountain (identical mountains hide each other). Return the number of visible peaks.</p>
<ul><li><code>1 &lt;= peaks.length &lt;= 10^5</code></li><li><code>0 &lt;= x, y &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Turn each mountain into a base interval [x - y, x + y]; a peak is hidden when another interval contains its interval. Sort by left end, larger right end first",
                module="Silver: Custom Comparators and Coordinate Compression", url="https://usaco.guide/silver/sorting-custom",
                similar="USACO Mountain View ★")
    examples = [([[4, 6], [7, 2], [2, 5]],), ([[1, 1], [1, 1]],)]
    edges = [([[5, 0]],), ([[0, 3], [10, 3]],)]

    def ref(peaks: List[List[int]]) -> int:
        iv = [(x - y, x + y) for x, y in peaks]
        dup = Counter(iv)
        visible, reach = 0, float("-inf")
        for l, r in sorted(iv, key=lambda t: (t[0], -t[1])):
            if r > reach and dup[(l, r)] == 1:
                visible += 1
            reach = max(reach, r)
        return visible

    def brute(peaks):
        iv = [(x - y, x + y) for x, y in peaks]
        return sum(not any(j != i and iv[j][0] <= iv[i][0] and iv[i][1] <= iv[j][1] for j in range(len(iv))) for i in range(len(iv)))

    def gen(rng, big):
        n, V = (100000, 10**9) if big else (rng.randint(1, 7), 6)
        return ([[rng.randint(0, V), rng.randint(0, V if not big else 10**6)] for _ in range(n)],)


@problem
class TastingLine:
    title = "Tasting Line"
    difficulty = "Medium"
    func = "longestWait"
    statement = """
<p>Guests arrive at a one-person tasting booth. Guest <code>i</code> arrives at <code>guests[i][0]</code> and spends
<code>guests[i][1]</code> minutes inside; a lower index means a more senior guest. When the booth is free, the most
senior guest who has already arrived (arrival time &lt;= now) goes in; if nobody is waiting, the booth stays empty until
the next arrival. Return the longest time any guest waits.</p>
<ul><li><code>1 &lt;= guests.length &lt;= 10^5</code></li><li><code>0 &lt;= arrival &lt;= 10^9</code>, <code>1 &lt;= minutes &lt;= 10^4</code></li></ul>"""
    hint = dict(pattern="Event simulation: sort by arrival, keep arrived guests in a min-heap keyed by seniority",
                module="Silver: Priority Queues", url="https://usaco.guide/silver/priority-queues", similar="USACO Convention II ★")
    examples = [([[25, 3], [105, 30], [20, 50], [10, 17], [100, 10], [10, 30]],), ([[0, 5]],)]
    edges = [([[5, 1], [5, 1]],), ([[0, 10], [1, 1], [2, 1]],)]

    def ref(guests: List[List[int]]) -> int:
        order = sorted(range(len(guests)), key=lambda i: (guests[i][0], i))
        heap, now, nxt, worst = [], 0, 0, 0
        while nxt < len(order) or heap:
            if not heap and guests[order[nxt]][0] > now:
                now = guests[order[nxt]][0]
            while nxt < len(order) and guests[order[nxt]][0] <= now:
                heappush(heap, order[nxt])
                nxt += 1
            i = heappop(heap)
            worst = max(worst, now - guests[i][0])
            now += guests[i][1]
        return worst

    def brute(guests):
        left, now, worst = set(range(len(guests))), 0, 0
        while left:
            ready = [i for i in left if guests[i][0] <= now]
            if not ready:
                now = min(guests[i][0] for i in left)
                continue
            i = min(ready)
            worst = max(worst, now - guests[i][0])
            now += guests[i][1]
            left.remove(i)
        return worst

    def gen(rng, big):
        n, T = (100000, 10**9) if big else (rng.randint(1, 7), 15)
        return ([[rng.randint(0, T), rng.randint(1, 10**4 if big else 6)] for _ in range(n)],)


@problem
class DairyDecisions:
    title = "Dairy Decisions"
    difficulty = "Medium"
    func = "maxProfit"
    statement = """
<p>A farmer has cows that each produce <code>milk[i]</code> gallons a day. Shops <code>[gallons, price]</code> each buy
up to <code>gallons</code> gallons at <code>price</code> per gallon. Neighbors each offer to rent one cow for
<code>rents[j]</code> a day. Every cow is either milked (its milk sold to shops) or rented to one neighbor. Return the
largest daily profit.</p>
<ul><li><code>1 &lt;= milk.length, shops.length, rents.length &lt;= 10^5</code></li><li>all values between <code>1</code> and <code>10^6</code></li></ul>"""
    hint = dict(pattern="Greedy with sorting: milk the best producers, rent out the rest to the highest bids; try every split point with prefix sums",
                module="Silver: Custom Comparators and Coordinate Compression", url="https://usaco.guide/silver/sorting-custom",
                similar="USACO Rental Service ★")
    examples = [([6, 2, 4, 7, 1], [[10, 25], [2, 15], [15, 26]], [250, 80, 100, 40]),]
    edges = [([5], [[10, 1]], [6]), ([5], [[10, 2]], [6])]

    def ref(milk: List[int], shops: List[List[int]], rents: List[int]) -> int:
        cows = sorted(milk, reverse=True)
        stores = sorted(shops, key=lambda s: -s[1])
        sell, si, left, earned = [0], 0, stores[0][0], 0  # sell[k]: revenue from milking the top k cows
        for m in cows:
            while m and si < len(stores):
                take = min(m, left)
                earned += take * stores[si][1]
                m -= take
                left -= take
                if not left:
                    si += 1
                    left = stores[si][0] if si < len(stores) else 0
            sell.append(earned)
        rent = [0]
        for r in sorted(rents, reverse=True):
            rent.append(rent[-1] + r)
        n = len(cows)
        return max(sell[k] + rent[min(n - k, len(rents))] for k in range(n + 1))

    def brute(milk, shops, rents):
        n, best = len(milk), 0
        for m in range(1 << n):
            gallons = sum(milk[i] for i in range(n) if m >> i & 1)
            renters = n - bin(m).count("1")
            income = sum(sorted(rents, reverse=True)[:renters])
            for g, p in sorted(shops, key=lambda s: -s[1]):
                take = min(g, gallons)
                income += take * p
                gallons -= take
            best = max(best, income)
        return best

    def gen(rng, big):
        n, s, r, V = (100000, 100000, 100000, 10**6) if big else (rng.randint(1, 6), rng.randint(1, 3), rng.randint(1, 4), 9)
        return ([rng.randint(1, V) for _ in range(n)], [[rng.randint(1, V), rng.randint(1, V)] for _ in range(s)],
                [rng.randint(1, V * (1 if big else 5)) for _ in range(r)])


@problem
class HighLow:
    title = "High-Low Showdown"
    difficulty = "Medium"
    func = "maxWins"
    statement = """
<p>Cards numbered <code>1</code> to <code>2n</code> are split between two players. Your opponent will play their
<code>n</code> cards in the order given by <code>opponent</code>; you hold the other <code>n</code> cards and know that
order. Each round you play one card. In the first <code>n / 2</code> rounds the <b>higher</b> card wins; in the last
<code>n / 2</code> rounds the <b>lower</b> card wins. Return the most rounds you can win.</p>
<ul><li><code>2 &lt;= n &lt;= 10^5</code>, <code>n</code> is even</li></ul>"""
    hint = dict(pattern="Save your top n/2 cards for the high rounds and the rest for the low rounds, then greedily match each half with sorted two pointers",
                module="Silver: Greedy Algorithms with Sorting", url="https://usaco.guide/silver/greedy-sorting", similar="USACO High Card Low Card ★")
    examples = [([1, 8, 4, 3],), ([2, 3],)]
    edges = [([1, 2],), ([4, 3],)]

    def ref(opponent: List[int]) -> int:
        n = len(opponent)
        mine = sorted(set(range(1, 2 * n + 1)) - set(opponent))
        high, low, half = mine[n // 2:], mine[:n // 2], n // 2
        wins, j = 0, 0
        for e in sorted(opponent[:half]):  # beat each card with the smallest bigger card we still have
            while j < half and high[j] < e:
                j += 1
            if j == half:
                break
            wins += 1
            j += 1
        j = half - 1
        for e in sorted(opponent[half:], reverse=True):  # undercut with the largest smaller card
            while j >= 0 and low[j] > e:
                j -= 1
            if j < 0:
                break
            wins += 1
            j -= 1
        return wins

    def brute(opponent):
        from itertools import permutations
        n = len(opponent)
        mine = sorted(set(range(1, 2 * n + 1)) - set(opponent))
        return max(sum((m > e) if r < n // 2 else (m < e) for r, (m, e) in enumerate(zip(order, opponent)))
                   for order in permutations(mine))

    def gen(rng, big):
        n = 100000 if big else rng.choice([2, 4, 6])
        cards = list(range(1, 2 * n + 1))
        rng.shuffle(cards)
        return (cards[:n],)


@problem
class StreetLights:
    title = "Street Lights"
    difficulty = "Medium"
    func = "darkestStretch"
    statement = """
<p>A street runs from position <code>0</code> to <code>length</code>. Street lights are installed one at a time at
distinct positions <code>lights</code> (strictly between 0 and <code>length</code>). After each installation, report the
length of the longest stretch of street with no light inside it (the ends of the street count as boundaries).</p>
<ul><li><code>1 &lt;= lights.length &lt;= 10^5</code></li><li><code>2 &lt;= length &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Sorted set of lights + a multiset of gap lengths (heap with lazy deletion); or process offline in reverse with a linked list",
                module="Gold: More Operations on Sorted Sets", url="https://usaco.guide/gold/intro-sorted-sets", similar="CSES Traffic Lights ★")
    examples = [(8, [3, 6, 2]), (10, [5])]
    edges = [(2, [1]), (5, [1, 2, 3, 4])]

    def ref(length: int, lights: List[int]) -> List[int]:
        pts = sorted([0, length] + lights)
        prev = {pts[i]: pts[i - 1] for i in range(1, len(pts))}
        nxt = {pts[i]: pts[i + 1] for i in range(len(pts) - 1)}
        best = max(b - a for a, b in zip(pts, pts[1:]))
        out = [0] * len(lights)
        for i in range(len(lights) - 1, -1, -1):  # removing lights in reverse only merges gaps
            out[i] = best
            p = lights[i]
            a, b = prev[p], nxt[p]
            nxt[a], prev[b] = b, a
            best = max(best, b - a)
        return out

    def brute(length, lights):
        out = []
        for i in range(len(lights)):
            pts = sorted([0, length] + lights[:i + 1])
            out.append(max(b - a for a, b in zip(pts, pts[1:])))
        return out

    def gen(rng, big):
        length = 10**9 if big else rng.randint(2, 12)
        n = 100000 if big else rng.randint(1, length - 1)
        return length, rng.sample(range(1, length), n)


@problem
class ScreeningRooms:
    title = "Screening Rooms"
    difficulty = "Hard"
    func = "maxScreenings"
    statement = """
<p>A club of <code>k</code> friends wants to watch as many festival movies as possible in total. Movie
<code>[start, end]</code> must be watched from start to end by one friend; a friend can start a movie at the moment their
previous one ends. Return the largest total number of movies the club can watch.</p>
<ul><li><code>1 &lt;= movies.length &lt;= 10^5</code></li><li><code>1 &lt;= k &lt;= 1000</code></li><li><code>0 &lt;= start &lt; end &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Sort by end time; give each movie to the friend who became free most recently but still in time (largest free time <= start), via a sorted list",
                module="Gold: More Operations on Sorted Sets", url="https://usaco.guide/gold/intro-sorted-sets", similar="CSES Movie Festival II ★")
    examples = [([[1, 5], [8, 10], [3, 6], [2, 5], [6, 9]], 2), ([[0, 4], [1, 3]], 1)]
    edges = [([[0, 1]], 3), ([[0, 2], [0, 2], [0, 2]], 2)]

    def ref(movies: List[List[int]], k: int) -> int:
        from bisect import bisect_right, insort
        free, watched = [-1] * k, 0
        for s, e in sorted(movies, key=lambda m: m[1]):
            i = bisect_right(free, s) - 1
            if i >= 0:
                free.pop(i)
                insort(free, e)
                watched += 1
        return watched

    def brute(movies, k):
        n, best = len(movies), 0
        for m in range(1 << n):
            pick = [movies[i] for i in range(n) if m >> i & 1]
            events = sorted([(s, 1) for s, _ in pick] + [(e, -1) for _, e in pick])
            cur = peak = 0
            for _, d in events:
                cur += d
                peak = max(peak, cur)
            if peak <= k:
                best = max(best, len(pick))
        return best

    def gen(rng, big):
        n, T = (100000, 10**9) if big else (rng.randint(1, 8), 10)
        out = []
        for _ in range(n):
            s = rng.randint(0, T - 1)
            out.append([s, rng.randint(s + 1, min(T, s + (T // 2000 if big else 5)))])
        return out, rng.randint(1, 1000 if big else 3)


# ================================================================ starred: graphs

def _find(parent, x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def _components(n, pairs):
    """Component label per node, by plain BFS (used by brute forces)."""
    adj = defaultdict(list)
    for a, b in pairs:
        adj[a].append(b)
        adj[b].append(a)
    comp = [-1] * n
    for s in range(n):
        if comp[s] == -1:
            comp[s], q = s, [s]
            for u in q:
                for v in adj[u]:
                    if comp[v] == -1:
                        comp[v] = s
                        q.append(v)
    return comp


@problem
class CountingRooms:
    title = "Counting Rooms"
    difficulty = "Easy"
    func = "countRooms"
    statement = """
<p>A building map is a list of strings: <code>'.'</code> is floor and <code>'#'</code> is wall. A room is a group of
floor cells connected up/down/left/right. Return the number of rooms.</p>
<ul><li><code>1 &lt;= rows * cols &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="Flood fill (iterative BFS/DFS) from every unvisited floor cell",
                module="Silver: Flood Fill", url="https://usaco.guide/silver/flood-fill", similar="CSES Counting Rooms (focus problem) · LeetCode 200")
    examples = [(["########", "#..#...#", "####.#.#", "#..#...#", "########"],), (["#.#"],)]
    edges = [(["."],), (["#"],)]

    def ref(grid: List[str]) -> int:
        m, n = len(grid), len(grid[0])
        seen, rooms = [[False] * n for _ in range(m)], 0
        for si in range(m):
            for sj in range(n):
                if grid[si][sj] == "." and not seen[si][sj]:
                    rooms += 1
                    seen[si][sj], stack = True, [(si, sj)]
                    while stack:
                        i, j = stack.pop()
                        for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                            if 0 <= a < m and 0 <= b < n and grid[a][b] == "." and not seen[a][b]:
                                seen[a][b] = True
                                stack.append((a, b))
        return rooms

    def brute(grid):
        m, n = len(grid), len(grid[0])
        cells = [(i, j) for i in range(m) for j in range(n) if grid[i][j] == "."]
        idx = {c: k for k, c in enumerate(cells)}
        pairs = [(idx[(i, j)], idx[(a, b)]) for (i, j) in cells for a, b in ((i + 1, j), (i, j + 1)) if (a, b) in idx]
        return len(set(_components(len(cells), pairs)))

    def gen(rng, big):
        m, n = (300, 333) if big else (rng.randint(1, 5), rng.randint(1, 5))
        return (["".join("#" if rng.random() < 0.45 else "." for _ in range(n)) for _ in range(m)],)


@problem
class UnionQueries:
    title = "Friend Groups"
    difficulty = "Easy"
    func = "processQueries"
    statement = """
<p>There are <code>n</code> people and no friendships yet. Process <code>queries</code> in order:
<code>[0, u, v]</code> makes <code>u</code> and <code>v</code> friends; <code>[1, u, v]</code> asks whether <code>u</code>
and <code>v</code> are in the same friend group (connected through friendships). Return <code>1</code> or
<code>0</code> for each type-1 query.</p>
<ul><li><code>1 &lt;= n, queries.length &lt;= 2 * 10^5</code></li></ul>"""
    hint = dict(pattern="Union-find with path compression (and union by size)",
                module="Gold: Disjoint Set Union", url="https://usaco.guide/gold/dsu", similar="Yosupo Union Find (focus problem)")
    examples = [(4, [[1, 0, 1], [0, 0, 1], [0, 2, 3], [1, 0, 1], [1, 1, 2], [0, 1, 3], [1, 0, 3]]),]
    edges = [(1, [[1, 0, 0]]), (2, [[0, 0, 1], [0, 1, 0], [1, 1, 0]])]

    def ref(n: int, queries: List[List[int]]) -> List[int]:
        def find(x):  # root with path halving
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        parent, out = list(range(n)), []
        for t, u, v in queries:
            ru, rv = find(u), find(v)
            if t == 0:
                parent[ru] = rv
            else:
                out.append(int(ru == rv))
        return out

    def brute(n, queries):
        label, out = list(range(n)), []
        for t, u, v in queries:
            if t == 0:
                old, new = label[u], label[v]
                label = [new if x == old else x for x in label]
            else:
                out.append(int(label[u] == label[v]))
        return out

    def gen(rng, big):
        n, q = (200000, 200000) if big else (rng.randint(1, 6), rng.randint(1, 8))
        return n, [[rng.randint(0, 1), rng.randrange(n), rng.randrange(n)] for _ in range(q)]


@problem
class DoubleVisit:
    title = "Blame Game"
    difficulty = "Easy"
    func = "secondVisit"
    statement = """
<p>Each student <code>i</code>, when questioned, blames student <code>blames[i]</code>. The teacher starts with some
student, marks them, and moves on to whoever they blame, again and again, until reaching a student who is already
marked. For every possible starting student, return the student who gets marked twice.</p>
<ul><li><code>1 &lt;= blames.length &lt;= 10^5</code>; a student may blame themself</li></ul>"""
    hint = dict(pattern="Functional graph: every walk ends in a cycle. Cycle students answer themselves; everyone else answers what their target answers",
                module="Silver: Introduction to Functional Graphs", url="https://usaco.guide/silver/func-graphs", similar="CF Badge (focus problem)")
    examples = [([1, 2, 1],), ([0, 1, 2],)]
    edges = [([0],), ([1, 0],)]

    def ref(blames: List[int]) -> List[int]:
        n = len(blames)
        ans, state = [-1] * n, [0] * n  # 0 new, 1 on current walk, 2 done
        for s in range(n):
            walk, u = [], s
            while state[u] == 0:
                state[u] = 1
                walk.append(u)
                u = blames[u]
            if state[u] == 1:  # closed a new cycle starting at u
                k = walk.index(u)
                for v in walk[k:]:
                    ans[v], state[v] = v, 2
                walk = walk[:k]
            for v in reversed(walk):
                ans[v], state[v] = ans[blames[v]], 2
        return ans

    def brute(blames):
        out = []
        for s in range(len(blames)):
            seen, u = set(), s
            while u not in seen:
                seen.add(u)
                u = blames[u]
            out.append(u)
        return out

    def gen(rng, big):
        n = 100000 if big else rng.randint(1, 8)
        return ([rng.randrange(n) for _ in range(n)],)


@problem
class PlanetCycles:
    title = "Portal Loops"
    difficulty = "Medium"
    func = "jumpsUntilRepeat"
    statement = """
<p>Each planet <code>i</code> has a one-way portal to planet <code>portal[i]</code>. Starting from a planet, you keep
taking the portal from wherever you are. For each starting planet, return how many jumps you make before you first
arrive at a planet you have already visited on this trip.</p>
<ul><li><code>1 &lt;= portal.length &lt;= 10^5</code>; a portal may lead back to its own planet</li></ul>"""
    hint = dict(pattern="Functional graph: answer = distance to the cycle + cycle length; find cycles once, then fill tails backwards",
                module="Silver: Introduction to Functional Graphs", url="https://usaco.guide/silver/func-graphs", similar="CSES Planets Cycles ★")
    examples = [([4, 3, 2, 2, 1],), ([0, 0],)]
    edges = [([0],), ([1, 2, 0],)]

    def ref(portal: List[int]) -> List[int]:
        n = len(portal)
        ans, state = [0] * n, [0] * n
        for s in range(n):
            walk, u = [], s
            while state[u] == 0:
                state[u] = 1
                walk.append(u)
                u = portal[u]
            if state[u] == 1:
                k = walk.index(u)
                for v in walk[k:]:
                    ans[v], state[v] = len(walk) - k, 2
                walk = walk[:k]
            for v in reversed(walk):
                ans[v], state[v] = ans[portal[v]] + 1, 2
        return ans

    def brute(portal):
        out = []
        for s in range(len(portal)):
            seen, u, jumps = {s}, portal[s], 1
            while u not in seen:
                seen.add(u)
                u = portal[u]
                jumps += 1
            out.append(jumps)
        return out

    def gen(rng, big):
        n = 100000 if big else rng.randint(1, 8)
        if big and rng.random() < 0.5:  # one big cycle plus one long tail leading into it
            perm = rng.sample(range(n), n)
            cyc, portal = perm[:n // 2], [0] * n
            for k, v in enumerate(cyc):
                portal[v] = cyc[(k + 1) % len(cyc)]
            for k in range(n // 2, n):
                portal[perm[k]] = perm[k - 1]
            return (portal,)
        return ([rng.randrange(n) for _ in range(n)],)


@problem
class HerdFence:
    title = "Herd Fence"
    difficulty = "Medium"
    func = "smallestFence"
    statement = """
<p>Cows stand at points <code>cows[i] = [x, y]</code>. Each pair in <code>links</code> means two cows talk to each
other; a <b>herd</b> is a group of cows connected through such links. You want to fence in one entire herd with an
axis-aligned rectangle (it may have zero width or height). Return the smallest possible fence perimeter.</p>
<ul><li><code>1 &lt;= cows.length &lt;= 10^5</code></li><li><code>0 &lt;= links.length &lt;= 10^5</code></li><li><code>0 &lt;= x, y &lt;= 10^8</code></li></ul>"""
    hint = dict(pattern="Find connected components (DSU or BFS) and track each one's min/max x and y",
                module="Silver: Graph Traversal", url="https://usaco.guide/silver/graph-traversal", similar="USACO Fence Planning ★")
    examples = [([[0, 5], [10, 5], [5, 0], [5, 10], [3, 3], [7, 7]], [[0, 1], [2, 3], [4, 5]]),]
    edges = [([[4, 4]], []), ([[0, 0], [3, 4]], [[0, 1]])]

    def ref(cows: List[List[int]], links: List[List[int]]) -> int:
        def find(x):  # root with path halving
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        n = len(cows)
        parent = list(range(n))
        for a, b in links:
            parent[find(a)] = find(b)
        box = {}
        for i, (x, y) in enumerate(cows):
            r = find(i)
            if r in box:
                b = box[r]
                b[0], b[1], b[2], b[3] = min(b[0], x), max(b[1], x), min(b[2], y), max(b[3], y)
            else:
                box[r] = [x, x, y, y]
        return min(2 * (b[1] - b[0] + b[3] - b[2]) for b in box.values())

    def brute(cows, links):
        comp = _components(len(cows), links)
        best = None
        for c in set(comp):
            xs = [cows[i][0] for i in range(len(cows)) if comp[i] == c]
            ys = [cows[i][1] for i in range(len(cows)) if comp[i] == c]
            p = 2 * (max(xs) - min(xs) + max(ys) - min(ys))
            best = p if best is None else min(best, p)
        return best

    def gen(rng, big):
        n, m, V = (100000, 90000, 10**8) if big else (rng.randint(1, 7), rng.randint(0, 6), 9)
        return [[rng.randint(0, V), rng.randint(0, V)] for _ in range(n)], [rng.sample(range(n), 2) for _ in range(m)] if n > 1 else []


@problem
class RadioRelay:
    title = "Radio Relay"
    difficulty = "Medium"
    func = "maxReach"
    statement = """
<p>Each cow <code>[x, y, p]</code> carries a radio that reaches every cow within distance <code>p</code> (inclusive,
straight-line distance). Messages can be relayed from cow to cow. Starting a message at the best possible cow, return
the largest number of cows (including the starter) that can receive it. Note that cow A reaching cow B does not mean B
reaches A.</p>
<ul><li><code>1 &lt;= cows.length &lt;= 120</code></li><li><code>0 &lt;= x, y &lt;= 25000</code>, <code>1 &lt;= p &lt;= 25000</code></li></ul>"""
    hint = dict(pattern="Directed graph (compare squared distances to avoid floats), then BFS/DFS from every cow",
                module="Silver: Graph Traversal", url="https://usaco.guide/silver/graph-traversal", similar="USACO Moocast ★")
    examples = [([[1, 3, 5], [5, 4, 3], [7, 9, 1], [4, 5, 2]],),]
    edges = [([[0, 0, 1]],), ([[0, 0, 5], [10, 0, 1]],)]

    def ref(cows: List[List[int]]) -> int:
        n = len(cows)
        adj = [[j for j in range(n) if (cows[i][0] - cows[j][0]) ** 2 + (cows[i][1] - cows[j][1]) ** 2 <= cows[i][2] ** 2]
               for i in range(n)]
        best = 0
        for s in range(n):
            seen, stack = {s}, [s]
            while stack:
                for v in adj[stack.pop()]:
                    if v not in seen:
                        seen.add(v)
                        stack.append(v)
            best = max(best, len(seen))
        return best

    def brute(cows):
        n = len(cows)
        reach = [[i == j or (cows[i][0] - cows[j][0]) ** 2 + (cows[i][1] - cows[j][1]) ** 2 <= cows[i][2] ** 2 for j in range(n)]
                 for i in range(n)]
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    reach[i][j] = reach[i][j] or (reach[i][k] and reach[k][j])
        return max(sum(row) for row in reach)

    def gen(rng, big):
        n, V, P = (120, 25000, 3000) if big else (rng.randint(1, 6), 10, 6)
        return ([[rng.randint(0, V), rng.randint(0, V), rng.randint(1, P)] for _ in range(n)],)


@problem
class FencedFields:
    title = "Fenced Fields"
    difficulty = "Medium"
    func = "separatedPairs"
    statement = """
<p>A farm is an <code>n x n</code> grid of fields. Cows walk between fields that share a side, except across the
fences listed in <code>fences</code>: <code>[r1, c1, r2, c2]</code> blocks the side between those two adjacent fields.
Some fields hold one cow each, at <code>cows[i] = [r, c]</code>. Return the number of pairs of cows that cannot reach
each other.</p>
<ul><li><code>1 &lt;= n &lt;= 100</code></li><li><code>0 &lt;= fences.length &lt;= 2 * n * (n - 1)</code></li>
<li><code>1 &lt;= cows.length &lt;= n * n</code>, all in different fields</li></ul>"""
    hint = dict(pattern="Flood fill regions while treating fenced sides as walls, count cows per region, then subtract same-region pairs",
                module="Silver: Flood Fill", url="https://usaco.guide/silver/flood-fill", similar="USACO Why Did the Cow Cross the Road III ★")
    examples = [(3, [[1, 0, 1, 1], [1, 1, 2, 1], [1, 2, 1, 1]], [[1, 2], [1, 1], [2, 1]]),]
    edges = [(1, [], [[0, 0]]), (2, [[0, 0, 0, 1], [0, 0, 1, 0]], [[0, 0], [1, 1]])]

    def ref(n: int, fences: List[List[int]], cows: List[List[int]]) -> int:
        blocked = {(a, b, c, d) for a, b, c, d in fences} | {(c, d, a, b) for a, b, c, d in fences}
        region = [[-1] * n for _ in range(n)]
        for si in range(n):
            for sj in range(n):
                if region[si][sj] == -1:
                    region[si][sj], stack = si * n + sj, [(si, sj)]
                    while stack:
                        i, j = stack.pop()
                        for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                            if 0 <= a < n and 0 <= b < n and region[a][b] == -1 and (i, j, a, b) not in blocked:
                                region[a][b] = region[si][sj]
                                stack.append((a, b))
        per = Counter(region[r][c] for r, c in cows)
        k = len(cows)
        return k * (k - 1) // 2 - sum(c * (c - 1) // 2 for c in per.values())

    def brute(n, fences, cows):
        blocked = {(a, b, c, d) for a, b, c, d in fences} | {(c, d, a, b) for a, b, c, d in fences}
        idx = lambda i, j: i * n + j
        pairs = [(idx(i, j), idx(a, b)) for i in range(n) for j in range(n) for a, b in ((i + 1, j), (i, j + 1))
                 if a < n and b < n and (i, j, a, b) not in blocked]
        comp = _components(n * n, pairs)
        return sum(comp[idx(*cows[x])] != comp[idx(*cows[y])] for x, y in combinations(range(len(cows)), 2))

    def gen(rng, big):
        n = 100 if big else rng.randint(1, 4)
        sides = [[i, j, i + 1, j] for i in range(n - 1) for j in range(n)] + [[i, j, i, j + 1] for i in range(n) for j in range(n - 1)]
        fences = [s for s in sides if rng.random() < 0.45]
        cells = [[i, j] for i in range(n) for j in range(n)]
        return n, fences, rng.sample(cells, rng.randint(1, min(len(cells), 3000 if big else 6)))


@problem
class RouteAudit:
    title = "Route Audit"
    difficulty = "Medium"
    func = "findGap"
    statement = """
<p>An airline has <code>n</code> cities and one-way <code>flights</code> <code>[a, b]</code>. Check whether every city
can reach every other city. If so, return an empty list; otherwise return <code>[a, b]</code> such that there is no
route from city <code>a</code> to city <code>b</code>. Any such pair is accepted.</p>
<ul><li><code>2 &lt;= n &lt;= 10^5</code></li><li><code>0 &lt;= flights.length &lt;= 2 * 10^5</code></li></ul>"""
    hint = dict(pattern="Strongly connected iff city 0 reaches everyone AND everyone reaches city 0: one BFS on the graph, one on the reversed graph",
                module="Silver: Graph Traversal", url="https://usaco.guide/silver/graph-traversal", similar="CSES Flight Routes Check ★")
    examples = [(4, [[0, 1], [1, 2], [2, 0], [0, 3]]), (3, [[0, 1], [1, 2], [2, 0]])]
    edges = [(2, []), (2, [[0, 1], [1, 0]])]

    def ref(n: int, flights: List[List[int]]) -> List[int]:
        fwd, back = [[] for _ in range(n)], [[] for _ in range(n)]
        for a, b in flights:
            fwd[a].append(b)
            back[b].append(a)

        def reach(adj):
            seen = [False] * n
            seen[0], q = True, [0]
            for u in q:
                for v in adj[u]:
                    if not seen[v]:
                        seen[v] = True
                        q.append(v)
            return seen

        out_ok, in_ok = reach(fwd), reach(back)
        for v in range(n):
            if not out_ok[v]:
                return [0, v]
            if not in_ok[v]:
                return [v, 0]
        return []

    def brute(n, flights):
        reach = [[i == j for j in range(n)] for i in range(n)]
        for a, b in flights:
            reach[a][b] = True
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    reach[i][j] = reach[i][j] or (reach[i][k] and reach[k][j])
        return next(([i, j] for i in range(n) for j in range(n) if not reach[i][j]), [])

    def check(args, out, expected):
        n, flights = args
        if not expected:
            return out == []
        if not (isinstance(out, list) and len(out) == 2 and all(type(c) is int and 0 <= c < n for c in out)):
            return False
        adj = defaultdict(list)
        for a, b in flights:
            adj[a].append(b)
        seen, q = {out[0]}, [out[0]]
        for u in q:
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        return out[1] not in seen

    def gen(rng, big):
        n = 100000 if big else rng.randint(2, 6)
        cyc = list(range(n))
        rng.shuffle(cyc)
        flights = [[cyc[i], cyc[(i + 1) % n]] for i in range(n)]  # strongly connected base...
        if rng.random() < 0.6:
            flights.pop(rng.randrange(len(flights)))  # ...sometimes broken
        flights += [rng.sample(range(n), 2) for _ in range(rng.randint(0, 100000 if big else 4))]
        rng.shuffle(flights)
        return n, flights


@problem
class PortalSort:
    title = "Portal Sort"
    difficulty = "Medium"
    tl = 3.0  # binary search x union-find is ~0.75s in Python at full size
    func = "widestPortal"
    statement = """
<p>Cows stand in positions <code>0</code> to <code>n - 1</code>; the cow at position <code>i</code> is
<code>cows[i]</code> (a permutation). They want to be sorted, so that position <code>i</code> holds cow <code>i</code>.
Portal <code>[a, b, w]</code> lets the cows at positions <code>a</code> and <code>b</code> swap any number of times, but only
portals of width at least some minimum <code>W</code> can be used. Return the largest <code>W</code> that still lets the
cows sort themselves, or <code>-1</code> if they are already sorted. The portals always allow sorting.</p>
<ul><li><code>1 &lt;= n, portals.length &lt;= 5 * 10^4</code></li><li><code>1 &lt;= w &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Sortable iff every position i is connected to position cows[i]; binary search W with union-find (or add portals widest-first)",
                module="Gold: Disjoint Set Union", url="https://usaco.guide/gold/dsu", similar="USACO Wormhole Sort ★ (Silver and Gold)")
    examples = [([3, 2, 1, 0], [[0, 3, 9], [1, 2, 7], [0, 1, 8], [1, 3, 5]]), ([0, 1], [[0, 1, 4]])]
    edges = [([1, 0], [[0, 1, 6], [1, 0, 2]]),]

    def ref(cows: List[int], portals: List[List[int]]) -> int:
        n = len(cows)
        if all(c == i for i, c in enumerate(cows)):
            return -1

        def sortable(w):
            parent = list(range(n))

            def find(x):  # root with path halving
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x

            for a, b, width in portals:
                if width >= w:
                    parent[find(a)] = find(b)
            return all(find(i) == find(c) for i, c in enumerate(cows))

        widths = sorted({w for _, _, w in portals})
        lo, hi = 0, len(widths) - 1  # largest index whose width still works
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if sortable(widths[mid]):
                lo = mid
            else:
                hi = mid - 1
        return widths[lo]

    def brute(cows, portals):
        n = len(cows)
        if all(c == i for i, c in enumerate(cows)):
            return -1
        for w in sorted({w for _, _, w in portals}, reverse=True):
            comp = _components(n, [(a, b) for a, b, x in portals if x >= w])
            if all(comp[i] == comp[c] for i, c in enumerate(cows)):
                return w

    def gen(rng, big):
        n = 50000 if big else rng.randint(2, 6)
        cows = list(range(n))
        rng.shuffle(cows)
        W = 10**9 if big else 9
        portals = [[rng.randrange(i), i, rng.randint(1, W)] for i in range(1, n)]  # spanning tree: always sortable
        portals += [[*rng.sample(range(n), 2), rng.randint(1, W)] for _ in range(rng.randint(0, n if big else 3))]
        rng.shuffle(portals)
        return cows, portals


@problem
class SkiTrail:
    title = "Ski Trail"
    difficulty = "Medium"
    func = "minDifficulty"
    statement = """
<p>A ski area is a grid of elevations <code>heights</code>. A skier with difficulty rating <code>D</code> can move
between side-adjacent cells whose elevations differ by at most <code>D</code>. Cells where <code>marks[r][c] = 1</code>
are checkpoints. Return the smallest <code>D</code> that lets a skier travel between <b>every</b> pair of checkpoints.</p>
<ul><li><code>1 &lt;= rows, cols &lt;= 300</code></li><li><code>0 &lt;= heights[r][c] &lt;= 10^9</code></li><li>At least one checkpoint</li></ul>"""
    hint = dict(pattern="Binary search D with a flood fill, or Kruskal-style: add cell-to-cell edges by increasing difference until all checkpoints share a component",
                module="Silver: Flood Fill", url="https://usaco.guide/silver/flood-fill", similar="USACO Cross Country Skiing ★")
    examples = [([[20, 21, 18, 99, 5], [19, 22, 20, 16, 26], [18, 17, 40, 60, 80]],
                 [[1, 0, 0, 0, 1], [0, 0, 0, 0, 0], [0, 0, 0, 0, 1]]),]
    edges = [([[5]], [[1]]), ([[1, 9]], [[1, 1]])]

    def ref(heights: List[List[int]], marks: List[List[int]]) -> int:
        m, n = len(heights), len(heights[0])
        total = sum(map(sum, marks))
        if total <= 1:
            return 0
        edges = []
        for i in range(m):
            for j in range(n):
                if i + 1 < m:
                    edges.append((abs(heights[i][j] - heights[i + 1][j]), i * n + j, (i + 1) * n + j))
                if j + 1 < n:
                    edges.append((abs(heights[i][j] - heights[i][j + 1]), i * n + j, i * n + j + 1))
        edges.sort()
        parent = list(range(m * n))

        def find(x):  # root with path halving
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        count = [marks[i][j] for i in range(m) for j in range(n)]
        for d, a, b in edges:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
                count[rb] += count[ra]
                if count[rb] == total:
                    return d

    def brute(heights, marks):
        m, n = len(heights), len(heights[0])
        pts = [(i, j) for i in range(m) for j in range(n) if marks[i][j]]
        diffs = sorted({0} | {abs(heights[i][j] - heights[a][b]) for i in range(m) for j in range(n)
                              for a, b in ((i + 1, j), (i, j + 1)) if a < m and b < n})
        for D in diffs:
            seen, q = {pts[0]}, [pts[0]]
            for i, j in q:
                for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                    if 0 <= a < m and 0 <= b < n and (a, b) not in seen and abs(heights[i][j] - heights[a][b]) <= D:
                        seen.add((a, b))
                        q.append((a, b))
            if all(p in seen for p in pts):
                return D

    def gen(rng, big):
        m, n = (300, 300) if big else (rng.randint(1, 4), rng.randint(1, 4))
        V = 10**9 if big else 20
        marks = [[int(rng.random() < (0.01 if big else 0.3)) for _ in range(n)] for _ in range(m)]
        if not any(map(any, marks)):
            marks[rng.randrange(m)][rng.randrange(n)] = 1
        return [[rng.randint(0, V) for _ in range(n)] for _ in range(m)], marks


@problem
class VideoRecs:
    title = "Video Recommendations"
    difficulty = "Hard"
    func = "countRelated"
    statement = """
<p><code>n</code> videos are linked into a tree by <code>links</code> <code>[a, b, r]</code>, where <code>r</code> is how
related the two videos are. The relatedness of any two videos is the <b>smallest</b> <code>r</code> on the tree path
between them. For each query <code>[k, v]</code>, return how many other videos have relatedness at least
<code>k</code> to video <code>v</code>.</p>
<ul><li><code>1 &lt;= n, queries.length &lt;= 10^5</code></li><li><code>1 &lt;= r, k &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Offline union-find: sort links and queries by threshold, descending; add every link with r >= k, then answer size(v) - 1",
                module="Gold: Disjoint Set Union", url="https://usaco.guide/gold/dsu", similar="USACO MooTube ★ (Silver: BFS per query; Gold: offline DSU)")
    examples = [(4, [[0, 1, 3], [1, 2, 2], [1, 3, 4]], [[1, 1], [4, 0], [3, 0]]),]
    edges = [(1, [], [[5, 0]]), (2, [[0, 1, 5]], [[5, 0], [6, 1]])]

    def ref(n: int, links: List[List[int]], queries: List[List[int]]) -> List[int]:
        parent, size = list(range(n)), [1] * n

        def find(x):  # root with path halving
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        es = sorted(links, key=lambda e: -e[2])
        out, j = [0] * len(queries), 0
        for qi in sorted(range(len(queries)), key=lambda i: -queries[i][0]):
            k, v = queries[qi]
            while j < len(es) and es[j][2] >= k:
                ra, rb = find(es[j][0]), find(es[j][1])
                if ra != rb:
                    parent[ra] = rb
                    size[rb] += size[ra]
                j += 1
            out[qi] = size[find(v)] - 1
        return out

    def brute(n, links, queries):
        out = []
        for k, v in queries:
            comp = _components(n, [(a, b) for a, b, r in links if r >= k])
            out.append(comp.count(comp[v]) - 1)
        return out

    def gen(rng, big):
        n, q = (100000, 100000) if big else (rng.randint(1, 7), rng.randint(1, 5))
        R = 10**9 if big else 6
        links = [[rng.randrange(i), i, rng.randint(1, R)] for i in range(1, n)]
        return n, links, [[rng.randint(1, R), rng.randrange(n)] for _ in range(q)]


@problem
class GameRoutes:
    title = "Level Routes"
    difficulty = "Medium"
    func = "countRoutes"
    statement = """
<p>A game has <code>n</code> levels and one-way <code>teleporters</code> <code>[a, b]</code>; there are no loops
(you can never return to a level). Count the different routes from level <code>0</code> to level <code>n - 1</code>,
modulo <code>10^9 + 7</code>. Repeated teleporters count as different routes.</p>
<ul><li><code>2 &lt;= n &lt;= 10^5</code></li><li><code>0 &lt;= teleporters.length &lt;= 2 * 10^5</code></li></ul>"""
    hint = dict(pattern="DP in topological order: ways[v] = sum of ways[u] over teleporters u -> v",
                module="Gold: Topological Sort", url="https://usaco.guide/gold/toposort", similar="CSES Game Routes ★")
    examples = [(4, [[0, 1], [0, 2], [1, 3], [2, 3], [0, 3]]), (3, [[1, 2]])]
    edges = [(2, [[0, 1], [0, 1]]), (2, [])]

    def ref(n: int, teleporters: List[List[int]]) -> int:
        adj, indeg = [[] for _ in range(n)], [0] * n
        for a, b in teleporters:
            adj[a].append(b)
            indeg[b] += 1
        ways = [0] * n
        ways[0] = 1
        order = [i for i in range(n) if indeg[i] == 0]
        for u in order:
            for v in adj[u]:
                ways[v] = (ways[v] + ways[u]) % (10**9 + 7)
                indeg[v] -= 1
                if indeg[v] == 0:
                    order.append(v)
        return ways[n - 1]

    def brute(n, teleporters):
        @lru_cache(None)
        def f(u):
            return 1 if u == n - 1 else sum(f(b) for a, b in teleporters if a == u)
        return f(0) % MOD

    def gen(rng, big):
        n, m = (100000, 200000) if big else (rng.randint(2, 6), rng.randint(0, 9))
        order = [0] + rng.sample(range(1, n - 1), n - 2) + [n - 1]  # 0 first, n-1 last in a random topological order
        tel = []
        for _ in range(m):
            i, j = sorted(rng.sample(range(n), 2))
            tel.append([order[i], order[j]])
        if big:
            tel += [[order[i], order[i + 1]] for i in range(n - 1)]
        return n, tel


@problem
class PriorityCourses:
    title = "Priority Courses"
    difficulty = "Hard"
    func = "priorityOrder"
    statement = """
<p>There are <code>n</code> courses; <code>[a, b]</code> in <code>prereqs</code> means course <code>a</code> must come
before course <code>b</code> (no cycles). Among all valid orders, choose the one where course <code>0</code> comes as
early as possible; among those, course <code>1</code> as early as possible; and so on. Return that order.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li><code>0 &lt;= prereqs.length &lt;= 2 * 10^5</code></li></ul>"""
    hint = dict(pattern="Not the smallest-label-first order! Build the order backwards on the reversed graph, always placing the LARGEST available course last",
                module="Gold: Topological Sort", url="https://usaco.guide/gold/toposort", similar="CSES Course Schedule II ★")
    examples = [(4, [[2, 0], [3, 1]]), (3, [[2, 1]])]
    edges = [(1, []), (3, [[1, 0], [2, 0]])]

    def ref(n: int, prereqs: List[List[int]]) -> List[int]:
        back, outdeg = [[] for _ in range(n)], [0] * n
        for a, b in prereqs:
            back[b].append(a)
            outdeg[a] += 1
        heap = [-i for i in range(n) if outdeg[i] == 0]
        heapify(heap)
        rev = []
        while heap:
            u = -heappop(heap)
            rev.append(u)
            for a in back[u]:
                outdeg[a] -= 1
                if outdeg[a] == 0:
                    heappush(heap, -a)
        return rev[::-1]

    def brute(n, prereqs):
        from itertools import permutations
        best = None
        for perm in permutations(range(n)):
            pos = [0] * n
            for i, c in enumerate(perm):
                pos[c] = i
            if all(pos[a] < pos[b] for a, b in prereqs) and (best is None or pos < best[0]):
                best = (pos, list(perm))
        return best[1]

    def gen(rng, big):
        n, m = (100000, 200000) if big else (rng.randint(1, 6), rng.randint(0, 6))
        order = list(range(n))
        rng.shuffle(order)
        pairs = []
        for _ in range(m if n > 1 else 0):
            i, j = sorted(rng.sample(range(n), 2))
            pairs.append([order[i], order[j]])
        return n, pairs


@problem
class ShortestRoutes:
    title = "Shortest Routes"
    difficulty = "Medium"
    func = "shortestFromStart"
    statement = """
<p>There are <code>n</code> cities and one-way <code>flights</code> <code>[a, b, cost]</code>. Return the cheapest cost
from city <code>0</code> to every city (<code>0</code> for city 0 itself, <code>-1</code> if unreachable).</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li><code>0 &lt;= flights.length &lt;= 2 * 10^5</code></li><li><code>1 &lt;= cost &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Dijkstra with a binary heap; skip stale heap entries",
                module="Gold: Shortest Paths with Non-Negative Edge Weights", url="https://usaco.guide/gold/shortest-paths",
                similar="CSES Shortest Routes I (focus problem) · LeetCode 743")
    examples = [(3, [[0, 1, 5], [0, 2, 3], [2, 1, 1]]), (3, [[1, 2, 4]])]
    edges = [(1, []), (2, [[0, 1, 3], [0, 1, 1]])]

    def ref(n: int, flights: List[List[int]]) -> List[int]:
        adj = [[] for _ in range(n)]
        for a, b, c in flights:
            adj[a].append((b, c))
        dist = [-1] * n
        heap = [(0, 0)]
        while heap:
            d, u = heappop(heap)
            if dist[u] != -1:
                continue
            dist[u] = d
            for v, c in adj[u]:
                if dist[v] == -1:
                    heappush(heap, (d + c, v))
        return dist

    def brute(n, flights):
        d = [0] + [float("inf")] * (n - 1)
        for _ in range(n):
            for a, b, c in flights:
                d[b] = min(d[b], d[a] + c)
        return [-1 if x == float("inf") else x for x in d]

    def gen(rng, big):
        n, m, C = (100000, 200000, 10**9) if big else (rng.randint(1, 6), rng.randint(0, 9), 9)
        return n, [[*rng.sample(range(n), 2), rng.randint(1, C)] for _ in range(m)] if n > 1 else []


@problem
class RouteInvestigation:
    title = "Route Investigation"
    difficulty = "Hard"
    func = "analyzeRoutes"
    statement = """
<p>There are <code>n</code> cities and one-way <code>flights</code> <code>[a, b, price]</code>; city <code>n - 1</code>
is always reachable from city <code>0</code>. Considering only the <b>cheapest</b> routes from 0 to <code>n - 1</code>,
return <code>[cheapest price, number of cheapest routes mod 10^9 + 7, fewest flights on a cheapest route, most flights on
a cheapest route]</code>. Repeated flights count as different routes.</p>
<ul><li><code>2 &lt;= n &lt;= 10^5</code></li><li><code>1 &lt;= flights.length &lt;= 2 * 10^5</code></li><li><code>1 &lt;= price &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Dijkstra that carries extra DP values per city: route count, min and max flights; reset them on a strictly better price, merge them on a tie",
                module="Gold: Shortest Paths with Non-Negative Edge Weights", url="https://usaco.guide/gold/shortest-paths", similar="CSES Investigation ★")
    examples = [(4, [[0, 3, 5], [0, 1, 2], [1, 3, 3], [0, 2, 1], [2, 1, 1]]), (2, [[0, 1, 7], [0, 1, 7]])]
    edges = [(2, [[0, 1, 1]]),]

    def ref(n: int, flights: List[List[int]]) -> List[int]:
        adj = [[] for _ in range(n)]
        for a, b, c in flights:
            adj[a].append((b, c))
        INF = float("inf")
        dist, cnt, lo, hi = [INF] * n, [0] * n, [0] * n, [0] * n
        dist[0], cnt[0] = 0, 1
        heap = [(0, 0)]
        while heap:
            d, u = heappop(heap)
            if d > dist[u]:
                continue
            for v, c in adj[u]:
                nd = d + c
                if nd < dist[v]:
                    dist[v], cnt[v], lo[v], hi[v] = nd, cnt[u], lo[u] + 1, hi[u] + 1
                    heappush(heap, (nd, v))
                elif nd == dist[v]:
                    cnt[v] = (cnt[v] + cnt[u]) % (10**9 + 7)
                    lo[v], hi[v] = min(lo[v], lo[u] + 1), max(hi[v], hi[u] + 1)
        return [dist[-1], cnt[-1], lo[-1], hi[-1]]

    def brute(n, flights):
        found = []  # (price, flights) of every simple route; prices are positive so cheapest routes are simple

        def dfs(u, price, used, seen):
            if u == n - 1:
                found.append((price, used))
                return
            for a, b, c in flights:
                if a == u and b not in seen:
                    dfs(b, price + c, used + 1, seen | {b})

        dfs(0, 0, 0, {0})
        best = min(p for p, _ in found)
        hops = [h for p, h in found if p == best]
        return [best, len(hops) % MOD, min(hops), max(hops)]

    def gen(rng, big):
        n, m, C = (100000, 200000, 3) if big else (rng.randint(2, 6), rng.randint(0, 8), 3)
        flights = [[i, i + 1, rng.randint(1, C)] for i in range(n - 1)]  # guarantees reachability
        flights += [[*rng.sample(range(n), 2), rng.randint(1, C)] for _ in range(m if not big else m - n + 1)]
        rng.shuffle(flights)
        return n, flights


@problem
class GraphGirth:
    title = "Shortest Loop"
    difficulty = "Medium"
    func = "shortestCycle"
    statement = """
<p>A road network has <code>n</code> towns and two-way <code>roads</code> (no road connects a town to itself, and no two
roads connect the same pair). Return the number of roads on the shortest round trip that uses no road twice and visits
no town twice, or <code>-1</code> if the network has no cycle.</p>
<ul><li><code>1 &lt;= n &lt;= 500</code></li><li><code>0 &lt;= roads.length &lt;= 1000</code></li></ul>"""
    hint = dict(pattern="BFS from every town; a non-tree edge (u, v) closes a cycle of length dist[u] + dist[v] + 1",
                module="Gold: Shortest Paths with Unweighted Edges", url="https://usaco.guide/gold/unweighted-shortest-paths",
                similar="CSES Graph Girth ★ · LeetCode 2608")
    examples = [(5, [[0, 1], [1, 2], [2, 3], [3, 0], [1, 4], [4, 2]]), (3, [[0, 1], [1, 2]])]
    edges = [(1, []), (3, [[0, 1], [1, 2], [2, 0]])]

    def ref(n: int, roads: List[List[int]]) -> int:
        adj = [[] for _ in range(n)]
        for a, b in roads:
            adj[a].append(b)
            adj[b].append(a)
        best = float("inf")
        for s in range(n):
            dist, par = [-1] * n, [-1] * n
            dist[s], q = 0, [s]
            for u in q:
                if 2 * dist[u] + 1 >= best:
                    break
                for v in adj[u]:
                    if dist[v] == -1:
                        dist[v], par[v] = dist[u] + 1, u
                        q.append(v)
                    elif par[u] != v:
                        best = min(best, dist[u] + dist[v] + 1)
        return -1 if best == float("inf") else best

    def brute(n, roads):
        best = float("inf")
        for i, (a, b) in enumerate(roads):  # remove one road, shortest detour between its ends
            others = roads[:i] + roads[i + 1:]
            adj = defaultdict(list)
            for x, y in others:
                adj[x].append(y)
                adj[y].append(x)
            dist, q = {a: 0}, deque([a])
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if v not in dist:
                        dist[v] = dist[u] + 1
                        q.append(v)
            if b in dist:
                best = min(best, dist[b] + 1)
        return -1 if best == float("inf") else best

    def gen(rng, big):
        n = 500 if big else rng.randint(1, 7)
        target = 1000 if big else rng.randint(0, n * (n - 1) // 2)
        pairs = set()
        while len(pairs) < min(target, n * (n - 1) // 2):
            a, b = sorted(rng.sample(range(n), 2))
            pairs.add((a, b))
        return n, [list(p) for p in pairs]


@problem
class LaserRelay:
    title = "Laser Relay"
    difficulty = "Hard"
    func = "minMirrors"
    statement = """
<p>A laser at <code>laser = [x, y]</code> can fire north, south, east or west. A receiver sits at
<code>receiver = [x, y]</code>. Mirrors can be placed only on the posts at <code>posts</code>; a mirror turns the beam
90 degrees (either way), and posts without mirrors do not block the beam. Return the fewest mirrors needed to hit the
receiver, or <code>-1</code> if it is impossible.</p>
<ul><li><code>0 &lt;= posts.length &lt;= 10^5</code></li><li>Coordinates are between <code>0</code> and <code>10^9</code>; all points are distinct</li></ul>"""
    hint = dict(pattern="BFS over lines, not cells: rows and columns are the nodes, each post connects its row to its column (one mirror)",
                module="Gold: Shortest Paths with Unweighted Edges", url="https://usaco.guide/gold/unweighted-shortest-paths",
                similar="USACO Lasers and Mirrors ★")
    examples = [([0, 0], [7, 2], [[3, 2], [0, 2], [3, 5]]), ([0, 0], [3, 3], [])]
    edges = [([0, 0], [0, 9], []), ([1, 1], [5, 5], [[1, 5]])]

    def ref(laser: List[int], receiver: List[int], posts: List[List[int]]) -> int:
        on_row, on_col = defaultdict(list), defaultdict(list)  # row y -> post xs, column x -> post ys
        for x, y in posts:
            on_row[y].append(x)
            on_col[x].append(y)
        start = [("row", laser[1]), ("col", laser[0])]
        dist = {s: 0 for s in start}
        q = deque(start)
        while q:
            kind, c = q.popleft()
            d = dist[(kind, c)]
            if (kind == "row" and c == receiver[1]) or (kind == "col" and c == receiver[0]):
                return d
            crossing = on_row.pop(c, []) if kind == "row" else on_col.pop(c, [])
            for other in crossing:
                nxt = ("col", other) if kind == "row" else ("row", other)
                if nxt not in dist:
                    dist[nxt] = d + 1
                    q.append(nxt)
        return -1

    def brute(laser, receiver, posts):
        pts = [tuple(laser)] + [tuple(p) for p in posts]
        best = {(0, "h"): 0, (0, "v"): 0}  # (point index, beam axis) -> mirrors used; 0-1 BFS
        dq = deque(best)
        answer = float("inf")
        while dq:
            i, axis = dq.popleft()
            d = best[(i, axis)]
            x, y = pts[i]
            if (axis == "h" and y == receiver[1]) or (axis == "v" and x == receiver[0]):
                answer = min(answer, d)
            for j, (a, b) in enumerate(pts):
                if j and j != i and ((axis == "h" and b == y) or (axis == "v" and a == x)):
                    turn = (j, "v" if axis == "h" else "h")
                    if best.get(turn, float("inf")) > d + 1:
                        best[turn] = d + 1
                        dq.append(turn)
        return -1 if answer == float("inf") else answer

    def gen(rng, big):
        V = 10**9 if big else 5
        n = 100000 if big else rng.randint(0, 6)
        span = 300 if big else V  # few distinct rows/columns so beams can actually meet posts
        pick = lambda: [rng.randint(0, span), rng.randint(0, span)]
        pts = set()
        while len(pts) < n + 2 and len(pts) < (span + 1) ** 2:
            pts.add(tuple(pick()))
        pts = [list(p) for p in pts]
        rng.shuffle(pts)
        return pts[0], pts[1], pts[2:]


# ================================================================ starred: DP, trees, stacks, math

@problem
class DiceSums:
    title = "Dice Sums"
    difficulty = "Easy"
    func = "countWays"
    statement = """
<p>You roll a six-sided die (faces 1 to 6) one or more times and add up the results. Count the ordered sequences of
rolls whose sum is exactly <code>target</code>, modulo <code>10^9 + 7</code>.</p>
<ul><li><code>1 &lt;= target &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="ways[s] = ways[s-1] + ... + ways[s-6] (keep a running window sum)",
                module="Gold: Knapsack DP", url="https://usaco.guide/gold/knapsack", similar="CSES Dice Combinations (focus problem) · LeetCode 70")
    examples = [(3,), (7,)]
    edges = [(1,), (6,)]

    def ref(target: int) -> int:
        ways = [1] + [0] * target
        for s in range(1, target + 1):
            ways[s] = sum(ways[max(0, s - 6):s]) % (10**9 + 7)
        return ways[target]

    def brute(target):
        f = lambda s: 1 if s == 0 else sum(f(s - d) for d in range(1, 7) if d <= s)
        return f(target) % MOD

    def gen(rng, big):
        return (100000 if big else rng.randint(1, 14),)


@problem
class FewestCoins:
    title = "Fewest Coins"
    difficulty = "Easy"
    func = "minCoins"
    statement = """
<p>Using unlimited coins of the distinct values in <code>coins</code>, return the fewest coins that add up to exactly
<code>target</code>, or <code>-1</code> if it is impossible.</p>
<ul><li><code>1 &lt;= coins.length &lt;= 100</code></li><li><code>1 &lt;= coins[i], target &lt;= 10^4</code></li></ul>"""
    hint = dict(pattern="Unbounded knapsack: best[s] = 1 + min(best[s - c]) over coins c <= s",
                module="Gold: Knapsack DP", url="https://usaco.guide/gold/knapsack", similar="CSES Minimizing Coins ★ · LeetCode 322")
    examples = [([1, 5, 7], 11), ([4], 6)]
    edges = [([1], 1), ([3, 7], 14)]

    def ref(coins: List[int], target: int) -> int:
        INF = float("inf")
        best = [0] + [INF] * target
        for s in range(1, target + 1):
            best[s] = min((best[s - c] for c in coins if c <= s), default=INF) + 1
        return -1 if best[target] == INF else best[target]

    def brute(coins, target):
        @lru_cache(None)
        def f(s):
            return 0 if s == 0 else min((1 + f(s - c) for c in coins if c <= s), default=float("inf"))
        r = f(target)
        return -1 if r == float("inf") else r

    def gen(rng, big):
        if big:
            return rng.sample(range(2, 10**4 + 1), 100), 10**4
        return rng.sample(range(1, 9), rng.randint(1, 3)), rng.randint(1, 20)


@problem
class ChangeCombinations:
    title = "Change Combinations"
    difficulty = "Medium"
    func = "countCombinations"
    statement = """
<p>Using unlimited coins of the distinct values in <code>coins</code>, count the different <b>multisets</b> of coins
that add up to exactly <code>target</code> (order does not matter, so 1+2 and 2+1 are the same). Return the count modulo
<code>10^9 + 7</code>.</p>
<ul><li><code>1 &lt;= coins.length &lt;= 100</code></li><li><code>1 &lt;= coins[i], target &lt;= 10^4</code></li></ul>"""
    hint = dict(pattern="Coin loop OUTSIDE, amount loop inside: each coin is added once in a fixed order, so orders aren't double-counted",
                module="Gold: Knapsack DP", url="https://usaco.guide/gold/knapsack",
                similar="CSES Coin Combinations II ★ · LeetCode 518 (compare Ordered Change)")
    examples = [([1, 2, 3], 4), ([2], 3)]
    edges = [([1], 1), ([5], 5)]

    def ref(coins: List[int], target: int) -> int:
        ways = [1] + [0] * target
        for c in coins:
            for s in range(c, target + 1):
                ways[s] = (ways[s] + ways[s - c]) % (10**9 + 7)
        return ways[target]

    def brute(coins, target):
        cs = sorted(coins)

        def f(i, s):  # use coins cs[i:], non-decreasing order
            if s == 0:
                return 1
            return sum(f(j, s - cs[j]) for j in range(i, len(cs)) if cs[j] <= s)

        return f(0, target) % MOD

    def gen(rng, big):
        if big:
            return [1] + rng.sample(range(2, 10**4 + 1), 99), 10**4
        return rng.sample(range(1, 7), rng.randint(1, 3)), rng.randint(1, 14)


@problem
class CommonThread:
    title = "Common Thread"
    difficulty = "Medium"
    func = "longestCommon"
    statement = """
<p>Return the length of the longest string that is a subsequence of both <code>a</code> and <code>b</code> (characters
in order, not necessarily adjacent).</p>
<ul><li><code>1 &lt;= a.length, b.length &lt;= 1000</code>, lowercase letters</li></ul>"""
    hint = dict(pattern="2-D DP on prefixes: match the last characters if equal, otherwise drop one of them",
                module="Gold: Paths on Grids", url="https://usaco.guide/gold/paths-grids", similar="LeetCode 1143 Longest Common Subsequence (focus problem)")
    examples = [("abcde", "ace"), ("abc", "def")]
    edges = [("a", "a"), ("aaa", "aa")]

    def ref(a: str, b: str) -> int:
        prev = [0] * (len(b) + 1)
        for ch in a:
            cur = [0]
            for j, cb in enumerate(b):
                cur.append(prev[j] + 1 if ch == cb else max(prev[j + 1], cur[j]))
            prev = cur
        return prev[-1]

    def brute(a, b):
        @lru_cache(None)
        def f(i, j):
            if i == len(a) or j == len(b):
                return 0
            return 1 + f(i + 1, j + 1) if a[i] == b[j] else max(f(i + 1, j), f(i, j + 1))
        return f(0, 0)

    def gen(rng, big):
        if big:
            return "".join(rng.choice("abcdefghij") for _ in range(1000)), "".join(rng.choice("abcdefghij") for _ in range(1000))
        return "".join(rng.choice("abc") for _ in range(rng.randint(1, 7))), "".join(rng.choice("abc") for _ in range(rng.randint(1, 7)))


@problem
class TypoFixer:
    title = "Typo Fixer"
    difficulty = "Medium"
    func = "editDistance"
    statement = """
<p>Return the minimum number of single-character edits (insert a character, delete a character, or replace a
character) that turn <code>a</code> into <code>b</code>.</p>
<ul><li><code>1 &lt;= a.length, b.length &lt;= 1000</code>, uppercase letters</li></ul>"""
    hint = dict(pattern="2-D DP on prefixes: dist[i][j] = min(delete, insert, replace-or-match)",
                module="Gold: Paths on Grids", url="https://usaco.guide/gold/paths-grids", similar="CSES Edit Distance ★ · LeetCode 72")
    examples = [("LOVE", "MOVIE"), ("ABC", "ABC")]
    edges = [("A", "B"), ("A", "AAAA")]

    def ref(a: str, b: str) -> int:
        prev = list(range(len(b) + 1))
        for i, ch in enumerate(a, 1):
            cur = [i]
            for j, cb in enumerate(b, 1):
                cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ch != cb)))
            prev = cur
        return prev[-1]

    def brute(a, b):
        @lru_cache(None)
        def f(i, j):
            if i == len(a):
                return len(b) - j
            if j == len(b):
                return len(a) - i
            return min(f(i + 1, j) + 1, f(i, j + 1) + 1, f(i + 1, j + 1) + (a[i] != b[j]))
        return f(0, 0)

    def gen(rng, big):
        if big:  # full size, so an exponential or cubic solution times out
            return "".join(rng.choice("ABCDEFGH") for _ in range(1000)), "".join(rng.choice("ABCDEFGH") for _ in range(1000))
        return "".join(rng.choice("AB") for _ in range(rng.randint(1, 6))), "".join(rng.choice("AB") for _ in range(rng.randint(1, 6)))


@problem
class MatchingPlaylists:
    title = "Matching Playlists"
    difficulty = "Hard"
    func = "longestShared"
    statement = """
<p>Two friends each ranked the same <code>n</code> songs, numbered <code>1</code> to <code>n</code>, so <code>a</code> and
<code>b</code> are both permutations of <code>1..n</code>. Return the length of the longest list of songs that appears in
the same relative order in both rankings.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="Longest common subsequence of two permutations = LIS: replace each song in a by its position in b",
                module="Gold: Longest Increasing Subsequence", url="https://usaco.guide/gold/lis", similar="CF LCS on Permutations ★")
    examples = [([1, 3, 2, 4], [3, 1, 4, 2]), ([1, 2, 3], [3, 2, 1])]
    edges = [([1], [1]), ([2, 1], [2, 1])]

    def ref(a: List[int], b: List[int]) -> int:
        pos = {song: i for i, song in enumerate(b)}
        tails = []
        for song in a:
            p = pos[song]
            i = bisect_left(tails, p)
            if i == len(tails):
                tails.append(p)
            else:
                tails[i] = p
        return len(tails)

    def brute(a, b):
        @lru_cache(None)
        def f(i, j):
            if i == len(a) or j == len(b):
                return 0
            return 1 + f(i + 1, j + 1) if a[i] == b[j] else max(f(i + 1, j), f(i, j + 1))
        return f(0, 0)

    def gen(rng, big):
        n = 100000 if big else rng.randint(1, 8)
        return rng.sample(range(1, n + 1), n), rng.sample(range(1, n + 1), n)


@problem
class ProfitTour:
    title = "Profit Tour"
    difficulty = "Hard"
    func = "bestProfit"
    tl = 3.0
    statement = """
<p>A salesperson starts in city <code>0</code>. Each day they take one of the one-way <code>roads</code>
<code>[a, b]</code>, and on arriving in city <code>v</code> they earn <code>money[v]</code> (every time they arrive there).
A trip of <code>T</code> days costs <code>cost * T^2</code> in total. The trip must end back in city 0 (a trip of 0 days is
allowed and earns nothing). Return the largest profit.</p>
<ul><li><code>1 &lt;= n &lt;= 500</code></li><li><code>0 &lt;= roads.length &lt;= 1000</code></li>
<li><code>0 &lt;= money[v] &lt;= 1000</code>, <code>1 &lt;= cost &lt;= 1000</code></li></ul>"""
    hint = dict(pattern="DP over (day, city): best money on arrival. Days beyond max(money) / cost can never pay off, which bounds T",
                module="Gold: Introduction to DP", url="https://usaco.guide/gold/intro-dp", similar="USACO Time is Mooney ★")
    examples = [([0, 10, 20], [[0, 1], [1, 2], [2, 0], [1, 0]], 1), ([0, 5], [[0, 1]], 1)]
    edges = [([7], [], 3), ([0, 3], [[0, 1], [1, 0]], 1)]

    def ref(money: List[int], roads: List[List[int]], cost: int) -> int:
        n = len(money)
        cur = [-1] * n  # most money on arriving at each city after t days (-1 = impossible)
        cur[0] = 0
        best = 0
        for t in range(1, max(money) // cost + 2):
            nxt = [-1] * n
            for a, b in roads:
                if cur[a] >= 0 and cur[a] + money[b] > nxt[b]:
                    nxt[b] = cur[a] + money[b]
            cur = nxt
            if cur[0] >= 0:
                best = max(best, cur[0] - cost * t * t)
        return best

    def brute(money, roads, cost):
        best, limit = 0, max(money) // cost + 1

        def walk(v, t, earned):
            nonlocal best
            if t and v == 0:
                best = max(best, earned - cost * t * t)
            if t < limit:
                for a, b in roads:
                    if a == v:
                        walk(b, t + 1, earned + money[b])

        walk(0, 0, 0)
        return best

    def gen(rng, big):
        n, m = (500, 1000) if big else (rng.randint(1, 4), rng.randint(0, 6))
        roads = [rng.sample(range(n), 2) for _ in range(m)] if n > 1 else []
        if big:
            roads += [[i, (i + 1) % n] for i in range(0, n, 25)]
        return [rng.randint(0, 1000 if big else 6) for _ in range(n)], roads, rng.randint(1, 3)


@problem
class NetworkSpan:
    title = "Network Span"
    difficulty = "Medium"
    func = "diameter"
    statement = """
<p><code>n</code> routers are connected by <code>n - 1</code> cables <code>edges</code> forming a tree. Return the largest
number of cables between any two routers.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li>The tree may be very deep.</li></ul>"""
    hint = dict(pattern="Two BFS passes: the farthest node from anywhere is one end of a diameter; BFS again from it",
                module="Silver: Introduction to Tree Algorithms", url="https://usaco.guide/silver/intro-tree", similar="CSES Tree Diameter ★ · LeetCode 1245")
    examples = [(5, [[0, 1], [0, 2], [2, 3], [2, 4]]), (2, [[0, 1]])]
    edges = [(1, []), (3, [[0, 1], [1, 2]])]

    def ref(n: int, edges: List[List[int]]) -> int:
        adj = [[] for _ in range(n)]
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)

        def farthest(s):
            dist = [-1] * n
            dist[s], q = 0, [s]
            for u in q:
                for v in adj[u]:
                    if dist[v] == -1:
                        dist[v] = dist[u] + 1
                        q.append(v)
            far = max(range(n), key=dist.__getitem__)
            return far, dist[far]

        return farthest(farthest(0)[0])[1]

    def brute(n, edges):
        adj = defaultdict(list)
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        best = 0
        for s in range(n):
            dist, q = {s: 0}, deque([s])
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if v not in dist:
                        dist[v] = dist[u] + 1
                        q.append(v)
            best = max(best, max(dist.values()))
        return best

    def gen(rng, big):
        n = 100000 if big else rng.randint(1, 9)
        label = rng.sample(range(n), n)
        path = big and rng.random() < 0.5
        return n, [[label[i - 1 if path else rng.randrange(i)], label[i]] for i in range(1, n)]


@problem
class FlowerBeds:
    title = "Flower Beds"
    difficulty = "Easy"
    func = "minFlowerTypes"
    statement = """
<p><code>n</code> flower beds are joined by <code>n - 1</code> paths <code>paths</code> forming a tree. Each bed gets one
flower type. Beds joined by a path must differ, and so must any two beds that are both joined to the same third bed.
Return the fewest flower types needed.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="A bed and all its neighbors must be pairwise different, so the answer is (max degree) + 1, and that is always enough in a tree",
                module="Silver: Introduction to Tree Algorithms", url="https://usaco.guide/silver/intro-tree", similar="USACO Grass Planting ★")
    examples = [(4, [[0, 1], [3, 1], [1, 2]]), (3, [[0, 1], [1, 2]])]
    edges = [(1, []), (2, [[0, 1]])]

    def ref(n: int, paths: List[List[int]]) -> int:
        deg = [0] * n
        for a, b in paths:
            deg[a] += 1
            deg[b] += 1
        return max(deg) + 1

    def brute(n, paths):
        adj = defaultdict(set)
        for a, b in paths:
            adj[a].add(b)
            adj[b].add(a)
        clash = [adj[v] | {w for u in adj[v] for w in adj[u]} - {v} for v in range(n)]
        for k in range(1, n + 1):
            color = [-1] * n

            def place(v):
                if v == n:
                    return True
                for c in range(k):
                    if all(color[u] != c for u in clash[v]):
                        color[v] = c
                        if place(v + 1):
                            return True
                color[v] = -1
                return False

            if place(0):
                return k

    def gen(rng, big):
        n = 100000 if big else rng.randint(1, 7)
        return n, [[rng.randrange(i), i] for i in range(1, n)]


@problem
class TasteRoute:
    title = "Taste Route"
    difficulty = "Medium"
    func = "canSatisfy"
    statement = """
<p><code>n</code> farms are joined by roads <code>edges</code> forming a tree; farm <code>i</code> makes cheese of type
<code>types[i]</code> (<code>'H'</code> or <code>'G'</code>). Each query <code>[a, b, t]</code> describes a friend who
travels the tree path from farm <code>a</code> to farm <code>b</code> and wants to taste type <code>t</code> somewhere
along it (including the ends). Return <code>1</code> if they can, otherwise <code>0</code>, for each query.</p>
<ul><li><code>1 &lt;= n, queries.length &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="Group farms into same-type connected regions; a path misses type t only if both ends are in one region of the other type",
                module="Silver: Introduction to Tree Algorithms", url="https://usaco.guide/silver/intro-tree", similar="USACO Milk Visits ★ (Silver)")
    examples = [("HHGHG", [[0, 1], [1, 2], [2, 3], [1, 4]], [[0, 4, "H"], [0, 3, "G"], [0, 1, "G"], [3, 3, "H"], [3, 3, "G"]]),]
    edges = [("G", [], [[0, 0, "G"], [0, 0, "H"]])]

    def ref(types: str, edges: List[List[int]], queries: List[list]) -> List[int]:
        parent = list(range(len(types)))

        def find(x):  # root with path halving
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for a, b in edges:
            if types[a] == types[b]:
                parent[find(a)] = find(b)
        return [int(find(a) != find(b) or types[a] == t) for a, b, t in queries]

    def brute(types, edges, queries):
        adj = defaultdict(list)
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        out = []
        for a, b, t in queries:
            par, q = {a: None}, deque([a])
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if v not in par:
                        par[v] = u
                        q.append(v)
            node, seen = b, False
            while node is not None:
                seen |= types[node] == t
                node = par[node]
            out.append(int(seen))
        return out

    def gen(rng, big):
        n, q = (100000, 100000) if big else (rng.randint(1, 7), rng.randint(1, 5))
        types = "".join(rng.choice("HG") if not big else rng.choice("HHHG") for _ in range(n))
        return types, [[rng.randrange(i), i] for i in range(1, n)], [[rng.randrange(n), rng.randrange(n), rng.choice("HG")] for _ in range(q)]


@problem
class PreviousCheaper:
    title = "Previous Cheaper"
    difficulty = "Easy"
    func = "previousSmaller"
    statement = """
<p>For each day <code>i</code> in <code>prices</code>, return the index of the most recent earlier day with a strictly
lower price, or <code>-1</code> if there is none.</p>
<ul><li><code>1 &lt;= prices.length &lt;= 10^5</code></li><li><code>1 &lt;= prices[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Monotonic stack of indices with increasing prices: pop everything >= the current price, the top is the answer",
                module="Gold: Stacks", url="https://usaco.guide/gold/stacks", similar="CSES Nearest Smaller Values (focus problem) · LeetCode 739 (mirror image)")
    examples = [([2, 5, 1, 4, 8, 3, 2, 5],), ([3, 3],)]
    edges = [([7],), ([1, 2, 3],)]

    def ref(prices: List[int]) -> List[int]:
        stack, out = [], []
        for i, p in enumerate(prices):
            while stack and prices[stack[-1]] >= p:
                stack.pop()
            out.append(stack[-1] if stack else -1)
            stack.append(i)
        return out

    def brute(prices):
        return [next((j for j in range(i - 1, -1, -1) if prices[j] < prices[i]), -1) for i in range(len(prices))]

    def gen(rng, big):
        if big:
            return ([rng.randint(1, 10**9) for _ in range(100000)],)
        return ([rng.randint(1, 5) for _ in range(rng.randint(1, 9))],)


@problem
class TeamStrength:
    title = "Team Strength"
    difficulty = "Medium"
    func = "bestBySize"
    statement = """
<p>Players stand in a row with heights <code>heights</code>. A team is a group of consecutive players, and its strength
is the height of its shortest member. For every team size <code>x</code> from 1 to <code>n</code>, return the greatest
strength of any team of exactly <code>x</code> players.</p>
<ul><li><code>1 &lt;= heights.length &lt;= 10^5</code></li><li><code>1 &lt;= heights[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Monotonic stack: each player is the shortest of a widest window of some length L; record it for L, then take suffix maxima",
                module="Gold: Stacks", url="https://usaco.guide/gold/stacks", similar="CF Mike and Feet ★")
    examples = [([1, 2, 3, 4, 5, 4, 3, 2, 1, 6],), ([4, 4],)]
    edges = [([5],), ([3, 1, 3],)]

    def ref(heights: List[int]) -> List[int]:
        n = len(heights)
        left, right, stack = [-1] * n, [n] * n, []
        for i, h in enumerate(heights):
            while stack and heights[stack[-1]] >= h:
                right[stack.pop()] = i
            left[i] = stack[-1] if stack else -1
            stack.append(i)
        best = [0] * (n + 2)
        for i, h in enumerate(heights):
            width = right[i] - left[i] - 1
            best[width] = max(best[width], h)
        for x in range(n - 1, 0, -1):
            best[x] = max(best[x], best[x + 1])
        return best[1:n + 1]

    def brute(heights):
        n = len(heights)
        return [max(min(heights[i:i + x]) for i in range(n - x + 1)) for x in range(1, n + 1)]

    def gen(rng, big):
        if big:
            return ([rng.randint(1, 10**9) for _ in range(100000)],)
        return ([rng.randint(1, 5) for _ in range(rng.randint(1, 9))],)


@problem
class BulkDiscounts:
    title = "Bulk Discounts"
    difficulty = "Medium"
    func = "processQueries"
    tl = 3.0
    statement = """
<p>A store tracks <code>prices</code>. Process <code>queries</code> in order:</p>
<ul><li><code>[1, l, r, delta]</code>: add <code>delta</code> to every price in <code>prices[l..r]</code>, inclusive.</li>
<li><code>[2, i]</code>: report the current <code>prices[i]</code>.</li></ul>
<p>Return the answers to all type-2 queries, in order.</p>
<ul><li><code>1 &lt;= prices.length, queries.length &lt;= 10^5</code></li><li><code>-10^9 &lt;= prices[i], delta &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Fenwick tree over a difference array: a range add is two point updates, a point value is a prefix sum",
                module="Gold: Point Update Range Sum", url="https://usaco.guide/gold/PURS", similar="CSES Range Update Queries ★")
    examples = [([3, 2, 4, 5, 1], [[2, 2], [1, 1, 3, 10], [2, 2], [2, 4]]),]
    edges = [([0], [[1, 0, 0, 5], [2, 0]]),]

    def ref(prices: List[int], queries: List[List[int]]) -> List[int]:
        n = len(prices)
        tree, out = [0] * (n + 2), []

        def add(i, v):
            i += 1
            while i <= n:
                tree[i] += v
                i += i & -i

        for q in queries:
            if q[0] == 1:
                add(q[1], q[3])
                add(q[2] + 1, -q[3])
            else:
                i, s = q[1] + 1, 0
                while i > 0:
                    s += tree[i]
                    i -= i & -i
                out.append(prices[q[1]] + s)
        return out

    def brute(prices, queries):
        p, out = prices[:], []
        for q in queries:
            if q[0] == 1:
                for i in range(q[1], q[2] + 1):
                    p[i] += q[3]
            else:
                out.append(p[q[1]])
        return out

    def gen(rng, big):
        n, Q, V = (100000, 100000, 10**9) if big else (rng.randint(1, 6), rng.randint(1, 8), 9)
        qs = []
        for _ in range(Q):
            if rng.random() < 0.5:
                l, r = sorted((rng.randrange(n), rng.randrange(n)))
                qs.append([1, l, r, rng.randint(-V, V)])
            else:
                qs.append([2, rng.randrange(n)])
        return [rng.randint(-V, V) for _ in range(n)], qs


@problem
class FastPower:
    title = "Fast Power"
    difficulty = "Easy"
    func = "powerMod"
    statement = """
<p>For each query <code>[a, b]</code>, return <code>a^b</code> modulo <code>10^9 + 7</code> (take <code>0^0 = 1</code>).
Try it without the built-in three-argument <code>pow</code>.</p>
<ul><li><code>1 &lt;= queries.length &lt;= 10^5</code></li><li><code>0 &lt;= a, b &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Binary exponentiation: square the base and halve the exponent, multiplying in the base when the low bit is 1",
                module="Gold: Modular Arithmetic", url="https://usaco.guide/gold/modular", similar="CSES Exponentiation (focus problem) · LeetCode 50")
    examples = [([[3, 4], [2, 8], [123, 0]],),]
    edges = [([[0, 0], [0, 5], [10**9, 10**9]],)]

    def ref(queries: List[List[int]]) -> List[int]:
        M, out = 10**9 + 7, []
        for a, b in queries:
            result, base = 1, a % M
            while b:
                if b & 1:
                    result = result * base % M
                base = base * base % M
                b >>= 1
            out.append(result)
        return out

    def brute(queries):
        return [pow(a, b, MOD) for a, b in queries]

    def gen(rng, big):
        n, V = (100000, 10**9) if big else (rng.randint(1, 5), 20)
        return ([[rng.randint(0, V), rng.randint(0, V)] for _ in range(n)],)


@problem
class DivisorCounts:
    title = "Divisor Counts"
    difficulty = "Medium"
    func = "divisorCounts"
    tl = 3.0
    statement = """
<p>For each number in <code>nums</code>, return how many positive divisors it has.</p>
<ul><li><code>1 &lt;= nums.length &lt;= 10^5</code></li><li><code>1 &lt;= nums[i] &lt;= 2 * 10^5</code></li></ul>"""
    hint = dict(pattern="Sieve: for every d, add 1 to all multiples of d (n/1 + n/2 + ... = O(n log n)); trial division per query is too slow",
                module="Gold: Divisibility", url="https://usaco.guide/gold/divisibility", similar="CSES Counting Divisors (focus problem)")
    examples = [([16, 17, 18],), ([1],)]
    edges = [([200000, 1, 2],)]

    def ref(nums: List[int]) -> List[int]:
        top = max(nums)
        count = [0] * (top + 1)
        for d in range(1, top + 1):
            for m in range(d, top + 1, d):
                count[m] += 1
        return [count[x] for x in nums]

    def brute(nums):
        return [sum(x % d == 0 for d in range(1, x + 1)) for x in nums]

    def gen(rng, big):
        if big:
            return ([rng.randint(1, 2 * 10**5) for _ in range(100000)],)
        return ([rng.randint(1, 60) for _ in range(rng.randint(1, 5))],)


# ================================================================ Bronze: simulation, geometry, sorting, sets

@problem
class ShellGame:
    title = "Shell Game"
    difficulty = "Easy"
    func = "bestScore"
    statement = """
<p>A pebble is hidden under one of three shells (numbered 0, 1, 2), but you don't know which. Each move
<code>[a, b, g]</code> swaps shells <code>a</code> and <code>b</code>, then a guess says the pebble is under shell
<code>g</code>. For the best possible starting shell, return how many guesses would be correct.</p>
<ul><li><code>1 &lt;= moves.length &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="Complete search: simulate all three possible starting shells and keep the best score",
                module="Bronze: Simulation", url="https://usaco.guide/bronze/simulation", similar="USACO Shell Game (focus problem)")
    examples = [([[0, 1, 0], [2, 1, 1], [1, 2, 0]],),]
    edges = [([[0, 0, 0]],), ([[0, 1, 2]],)]

    def ref(moves: List[List[int]]) -> int:
        best = 0
        for start in range(3):
            pos, score = start, 0
            for a, b, g in moves:
                if pos == a:
                    pos = b
                elif pos == b:
                    pos = a
                score += pos == g
            best = max(best, score)
        return best

    def brute(moves):
        best = 0
        for start in range(3):
            shells = [s == start for s in range(3)]
            score = 0
            for a, b, g in moves:
                shells[a], shells[b] = shells[b], shells[a]
                score += shells[g]
            best = max(best, score)
        return best

    def gen(rng, big):
        return ([[*rng.sample(range(3), 2), rng.randrange(3)] for _ in range(100000 if big else rng.randint(1, 6))],)


@problem
class MixingMilk:
    title = "Mixing Milk"
    difficulty = "Easy"
    func = "pourMilk"
    statement = """
<p>Three buckets have capacities <code>capacity</code> and currently hold <code>milk</code>. You pour bucket 0 into
bucket 1, then 1 into 2, then 2 into 0, then 0 into 1 again, and so on, for <code>pours</code> pours in total. Each
pour moves as much milk as fits. Return the final amounts.</p>
<ul><li><code>1 &lt;= capacity[i] &lt;= 10^9</code>, <code>0 &lt;= milk[i] &lt;= capacity[i]</code></li><li><code>0 &lt;= pours &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="Direct simulation: the amount moved is min(source, room left in the target)",
                module="Bronze: Simulation", url="https://usaco.guide/bronze/simulation", similar="USACO Mixing Milk (focus problem)")
    examples = [([10, 11, 12], [3, 4, 5], 100), ([5, 5, 5], [5, 0, 0], 2)]
    edges = [([1, 1, 1], [1, 1, 1], 7), ([4, 4, 4], [2, 3, 1], 0)]

    def ref(capacity: List[int], milk: List[int], pours: int) -> List[int]:
        m = milk[:]
        for k in range(pours):
            a, b = k % 3, (k + 1) % 3
            moved = min(m[a], capacity[b] - m[b])
            m[a] -= moved
            m[b] += moved
        return m

    def brute(capacity, milk, pours):
        m = milk[:]
        for k in range(pours):
            a, b = k % 3, (k + 1) % 3
            while m[a] and m[b] < capacity[b]:  # one unit at a time
                m[a] -= 1
                m[b] += 1
        return m

    def gen(rng, big):
        cap = [rng.randint(1, 10**9 if big else 6) for _ in range(3)]
        return cap, [rng.randint(0, c) for c in cap], 100000 if big else rng.randint(0, 8)


@problem
class SpeedingTicket:
    title = "Speeding Ticket"
    difficulty = "Easy"
    func = "worstSpeeding"
    statement = """
<p>A road is split into segments <code>limits[i] = [length, speed limit]</code>, and a trip along it is split into
segments <code>trip[j] = [length, speed]</code>; both cover the same total length. Return the most the driver ever went
over the limit (<code>0</code> if never).</p>
<ul><li><code>1 &lt;= limits.length, trip.length &lt;= 10^4</code></li><li>total length <code>&lt;= 10^5</code>; speeds <code>&lt;= 10^4</code></li></ul>"""
    hint = dict(pattern="Expand both lists to one value per mile (or sweep both segment lists with two pointers) and compare",
                module="Bronze: Simulation", url="https://usaco.guide/bronze/simulation", similar="USACO Speeding Ticket ★")
    examples = [([[40, 75], [50, 35], [10, 45]], [[40, 76], [20, 30], [40, 40]]),]
    edges = [([[5, 10]], [[5, 10]]), ([[1, 3], [1, 1]], [[2, 2]])]

    def ref(limits: List[List[int]], trip: List[List[int]]) -> int:
        i = j = worst = 0
        left_i, left_j = limits[0][0], trip[0][0]
        while i < len(limits) and j < len(trip):
            worst = max(worst, trip[j][1] - limits[i][1])
            step = min(left_i, left_j)
            left_i -= step
            left_j -= step
            if not left_i:
                i += 1
                left_i = limits[i][0] if i < len(limits) else 0
            if not left_j:
                j += 1
                left_j = trip[j][0] if j < len(trip) else 0
        return worst

    def brute(limits, trip):
        a = [s for length, s in limits for _ in range(length)]
        b = [s for length, s in trip for _ in range(length)]
        return max(0, max(y - x for x, y in zip(a, b)))

    def gen(rng, big):
        total = 100000 if big else rng.randint(1, 10)

        def split():
            cuts = sorted(rng.sample(range(1, total), min(total - 1, 9999 if big else rng.randint(0, 3)))) if total > 1 else []
            pts = [0] + cuts + [total]
            return [[b - a, rng.randint(1, 10**4 if big else 9)] for a, b in zip(pts, pts[1:])]

        return split(), split()


@problem
class BlockGame:
    title = "Letter Blocks"
    difficulty = "Easy"
    func = "blocksNeeded"
    statement = """
<p>Each card in <code>cards</code> has a word on the front and a word on the back (<code>[front, back]</code>); only one
side will be shown, and you don't know which. To spell whatever word is shown on every card at the same time, you need
letter blocks. Return how many blocks of each letter <code>'a'</code> to <code>'z'</code> you need to be sure to have
enough (a list of 26 counts).</p>
<ul><li><code>1 &lt;= cards.length &lt;= 10^4</code></li><li>words are lowercase, 1 to 10 letters</li></ul>"""
    hint = dict(pattern="For each card and letter, you need the larger of the two words' counts; add those up over all cards",
                module="Bronze: Simulation", url="https://usaco.guide/bronze/simulation", similar="USACO Block Game ★")
    examples = [([["fox", "box"], ["dog", "cat"], ["car", "bus"]],),]
    edges = [([["a", "a"]],), ([["aab", "b"]],)]

    def ref(cards: List[List[str]]) -> List[int]:
        need = [0] * 26
        for front, back in cards:
            cf, cb = Counter(front), Counter(back)
            for k in range(26):
                ch = chr(97 + k)
                need[k] += max(cf[ch], cb[ch])
        return need

    def brute(cards):
        from itertools import product
        need = [0] * 26
        for shown in product(*cards):  # every combination of shown sides (small cases only)
            total = Counter("".join(shown))
            for k in range(26):
                need[k] = max(need[k], total[chr(97 + k)])
        return need

    def gen(rng, big):
        n, alpha = (10000, "abcdefghijklmnopqrstuvwxyz") if big else (rng.randint(1, 5), "abc")
        word = lambda: "".join(rng.choice(alpha) for _ in range(rng.randint(1, 10 if big else 3)))
        return ([[word(), word()] for _ in range(n)],)


@problem
class FencePainting:
    title = "Fence Painting"
    difficulty = "Easy"
    func = "paintedLength"
    statement = """
<p>Two painters each paint one stretch of a fence: <code>first = [a, b]</code> covers positions <code>a</code> to
<code>b</code>, and <code>second = [c, d]</code> covers <code>c</code> to <code>d</code>. Return the total length of fence
that ends up painted.</p>
<ul><li><code>0 &lt;= a &lt; b &lt;= 10^9</code>, <code>0 &lt;= c &lt; d &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Add both lengths and subtract the overlap max(0, min(b, d) - max(a, c))",
                module="Bronze: Rectangle Geometry", url="https://usaco.guide/bronze/rect-geo", similar="USACO Fence Painting (focus problem)")
    examples = [([7, 10], [4, 8]), ([1, 2], [5, 9])]
    edges = [([0, 5], [0, 5]), ([0, 10], [3, 4])]

    def ref(first: List[int], second: List[int]) -> int:
        (a, b), (c, d) = first, second
        return (b - a) + (d - c) - max(0, min(b, d) - max(a, c))

    def brute(first, second):
        return len(set(range(*first)) | set(range(*second)))

    def gen(rng, big):
        V = 10**9 if big else 12  # big cases only time the reference; the brute force never sees them
        return sorted(rng.sample(range(V), 2)), sorted(rng.sample(range(V), 2))


@problem
class BlockedBillboard:
    title = "Blocked Billboards"
    difficulty = "Easy"
    func = "visibleArea"
    statement = """
<p>Two billboards <code>b1</code> and <code>b2</code> (which don't overlap each other) and a parked truck are axis-aligned
rectangles <code>[x1, y1, x2, y2]</code> (lower-left and upper-right corners). Return the total billboard area that is
still visible, i.e. not covered by the truck.</p>
<ul><li>coordinates between <code>-1000</code> and <code>1000</code></li></ul>"""
    hint = dict(pattern="Visible area = area(b) - overlap(b, truck) for each billboard; overlap width = max(0, min(right) - max(left))",
                module="Bronze: Rectangle Geometry", url="https://usaco.guide/bronze/rect-geo", similar="USACO Blocked Billboard (focus problem)")
    examples = [([1, 2, 3, 5], [6, 0, 10, 4], [2, 1, 8, 3]),]
    edges = [([0, 0, 1, 1], [2, 2, 3, 3], [-5, -5, 5, 5]), ([0, 0, 1, 1], [2, 2, 3, 3], [5, 5, 6, 6])]

    def ref(b1: List[int], b2: List[int], truck: List[int]) -> int:
        def area(r):
            return (r[2] - r[0]) * (r[3] - r[1])

        def overlap(a, b):
            w = min(a[2], b[2]) - max(a[0], b[0])
            h = min(a[3], b[3]) - max(a[1], b[1])
            return w * h if w > 0 and h > 0 else 0

        return area(b1) + area(b2) - overlap(b1, truck) - overlap(b2, truck)

    def brute(b1, b2, truck):
        cells = lambda r: {(x, y) for x in range(r[0], r[2]) for y in range(r[1], r[3])}
        return len((cells(b1) | cells(b2)) - cells(truck))

    def gen(rng, big):
        V = 1000 if big else 6

        def rect():
            x1, x2 = sorted(rng.sample(range(-V, V + 1), 2))
            y1, y2 = sorted(rng.sample(range(-V, V + 1), 2))
            return [x1, y1, x2, y2]

        while True:
            a, b = rect(), rect()
            if min(a[2], b[2]) <= max(a[0], b[0]) or min(a[3], b[3]) <= max(a[1], b[1]):  # billboards must not overlap
                return a, b, rect()


@problem
class BlockedBillboard2:
    title = "Tarp Cover"
    difficulty = "Medium"
    func = "tarpArea"
    statement = """
<p>A lawn-mower billboard <code>lawn</code> is partly hidden behind a feed billboard <code>feed</code> (both axis-aligned
rectangles <code>[x1, y1, x2, y2]</code>). You want to cover every <b>visible</b> part of the lawn-mower billboard with
one rectangular tarp (which may also cover other things). Return the smallest possible tarp area.</p>
<ul><li>coordinates between <code>-1000</code> and <code>1000</code></li></ul>"""
    hint = dict(pattern="The tarp only shrinks if the feed billboard covers a full-width or full-height strip from one edge; check corners carefully",
                module="Bronze: Rectangle Geometry", url="https://usaco.guide/bronze/rect-geo", similar="USACO Blocked Billboard II ★")
    examples = [([2, 1, 7, 4], [5, -1, 10, 3]), ([0, 0, 4, 4], [0, 2, 4, 9])]
    edges = [([0, 0, 2, 2], [-1, -1, 3, 3]), ([0, 0, 2, 2], [5, 5, 6, 6])]

    def ref(lawn: List[int], feed: List[int]) -> int:
        x1, y1, x2, y2 = lawn
        a1, b1, a2, b2 = feed
        if a1 <= x1 and b1 <= y1 and a2 >= x2 and b2 >= y2:
            return 0  # fully hidden
        covers_x = a1 <= x1 and a2 >= x2  # feed spans the whole width
        covers_y = b1 <= y1 and b2 >= y2  # feed spans the whole height
        if covers_x and b1 <= y1 < b2:  # bottom strip hidden
            y1 = b2
        elif covers_x and b1 < y2 <= b2:  # top strip hidden
            y2 = b1
        elif covers_y and a1 <= x1 < a2:  # left strip hidden
            x1 = a2
        elif covers_y and a1 < x2 <= a2:  # right strip hidden
            x2 = a1
        return (x2 - x1) * (y2 - y1)

    def brute(lawn, feed):
        vis = [(x, y) for x in range(lawn[0], lawn[2]) for y in range(lawn[1], lawn[3])
               if not (feed[0] <= x < feed[2] and feed[1] <= y < feed[3])]
        if not vis:
            return 0
        xs, ys = [p[0] for p in vis], [p[1] for p in vis]
        return (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1)

    def gen(rng, big):
        V = 1000 if big else 5

        def rect():
            x1, x2 = sorted(rng.sample(range(-V, V + 1), 2))
            y1, y2 = sorted(rng.sample(range(-V, V + 1), 2))
            return [x1, y1, x2, y2]

        return rect(), rect()


@problem
class DistinctNumbers:
    title = "Distinct Numbers"
    difficulty = "Easy"
    func = "countDistinct"
    statement = """
<p>Return how many different values appear in <code>nums</code>.</p>
<ul><li><code>1 &lt;= nums.length &lt;= 2 * 10^5</code></li><li><code>1 &lt;= nums[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="A set (or sort and count value changes)",
                module="Bronze: Introduction to Sets & Maps", url="https://usaco.guide/bronze/intro-sets",
                similar="CSES Distinct Numbers ★ (focus problem) · LeetCode 217")
    examples = [([2, 3, 2, 2, 3],), ([7],)]
    edges = [([1, 2, 3],)]

    def ref(nums: List[int]) -> int:
        return len(set(nums))

    def brute(nums):
        s = sorted(nums)
        return 1 + sum(a != b for a, b in zip(s, s[1:]))

    def gen(rng, big):
        if big:
            return ([rng.randint(1, 10**9 if rng.random() < 0.5 else 1000) for _ in range(200000)],)
        return ([rng.randint(1, 5) for _ in range(rng.randint(1, 8))],)


@problem
class Kayaking:
    title = "Kayak Pairs"
    difficulty = "Medium"
    func = "minInstability"
    statement = """
<p><code>2n</code> people with weights <code>weights</code> take <code>n - 1</code> two-person kayaks and <code>2</code>
one-person kayaks. A two-person kayak's instability is the difference between its riders' weights; one-person kayaks
have none. Return the smallest possible total instability.</p>
<ul><li><code>2 &lt;= n &lt;= 50</code> (so <code>4 &lt;= weights.length &lt;= 100</code>)</li><li><code>1 &lt;= weights[i] &lt;= 1000</code></li></ul>"""
    hint = dict(pattern="Try every pair of people for the solo kayaks; pair everyone else as neighbors in sorted order",
                module="Bronze: Introduction to Sorting", url="https://usaco.guide/bronze/intro-sorting", similar="CF Kayaking ★")
    examples = [([1, 2, 3, 4],), ([1, 3, 4, 6, 3, 4, 100, 200],)]
    edges = [([5, 5, 5, 5],)]

    def ref(weights: List[int]) -> int:
        w, best = sorted(weights), float("inf")
        for i in range(len(w)):
            for j in range(i + 1, len(w)):
                rest = w[:i] + w[i + 1:j] + w[j + 1:]
                best = min(best, sum(rest[k + 1] - rest[k] for k in range(0, len(rest), 2)))
        return best

    def brute(weights):
        @lru_cache(None)
        def f(left, solos):  # left: sorted tuple of unplaced people
            if not left:
                return 0 if solos == 0 else float("inf")
            first, rest = left[0], left[1:]
            best = f(rest, solos - 1) if solos else float("inf")
            for k in range(len(rest)):
                best = min(best, abs(rest[k] - first) + f(rest[:k] + rest[k + 1:], solos))
            return best

        return f(tuple(sorted(weights)), 2)

    def gen(rng, big):
        n = 50 if big else rng.randint(2, 4)
        return ([rng.randint(1, 1000 if big else 20) for _ in range(2 * n)],)


@problem
class BubbleSortStats:
    title = "Bubble Sort Report"
    difficulty = "Easy"
    func = "bubbleReport"
    statement = """
<p>Sort <code>nums</code> into ascending order with bubble sort (repeatedly swap adjacent out-of-order elements). Return
<code>[number of swaps made, first element, last element]</code> of the sorted array.</p>
<ul><li><code>1 &lt;= nums.length &lt;= 1000</code></li><li><code>1 &lt;= nums[i] &lt;= 10^6</code></li></ul>"""
    hint = dict(pattern="Simulate bubble sort and count the swaps (the count equals the number of inversions)",
                module="Bronze: Introduction to Sorting", url="https://usaco.guide/bronze/intro-sorting", similar="HackerRank Sorting: Bubble Sort (focus problem)")
    examples = [([3, 2, 1],), ([1, 2, 3],)]
    edges = [([5],), ([2, 2, 1],)]

    def ref(nums: List[int]) -> List[int]:
        a, swaps = nums[:], 0
        for i in range(len(a)):
            for j in range(len(a) - 1 - i):
                if a[j] > a[j + 1]:
                    a[j], a[j + 1] = a[j + 1], a[j]
                    swaps += 1
        return [swaps, a[0], a[-1]]

    def brute(nums):
        inv = sum(nums[i] > nums[j] for i in range(len(nums)) for j in range(i + 1, len(nums)))
        return [inv, min(nums), max(nums)]

    def gen(rng, big):
        if big:
            return ([rng.randint(1, 10**6) for _ in range(1000)],)
        return ([rng.randint(1, 5) for _ in range(rng.randint(1, 8))],)


@problem
class WhereAmI:
    title = "Where Am I?"
    difficulty = "Easy"
    func = "smallestUniqueWindow"
    statement = """
<p>Mailboxes along a road are painted with colors, given as the letters of <code>road</code>. Return the smallest
<code>k</code> such that every block of <code>k</code> consecutive mailboxes has a different color pattern from every
other such block, so that seeing any <code>k</code> mailboxes in a row tells you exactly where you are.</p>
<ul><li><code>1 &lt;= road.length &lt;= 500</code>, uppercase letters</li></ul>"""
    hint = dict(pattern="Try k = 1, 2, ...: put all length-k substrings in a set and stop when there are no repeats",
                module="Bronze: Introduction to Sets & Maps", url="https://usaco.guide/bronze/intro-sets", similar="USACO Where Am I? ★")
    examples = [("ABCDABC",), ("AAAA",)]
    edges = [("A",), ("AB",)]

    def ref(road: str) -> int:
        for k in range(1, len(road) + 1):
            subs = [road[i:i + k] for i in range(len(road) - k + 1)]
            if len(set(subs)) == len(subs):
                return k

    def brute(road):
        n = len(road)
        for k in range(1, n + 1):
            if all(road[i:i + k] != road[j:j + k] for i in range(n - k + 1) for j in range(i + 1, n - k + 1)):
                return k

    def gen(rng, big):
        n, alpha = (500, "AB") if big else (rng.randint(1, 9), "AB")
        return ("".join(rng.choice(alpha) for _ in range(n)),)


@problem
class DontBeLast:
    title = "Don't Be Last"
    difficulty = "Easy"
    func = "secondLowest"
    statement = """
<p>Seven cows, <code>Bessie, Elsie, Daisy, Gertie, Annabelle, Maggie, Henrietta</code>, produce milk. Each log entry
<code>[name, gallons]</code> records some milk from one cow (a cow may appear many times or never). Return the name of
the cow with the <b>second-smallest</b> total, meaning the smallest total that is larger than the minimum. If several
cows share that total, or there is no such total, return <code>"Tie"</code>.</p>
<ul><li><code>0 &lt;= log.length &lt;= 100</code>, <code>1 &lt;= gallons &lt;= 100</code></li></ul>"""
    hint = dict(pattern="Totals in a hash map (start every cow at 0), then find the smallest value above the minimum",
                module="Bronze: Introduction to Sets & Maps", url="https://usaco.guide/bronze/intro-sets", similar="USACO Don't Be Last! ★")
    COWS = ["Bessie", "Elsie", "Daisy", "Gertie", "Annabelle", "Maggie", "Henrietta"]
    examples = [([["Bessie", 1], ["Maggie", 13], ["Elsie", 3], ["Elsie", 4], ["Henrietta", 4], ["Gertie", 12], ["Daisy", 7],
                  ["Annabelle", 10], ["Bessie", 6], ["Henrietta", 5]],),]
    edges = [([],), ([["Bessie", 5]],)]

    def ref(log: List[list]) -> str:
        total = dict.fromkeys(["Bessie", "Elsie", "Daisy", "Gertie", "Annabelle", "Maggie", "Henrietta"], 0)
        for name, g in log:
            total[name] += g
        low = min(total.values())
        above = [v for v in total.values() if v > low]
        if not above:
            return "Tie"
        second = min(above)
        names = [c for c, v in total.items() if v == second]
        return names[0] if len(names) == 1 else "Tie"

    def brute(log):
        totals = sorted((sum(g for n, g in log if n == c), c) for c in DontBeLast.COWS)
        distinct = sorted({t for t, _ in totals})
        if len(distinct) < 2:
            return "Tie"
        who = [c for t, c in totals if t == distinct[1]]
        return who[0] if len(who) == 1 else "Tie"

    def gen(rng, big):
        n = 100 if big else rng.randint(0, 8)
        return ([[rng.choice(DontBeLast.COWS), rng.randint(1, 100 if big else 4)] for _ in range(n)],)


@problem
class AssociativeArray:
    title = "Key-Value Store"
    difficulty = "Easy"
    func = "processQueries"
    statement = """
<p>Start with a store where every key's value is 0. Process <code>queries</code>: <code>[0, key, value]</code> sets the
key's value; <code>[1, key]</code> reads it. Return the values read, in order.</p>
<ul><li><code>1 &lt;= queries.length &lt;= 2 * 10^5</code></li><li><code>0 &lt;= key, value &lt;= 10^18</code></li></ul>"""
    hint = dict(pattern="A hash map with a default of 0",
                module="Bronze: Introduction to Sets & Maps", url="https://usaco.guide/bronze/intro-sets", similar="Yosupo Associative Array (focus problem)")
    examples = [([[0, 1, 2], [1, 1], [1, 2], [0, 2, 3], [1, 1], [1, 2]],),]
    edges = [([[1, 5]],), ([[0, 7, 1], [0, 7, 2], [1, 7]],)]

    def ref(queries: List[List[int]]) -> List[int]:
        store, out = {}, []
        for q in queries:
            if q[0] == 0:
                store[q[1]] = q[2]
            else:
                out.append(store.get(q[1], 0))
        return out

    def brute(queries):
        pairs, out = [], []
        for q in queries:
            if q[0] == 0:
                pairs.append((q[1], q[2]))
            else:
                out.append(next((v for k, v in reversed(pairs) if k == q[1]), 0))
        return out

    def gen(rng, big):
        n, K = (200000, 10**18) if big else (rng.randint(1, 8), 4)
        keys = [rng.randint(0, K) for _ in range(50 if big else 4)]
        return ([[0, rng.choice(keys), rng.randint(0, K)] if rng.random() < 0.5 else [1, rng.choice(keys)] for _ in range(n)],)


# ================================================================ Bronze: complete search, recursion, greedy, ad hoc

@problem
class MaxDistance:
    title = "Farthest Pair"
    difficulty = "Easy"
    func = "maxSquaredDistance"
    tl = 3.0
    statement = """
<p>Point <code>i</code> is at <code>(xs[i], ys[i])</code>. Return the largest <b>squared</b> distance between any two
points.</p>
<ul><li><code>2 &lt;= n &lt;= 1500</code></li><li><code>-1000 &lt;= xs[i], ys[i] &lt;= 1000</code></li></ul>"""
    hint = dict(pattern="Complete search over all pairs: n^2 / 2 checks is fast enough here",
                module="Bronze: Basic Complete Search", url="https://usaco.guide/bronze/intro-complete", similar="CF Maximum Distance (focus problem)")
    examples = [([321, -15, -525], [404, 373, 990]), ([0, 0], [0, 0])]
    edges = [([1, -1], [1, -1]),]

    def ref(xs: List[int], ys: List[int]) -> int:
        best = 0
        for i in range(len(xs)):
            xi, yi = xs[i], ys[i]
            for j in range(i + 1, len(xs)):
                d = (xi - xs[j]) ** 2 + (yi - ys[j]) ** 2
                if d > best:
                    best = d
        return best

    def brute(xs, ys):
        return max((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 for a, b in combinations(zip(xs, ys), 2))

    def gen(rng, big):
        n = 1500 if big else rng.randint(2, 6)
        return [rng.randint(-1000, 1000) for _ in range(n)], [rng.randint(-1000, 1000) for _ in range(n)]


@problem
class CowGymnastics:
    title = "Consistent Rankings"
    difficulty = "Easy"
    func = "consistentPairs"
    statement = """
<p>After several practice sessions, each session ranks the same <code>n</code> gymnasts: <code>sessions[s]</code> lists
the gymnasts <code>0..n-1</code> from best to worst. Count the ordered pairs <code>(a, b)</code> such that <code>a</code>
ranked above <code>b</code> in <b>every</b> session.</p>
<ul><li><code>1 &lt;= sessions.length &lt;= 10</code></li><li><code>1 &lt;= n &lt;= 100</code></li></ul>"""
    hint = dict(pattern="Complete search over pairs, with each session turned into a position lookup",
                module="Bronze: Basic Complete Search", url="https://usaco.guide/bronze/intro-complete", similar="USACO Cow Gymnastics ★")
    examples = [([[3, 0, 1, 2], [3, 0, 2, 1], [3, 1, 0, 2]],),]
    edges = [([[0]],), ([[0, 1], [1, 0]],)]

    def ref(sessions: List[List[int]]) -> int:
        n = len(sessions[0])
        pos = []
        for s in sessions:
            p = [0] * n
            for rank, g in enumerate(s):
                p[g] = rank
            pos.append(p)
        return sum(all(p[a] < p[b] for p in pos) for a in range(n) for b in range(n) if a != b)

    def brute(sessions):
        n = len(sessions[0])
        return sum(all(s.index(a) < s.index(b) for s in sessions) for a in range(n) for b in range(n) if a != b)

    def gen(rng, big):
        n, k = (100, 10) if big else (rng.randint(1, 5), rng.randint(1, 3))
        base = rng.sample(range(n), n)
        out = []
        for _ in range(k):  # mostly agreeing rankings, a few random swaps
            s = base[:]
            for _ in range(rng.randint(0, n)):
                i, j = rng.randrange(n), rng.randrange(n)
                s[i], s[j] = s[j], s[i]
            out.append(s)
        return (out,)


@problem
class GenomeClues:
    title = "Genome Clues"
    difficulty = "Easy"
    func = "explainingPositions"
    statement = """
<p>Each spotted and each plain cow has a genome: strings in <code>spotty</code> and <code>plain</code>, all the same
length, over the letters A, C, G, T. A position <b>explains</b> spottiness if no letter appearing there in a spotted
genome also appears there in a plain genome. Count such positions.</p>
<ul><li><code>1 &lt;= spotty.length, plain.length &lt;= 100</code></li><li>genome length <code>&lt;= 100</code></li></ul>"""
    hint = dict(pattern="For each position, build the set of spotted letters and check the plain letters against it",
                module="Bronze: Basic Complete Search", url="https://usaco.guide/bronze/intro-complete", similar="USACO Bovine Genomics ★ (Bronze)")
    examples = [(["AATCCCAT", "GATTGCAA", "GGTCGCAA"], ["ACTCCCAG", "ACTCGCAT", "ACTTCCAT"]),]
    edges = [(["A"], ["C"]), (["A"], ["A"])]

    def ref(spotty: List[str], plain: List[str]) -> int:
        return sum(not ({s[j] for s in spotty} & {p[j] for p in plain}) for j in range(len(spotty[0])))

    def brute(spotty, plain):
        return sum(all(s[j] != p[j] for s in spotty for p in plain) for j in range(len(spotty[0])))

    def gen(rng, big):
        n, m = (100, 100) if big else (rng.randint(1, 3), rng.randint(1, 6))
        g = lambda alpha: "".join(rng.choice(alpha) for _ in range(m))
        return [g("AC") for _ in range(n)], [g("GTA") for _ in range(n)]


@problem
class GenomeTriples:
    title = "Genome Triples"
    difficulty = "Hard"
    func = "explainingTriples"
    statement = """
<p>Spotted and plain cows have genomes <code>spotty</code> and <code>plain</code> (equal-length strings over A, C, G, T).
A set of three positions <code>i &lt; j &lt; k</code> <b>explains</b> spottiness if no three-letter combination read at
those positions from a spotted genome also appears there in a plain genome. Count such triples.</p>
<ul><li><code>1 &lt;= spotty.length, plain.length &lt;= 200</code></li><li>genome length <code>&lt;= 30</code></li></ul>"""
    hint = dict(pattern="Complete search over position triples; encode the three letters as one number 0..63 and use a small lookup array instead of a set",
                module="Bronze: Basic Complete Search", url="https://usaco.guide/bronze/intro-complete", similar="USACO Bovine Genomics ★ (Silver)")
    examples = [(["AATCCCAT", "GATTGCAA", "GGTCGCAA"], ["ACTCCCAG", "ACTCGCAT", "ACTTCCAT"]),]
    edges = [(["AAA"], ["AAA"]), (["ACG"], ["CGT"])]

    def ref(spotty: List[str], plain: List[str]) -> int:
        code = {"A": 0, "C": 1, "G": 2, "T": 3}
        S = [[code[ch] for ch in g] for g in spotty]
        P = [[code[ch] for ch in g] for g in plain]
        m, count = len(spotty[0]), 0
        for i in range(m):
            for j in range(i + 1, m):
                for k in range(j + 1, m):
                    seen = [False] * 64
                    for g in S:
                        seen[g[i] * 16 + g[j] * 4 + g[k]] = True
                    if not any(seen[g[i] * 16 + g[j] * 4 + g[k]] for g in P):
                        count += 1
        return count

    def brute(spotty, plain):
        m = len(spotty[0])
        return sum(not ({s[i] + s[j] + s[k] for s in spotty} & {p[i] + p[j] + p[k] for p in plain})
                   for i, j, k in combinations(range(m), 3))

    def gen(rng, big):
        n, m = (200, 30) if big else (rng.randint(1, 3), rng.randint(3, 6))
        g = lambda: "".join(rng.choice("ACGT") for _ in range(m))
        return [g() for _ in range(n)], [g() for _ in range(n)]


@problem
class CrossingPairs:
    title = "Crossing Paths"
    difficulty = "Medium"
    func = "crossingPairs"
    statement = """
<p>A circular track is marked at evenly spaced points, listed clockwise in <code>track</code>. Each letter appears exactly
twice: that cow always walks between her two marks along a straight chord across the field. Count the pairs of cows
whose chords cross, i.e. whose marks alternate around the circle (a, b, a, b).</p>
<ul><li><code>2 &lt;= track.length &lt;= 52</code>; uppercase letters, each exactly twice</li></ul>"""
    hint = dict(pattern="Two chords cross iff exactly one mark of b lies between the two marks of a",
                module="Bronze: Basic Complete Search", url="https://usaco.guide/bronze/intro-complete", similar="USACO Why Did the Cow Cross the Road II ★ (Bronze)")
    examples = [("ABCCABDDEEZZ",), ("AABB",)]
    edges = [("ABAB",), ("ABBA",)]

    def ref(track: str) -> int:
        first, second = {}, {}
        for i, ch in enumerate(track):
            (second if ch in first else first)[ch] = i
        cows = list(first)
        return sum((first[a] < first[b] < second[a]) != (first[a] < second[b] < second[a])
                   for x, a in enumerate(cows) for b in cows[x + 1:])

    def brute(track):
        cows, count = sorted(set(track)), 0
        for a, b in combinations(cows, 2):
            seq = "".join(ch for ch in track if ch in (a, b))
            count += seq in (a + b + a + b, b + a + b + a)
        return count

    def gen(rng, big):
        k = 26 if big else rng.randint(1, 5)
        letters = [chr(65 + i) for i in range(k)] * 2
        rng.shuffle(letters)
        return ("".join(letters),)


@problem
class LoadBalancing:
    title = "Load Balancing"
    difficulty = "Medium"
    func = "bestFence"
    statement = """
<p>Cows stand at points <code>cows[i] = [x, y]</code> with odd coordinates. You build one north-south fence along
<code>x = a</code> and one east-west fence along <code>y = b</code>, with <code>a</code> and <code>b</code> even, splitting
the field into four regions. Return the smallest possible size of the most crowded region.</p>
<ul><li><code>1 &lt;= cows.length &lt;= 100</code></li><li><code>1 &lt;= x, y &lt;= 10^6</code>, both odd</li></ul>"""
    hint = dict(pattern="Only fence positions just past a cow (x + 1, y + 1) or before everyone (0) matter: try all of them",
                module="Bronze: Basic Complete Search", url="https://usaco.guide/bronze/intro-complete", similar="USACO Load Balancing ★ (Bronze)")
    examples = [([[7, 3], [5, 5], [9, 7], [3, 1], [7, 7], [5, 3], [9, 1]],),]
    edges = [([[1, 1]],), ([[1, 1], [3, 3]],)]

    def ref(cows: List[List[int]]) -> int:
        best = len(cows)
        for a in {0} | {x + 1 for x, _ in cows}:
            for b in {0} | {y + 1 for _, y in cows}:
                q = [0, 0, 0, 0]
                for x, y in cows:
                    q[(x > a) * 2 + (y > b)] += 1
                best = min(best, max(q))
        return best

    def brute(cows):
        top = max(max(x, y) for x, y in cows) + 1
        best = len(cows)
        for a in range(0, top + 1, 2):
            for b in range(0, top + 1, 2):
                regions = Counter((x < a, y < b) for x, y in cows)
                best = min(best, max(regions.values()))
        return best

    def gen(rng, big):
        n, V = (100, 10**6) if big else (rng.randint(1, 6), 9)
        odd = lambda: rng.randrange(1, V + 1, 2)
        return ([[odd(), odd()] for _ in range(n)],)


@problem
class SleepingInClass:
    title = "Even Logs"
    difficulty = "Hard"
    func = "minMerges"
    statement = """
<p>A study log records <code>hours[i]</code> for each day. In one move you merge two <b>adjacent</b> entries into a single
entry holding their sum. Return the fewest moves needed so that all remaining entries are equal.</p>
<ul><li><code>1 &lt;= hours.length &lt;= 2 * 10^4</code></li><li><code>0 &lt;= hours[i]</code>, total <code>&lt;= 10^6</code></li></ul>"""
    hint = dict(pattern="If k entries remain, each equals total / k: try every divisor k of the total, largest first, and check greedily with running sums",
                module="Bronze: Basic Complete Search", url="https://usaco.guide/bronze/intro-complete", similar="USACO Sleeping in Class ★")
    examples = [([1, 2, 3, 1, 1, 1],), ([2, 2, 3],), ([0, 0, 0, 0, 0],)]
    edges = [([5],), ([1, 0, 1],)]

    def ref(hours: List[int]) -> int:
        total, n = sum(hours), len(hours)
        if total == 0:
            return 0
        for k in range(n, 0, -1):
            if total % k:
                continue
            target, run, ok = total // k, 0, True
            for h in hours:
                run += h
                if run == target:
                    run = 0
                elif run > target:
                    ok = False
                    break
            if ok and run == 0:
                return n - k

    def brute(hours):
        start = tuple(hours)
        dist, q = {start: 0}, deque([start])
        while q:
            a = q.popleft()
            if len(set(a)) == 1:
                return dist[a]
            for i in range(len(a) - 1):
                b = a[:i] + (a[i] + a[i + 1],) + a[i + 2:]
                if b not in dist:
                    dist[b] = dist[a] + 1
                    q.append(b)

    def gen(rng, big):
        if big:
            return ([rng.choice([0, 1, 2, 2, 3, 50]) for _ in range(20000)],)
        return ([rng.randint(0, 3) for _ in range(rng.randint(1, 7))],)


@problem
class CowCheckups:
    title = "Checkup Reversals"
    difficulty = "Hard"
    func = "checkupCounts"
    tl = 3.0
    statement = """
<p>Cows line up in order <code>a</code>; the vet wants to check cow <code>b[i]</code> at position <code>i</code>. Before
the checkups you reverse exactly one segment <code>a[l..r]</code> (<code>l &lt;= r</code>; a one-cow segment changes
nothing). For each count <code>c</code> from 0 to <code>n</code>, return how many of the <code>n(n+1)/2</code> choices
of segment leave exactly <code>c</code> positions where <code>a[i] == b[i]</code>.</p>
<ul><li><code>1 &lt;= n &lt;= 1500</code></li><li><code>1 &lt;= a[i], b[i] &lt;= n</code></li></ul>"""
    hint = dict(pattern="Expand segments around each center: growing [l, r] to [l-1, r+1] changes the match count by O(1), so all segments take O(n^2)",
                module="Bronze: Basic Complete Search", url="https://usaco.guide/bronze/intro-complete", similar="USACO Cow Checkups ★ (Bronze and Silver)")
    examples = [([1, 3, 2], [3, 2, 1]), ([1, 2, 3], [1, 2, 3])]
    edges = [([1], [1]), ([1], [2])]

    def ref(a: List[int], b: List[int]) -> List[int]:
        n = len(a)
        same = [int(x == y) for x, y in zip(a, b)]
        base = sum(same)
        out = [0] * (n + 1)
        for center in range(2 * n - 1):
            l, r = center // 2, (center + 1) // 2
            inside_old = inside_new = 0
            while l >= 0 and r < n:
                if l == r:
                    inside_old += same[l]
                    inside_new += same[l]
                else:
                    inside_old += same[l] + same[r]
                    inside_new += (a[r] == b[l]) + (a[l] == b[r])
                out[base - inside_old + inside_new] += 1
                l -= 1
                r += 1
        return out

    def brute(a, b):
        n, out = len(a), [0] * (len(a) + 1)
        for l in range(n):
            for r in range(l, n):
                c = a[:l] + a[l:r + 1][::-1] + a[r + 1:]
                out[sum(x == y for x, y in zip(c, b))] += 1
        return out

    def gen(rng, big):
        n = 1500 if big else rng.randint(1, 6)
        V = 3 if not big else n
        return [rng.randint(1, V) for _ in range(n)], [rng.randint(1, V) for _ in range(n)]


def _contact_sim(n, shakes, p, K):
    """Infection state after all handshakes when cow p starts sick and each sick cow passes it on in her next K handshakes."""
    sick, left = [False] * n, [0] * n
    sick[p], left[p] = True, K
    for _, x, y in sorted(shakes):
        sx, sy = sick[x] and left[x] > 0, sick[y] and left[y] > 0
        if sick[x]:
            left[x] = max(0, left[x] - 1)
        if sick[y]:
            left[y] = max(0, left[y] - 1)
        if sx and not sick[y]:
            sick[y], left[y] = True, K
        if sy and not sick[x]:
            sick[x], left[x] = True, K
    return "".join("1" if s else "0" for s in sick)


@problem
class ContactTracing:
    title = "Contact Tracing"
    difficulty = "Hard"
    func = "traceOutbreak"
    statement = """
<p><code>n</code> cows shook hooves; each handshake is <code>[time, x, y]</code> (all times distinct, listed in any
order). Exactly one cow, patient zero, was sick at the start. A sick cow passes the illness on during her next
<code>K</code> handshakes after getting sick (every handshake counts toward K, even with a cow that is already sick);
after that she stays sick but is no longer contagious. <code>final[i]</code> is <code>'1'</code> if cow <code>i</code> is
sick at the end. Return <code>[number of cows that could be patient zero, smallest possible K, largest possible K]</code>,
using <code>-1</code> for the largest K if it could be arbitrarily large. At least one scenario fits.</p>
<ul><li><code>1 &lt;= n &lt;= 50</code></li><li><code>0 &lt;= shakes.length &lt;= 150</code></li></ul>"""
    hint = dict(pattern="Complete search: simulate every (patient zero, K) with K from 0 to the number of handshakes (any larger K behaves the same)",
                module="Bronze: Basic Complete Search", url="https://usaco.guide/bronze/intro-complete", similar="USACO Cowntact Tracing ★")
    examples = [(4, "1111", [[3, 2, 3], [1, 0, 1], [2, 1, 2]]), (3, "110", [[1, 0, 1], [2, 0, 2]])]
    edges = [(1, "1", []), (2, "11", [[1, 0, 1]])]

    def ref(n: int, final: str, shakes: List[List[int]]) -> List[int]:
        order = sorted(shakes)
        T = len(order)

        def simulate(p, K):
            sick, left = [False] * n, [0] * n
            sick[p], left[p] = True, K
            for _, x, y in order:
                sx, sy = sick[x] and left[x] > 0, sick[y] and left[y] > 0
                if sick[x]:
                    left[x] = max(0, left[x] - 1)
                if sick[y]:
                    left[y] = max(0, left[y] - 1)
                if sx and not sick[y]:
                    sick[y], left[y] = True, K
                if sy and not sick[x]:
                    sick[x], left[x] = True, K
            return all(s == (c == "1") for s, c in zip(sick, final))

        zeros, ks = 0, []
        for p in range(n):
            if final[p] != "1":
                continue
            good = [K for K in range(T + 1) if simulate(p, K)]
            if good:
                zeros += 1
                ks += good
        return [zeros, min(ks), -1 if max(ks) == T else max(ks)]

    def brute(n, final, shakes):
        T, zeros, ks = len(shakes), 0, set()
        for p in range(n):
            fits = {K for K in range(T + 3) if _contact_sim(n, shakes, p, K) == final}
            if fits:
                zeros += 1
                ks |= fits
        return [zeros, min(ks), -1 if max(ks) >= T + 2 else max(ks)]

    def gen(rng, big):
        n, T = (50, 150) if big else (rng.randint(1, 5), rng.randint(0, 6))
        times = rng.sample(range(1, 10 * T + 2), T)
        shakes = [[t, *rng.sample(range(n), 2)] for t in times] if n > 1 else []
        return n, _contact_sim(n, shakes, rng.randrange(n), rng.randint(0, T + 1)), shakes


@problem
class CoolingPlan:
    title = "Cooling Plan"
    difficulty = "Medium"
    func = "cheapestCooling"
    statement = """
<p>Stalls are numbered 1 to 100. Cow <code>[s, t, c]</code> occupies stalls <code>s..t</code> and needs every one of them
cooled by at least <code>c</code>. Air conditioner <code>[a, b, p, m]</code> cools stalls <code>a..b</code> by
<code>p</code> each and costs <code>m</code> to run. Choose air conditioners to satisfy every cow at the lowest total cost
and return it. Running all of them is always enough.</p>
<ul><li><code>1 &lt;= cows.length &lt;= 20</code></li><li><code>1 &lt;= units.length &lt;= 10</code></li></ul>"""
    hint = dict(pattern="Complete search over all 2^m subsets of air conditioners; check each with a per-stall cooling array",
                module="Bronze: Complete Search with Recursion", url="https://usaco.guide/bronze/complete-rec", similar="USACO Air Cownditioning II ★")
    examples = [([[1, 5, 2], [7, 9, 3]], [[2, 9, 2, 3], [1, 6, 2, 8], [1, 2, 4, 2], [6, 9, 1, 5]]),]
    edges = [([[1, 1, 1]], [[1, 1, 1, 5]]),]

    def ref(cows: List[List[int]], units: List[List[int]]) -> int:
        need = [0] * 101
        for s, t, c in cows:
            for x in range(s, t + 1):
                need[x] = max(need[x], c)
        best = None
        for mask in range(1 << len(units)):
            cost = sum(units[i][3] for i in range(len(units)) if mask >> i & 1)
            if best is not None and cost >= best:
                continue
            cool = [0] * 102
            for i, (a, b, p, _) in enumerate(units):
                if mask >> i & 1:
                    cool[a] += p
                    cool[b + 1] -= p
            run, ok = 0, True
            for x in range(1, 101):
                run += cool[x]
                if run < need[x]:
                    ok = False
                    break
            if ok:
                best = cost
        return best

    def brute(cows, units):
        best = float("inf")

        def go(i, chosen, cost):
            nonlocal best
            if cost >= best:
                return
            if i == len(units):
                if all(sum(p for a, b, p, _ in chosen if a <= x <= b) >= c for s, t, c in cows for x in range(s, t + 1)):
                    best = cost
                return
            go(i + 1, chosen + [units[i]], cost + units[i][3])
            go(i + 1, chosen, cost)

        go(0, [], 0)
        return best

    def gen(rng, big):
        n, m = (20, 10) if big else (rng.randint(1, 3), rng.randint(1, 4))
        cows = []
        for _ in range(n):
            s = rng.randint(1, 100)
            cows.append([s, rng.randint(s, min(100, s + 20)), rng.randint(1, 5)])
        units = [[1, 100, 10, rng.randint(50, 100)]]  # an expensive catch-all keeps every case solvable
        for _ in range(m - 1):
            a = rng.randint(1, 100)
            units.append([a, rng.randint(a, 100), rng.randint(1, 5), rng.randint(1, 30)])
        rng.shuffle(units)
        return cows, units


@problem
class LivestockLineup:
    title = "Lineup Rules"
    difficulty = "Medium"
    func = "lineup"
    statement = """
<p>Eight cows, <code>Beatrice, Belinda, Bella, Bessie, Betsy, Blue, Buttercup, Sue</code>, must stand in a line. Each
rule <code>[X, Y]</code> says X and Y must stand next to each other. Return the alphabetically first lineup (compare the
name lists element by element) that obeys every rule. A valid lineup always exists.</p>"""
    hint = dict(pattern="Complete search over the 8! orderings in sorted order works; or build it greedily from chains of rules",
                module="Bronze: Complete Search with Recursion", url="https://usaco.guide/bronze/complete-rec", similar="USACO Livestock Lineup ★ (focus problem)")
    COWS = sorted(["Beatrice", "Belinda", "Bella", "Bessie", "Betsy", "Blue", "Buttercup", "Sue"])
    examples = [([["Buttercup", "Bella"], ["Blue", "Bella"], ["Sue", "Beatrice"]],),]
    edges = [([],)]

    def ref(rules: List[List[str]]) -> List[str]:
        cows = sorted(["Beatrice", "Belinda", "Bella", "Bessie", "Betsy", "Blue", "Buttercup", "Sue"])
        nbr = {c: set() for c in cows}
        for x, y in rules:
            nbr[x].add(y)
            nbr[y].add(x)
        order, used = [], set()
        for c in cows:  # start a chain at the smallest unused cow that is a chain end
            if c in used or len(nbr[c]) > 1:
                continue
            cur = c
            while cur is not None:
                order.append(cur)
                used.add(cur)
                cur = next((v for v in sorted(nbr[cur]) if v not in used), None)
        return order

    def brute(rules):
        from itertools import permutations
        for perm in permutations(LivestockLineup.COWS):
            pos = {c: i for i, c in enumerate(perm)}
            if all(abs(pos[x] - pos[y]) == 1 for x, y in rules):
                return list(perm)

    def gen(rng, big):
        line = rng.sample(LivestockLineup.COWS, 8)
        pairs = [[line[i], line[i + 1]] for i in range(7)]
        rules = rng.sample(pairs, rng.randint(0, 7))
        for r in rules:
            rng.shuffle(r)
        return (rules,)


def _logo_grid_ok(logos, grid):
    """True if grid is a filled square where 'A', 'B', 'C' are solid rectangles matching the logos (rotation allowed)."""
    if not isinstance(grid, list) or not grid or any(not isinstance(r, str) or len(r) != len(grid) for r in grid):
        return False
    for letter, (w, h) in zip("ABC", logos):
        cells = [(i, j) for i, row in enumerate(grid) for j, ch in enumerate(row) if ch == letter]
        if not cells:
            return False
        rows = [i for i, _ in cells]
        cols = [j for _, j in cells]
        hh, ww = max(rows) - min(rows) + 1, max(cols) - min(cols) + 1
        if hh * ww != len(cells) or sorted((hh, ww)) != sorted((w, h)):
            return False
    return all(ch in "ABC" for row in grid for ch in row)


@problem
class ThreeLogos:
    title = "Three Logos"
    difficulty = "Hard"
    func = "arrangeLogos"
    statement = """
<p>Three rectangular logos have sizes <code>logos[i] = [w, h]</code> and may be rotated 90 degrees. Place all three, without
overlapping, so that together they exactly fill a square. Return the square as a list of strings where each cell holds
<code>'A'</code>, <code>'B'</code> or <code>'C'</code> (for logos 0, 1, 2), or an empty list if it is impossible. Any
valid arrangement is accepted.</p>
<ul><li><code>1 &lt;= w, h &lt;= 100</code></li></ul>"""
    hint = dict(pattern="The square's side is sqrt(total area). Only two layouts exist: three full-width strips, or one strip plus two side-by-side pieces; try all orders and rotations",
                module="Bronze: Complete Search with Recursion", url="https://usaco.guide/bronze/complete-rec", similar="CF Three Logos ★")
    examples = [([[5, 1], [2, 5], [5, 2]],), ([[4, 4], [2, 6], [4, 2]],), ([[1, 1], [1, 1], [1, 1]],)]
    edges = [([[1, 2], [1, 2], [2, 1]],)]

    def ref(logos: List[List[int]]) -> List[str]:
        from itertools import permutations, product
        from math import isqrt
        s = isqrt(sum(w * h for w, h in logos))
        if s * s != sum(w * h for w, h in logos):
            return []
        for order in permutations(range(3)):
            for flips in product((False, True), repeat=3):
                (w0, h0), (w1, h1), (w2, h2) = [(logos[i][1], logos[i][0]) if f else tuple(logos[i]) for i, f in zip(order, flips)]
                a, b, c = ("ABC"[i] for i in order)
                if w0 == s and w1 == s and w2 == s and h0 + h1 + h2 == s:  # three strips
                    return [a * s] * h0 + [b * s] * h1 + [c * s] * h2
                if w0 == s and h1 == h2 == s - h0 and w1 + w2 == s:  # strip + two side by side
                    return [a * s] * h0 + [b * w1 + c * w2] * (s - h0)
        return []

    def brute(logos):
        from math import isqrt
        area = sum(w * h for w, h in logos)
        s = isqrt(area)
        if s * s != area:
            return []
        grid = [[""] * s for _ in range(s)]

        def place(used):
            empty = next(((i, j) for i in range(s) for j in range(s) if not grid[i][j]), None)
            if empty is None:
                return True
            i, j = empty
            for k in range(3):
                if used >> k & 1:
                    continue
                for h, w in {tuple(logos[k]), tuple(logos[k][::-1])}:
                    if i + h <= s and j + w <= s and all(not grid[a][b] for a in range(i, i + h) for b in range(j, j + w)):
                        for a in range(i, i + h):
                            for b in range(j, j + w):
                                grid[a][b] = "ABC"[k]
                        if place(used | 1 << k):
                            return True
                        for a in range(i, i + h):
                            for b in range(j, j + w):
                                grid[a][b] = ""
            return False

        return ["".join(r) for r in grid] if place(0) else []

    def check(args, out, expected):
        if not expected:
            return out == []
        return _logo_grid_ok(args[0], out)

    def gen(rng, big):
        s = rng.randint(2, 100 if big else 6)
        if rng.random() < 0.7:  # cut a square into three rectangles
            h0 = rng.randint(1, s - 1)
            if rng.random() < 0.5 and s - h0 >= 2:
                h1 = rng.randint(1, s - h0 - 1)
                pieces = [[s, h0], [s, h1], [s, s - h0 - h1]]
            else:
                w1 = rng.randint(1, s - 1)
                pieces = [[s, h0], [w1, s - h0], [s - w1, s - h0]]
            if s - h0 < 1:
                pieces = [[s, s - 1], [1, 1], [s - 1, 1]]
        else:
            pieces = [[rng.randint(1, s), rng.randint(1, s)] for _ in range(3)]
        for p in pieces:
            if rng.random() < 0.5:
                p.reverse()
        rng.shuffle(pieces)
        return (pieces,)


@problem
class AllArrangements:
    title = "All Arrangements"
    difficulty = "Easy"
    func = "arrangements"
    statement = """
<p>Return every different string that can be made by rearranging the letters of <code>s</code>, in alphabetical
order (no duplicates).</p>
<ul><li><code>1 &lt;= s.length &lt;= 8</code>, lowercase letters</li></ul>"""
    hint = dict(pattern="Recursive backtracking over letter counts (a sorted Counter) builds each distinct string once, already in order",
                module="Bronze: Complete Search with Recursion", url="https://usaco.guide/bronze/complete-rec",
                similar="CSES Creating Strings (focus problem) · LeetCode 47")
    examples = [("aabac",), ("ab",)]
    edges = [("a",), ("aaa",)]

    def ref(s: str) -> List[str]:
        counts, out, cur = Counter(s), [], []
        letters = sorted(counts)

        def build():
            if len(cur) == len(s):
                out.append("".join(cur))
                return
            for ch in letters:
                if counts[ch]:
                    counts[ch] -= 1
                    cur.append(ch)
                    build()
                    cur.pop()
                    counts[ch] += 1

        build()
        return out

    def brute(s):
        from itertools import permutations
        return sorted({"".join(p) for p in permutations(s)})

    def gen(rng, big):
        return ("".join(rng.choice("abc" if not big else "abcd") for _ in range(8 if big else rng.randint(1, 6))),)


@problem
class BlockedQueens:
    title = "Blocked Queens"
    difficulty = "Medium"
    func = "countPlacements"
    statement = """
<p>An 8x8 board is given as 8 strings; <code>'*'</code> squares are blocked and <code>'.'</code> squares are free. Count
the ways to place 8 queens on free squares so that no two queens attack each other (same row, column or diagonal).</p>"""
    hint = dict(pattern="Backtracking row by row with sets for used columns and both diagonals, skipping blocked squares",
                module="Bronze: Complete Search with Recursion", url="https://usaco.guide/bronze/complete-rec",
                similar="CSES Chessboard and Queens (focus problem) · LeetCode 52")
    examples = [(["........", "........", "..*.....", "........", "........", ".....**.", "...*....", "........"],),]
    edges = [(["........"] * 8,), (["*......."] * 8,)]

    def ref(board: List[str]) -> int:
        cols, d1, d2 = set(), set(), set()

        def place(r):
            if r == 8:
                return 1
            total = 0
            for c in range(8):
                if board[r][c] == "." and c not in cols and r + c not in d1 and r - c not in d2:
                    cols.add(c), d1.add(r + c), d2.add(r - c)
                    total += place(r + 1)
                    cols.discard(c), d1.discard(r + c), d2.discard(r - c)
            return total

        return place(0)

    def brute(board):
        from itertools import permutations
        return sum(all(board[r][c] == "." for r, c in enumerate(p)) and len({r + c for r, c in enumerate(p)}) == 8
                   and len({r - c for r, c in enumerate(p)}) == 8 for p in permutations(range(8)))

    def gen(rng, big):
        dens = 0.0 if big else rng.choice([0.0, 0.05, 0.1, 0.2])
        return (["".join("*" if rng.random() < dens else "." for _ in range(8)) for _ in range(8)],)


@problem
class SleepyHerding:
    title = "Sleepy Herding"
    difficulty = "Medium"
    func = "herdMoves"
    statement = """
<p>Three cows stand at distinct positions <code>positions</code> on a number line. In one move, a cow at either end
(leftmost or rightmost) walks to an empty integer position strictly between the other two cows. The cows stop once they
stand at three consecutive positions. Return <code>[fewest moves, most moves]</code> needed to get there.</p>
<ul><li><code>1 &lt;= positions[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Casework on the two gaps: min is 0, 1 or 2 depending on whether a gap of exactly 2 exists; max is the larger gap minus 1",
                module="Bronze: Ad Hoc / Casework", url="https://usaco.guide/bronze/ad-hoc", similar="USACO Sleepy Cow Herding (focus problem)")
    examples = [([4, 7, 9],), ([1, 2, 3],)]
    edges = [([1, 3, 10],), ([10, 1, 5],)]

    def ref(positions: List[int]) -> List[int]:
        a, b, c = sorted(positions)
        if c - a == 2:
            lo = 0
        elif b - a == 2 or c - b == 2:
            lo = 1
        else:
            lo = 2
        return [lo, max(b - a, c - b) - 1]

    def brute(positions):
        @lru_cache(None)
        def moves(state):  # (fewest, most) moves from a sorted state
            a, b, c = state
            if c - a == 2:
                return 0, 0
            options = [tuple(sorted((b, c, x))) for x in range(b + 1, c)] + [tuple(sorted((a, b, x))) for x in range(a + 1, b)]
            results = [moves(s) for s in options]
            return 1 + min(r[0] for r in results), 1 + max(r[1] for r in results)

        return list(moves(tuple(sorted(positions))))

    def gen(rng, big):
        V = 10**9 if big else 12
        return (rng.sample(range(1, V + 1), 3),)


@problem
class OutOfPlace:
    title = "Out of Place"
    difficulty = "Medium"
    func = "minSwaps"
    statement = """
<p>Students stood in a line sorted by height, then exactly one student stepped out and back in at a different spot,
giving <code>heights</code>. In one move, any two students swap places. Return the fewest swaps needed to sort the line
again.</p>
<ul><li><code>2 &lt;= heights.length &lt;= 10^5</code></li><li><code>1 &lt;= heights[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Compare with the sorted line: the misplaced positions form one chain, so the answer is (number of mismatched positions) - 1",
                module="Bronze: Introduction to Greedy", url="https://usaco.guide/bronze/intro-greedy", similar="USACO Out of Place ★")
    examples = [([2, 4, 7, 7, 9, 3],), ([1, 2, 3],)]
    edges = [([2, 1],), ([5, 5, 5],)]

    def ref(heights: List[int]) -> int:
        wrong = sum(a != b for a, b in zip(heights, sorted(heights)))
        return max(0, wrong - 1)

    def brute(heights):
        start, goal = tuple(heights), tuple(sorted(heights))
        dist, q = {start: 0}, deque([start])
        while q:
            a = q.popleft()
            if a == goal:
                return dist[a]
            for i, j in combinations(range(len(a)), 2):
                b = list(a)
                b[i], b[j] = b[j], b[i]
                b = tuple(b)
                if b not in dist:
                    dist[b] = dist[a] + 1
                    q.append(b)

    def gen(rng, big):
        n, V = (100000, 10**9) if big else (rng.randint(2, 6), 6)
        line = sorted(rng.randint(1, V) for _ in range(n))
        x = line.pop(rng.randrange(n))
        line.insert(rng.randrange(n), x)
        return (line,)


@problem
class PhotoLineup:
    title = "Photo Lineup"
    difficulty = "Medium"
    func = "restoreLineup"
    statement = """
<p>Cows numbered <code>1..n</code> stood in a line (a permutation), but only the sums of neighbors were recorded:
<code>sums[i]</code> is the sum of the cows at positions <code>i</code> and <code>i + 1</code>. Return the
alphabetically (lexicographically) smallest lineup consistent with the sums. One always exists.</p>
<ul><li><code>2 &lt;= n &lt;= 1000</code>, so <code>sums.length = n - 1</code></li></ul>"""
    hint = dict(pattern="The first cow determines everyone else; try first cow = 1, 2, ... and take the first that gives a valid permutation",
                module="Bronze: Introduction to Greedy", url="https://usaco.guide/bronze/intro-greedy", similar="USACO Photoshoot ★")
    examples = [([4, 6, 7, 6],), ([3],)]
    edges = [([5, 5],)]

    def ref(sums: List[int]) -> List[int]:
        n = len(sums) + 1
        for first in range(1, n + 1):
            line = [first]
            for s in sums:
                line.append(s - line[-1])
            if sorted(line) == list(range(1, n + 1)):
                return line

    def brute(sums):
        from itertools import permutations
        n = len(sums) + 1
        for p in permutations(range(1, n + 1)):
            if all(p[i] + p[i + 1] == s for i, s in enumerate(sums)):
                return list(p)

    def gen(rng, big):
        n = 1000 if big else rng.randint(2, 7)
        p = rng.sample(range(1, n + 1), n)
        return ([p[i] + p[i + 1] for i in range(n - 1)],)


@problem
class RaceFinish:
    title = "Race Finish"
    difficulty = "Hard"
    func = "minTimes"
    statement = """
<p>A runner starts at speed 0 and must cover <code>length</code> meters. At the start of each second they may raise their
speed by 1, keep it, or lower it by 1 (never below 0), then run that many meters during the second. For each limit
<code>x</code> in <code>limits</code>, return the fewest seconds needed to reach or pass the finish line while moving at a
speed of at most <code>x</code> during the second they cross it.</p>
<ul><li><code>1 &lt;= length &lt;= 10^7</code></li><li><code>1 &lt;= limits.length &lt;= 1000</code>, <code>1 &lt;= x &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="Greedy two-sided build: speed up 1, 2, 3, ... from the start, and mirror each speed above x as slowing down at the end, until the two sides meet",
                module="Bronze: Introduction to Greedy", url="https://usaco.guide/bronze/intro-greedy", similar="USACO Race ★")
    examples = [(10, [1, 2, 3, 4, 5]),]
    edges = [(1, [1]), (5, [100])]

    def ref(length: int, limits: List[int]) -> List[int]:
        out = []
        for x in limits:
            front = back = t = 0  # meters covered speeding up, meters reserved for slowing down
            speed = 0
            while True:
                speed += 1
                front += speed
                t += 1
                if front + back >= length:
                    break
                if speed >= x:
                    back += speed
                    t += 1
                    if front + back >= length:
                        break
            out.append(t)
        return out

    def brute(length, limits):
        out = []
        for x in limits:
            seen, q, found = {(0, 0)}, deque([(0, 0, 0)]), None
            while q and found is None:
                pos, v, t = q.popleft()
                for nv in (v - 1, v, v + 1):
                    if nv < 0:
                        continue
                    np = pos + nv
                    if np >= length:
                        if nv <= x:
                            found = t + 1
                            break
                        continue
                    if (np, nv) not in seen:
                        seen.add((np, nv))
                        q.append((np, nv, t + 1))
            out.append(found)
        return out

    def gen(rng, big):
        if big:
            return 10**7, [rng.randint(1, 10**5) for _ in range(1000)]
        return rng.randint(1, 30), [rng.randint(1, 8) for _ in range(rng.randint(1, 4))]


@problem
class MadScientist:
    title = "Gene Flips"
    difficulty = "Easy"
    func = "minFlips"
    statement = """
<p>Strings <code>a</code> and <code>b</code> have the same length and contain only <code>'G'</code> and <code>'H'</code>.
One operation picks a contiguous substring of <code>a</code> and flips every character in it (G becomes H and H becomes
G). Return the fewest operations that turn <code>a</code> into <code>b</code>.</p>
<ul><li><code>1 &lt;= a.length &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="Each maximal run of mismatched positions needs exactly one flip, and flipping beyond a run never helps",
                module="Bronze: Introduction to Greedy", url="https://usaco.guide/bronze/intro-greedy", similar="USACO Mad Scientist (focus problem)")
    examples = [("GHHHGHHGGGHG", "GHGGHHGGGGHG"), ("GH", "GH")]
    edges = [("G", "H"), ("GGG", "HHH")]

    def ref(a: str, b: str) -> int:
        runs, inside = 0, False
        for x, y in zip(a, b):
            if x != y and not inside:
                runs += 1
            inside = x != y
        return runs

    def brute(a, b):
        flip = {"G": "H", "H": "G"}
        dist, q = {a: 0}, deque([a])
        while q:
            s = q.popleft()
            if s == b:
                return dist[s]
            for i in range(len(s)):
                for j in range(i + 1, len(s) + 1):
                    t = s[:i] + "".join(flip[c] for c in s[i:j]) + s[j:]
                    if t not in dist:
                        dist[t] = dist[s] + 1
                        q.append(t)

    def gen(rng, big):
        n = 100000 if big else rng.randint(1, 7)
        g = lambda: "".join(rng.choice("GH") for _ in range(n))
        return g(), g()


@problem
class MilkFactory:
    title = "Milk Factory"
    difficulty = "Easy"
    func = "collectionPoint"
    statement = """
<p>A factory has <code>n</code> stations joined by <code>n - 1</code> one-way conveyor belts <code>[a, b]</code> (from
<code>a</code> to <code>b</code>); ignoring direction they form a tree. Return the smallest-numbered station that every
station can send milk to (directly or through other belts), or <code>-1</code> if there is none.</p>
<ul><li><code>1 &lt;= n &lt;= 100</code></li></ul>"""
    hint = dict(pattern="For each station, search the reversed graph from it and check that it reaches everyone",
                module="Bronze: Introduction to Graphs", url="https://usaco.guide/bronze/intro-graphs", similar="USACO Milk Factory ★")
    examples = [(3, [[0, 1], [2, 1]]), (3, [[1, 0], [1, 2]])]
    edges = [(1, []), (2, [[1, 0]])]

    def ref(n: int, belts: List[List[int]]) -> int:
        into = [[] for _ in range(n)]
        for a, b in belts:
            into[b].append(a)
        for v in range(n):
            seen, stack = {v}, [v]
            while stack:
                for u in into[stack.pop()]:
                    if u not in seen:
                        seen.add(u)
                        stack.append(u)
            if len(seen) == n:
                return v
        return -1

    def brute(n, belts):
        reach = [[i == j for j in range(n)] for i in range(n)]
        for a, b in belts:
            reach[a][b] = True
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    reach[i][j] = reach[i][j] or (reach[i][k] and reach[k][j])
        return next((v for v in range(n) if all(reach[u][v] for u in range(n))), -1)

    def gen(rng, big):
        n = 100 if big else rng.randint(1, 6)
        belts = []
        for i in range(1, n):
            p = rng.randrange(i)
            belts.append([i, p] if rng.random() < 0.8 else [p, i])  # mostly toward station 0's side
        return n, belts


# ================================================================ later: lower-priority starred and focus problems

@problem
class PackingRanges:
    title = "Locker Assignment"
    difficulty = "Medium"
    func = "canAssign"
    statement = """
<p>Lockers are numbered 1, 2, 3, ... (as many as needed). Student <code>i</code> must get one locker numbered between
<code>ranges[i][0]</code> and <code>ranges[i][1]</code>, inclusive, and no two students may share a locker. Return
<code>true</code> if everyone can get a locker.</p>
<ul><li><code>1 &lt;= ranges.length &lt;= 2 * 10^5</code></li><li><code>1 &lt;= L &lt;= R &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Sweep lockers in order: add students whose range has started to a min-heap of end points, give the next locker to the earliest deadline, jump over empty stretches",
                module="Silver: Priority Queues", url="https://usaco.guide/silver/priority-queues", similar="AtCoder Packing Under Range Regulations ★")
    examples = [([[1, 2], [2, 3]],), ([[1, 1], [1, 1]],)]
    edges = [([[5, 5]],), ([[1, 3], [1, 3], [1, 3]],)]

    def ref(ranges: List[List[int]]) -> bool:
        rs = sorted(ranges)
        heap, i, x = [], 0, 0
        while i < len(rs) or heap:
            if not heap:
                x = max(x, rs[i][0])
            while i < len(rs) and rs[i][0] <= x:
                heappush(heap, rs[i][1])
                i += 1
            if heappop(heap) < x:
                return False
            x += 1
        return True

    def brute(ranges):
        match = {}  # locker -> student, via augmenting paths

        def try_place(s, seen):
            for locker in range(ranges[s][0], ranges[s][1] + 1):
                if locker not in seen:
                    seen.add(locker)
                    if locker not in match or try_place(match[locker], seen):
                        match[locker] = s
                        return True
            return False

        return all(try_place(s, set()) for s in range(len(ranges)))

    def gen(rng, big):
        n, V = (200000, 10**9) if big else (rng.randint(1, 6), 6)
        out = []
        for _ in range(n):
            l = rng.randint(1, V)
            out.append([l, min(V, l + rng.randint(0, 3 if not big else V // n * 2))])
        return (out,)


@problem
class DistinctQueries:
    title = "Distinct in Range"
    difficulty = "Hard"
    func = "distinctInRanges"
    tl = 3.0
    statement = """
<p>For each query <code>[l, r]</code>, return how many different values appear in <code>nums[l..r]</code>, inclusive.</p>
<ul><li><code>1 &lt;= nums.length, queries.length &lt;= 10^5</code></li><li><code>1 &lt;= nums[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Offline: sort queries by r; sweep r, keep a Fenwick tree with a 1 only at each value's LAST occurrence so far; answer = sum over [l, r]",
                module="Gold: Point Update Range Sum", url="https://usaco.guide/gold/PURS", similar="CSES Distinct Values Queries ★")
    examples = [([3, 2, 3, 1, 2], [[0, 2], [1, 3], [0, 4], [2, 2]]),]
    edges = [([5], [[0, 0]]), ([1, 1, 1], [[0, 2], [1, 2]])]

    def ref(nums: List[int], queries: List[List[int]]) -> List[int]:
        n = len(nums)
        tree = [0] * (n + 1)

        def add(i, v):
            i += 1
            while i <= n:
                tree[i] += v
                i += i & -i

        def prefix(i):  # sum of positions 0..i-1
            s = 0
            while i > 0:
                s += tree[i]
                i -= i & -i
            return s

        last, out, r = {}, [0] * len(queries), -1
        for qi in sorted(range(len(queries)), key=lambda q: queries[q][1]):
            l, qr = queries[qi]
            while r < qr:
                r += 1
                if nums[r] in last:
                    add(last[nums[r]], -1)
                last[nums[r]] = r
                add(r, 1)
            out[qi] = prefix(qr + 1) - prefix(l)
        return out

    def brute(nums, queries):
        return [len(set(nums[l:r + 1])) for l, r in queries]

    def gen(rng, big):
        n, q, V = (100000, 100000, 10**9) if big else (rng.randint(1, 7), rng.randint(1, 5), 4)
        vals = [rng.randint(1, V) for _ in range(min(n, 5000) if big else V)]
        return [rng.choice(vals) for _ in range(n)], [sorted((rng.randrange(n), rng.randrange(n))) for _ in range(q)]


@problem
class ConnectedPaintings:
    title = "Connected Paintings"
    difficulty = "Hard"
    func = "paintingsContaining"
    statement = """
<p>A tree has <code>n</code> nodes joined by <code>edges</code>. You paint some nodes black so that the black nodes form one
connected group. For every node <code>v</code>, return the number of such paintings in which <code>v</code> is black,
modulo <code>m</code> (which need not be prime).</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li><code>2 &lt;= m &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Rerooting DP: down[v] = product of (down[child] + 1); to move the root you need the product of all OTHER children, so use prefix/suffix products (m isn't prime, so no division)",
                module="Gold: DP on Trees - Solving For All Roots", url="https://usaco.guide/gold/all-roots", similar="AtCoder DP Contest V (Subtree) ★")
    examples = [(3, [[0, 1], [1, 2]], 100), (4, [[0, 1], [0, 2], [0, 3]], 100)]
    edges = [(1, [], 7), (2, [[1, 0]], 2)]

    def ref(n: int, edges: List[List[int]], m: int) -> List[int]:
        adj = [[] for _ in range(n)]
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        parent, order = [-1] * n, [0]
        parent[0] = 0
        for u in order:
            for v in adj[u]:
                if parent[v] == -1:
                    parent[v] = u
                    order.append(v)
        kids = [[v for v in adj[u] if parent[v] == u] for u in range(n)]
        down = [1] * n
        for u in reversed(order):
            for c in kids[u]:
                down[u] = down[u] * (down[c] + 1) % m
        up = [0] * n  # up[v]: ways for the part above v (as a child of v), connected to v's parent
        ans = [0] * n
        for u in order:
            ks = kids[u]
            vals = [down[c] + 1 for c in ks]
            pre = [1] * (len(ks) + 1)
            for i, x in enumerate(vals):
                pre[i + 1] = pre[i] * x % m
            suf = [1] * (len(ks) + 1)
            for i in range(len(ks) - 1, -1, -1):
                suf[i] = suf[i + 1] * vals[i] % m
            above = up[u] + 1 if u != 0 else 1
            ans[u] = pre[-1] * above % m
            for i, c in enumerate(ks):
                up[c] = pre[i] * suf[i + 1] % m * above % m
        return ans

    def brute(n, edges, m):
        adj = defaultdict(set)
        for a, b in edges:
            adj[a].add(b)
            adj[b].add(a)
        out = [0] * n
        for mask in range(1, 1 << n):
            nodes = [v for v in range(n) if mask >> v & 1]
            seen, stack = {nodes[0]}, [nodes[0]]
            while stack:
                for w in adj[stack.pop()]:
                    if mask >> w & 1 and w not in seen:
                        seen.add(w)
                        stack.append(w)
            if len(seen) == len(nodes):
                for v in nodes:
                    out[v] += 1
        return [x % m for x in out]

    def gen(rng, big):
        n = 100000 if big else rng.randint(1, 8)
        label = rng.sample(range(n), n)
        edges = [[label[i - 1 if big and rng.random() < 0.3 else rng.randrange(i)], label[i]] for i in range(1, n)]
        return n, edges, rng.randint(2, 10**9)


@problem
class TreeMatching:
    title = "Buddy Pairs"
    difficulty = "Medium"
    func = "maxPairs"
    statement = """
<p>Employees form a tree: <code>edges</code> are direct working relationships among <code>n</code> people. Pair people up
as buddies; buddies must share an edge and nobody can be in two pairs. Return the largest number of pairs.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li>The tree may be very deep.</li></ul>"""
    hint = dict(pattern="Greedy from the leaves (post-order): if a node and its parent are both free, pair them. Or DP with states matched/unmatched",
                module="Gold: DP on Trees - Introduction", url="https://usaco.guide/gold/dp-trees", similar="CSES Tree Matching (focus problem)")
    examples = [(5, [[0, 1], [0, 2], [2, 3], [2, 4]]), (3, [[0, 1], [0, 2]])]
    edges = [(1, []), (2, [[0, 1]])]

    def ref(n: int, edges: List[List[int]]) -> int:
        adj = [[] for _ in range(n)]
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        parent, order = [-1] * n, [0]
        parent[0] = 0
        for u in order:
            for v in adj[u]:
                if parent[v] == -1:
                    parent[v] = u
                    order.append(v)
        used, pairs = [False] * n, 0
        for u in reversed(order[1:]):
            p = parent[u]
            if not used[u] and not used[p]:
                used[u] = used[p] = True
                pairs += 1
        return pairs

    def brute(n, edges):
        @lru_cache(None)
        def f(i, used):
            if i == len(edges):
                return 0
            a, b = edges[i]
            best = f(i + 1, used)
            if not (used >> a & 1 or used >> b & 1):
                best = max(best, 1 + f(i + 1, used | 1 << a | 1 << b))
            return best
        return f(0, 0)

    def gen(rng, big):
        n = 100000 if big else rng.randint(1, 10)
        label = rng.sample(range(n), n)
        return n, [[label[i - 1 if big and rng.random() < 0.5 else rng.randrange(i)], label[i]] for i in range(1, n)]


@problem
class FarthestFromEach:
    title = "Farthest Office"
    difficulty = "Medium"
    func = "farthestDistances"
    statement = """
<p>Offices form a tree of <code>n</code> nodes joined by <code>edges</code> of length 1. For every office, return the
distance to the office farthest from it.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li>The tree may be very deep.</li></ul>"""
    hint = dict(pattern="The farthest node from anywhere is an end of a diameter: BFS from both diameter ends and take the max (or reroot)",
                module="Gold: DP on Trees - Solving For All Roots", url="https://usaco.guide/gold/all-roots", similar="CSES Tree Distances I (focus problem)")
    examples = [(5, [[0, 1], [0, 2], [2, 3], [2, 4]]),]
    edges = [(1, []), (2, [[1, 0]])]

    def ref(n: int, edges: List[List[int]]) -> List[int]:
        adj = [[] for _ in range(n)]
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)

        def bfs(s):
            dist = [-1] * n
            dist[s], q = 0, [s]
            for u in q:
                for v in adj[u]:
                    if dist[v] == -1:
                        dist[v] = dist[u] + 1
                        q.append(v)
            return dist

        d0 = bfs(0)
        a = d0.index(max(d0))
        da = bfs(a)
        b = da.index(max(da))
        db = bfs(b)
        return [max(x, y) for x, y in zip(da, db)]

    def brute(n, edges):
        adj = defaultdict(list)
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        out = []
        for s in range(n):
            dist, q = {s: 0}, deque([s])
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if v not in dist:
                        dist[v] = dist[u] + 1
                        q.append(v)
            out.append(max(dist.values()))
        return out

    def gen(rng, big):
        n = 100000 if big else rng.randint(1, 10)
        label = rng.sample(range(n), n)
        return n, [[label[i - 1 if big and rng.random() < 0.5 else rng.randrange(i)], label[i]] for i in range(1, n)]


@problem
class LongestFlight:
    title = "Scenic Flights"
    difficulty = "Medium"
    func = "longestRoute"
    statement = """
<p>There are <code>n</code> cities and one-way <code>flights</code> <code>[a, b]</code>, with no way to fly in a circle.
A tourist wants to fly from city <code>0</code> to city <code>n - 1</code> visiting as many cities as possible. Return
the route as a list of cities (starting with 0 and ending with n - 1), or an empty list if city n - 1 cannot be reached.
Any longest route is accepted.</p>
<ul><li><code>2 &lt;= n &lt;= 10^5</code></li><li><code>0 &lt;= flights.length &lt;= 2 * 10^5</code></li></ul>"""
    hint = dict(pattern="Longest path in a DAG: DP in topological order with a parent pointer per city, starting only from city 0",
                module="Gold: Topological Sort", url="https://usaco.guide/gold/toposort", similar="CSES Longest Flight Route (focus problem)")
    examples = [(5, [[0, 1], [1, 4], [0, 2], [2, 3], [3, 4]]), (3, [[1, 2]])]
    edges = [(2, [[0, 1]]), (2, [[1, 0]])]

    def ref(n: int, flights: List[List[int]]) -> List[int]:
        adj, indeg = [[] for _ in range(n)], [0] * n
        for a, b in flights:
            adj[a].append(b)
            indeg[b] += 1
        best, par = [-1] * n, [-1] * n  # best[v]: most cities on a route 0 -> v (-1 = unreachable)
        best[0] = 1
        order = [i for i in range(n) if indeg[i] == 0]
        for u in order:
            for v in adj[u]:
                if best[u] > 0 and best[u] + 1 > best[v]:
                    best[v], par[v] = best[u] + 1, u
                indeg[v] -= 1
                if indeg[v] == 0:
                    order.append(v)
        if best[n - 1] < 0:
            return []
        route = [n - 1]
        while route[-1] != 0:
            route.append(par[route[-1]])
        return route[::-1]

    def brute(n, flights):
        adj = defaultdict(set)
        for a, b in flights:
            adj[a].add(b)
        best = []

        def dfs(path):
            nonlocal best
            if path[-1] == n - 1 and len(path) > len(best):
                best = path[:]
            for v in adj[path[-1]]:
                dfs(path + [v])

        dfs([0])
        return best

    def check(args, out, expected):
        n, flights = args
        if not expected:
            return out == []
        edges = {(a, b) for a, b in flights}
        return (isinstance(out, list) and len(out) == len(expected) and out[0] == 0 and out[-1] == n - 1
                and all((a, b) in edges for a, b in zip(out, out[1:])))

    def gen(rng, big):
        n, m = (100000, 200000) if big else (rng.randint(2, 6), rng.randint(0, 9))
        order = [0] + rng.sample(range(1, n - 1), n - 2) + [n - 1]
        flights = []
        for _ in range(m):
            i, j = sorted(rng.sample(range(n), 2))
            flights.append([order[i], order[j]])
        return n, flights


@problem
class AllPairsRoutes:
    title = "All-Pairs Routes"
    difficulty = "Medium"
    func = "answerQueries"
    tl = 3.0
    statement = """
<p><code>n</code> cities are joined by two-way <code>roads</code> <code>[a, b, length]</code> (there may be several roads
between two cities). For each query <code>[a, b]</code>, return the shortest distance between the cities, or
<code>-1</code> if they are not connected.</p>
<ul><li><code>1 &lt;= n &lt;= 150</code></li><li><code>0 &lt;= roads.length &lt;= n^2</code></li><li><code>1 &lt;= queries.length &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="Floyd-Warshall: for each middle city k, relax every pair through k; O(n^3) once, then O(1) per query",
                module="Gold: Shortest Paths with Non-Negative Edge Weights", url="https://usaco.guide/gold/shortest-paths",
                similar="CSES Shortest Routes II (focus problem)")
    examples = [(4, [[0, 1, 5], [0, 2, 9], [1, 2, 3]], [[0, 1], [0, 2], [2, 0], [0, 3]]),]
    edges = [(1, [], [[0, 0]]), (2, [[0, 1, 7], [0, 1, 2]], [[1, 0]])]

    def ref(n: int, roads: List[List[int]], queries: List[List[int]]) -> List[int]:
        INF = float("inf")
        d = [[0 if i == j else INF for j in range(n)] for i in range(n)]
        for a, b, w in roads:
            if w < d[a][b]:
                d[a][b] = d[b][a] = w
        for k in range(n):
            dk = d[k]
            for i in range(n):
                dik = d[i][k]
                if dik == INF:
                    continue
                di = d[i]
                for j in range(n):
                    if dik + dk[j] < di[j]:
                        di[j] = dik + dk[j]
        return [-1 if d[a][b] == INF else d[a][b] for a, b in queries]

    def brute(n, roads, queries):
        out = []
        for a, b in queries:
            dist = {a: 0}
            heap = [(0, a)]
            while heap:
                du, u = heappop(heap)
                if du > dist.get(u, float("inf")):
                    continue
                for x, y, w in roads:
                    for s, t in ((x, y), (y, x)):
                        if s == u and du + w < dist.get(t, float("inf")):
                            dist[t] = du + w
                            heappush(heap, (du + w, t))
            out.append(dist.get(b, -1))
        return out

    def gen(rng, big):
        n, m, q = (150, 3000, 100000) if big else (rng.randint(1, 5), rng.randint(0, 7), rng.randint(1, 4))
        roads = [[*rng.sample(range(n), 2), rng.randint(1, 10**9 if big else 9)] for _ in range(m)] if n > 1 else []
        return n, roads, [[rng.randrange(n), rng.randrange(n)] for _ in range(q)]


@problem
class BitRuns:
    title = "Bit Runs"
    difficulty = "Hard"
    func = "longestRuns"
    tl = 3.0
    statement = """
<p>A string <code>bits</code> of <code>'0'</code>s and <code>'1'</code>s is changed one position at a time: each value in
<code>flips</code> is an index whose bit gets inverted. After each flip, return the length of the longest block of equal
consecutive bits.</p>
<ul><li><code>1 &lt;= bits.length, flips.length &lt;= 5 * 10^4</code></li></ul>"""
    hint = dict(pattern="Segment tree where each node stores its length, longest prefix run, longest suffix run and best run; merge children in O(1)",
                module="Gold: More Operations on Sorted Sets", url="https://usaco.guide/gold/intro-sorted-sets", similar="CSES Bit Inversions (focus problem)")
    examples = [("001011", [2, 3, 4]),]
    edges = [("1", [0, 0]), ("01", [0])]

    def ref(bits: str, flips: List[int]) -> List[int]:
        n, b = len(bits), [int(c) for c in bits]
        size = 1
        while size < n:
            size *= 2
        # per node: number of real bits, longest run touching its left end / right end, best run, first index covered
        length, pre, suf, best, lo = ([0] * (2 * size) for _ in range(5))
        for i in range(size):
            k = size + i
            lo[k] = i
            if i < n:
                length[k] = pre[k] = suf[k] = best[k] = 1

        def pull(k):
            l, r = 2 * k, 2 * k + 1
            lo[k], length[k] = lo[l], length[l] + length[r]
            if not length[r]:  # padding on the right
                pre[k], suf[k], best[k] = pre[l], suf[l], best[l]
                return
            joined = b[lo[r] - 1] == b[lo[r]]  # last bit of the left half vs first bit of the right half
            pre[k] = pre[l] + pre[r] if joined and pre[l] == length[l] else pre[l]
            suf[k] = suf[r] + suf[l] if joined and suf[r] == length[r] else suf[r]
            best[k] = max(best[l], best[r], suf[l] + pre[r] if joined else 0)

        for k in range(size - 1, 0, -1):
            pull(k)
        out = []
        for i in flips:
            b[i] ^= 1
            k = (size + i) // 2
            while k:
                pull(k)
                k //= 2
            out.append(best[1])
        return out

    def brute(bits, flips):
        b, out = list(bits), []
        for i in flips:
            b[i] = "1" if b[i] == "0" else "0"
            s = "".join(b)
            out.append(max(len(run) for run in s.replace("01", "0 1").replace("10", "1 0").split()))
        return out

    def gen(rng, big):
        n, m = (50000, 50000) if big else (rng.randint(1, 8), rng.randint(1, 6))
        return "".join(rng.choice("01") for _ in range(n)), [rng.randrange(n) for _ in range(m)]


@problem
class BinomialQueries:
    title = "Choose Queries"
    difficulty = "Medium"
    func = "binomials"
    statement = """
<p>For each query <code>[a, b]</code>, return the number of ways to choose <code>b</code> items out of <code>a</code>
(the binomial coefficient), modulo <code>10^9 + 7</code>.</p>
<ul><li><code>1 &lt;= queries.length &lt;= 10^5</code></li><li><code>0 &lt;= b &lt;= a &lt;= 10^6</code></li></ul>"""
    hint = dict(pattern="Precompute factorials and inverse factorials (Fermat: x^(p-2)) once; each query is three multiplications",
                module="Gold: Combinatorics", url="https://usaco.guide/gold/combo", similar="CSES Binomial Coefficients (focus problem)")
    examples = [([[5, 3], [8, 1], [9, 5]],),]
    edges = [([[0, 0], [1, 1], [1000000, 0]],)]

    def ref(queries: List[List[int]]) -> List[int]:
        M = 10**9 + 7
        top = max(a for a, _ in queries)
        fact = [1] * (top + 1)
        for i in range(1, top + 1):
            fact[i] = fact[i - 1] * i % M
        inv = [1] * (top + 1)
        inv[top] = pow(fact[top], M - 2, M)
        for i in range(top, 0, -1):
            inv[i - 1] = inv[i] * i % M
        return [fact[a] * inv[b] % M * inv[a - b] % M for a, b in queries]

    def brute(queries):
        from math import comb
        return [comb(a, b) % MOD for a, b in queries]

    def gen(rng, big):
        n, A = (100000, 10**6) if big else (rng.randint(1, 5), 20)
        out = []
        for _ in range(n):
            a = rng.randint(0, A)
            out.append([a, rng.randint(0, a)])
        return (out,)


@problem
class AnagramWindows:
    title = "Anagram Windows"
    difficulty = "Hard"
    func = "countAnagramSubstrings"
    statement = """
<p>Count the <b>distinct</b> substrings of <code>text</code> that are rearrangements of <code>pattern</code> (equal
substrings at different positions count once).</p>
<ul><li><code>1 &lt;= pattern.length &lt;= text.length &lt;= 2 * 10^5</code>, lowercase letters</li></ul>"""
    hint = dict(pattern="Fixed-size sliding window with letter counts finds the anagram windows; a rolling hash (in a set) removes duplicates without storing whole strings",
                module="Gold: Hashing", url="https://usaco.guide/gold/hashing", similar="CCC Searching for Strings (focus problem) · LeetCode 438")
    examples = [("aab", "abacabaa"), ("abc", "def")]
    edges = [("a", "aaa"), ("ab", "abab")]

    def ref(pattern: str, text: str) -> int:
        k, n = len(pattern), len(text)
        need = [0] * 26
        for ch in pattern:
            need[ord(ch) - 97] += 1
        have = [0] * 26
        M, B = (1 << 61) - 1, 131
        top = pow(B, k - 1, M)
        h, seen = 0, set()
        for i, ch in enumerate(text):
            have[ord(ch) - 97] += 1
            h = (h * B + ord(ch)) % M
            if i >= k:
                out = text[i - k]
                have[ord(out) - 97] -= 1
                h = (h - ord(out) * top * B) % M
            if i >= k - 1 and have == need:
                seen.add(h)
        return len(seen)

    def brute(pattern, text):
        k, key = len(pattern), sorted(pattern)
        return len({text[i:i + k] for i in range(len(text) - k + 1) if sorted(text[i:i + k]) == key})

    def gen(rng, big):
        if big:
            text = "".join(rng.choice("ab") for _ in range(200000))
            return "".join(rng.choice("ab") for _ in range(rng.choice([3, 20, 1000]))), text
        text = "".join(rng.choice("abc") for _ in range(rng.randint(1, 10)))
        return "".join(rng.choice("abc") for _ in range(rng.randint(1, len(text)))), text


@problem
class PrefixSetEquality:
    title = "Prefix Sets"
    difficulty = "Hard"
    func = "samePrefixSets"
    statement = """
<p>Given lists <code>a</code> and <code>b</code>, each query <code>[x, y]</code> asks whether the <b>set</b> of values among
the first <code>x</code> elements of <code>a</code> equals the set of values among the first <code>y</code> elements of
<code>b</code>. Return <code>1</code> or <code>0</code> for each query.</p>
<ul><li><code>1 &lt;= a.length, b.length, queries.length &lt;= 10^5</code></li><li><code>1 &lt;= x &lt;= a.length</code>, <code>1 &lt;= y &lt;= b.length</code></li></ul>"""
    hint = dict(pattern="Number values by their first appearance in a; a prefix of a then holds exactly ids 1..k. Track for each prefix of b its distinct count and max id",
                module="Gold: Hashing", url="https://usaco.guide/gold/hashing", similar="AtCoder Prefix Equality (focus problem)")
    examples = [([1, 2, 3, 4, 5], [1, 2, 2, 4, 3], [[1, 1], [2, 2], [2, 3], [3, 3], [4, 4], [4, 5], [5, 5]]),]
    edges = [([7], [7], [[1, 1]]), ([7], [8], [[1, 1]])]

    def ref(a: List[int], b: List[int], queries: List[List[int]]) -> List[int]:
        ids, count_a = {}, []
        for x in a:
            if x not in ids:
                ids[x] = len(ids) + 1
            count_a.append(len(ids))
        seen, top, bad, info = set(), 0, False, []
        for y in b:
            if y not in ids:
                bad = True
            elif y not in seen:
                seen.add(y)
                top = max(top, ids[y])
            info.append((bad, len(seen), top))
        out = []
        for x, y in queries:
            is_bad, cnt, mx = info[y - 1]
            out.append(int(not is_bad and cnt == mx == count_a[x - 1]))
        return out

    def brute(a, b, queries):
        return [int(set(a[:x]) == set(b[:y])) for x, y in queries]

    def gen(rng, big):
        n, q, V = (100000, 100000, 1000) if big else (rng.randint(1, 6), rng.randint(1, 5), 4)
        a = [rng.randint(1, V) for _ in range(n)]
        b = [rng.randint(1, V) for _ in range(n)]
        return a, b, [[rng.randint(1, n), rng.randint(1, n)] for _ in range(q)]


@problem
class TreeEdgeUpdates:
    title = "Changing Road Lengths"
    difficulty = "Hard"
    func = "processQueries"
    tl = 3.0
    statement = """
<p><code>n</code> towns are joined by <code>n - 1</code> roads <code>roads[i] = [a, b, length]</code> forming a tree.
Process <code>queries</code> in order: <code>[1, i, w]</code> changes the length of road <code>i</code> to <code>w</code>;
<code>[2, u, v]</code> asks for the distance between towns <code>u</code> and <code>v</code>. Return the answers to the
type-2 queries.</p>
<ul><li><code>1 &lt;= n, queries.length &lt;= 5 * 10^4</code></li><li><code>1 &lt;= length, w &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Euler tour: a road's length is added to the whole subtree below it (Fenwick range add, point query = distance from the root); dist = d(u) + d(v) - 2 d(lca)",
                module="Gold: LCA with Euler Tour", url="https://usaco.guide/gold/lca-euler", similar="AtCoder Distance Queries on a Tree ★")
    examples = [(4, [[0, 1, 3], [1, 2, 4], [1, 3, 5]], [[2, 2, 3], [1, 0, 10], [2, 0, 2], [2, 3, 3]]),]
    edges = [(1, [], [[2, 0, 0]]), (2, [[0, 1, 5]], [[1, 0, 1], [2, 1, 0]])]

    def ref(n: int, roads: List[List[int]], queries: List[List[int]]) -> List[int]:
        adj = [[] for _ in range(n)]
        for i, (a, b, _) in enumerate(roads):
            adj[a].append((b, i))
            adj[b].append((a, i))
        parent, depth, child_of = [-1] * n, [0] * n, [0] * len(roads)  # child_of[i]: lower end of road i
        tin, order, stack = [0] * n, [], [0]
        parent[0] = 0
        while stack:  # iterative DFS gives a preorder in which every subtree is contiguous
            u = stack.pop()
            tin[u] = len(order)
            order.append(u)
            for v, i in adj[u]:
                if parent[v] == -1 and v != 0:
                    parent[v], depth[v], child_of[i] = u, depth[u] + 1, v
                    stack.append(v)
        size = [1] * n
        for u in reversed(order[1:]):
            size[parent[u]] += size[u]
        tree = [0] * (n + 2)

        def add(i, v):
            i += 1
            while i <= n:
                tree[i] += v
                i += i & -i

        def point(i):  # value at preorder index i = distance from the root
            i += 1
            s = 0
            while i > 0:
                s += tree[i]
                i -= i & -i
            return s

        def range_add(v, w):  # add w to the whole subtree of v
            add(tin[v], w)
            add(tin[v] + size[v], -w)

        length = [w for _, _, w in roads]
        for i, w in enumerate(length):
            range_add(child_of[i], w)
        LOG = max(1, n.bit_length())
        up = [parent[:]]
        for _ in range(1, LOG):
            prev = up[-1]
            up.append([prev[prev[v]] for v in range(n)])

        def lca(u, v):
            if depth[u] < depth[v]:
                u, v = v, u
            diff, k = depth[u] - depth[v], 0
            while diff:
                if diff & 1:
                    u = up[k][u]
                diff >>= 1
                k += 1
            if u == v:
                return u
            for k in range(LOG - 1, -1, -1):
                if up[k][u] != up[k][v]:
                    u, v = up[k][u], up[k][v]
            return parent[u]

        out = []
        for t, a, b in queries:
            if t == 1:
                range_add(child_of[a], b - length[a])
                length[a] = b
            else:
                out.append(point(tin[a]) + point(tin[b]) - 2 * point(tin[lca(a, b)]))
        return out

    def brute(n, roads, queries):
        length, out = [w for _, _, w in roads], []
        for t, a, b in queries:
            if t == 1:
                length[a] = b
                continue
            dist, q = {a: 0}, deque([a])
            while q:
                u = q.popleft()
                for i, (x, y, _) in enumerate(roads):
                    for s, e in ((x, y), (y, x)):
                        if s == u and e not in dist:
                            dist[e] = dist[u] + length[i]
                            q.append(e)
            out.append(dist[b])
        return out

    def gen(rng, big):
        n, q, W = (50000, 50000, 10**9) if big else (rng.randint(1, 7), rng.randint(1, 6), 9)
        label = rng.sample(range(n), n)
        roads = [[label[i - 1 if big and rng.random() < 0.5 else rng.randrange(i)], label[i], rng.randint(1, W)] for i in range(1, n)]
        qs = []
        for _ in range(q):
            if roads and rng.random() < 0.4:
                qs.append([1, rng.randrange(len(roads)), rng.randint(1, W)])
            else:
                qs.append([2, rng.randrange(n), rng.randrange(n)])
        return n, roads, qs


# ================================================================ stretch S1: number theory, combinatorics, counting

@problem
class PrimeMultiples:
    title = "Prime Multiples"
    difficulty = "Medium"
    func = "countMultiples"
    statement = """
<p>Count the integers from 1 to <code>n</code> that are divisible by at least one of the given distinct
<code>primes</code>.</p>
<ul><li><code>1 &lt;= n &lt;= 10^18</code></li><li><code>1 &lt;= primes.length &lt;= 20</code>, each prime <code>&lt;= n</code></li></ul>"""
    hint = dict(pattern="Inclusion-exclusion over subsets of primes; stop multiplying once the product exceeds n",
                module="Silver: Intro to Bitwise Operators", url="https://usaco.guide/silver/intro-bitwise", similar="CSES Prime Multiples ★")
    examples = [(20, [2, 5]), (10, [7])]
    edges = [(2, [2]), (30, [2, 3, 5])]

    def ref(n: int, primes: List[int]) -> int:
        total = 0

        def go(i, prod, sign):
            nonlocal total
            for j in range(i, len(primes)):
                p = prod * primes[j]
                if p > n:
                    continue
                total += sign * (n // p)
                go(j + 1, p, -sign)

        go(0, 1, 1)
        return total

    def brute(n, primes):
        return sum(any(x % p == 0 for p in primes) for x in range(1, n + 1))

    def gen(rng, big):
        small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71]
        if big:
            return 10**18, small_primes[:]
        n = rng.randint(2, 300)
        avail = [p for p in small_primes if p <= n]
        return n, sorted(rng.sample(avail, rng.randint(1, min(3, len(avail)))))


@problem
class ArrangementCount:
    title = "Arrangement Count"
    difficulty = "Medium"
    func = "countArrangements"
    statement = """
<p>Return the number of different strings that can be made by rearranging the letters of <code>s</code>, modulo
<code>10^9 + 7</code>.</p>
<ul><li><code>1 &lt;= s.length &lt;= 10^6</code>, lowercase letters</li></ul>"""
    hint = dict(pattern="n! divided by the factorial of each letter's count, using modular inverses (Fermat's little theorem)",
                module="Gold: Combinatorics", url="https://usaco.guide/gold/combo", similar="CSES Creating Strings II ★")
    examples = [("aabac",), ("abc",)]
    edges = [("a",), ("zzzz",)]

    def ref(s: str) -> int:
        M = 10**9 + 7
        fact = [1] * (len(s) + 1)
        for i in range(1, len(s) + 1):
            fact[i] = fact[i - 1] * i % M
        ans = fact[len(s)]
        for c in Counter(s).values():
            ans = ans * pow(fact[c], M - 2, M) % M
        return ans

    def brute(s):
        from itertools import permutations
        return len(set(permutations(s))) % MOD

    def gen(rng, big):
        if big:
            return ("".join(rng.choice("abcdefghij") for _ in range(10**6)),)
        return ("".join(rng.choice("abc") for _ in range(rng.randint(1, 7))),)


@problem
class SegmentComponents:
    title = "Coverage Components"
    difficulty = "Hard"
    func = "componentTotal"
    statement = """
<p>Each segment <code>[l, r]</code> covers the real numbers from <code>l</code> to <code>r</code>; all <code>2n</code>
endpoints are distinct. For every non-empty subset of the segments, count the connected pieces of their union. Return
the sum of those counts over all subsets, modulo <code>10^9 + 7</code>.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li>endpoints are distinct integers in <code>1..2n</code></li></ul>"""
    hint = dict(pattern="Count each piece by its leftmost segment: segment i starts a piece iff no chosen segment covers l_i, so it contributes 2^(n - 1 - #segments covering l_i)",
                module="Gold: Combinatorics", url="https://usaco.guide/gold/combo", similar="USACO Help Yourself ★")
    examples = [([[1, 6], [2, 3], [4, 5]],),]
    edges = [([[1, 2]],), ([[1, 2], [3, 4]],)]

    def ref(segments: List[List[int]]) -> int:
        M, n = 10**9 + 7, len(segments)
        segs = sorted(segments)
        pow2 = [1] * (n + 1)
        for i in range(n):
            pow2[i + 1] = pow2[i] * 2 % M
        heap, total = [], 0  # right ends of earlier segments; those still beyond l cover l
        for l, r in segs:
            while heap and heap[0] < l:
                heappop(heap)
            total += pow2[n - 1 - len(heap)]
            heappush(heap, r)
        return total % M

    def brute(segments):
        n, total = len(segments), 0
        for m in range(1, 1 << n):
            pick = sorted(segments[i] for i in range(n) if m >> i & 1)
            pieces, reach = 0, -1
            for l, r in pick:
                if l > reach:
                    pieces += 1
                reach = max(reach, r)
            total += pieces
        return total % MOD

    def gen(rng, big):
        n = 100000 if big else rng.randint(1, 6)
        pts = rng.sample(range(1, 2 * n + 1), 2 * n)
        return ([sorted(pts[2 * i:2 * i + 2]) for i in range(n)],)


@problem
class DigitSumRange:
    title = "Digit Sum Range"
    difficulty = "Medium"
    func = "digitSumBetween"
    statement = """
<p>Return the total of the digit sums of every integer from <code>a</code> to <code>b</code>, inclusive.</p>
<ul><li><code>0 &lt;= a &lt;= b &lt;= 10^15</code></li></ul>"""
    hint = dict(pattern="Answer = S(b) - S(a - 1), where S(x) sums digit sums of 0..x; count each digit position's contribution (or a digit DP)",
                module="Gold: Digit DP", url="https://usaco.guide/gold/digit-dp", similar="SPOJ Digit Sum ★")
    examples = [(0, 10), (28, 31)]
    edges = [(0, 0), (7, 7)]

    def ref(a: int, b: int) -> int:
        def upto(x):  # sum of digit sums of 0..x
            if x < 0:
                return 0
            total, p = 0, 1
            while p <= x:
                high, cur, low = x // (p * 10), x // p % 10, x % p
                total += high * 45 * p + (cur * (cur - 1) // 2) * p + cur * (low + 1)
                p *= 10
            return total

        return upto(b) - upto(a - 1)

    def brute(a, b):
        return sum(sum(map(int, str(x))) for x in range(a, b + 1))

    def gen(rng, big):
        if big:
            a = rng.randint(0, 10**15)
            return a, rng.randint(a, 10**15)
        a = rng.randint(0, 500)
        return a, rng.randint(a, 600)


@problem
class PermutationRounds:
    title = "Shuffle Rounds"
    difficulty = "Medium"
    func = "roundsToReturn"
    statement = """
<p>A shuffle moves the card at position <code>i</code> to position <code>perm[i]</code> (a permutation of
<code>0..n-1</code>). Starting from sorted order, return how many shuffles it takes to get back to sorted order for the
first time, modulo <code>10^9 + 7</code>.</p>
<ul><li><code>1 &lt;= n &lt;= 2 * 10^5</code></li></ul>"""
    hint = dict(pattern="The answer is the LCM of the cycle lengths; build it from the highest power of each prime (the real LCM is huge)",
                module="Gold: Divisibility", url="https://usaco.guide/gold/divisibility", similar="CSES Permutation Rounds ★")
    examples = [([4, 2, 1, 3, 0, 5],), ([0, 1],)]
    edges = [([0],), ([1, 0],)]

    def ref(perm: List[int]) -> int:
        n, seen, best = len(perm), [False] * len(perm), {}
        for s in range(n):
            length, u = 0, s
            while not seen[u]:
                seen[u] = True
                u = perm[u]
                length += 1
            p = 2
            while p * p <= length:  # factor the cycle length
                e = 0
                while length % p == 0:
                    length //= p
                    e += 1
                if e:
                    best[p] = max(best.get(p, 0), e)
                p += 1
            if length > 1:
                best[length] = max(best.get(length, 0), 1)
        ans = 1
        for p, e in best.items():
            ans = ans * pow(p, e, 10**9 + 7) % (10**9 + 7)
        return ans

    def brute(perm):
        cur, rounds = list(range(len(perm))), 0
        while True:
            nxt = [0] * len(perm)
            for i, c in enumerate(cur):
                nxt[perm[i]] = c
            cur, rounds = nxt, rounds + 1
            if cur == sorted(cur):
                return rounds % MOD

    def gen(rng, big):
        n = 200000 if big else rng.randint(1, 8)
        return (rng.sample(range(n), n),)


@problem
class NonCoprimePairs:
    title = "Shared Factor Pairs"
    difficulty = "Medium"
    func = "sharedFactorPairs"
    statement = """
<p>For each <code>n</code> in <code>queries</code>, count the pairs <code>(x, y)</code> with <code>1 &lt;= x &lt; y &lt;= n</code>
whose greatest common divisor is larger than 1.</p>
<ul><li><code>1 &lt;= queries.length &lt;= 10^5</code></li><li><code>1 &lt;= n &lt;= 2 * 10^5</code></li></ul>"""
    hint = dict(pattern="Total pairs minus coprime pairs; the coprime pairs with larger element y number phi(y), so sieve Euler's totient and prefix-sum it",
                module="Gold: Divisibility", url="https://usaco.guide/gold/divisibility", similar="SPOJ Playing with GCD ★")
    examples = [([4, 6, 10],),]
    edges = [([1, 2],)]

    def ref(queries: List[int]) -> List[int]:
        top = max(queries)
        phi = list(range(top + 1))
        for p in range(2, top + 1):
            if phi[p] == p:  # p is prime
                for m in range(p, top + 1, p):
                    phi[m] -= phi[m] // p
        coprime = [0] * (top + 1)  # coprime pairs x < y <= n
        for y in range(2, top + 1):
            coprime[y] = coprime[y - 1] + phi[y]
        return [n * (n - 1) // 2 - coprime[n] for n in queries]

    def brute(queries):
        from math import gcd
        return [sum(gcd(x, y) > 1 for x in range(1, n + 1) for y in range(x + 1, n + 1)) for n in queries]

    def gen(rng, big):
        if big:
            return ([rng.randint(1, 2 * 10**5) for _ in range(100000)],)
        return ([rng.randint(1, 30) for _ in range(rng.randint(1, 4))],)


@problem
class BestPairGcd:
    title = "Best Pair GCD"
    difficulty = "Medium"
    func = "maxPairGcd"
    statement = """
<p>Return the largest greatest common divisor of any two different elements (by position) of <code>nums</code>.</p>
<ul><li><code>2 &lt;= nums.length &lt;= 10^5</code></li><li><code>1 &lt;= nums[i] &lt;= 2 * 10^5</code></li></ul>"""
    hint = dict(pattern="For each d from the top down, count how many numbers are multiples of d (harmonic sum, O(V log V)); the first d with two multiples wins",
                module="Gold: Divisibility", url="https://usaco.guide/gold/divisibility", similar="CSES Common Divisors ★")
    examples = [([3, 14, 15, 7, 9],), ([5, 5],)]
    edges = [([1, 1],), ([2, 3],)]

    def ref(nums: List[int]) -> int:
        top = max(nums)
        cnt = [0] * (top + 1)
        for x in nums:
            cnt[x] += 1
        for d in range(top, 0, -1):
            total = 0
            for m in range(d, top + 1, d):
                total += cnt[m]
                if total >= 2:
                    return d

    def brute(nums):
        from math import gcd
        return max(gcd(a, b) for a, b in combinations(nums, 2))

    def gen(rng, big):
        if big:
            return ([rng.randint(1, 2 * 10**5) for _ in range(100000)],)
        return ([rng.randint(1, 30) for _ in range(rng.randint(2, 6))],)


@problem
class MaxGcdBySize:
    title = "GCD by Window Size"
    difficulty = "Hard"
    func = "maxGcdBySize"
    statement = """
<p>For every length <code>k</code> from 1 to <code>n</code>, return the largest greatest common divisor of any subarray
of <code>nums</code> with exactly <code>k</code> elements.</p>
<ul><li><code>1 &lt;= nums.length &lt;= 10^5</code></li><li><code>1 &lt;= nums[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Subarrays ending at i have at most ~30 distinct GCDs: keep (gcd, longest length) pairs per end, then take suffix maxima over length",
                module="Gold: Divisibility", url="https://usaco.guide/gold/divisibility", similar="CodeChef Maximum of GCDs (KSIZEGCD) ★")
    examples = [([12, 18, 9, 6],), ([5],)]
    edges = [([4, 4, 4],), ([2, 3],)]

    def ref(nums: List[int]) -> List[int]:
        from math import gcd
        n, best = len(nums), [0] * (len(nums) + 2)
        ends = {}  # gcd -> longest subarray ending here with that gcd
        for x in nums:
            nxt = {x: 1}
            for g, length in ends.items():
                ng = gcd(g, x)
                if nxt.get(ng, 0) < length + 1:
                    nxt[ng] = length + 1
            ends = nxt
            for g, length in ends.items():
                best[length] = max(best[length], g)
        for k in range(n - 1, 0, -1):  # a longer window's gcd is achievable (or beaten) by a shorter one
            best[k] = max(best[k], best[k + 1])
        return best[1:n + 1]

    def brute(nums):
        from math import gcd
        from functools import reduce
        n = len(nums)
        return [max(reduce(gcd, nums[i:i + k]) for i in range(n - k + 1)) for k in range(1, n + 1)]

    def gen(rng, big):
        if big:
            return ([rng.choice([2, 3, 4, 6, 12, 18, 36, 7]) * rng.randint(1, 10**7) for _ in range(100000)],)
        return ([rng.choice([2, 3, 4, 6, 8, 12]) for _ in range(rng.randint(1, 7))],)


@problem
class ExponentTower:
    title = "Exponent Tower"
    difficulty = "Medium"
    func = "towerMod"
    statement = """
<p>For each query <code>[a, b, c]</code>, return <code>a^(b^c)</code> modulo <code>10^9 + 7</code> (take
<code>0^0 = 1</code>).</p>
<ul><li><code>1 &lt;= queries.length &lt;= 10^5</code></li><li><code>0 &lt;= a, b, c &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Fermat: for a not divisible by p, reduce the exponent b^c modulo p - 1 (careful when a is a multiple of p)",
                module="Gold: Modular Arithmetic", url="https://usaco.guide/gold/modular", similar="CSES Exponentiation II ★")
    examples = [([[3, 7, 1], [15, 2, 2], [3, 4, 5]],),]
    edges = [([[0, 0, 0], [0, 0, 5], [0, 3, 0], [1000000007, 1, 1]],)]

    def ref(queries: List[List[int]]) -> List[int]:
        M, out = 10**9 + 7, []
        for a, b, c in queries:
            exponent_is_zero = b == 0 and c > 0  # b^c == 0 only when b = 0 and c >= 1
            if a % M == 0:
                out.append(1 if exponent_is_zero else 0)
            else:
                out.append(pow(a, pow(b, c, M - 1), M))
        return out

    def brute(queries):
        return [pow(a, b ** c, MOD) for a, b, c in queries]

    def gen(rng, big):
        if big:
            return ([[rng.randint(0, 10**9), rng.randint(0, 10**9), rng.randint(0, 10**9)] for _ in range(100000)],)
        return ([[rng.choice([0, 1, 2, 3, MOD, 2 * MOD]), rng.randint(0, 6), rng.randint(0, 4)] for _ in range(rng.randint(1, 4))],)


@problem
class DivisorSumPower:
    title = "Divisor Sum of a Power"
    difficulty = "Hard"
    func = "divisorSumOfPower"
    statement = """
<p>Return the sum of all positive divisors of <code>a^b</code>, modulo <code>9901</code>.</p>
<ul><li><code>1 &lt;= a &lt;= 5 * 10^7</code></li><li><code>0 &lt;= b &lt;= 5 * 10^7</code></li></ul>"""
    hint = dict(pattern="Factor a; the sum is a product of geometric series 1 + p + ... + p^(e*b). Watch out when p = 1 (mod 9901): the usual formula divides by zero",
                module="Gold: Modular Arithmetic", url="https://usaco.guide/gold/modular", similar="Kilonova Sumdiv ★ (POJ 1845)")
    examples = [(2, 3), (12, 1)]
    edges = [(1, 7), (9902, 1), (5, 0)]

    def ref(a: int, b: int) -> int:
        M, ans, p, x = 9901, 1, 2, a
        factors = []
        while p * p <= x:
            if x % p == 0:
                e = 0
                while x % p == 0:
                    x //= p
                    e += 1
                factors.append((p, e))
            p += 1
        if x > 1:
            factors.append((x, 1))
        for p, e in factors:
            terms = e * b + 1  # 1 + p + ... + p^(e*b)
            if p % M == 0:
                s = 1
            elif p % M == 1:
                s = terms % M
            else:
                s = (pow(p, terms, M) - 1) * pow(p - 1, M - 2, M) % M
            ans = ans * s % M
        return ans

    def brute(a, b):
        n, total, d = a ** b, 0, 1
        while d * d <= n:  # divisors come in pairs (d, n // d)
            if n % d == 0:
                total += d + (n // d if d * d != n else 0)
            d += 1
        return total % 9901

    def gen(rng, big):
        if big:
            return rng.randint(1, 5 * 10**7), rng.randint(0, 5 * 10**7)
        return rng.choice([1, 2, 6, 12, 9902, 19803, 30]), rng.randint(0, 2)


@problem
class DivisorAnalysis:
    title = "Divisor Analysis"
    difficulty = "Hard"
    func = "analyze"
    statement = """
<p>A number is given by its prime factorization: <code>factors[i] = [p, k]</code> means prime <code>p</code> appears
<code>k</code> times. Return <code>[number of divisors, sum of divisors, product of divisors]</code>, each modulo
<code>10^9 + 7</code>.</p>
<ul><li><code>1 &lt;= factors.length &lt;= 10^5</code>, distinct primes</li><li><code>2 &lt;= p &lt;= 10^6</code>, <code>1 &lt;= k &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Count and sum are products over primes. For the product, prime p appears k(k+1)/2 times per choice of the other exponents; reduce exponents mod p - 1 using prefix/suffix products",
                module="Gold: Modular Arithmetic", url="https://usaco.guide/gold/modular", similar="CSES Divisor Analysis ★")
    examples = [([[2, 2], [3, 1]],),]
    edges = [([[5, 1]],), ([[2, 20]],)]

    def ref(factors: List[List[int]]) -> List[int]:
        M = 10**9 + 7
        count = total = 1
        for p, k in factors:
            count = count * (k + 1) % M
            total = total * ((pow(p, k + 1, M) - 1) * pow(p - 1, M - 2, M) % M) % M
        n = len(factors)
        pre = [1] * (n + 1)  # products of (k + 1) modulo M - 1, for the exponents of the product
        for i, (_, k) in enumerate(factors):
            pre[i + 1] = pre[i] * (k + 1) % (M - 1)
        suf = [1] * (n + 1)
        for i in range(n - 1, -1, -1):
            suf[i] = suf[i + 1] * (factors[i][1] + 1) % (M - 1)
        product = 1
        for i, (p, k) in enumerate(factors):
            e = (k * (k + 1) // 2) % (M - 1) * pre[i] % (M - 1) * suf[i + 1] % (M - 1)
            product = product * pow(p, e, M) % M
        return [count, total, product]

    def brute(factors):
        n = 1
        for p, k in factors:
            n *= p ** k
        divs = [d for d in range(1, n + 1) if n % d == 0]
        prod = 1
        for d in divs:
            prod *= d
        return [len(divs) % MOD, sum(divs) % MOD, prod % MOD]

    def gen(rng, big):
        if big:
            sieve = bytearray([1]) * 1000001
            sieve[0] = sieve[1] = 0
            for i in range(2, 1001):
                if sieve[i]:
                    sieve[i * i::i] = bytearray(len(sieve[i * i::i]))
            primes = [i for i in range(1000001) if sieve[i]]
            return ([[p, rng.randint(1, 10**9)] for p in rng.sample(primes, 70000)],)
        return ([[p, rng.randint(1, 3)] for p in rng.sample([2, 3, 5, 7], rng.randint(1, 2))],)


@problem
class XorPaths:
    title = "XOR Paths"
    difficulty = "Hard"
    func = "countXorPaths"
    statement = """
<p>Count the paths from the top-left to the bottom-right cell of <code>grid</code> that move only right or down and
whose cells' values XOR to exactly <code>k</code>.</p>
<ul><li><code>1 &lt;= rows, cols &lt;= 20</code></li><li><code>0 &lt;= grid[r][c], k &lt;= 10^18</code></li></ul>"""
    hint = dict(pattern="Meet in the middle: enumerate paths from both corners to the middle anti-diagonal, store XORs per cell in hash maps, and match",
                module="Gold: Meet in the Middle", url="https://usaco.guide/gold/meet-in-the-middle", similar="CF Xor-Paths ★")
    examples = [([[2, 1, 5], [7, 10, 0], [12, 6, 4]], 11),]
    edges = [([[5]], 5), ([[5]], 4)]

    def ref(grid: List[List[int]], k: int) -> int:
        m, n = len(grid), len(grid[0])
        half = (m + n - 2) // 2
        meet = [defaultdict(int) for _ in range(m)]  # meet[r][x]: paths from the start to (r, half - r) with xor x (including that cell)
        stack = [(0, 0, grid[0][0])]
        while stack:
            r, c, x = stack.pop()
            if r + c == half:
                meet[r][x] += 1
                continue
            if r + 1 < m:
                stack.append((r + 1, c, x ^ grid[r + 1][c]))
            if c + 1 < n:
                stack.append((r, c + 1, x ^ grid[r][c + 1]))
        total = 0
        stack = [(m - 1, n - 1, grid[m - 1][n - 1])]
        while stack:
            r, c, x = stack.pop()
            if r + c == half:
                total += meet[r][x ^ grid[r][c] ^ k]  # the meeting cell was counted on both halves
                continue
            if r > 0:
                stack.append((r - 1, c, x ^ grid[r - 1][c]))
            if c > 0:
                stack.append((r, c - 1, x ^ grid[r][c - 1]))
        return total

    def brute(grid, k):
        m, n = len(grid), len(grid[0])

        def walk(r, c, x):
            x ^= grid[r][c]
            if (r, c) == (m - 1, n - 1):
                return int(x == k)
            return (walk(r + 1, c, x) if r + 1 < m else 0) + (walk(r, c + 1, x) if c + 1 < n else 0)

        return walk(0, 0, 0)

    def gen(rng, big):
        m, n = (20, 20) if big else (rng.randint(1, 4), rng.randint(1, 4))
        V = 10**18 if big else 3
        return [[rng.randint(0, V) for _ in range(n)] for _ in range(m)], rng.randint(0, V)


@problem
class EqualHeights:
    title = "Equal Heights"
    difficulty = "Medium"
    func = "minCost"
    statement = """
<p>Buildings have heights <code>heights</code>; changing building <code>i</code>'s height by 1 (up or down) costs
<code>costs[i]</code>. Return the minimum total cost to make all buildings the same height.</p>
<ul><li><code>1 &lt;= heights.length &lt;= 10^5</code></li><li><code>0 &lt;= heights[i] &lt;= 10^4</code>, <code>1 &lt;= costs[i] &lt;= 10^4</code></li></ul>"""
    hint = dict(pattern="The total cost is convex in the target height (ternary search works); the optimum is a weighted median of the heights",
                module="Gold: Optimizing Unimodal Functions", url="https://usaco.guide/gold/ternary-search", similar="SPOJ Building Construction ★")
    examples = [([1, 2, 3], [10, 100, 1000]), ([5, 5], [3, 7])]
    edges = [([7], [9]), ([0, 10000], [1, 1])]

    def ref(heights: List[int], costs: List[int]) -> int:
        pairs = sorted(zip(heights, costs))
        half, run = sum(costs), 0
        for h, c in pairs:  # weighted median
            run += c
            if 2 * run >= half:
                target = h
                break
        return sum(abs(h - target) * c for h, c in pairs)

    def brute(heights, costs):
        return min(sum(abs(h - t) * c for h, c in zip(heights, costs)) for t in range(min(heights), max(heights) + 1))

    def gen(rng, big):
        n, H = (100000, 10**4) if big else (rng.randint(1, 6), 12)
        return [rng.randint(0, H) for _ in range(n)], [rng.randint(1, 10**4 if big else 5) for _ in range(n)]


@problem
class Derangements:
    title = "Derangements"
    difficulty = "Medium"
    func = "derangements"
    statement = """
<p>A derangement of size <code>k</code> is a permutation of <code>1..k</code> where no number stays in its own position.
Return the number of derangements of each size <code>k = 1, 2, ..., n</code>, modulo <code>m</code> (which need not be
prime).</p>
<ul><li><code>1 &lt;= n &lt;= 10^6</code></li><li><code>2 &lt;= m &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Recurrence D(k) = (k - 1)(D(k - 1) + D(k - 2)): element k swaps with some j or slots into a derangement of the rest",
                module="Gold: Combinatorics", url="https://usaco.guide/gold/combo", similar="Yosupo Montmort Number (focus problem)")
    examples = [(5, 1000),]
    edges = [(1, 7), (2, 2)]

    def ref(n: int, m: int) -> List[int]:
        out, prev2, prev1 = [], 1, 0  # D(0) = 1, D(1) = 0
        out.append(0 % m)
        for k in range(2, n + 1):
            prev2, prev1 = prev1, (k - 1) * (prev1 + prev2) % m
            out.append(prev1)
        return out

    def brute(n, m):
        from itertools import permutations
        return [sum(all(p[i] != i for i in range(k)) for p in permutations(range(k))) % m for k in range(1, n + 1)]

    def gen(rng, big):
        return (10**6 if big else rng.randint(1, 7)), rng.randint(2, 10**9)


@problem
class DistributingApples:
    title = "Sharing Apples"
    difficulty = "Medium"
    func = "distributions"
    statement = """
<p>Return the number of ways to give <code>apples</code> identical apples to <code>children</code> children (a child may
get none), modulo <code>10^9 + 7</code>.</p>
<ul><li><code>1 &lt;= children, apples &lt;= 10^6</code></li></ul>"""
    hint = dict(pattern="Stars and bars: C(apples + children - 1, children - 1), with factorials and modular inverses",
                module="Gold: Combinatorics", url="https://usaco.guide/gold/combo", similar="CSES Distributing Apples (focus problem)")
    examples = [(3, 2), (1, 5)]
    edges = [(1, 1), (2, 1)]

    def ref(children: int, apples: int) -> int:
        M, top = 10**9 + 7, children + apples - 1
        fact = [1] * (top + 1)
        for i in range(1, top + 1):
            fact[i] = fact[i - 1] * i % M
        return fact[top] * pow(fact[children - 1], M - 2, M) % M * pow(fact[apples], M - 2, M) % M

    def brute(children, apples):
        @lru_cache(None)
        def f(c, a):
            return 1 if c == 1 else sum(f(c - 1, a - x) for x in range(a + 1))
        return f(children, apples) % MOD

    def gen(rng, big):
        if big:
            return 10**6, 10**6
        return rng.randint(1, 5), rng.randint(1, 6)


@problem
class GcdSum:
    title = "GCD Sum"
    difficulty = "Hard"
    func = "gcdSums"
    statement = """
<p>For each <code>n</code> in <code>queries</code>, return the sum of <code>gcd(i, j)</code> over all pairs
<code>1 &lt;= i &lt; j &lt;= n</code>.</p>
<ul><li><code>1 &lt;= queries.length &lt;= 10^5</code></li><li><code>1 &lt;= n &lt;= 2 * 10^5</code></li></ul>"""
    hint = dict(pattern="Sum over the larger element j: sum_{i<j} gcd(i, j) = sum over divisors d of j (d < j) of d * phi(j / d); sieve phi, add over multiples, prefix sums",
                module="Gold: Divisibility", url="https://usaco.guide/gold/divisibility", similar="SPOJ GCD Extreme (focus problem)")
    examples = [([3, 4, 10],),]
    edges = [([1, 2],)]

    def ref(queries: List[int]) -> List[int]:
        top = max(queries)
        phi = list(range(top + 1))
        for p in range(2, top + 1):
            if phi[p] == p:
                for m in range(p, top + 1, p):
                    phi[m] -= phi[m] // p
        f = [0] * (top + 1)  # f[j] = sum_{i<j} gcd(i, j)
        for d in range(1, top + 1):
            for k in range(2, top // d + 1):
                f[d * k] += d * phi[k]
        for j in range(1, top + 1):
            f[j] += f[j - 1]
        return [f[n] for n in queries]

    def brute(queries):
        from math import gcd
        return [sum(gcd(i, j) for i in range(1, n + 1) for j in range(i + 1, n + 1)) for n in queries]

    def gen(rng, big):
        if big:
            return ([rng.randint(1, 2 * 10**5) for _ in range(100000)],)
        return ([rng.randint(1, 30) for _ in range(rng.randint(1, 4))],)


@problem
class TotientQueries:
    title = "Totient Queries"
    difficulty = "Medium"
    func = "totients"
    statement = """
<p>For each number <code>x</code> in <code>nums</code>, return how many integers from 1 to <code>x</code> are coprime
with <code>x</code> (Euler's totient).</p>
<ul><li><code>1 &lt;= nums.length &lt;= 10^5</code></li><li><code>1 &lt;= nums[i] &lt;= 2 * 10^5</code></li></ul>"""
    hint = dict(pattern="Sieve: start phi[x] = x and, for every prime p, multiply each multiple's phi by (1 - 1/p)",
                module="Gold: Divisibility", url="https://usaco.guide/gold/divisibility", similar="SPOJ Euler Totient Function (focus problem)")
    examples = [([1, 2, 3, 4, 5, 10],),]
    edges = [([200000],)]

    def ref(nums: List[int]) -> List[int]:
        top = max(nums)
        phi = list(range(top + 1))
        for p in range(2, top + 1):
            if phi[p] == p:
                for m in range(p, top + 1, p):
                    phi[m] -= phi[m] // p
        return [phi[x] for x in nums]

    def brute(nums):
        from math import gcd
        return [sum(gcd(i, x) == 1 for i in range(1, x + 1)) for x in nums]

    def gen(rng, big):
        if big:
            return ([rng.randint(1, 2 * 10**5) for _ in range(100000)],)
        return ([rng.randint(1, 60) for _ in range(rng.randint(1, 5))],)


@problem
class SubsetCount:
    title = "Subset Count"
    difficulty = "Hard"
    func = "countSubsets"
    tl = 4.0
    statement = """
<p>Count the subsets of <code>nums</code> (by position, including the empty subset) whose elements add up to exactly
<code>target</code>.</p>
<ul><li><code>1 &lt;= nums.length &lt;= 36</code></li><li><code>1 &lt;= nums[i], target &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Meet in the middle: list all subset sums of each half (2^18 each), count one half in a hash map, look up target - s for the other",
                module="Gold: Meet in the Middle", url="https://usaco.guide/gold/meet-in-the-middle", similar="CSES Meet in the Middle (focus problem)")
    examples = [([2, 4, 1, 2], 5),]
    edges = [([5], 5), ([5], 4)]

    def ref(nums: List[int], target: int) -> int:
        def sums(part):
            out = [0]
            for x in part:
                out += [s + x for s in out]
            return out

        half = len(nums) // 2
        left = Counter(sums(nums[:half]))
        return sum(left[target - s] for s in sums(nums[half:]))

    def brute(nums, target):
        return sum(sum(nums[i] for i in range(len(nums)) if m >> i & 1) == target for m in range(1 << len(nums)))

    def gen(rng, big):
        if big:
            nums = [rng.randint(1, 50) for _ in range(36)]
            return nums, sum(nums) // 2
        nums = [rng.randint(1, 5) for _ in range(rng.randint(1, 10))]
        return nums, rng.randint(1, sum(nums))


# ================================================================ stretch S2: greedy, sorting, data structures, DP

@problem
class ResidueAlign:
    title = "Residue Alignment"
    difficulty = "Hard"
    func = "minOperations"
    statement = """
<p>One operation adds 1 to or subtracts 1 from a single element of <code>nums</code>. Return the fewest operations needed
so that all elements leave the same remainder when divided by <code>m</code>.</p>
<ul><li><code>1 &lt;= nums.length &lt;= 2 * 10^5</code></li><li><code>1 &lt;= m &lt;= 10^9</code>, <code>0 &lt;= nums[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Work with sorted remainders on a circle: double the list (add m), and the best target is the median of some window of n consecutive values; prefix sums make each window O(1)",
                module="Silver: Introduction to Prefix Sums", url="https://usaco.guide/silver/prefix-sums", similar="USACO Farmer John's Favorite Operation ★")
    examples = [([4, 2, 9, 1], 5), ([1, 1, 1], 2)]
    edges = [([7], 3), ([0, 5], 10)]

    def ref(nums: List[int], m: int) -> int:
        r = sorted(x % m for x in nums)
        n = len(r)
        b = r + [x + m for x in r]
        pre = [0]
        for x in b:
            pre.append(pre[-1] + x)
        best = None
        for i in range(n):
            mid = i + n // 2
            x = b[mid]
            cost = x * (mid - i) - (pre[mid] - pre[i]) + (pre[i + n] - pre[mid + 1]) - x * (i + n - mid - 1)
            best = cost if best is None else min(best, cost)
        return best

    def brute(nums, m):
        return min(sum(min((x - t) % m, (t - x) % m) for x in nums) for t in range(m))

    def gen(rng, big):
        if big:
            return [rng.randint(0, 10**9) for _ in range(200000)], rng.randint(1, 10**9)
        return [rng.randint(0, 20) for _ in range(rng.randint(1, 6))], rng.randint(1, 9)


@problem
class ForestComponents:
    title = "Forest Components"
    difficulty = "Hard"
    func = "componentsInRects"
    statement = """
<p>A map is a list of strings of <code>'0'</code> and <code>'1'</code>. The <code>'1'</code> cells, connected
up/down/left/right, form a forest: there is never more than one path between two <code>'1'</code> cells. For each query
<code>[r1, c1, r2, c2]</code>, return how many connected groups of <code>'1'</code> cells there are when you look only
inside that rectangle (inclusive).</p>
<ul><li><code>1 &lt;= rows, cols &lt;= 500</code></li><li><code>1 &lt;= queries.length &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="In a forest, components = vertices - edges; 2-D prefix sums of cells, horizontal links and vertical links answer each rectangle in O(1)",
                module="Silver: More on Prefix Sums", url="https://usaco.guide/silver/more-prefix-sums", similar="AtCoder Nuske vs Phantom Thnook ★")
    examples = [(["1101", "0110", "1101"], [[0, 0, 2, 3], [1, 1, 2, 3], [0, 0, 0, 0]]),]
    edges = [(["0"], [[0, 0, 0, 0]]), (["1"], [[0, 0, 0, 0]])]

    def ref(grid: List[str], queries: List[List[int]]) -> List[int]:
        m, n = len(grid), len(grid[0])

        def prefix(cell):
            P = [[0] * (n + 1) for _ in range(m + 1)]
            for i in range(m):
                for j in range(n):
                    P[i + 1][j + 1] = cell(i, j) + P[i][j + 1] + P[i + 1][j] - P[i][j]
            return P

        V = prefix(lambda i, j: grid[i][j] == "1")
        H = prefix(lambda i, j: j + 1 < n and grid[i][j] == "1" and grid[i][j + 1] == "1")  # link to the right
        D = prefix(lambda i, j: i + 1 < m and grid[i][j] == "1" and grid[i + 1][j] == "1")  # link downward

        def rect(P, r1, c1, r2, c2):
            if r1 > r2 or c1 > c2:
                return 0
            return P[r2 + 1][c2 + 1] - P[r1][c2 + 1] - P[r2 + 1][c1] + P[r1][c1]

        return [rect(V, r1, c1, r2, c2) - rect(H, r1, c1, r2, c2 - 1) - rect(D, r1, c1, r2 - 1, c2) for r1, c1, r2, c2 in queries]

    def brute(grid, queries):
        out = []
        for r1, c1, r2, c2 in queries:
            seen, comps = set(), 0
            for i in range(r1, r2 + 1):
                for j in range(c1, c2 + 1):
                    if grid[i][j] == "1" and (i, j) not in seen:
                        comps += 1
                        seen.add((i, j))
                        stack = [(i, j)]
                        while stack:
                            a, b = stack.pop()
                            for x, y in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                                if r1 <= x <= r2 and c1 <= y <= c2 and grid[x][y] == "1" and (x, y) not in seen:
                                    seen.add((x, y))
                                    stack.append((x, y))
            out.append(comps)
        return out

    def gen(rng, big):
        m, n, q = (500, 500, 100000) if big else (rng.randint(1, 5), rng.randint(1, 5), rng.randint(1, 4))
        parent = {}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        cells = [(i, j) for i in range(m) for j in range(n)]
        rng.shuffle(cells)
        for c in cells[:int(len(cells) * 0.7)]:  # add a cell only if it can't close a cycle
            roots = [find(nb) for nb in ((c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)) if nb in parent]
            if len(roots) == len(set(roots)):
                parent[c] = c
                for r in roots:
                    parent[r] = c
        grid = ["".join("1" if (i, j) in parent else "0" for j in range(n)) for i in range(m)]
        qs = []
        for _ in range(q):
            r1, r2 = sorted((rng.randrange(m), rng.randrange(m)))
            c1, c2 = sorted((rng.randrange(n), rng.randrange(n)))
            qs.append([r1, c1, r2, c2])
        return grid, qs


@problem
class WindyVoyage:
    title = "Windy Voyage"
    difficulty = "Hard"
    func = "minDays"
    statement = """
<p>A ship starts at <code>start = [x, y]</code> and must reach <code>goal = [x, y]</code>. The wind follows the repeating
pattern <code>wind</code> (letters <code>U</code>, <code>D</code>, <code>L</code>, <code>R</code>): on day <code>i</code> it
pushes the ship one unit in direction <code>wind[i mod len]</code>. Each day the ship may also move one unit in any of the
four directions or stay put, in addition to the wind. Return the fewest days to reach the goal, or <code>-1</code> if it
is impossible.</p>
<ul><li><code>1 &lt;= wind.length &lt;= 10^5</code></li><li>coordinates between <code>0</code> and <code>10^9</code></li></ul>"""
    hint = dict(pattern="Binary search on the number of days: after d days the wind alone moves you to a known spot (prefix sums), and you can cover any Manhattan distance <= d yourself",
                module="Silver: Binary Search", url="https://usaco.guide/silver/binary-search", similar="CF Magic Ship ★")
    examples = [([0, 0], [4, 6], "UUU"), ([0, 3], [0, 0], "UDD"), ([0, 0], [0, 1], "L")]
    edges = [([5, 5], [5, 5], "R"), ([0, 0], [0, 9], "D")]

    def ref(start: List[int], goal: List[int], wind: str) -> int:
        step = {"U": (0, 1), "D": (0, -1), "L": (-1, 0), "R": (1, 0)}
        px, py = [0], [0]
        for ch in wind:
            px.append(px[-1] + step[ch][0])
            py.append(py[-1] + step[ch][1])
        n = len(wind)

        def ok(d):
            q, r = divmod(d, n)
            wx, wy = q * px[n] + px[r], q * py[n] + py[r]
            return abs(goal[0] - start[0] - wx) + abs(goal[1] - start[1] - wy) <= d

        hi = 10**15
        if not ok(hi):
            return -1
        lo = 0
        while lo < hi:
            mid = (lo + hi) // 2
            if ok(mid):
                hi = mid
            else:
                lo = mid + 1
        return lo

    def brute(start, goal, wind):
        step = {"U": (0, 1), "D": (0, -1), "L": (-1, 0), "R": (1, 0)}
        x, y = start
        for d in range(0, 3000):  # small cases: the answer, if any, is tiny
            if abs(goal[0] - x) + abs(goal[1] - y) <= d:
                return d
            dx, dy = step[wind[d % len(wind)]]
            x, y = x + dx, y + dy
        return -1

    def gen(rng, big):
        if big:
            return [rng.randint(0, 10**9), rng.randint(0, 10**9)], [rng.randint(0, 10**9), rng.randint(0, 10**9)], \
                "".join(rng.choice("UDLR") for _ in range(100000))
        return [rng.randint(0, 5), rng.randint(0, 5)], [rng.randint(0, 5), rng.randint(0, 5)], "".join(rng.choice("UDLR") for _ in range(rng.randint(1, 4)))


@problem
class SplittingField:
    title = "Splitting the Field"
    difficulty = "Hard"
    func = "areaSaved"
    statement = """
<p>Cows stand at points <code>cows[i] = [x, y]</code>. One axis-aligned fence rectangle around all of them has some area.
Instead, you may use two axis-aligned rectangles that don't overlap (they can't even touch), each enclosing at least one
cow, together enclosing every cow. Return how much area that saves at best: the single rectangle's area minus the
smallest possible total area of two rectangles (<code>0</code> if two rectangles never help).</p>
<ul><li><code>2 &lt;= cows.length &lt;= 5 * 10^4</code></li><li><code>1 &lt;= x, y &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Two non-touching rectangles are split by a vertical or horizontal line: sort by x (then by y), use prefix and suffix min/max of the other coordinate, and skip splits between equal coordinates",
                module="Silver: Custom Comparators and Coordinate Compression", url="https://usaco.guide/silver/sorting-custom",
                similar="USACO Splitting the Field ★")
    examples = [([[4, 1], [10, 5], [1, 3], [3, 4], [9, 7], [7, 9]],), ([[1, 1], [1, 1]],)]
    edges = [([[1, 1], [2, 2]],), ([[1, 5], [1, 9], [1, 2]],)]

    def ref(cows: List[List[int]]) -> int:
        def best_split(pts):  # split by the first coordinate
            pts = sorted(pts)
            n = len(pts)
            lo, hi = [0] * n, [0] * n
            cur_lo = cur_hi = pts[0][1]
            for i, (_, y) in enumerate(pts):
                cur_lo, cur_hi = min(cur_lo, y), max(cur_hi, y)
                lo[i], hi[i] = cur_lo, cur_hi
            best, s_lo, s_hi = None, pts[-1][1], pts[-1][1]
            for i in range(n - 1, 0, -1):
                s_lo, s_hi = min(s_lo, pts[i][1]), max(s_hi, pts[i][1])
                if pts[i][0] == pts[i - 1][0]:
                    continue  # equal x on both sides would make the rectangles touch
                area = (pts[i - 1][0] - pts[0][0]) * (hi[i - 1] - lo[i - 1]) + (pts[-1][0] - pts[i][0]) * (s_hi - s_lo)
                best = area if best is None else min(best, area)
            return best

        xs, ys = [x for x, _ in cows], [y for _, y in cows]
        whole = (max(xs) - min(xs)) * (max(ys) - min(ys))
        options = [a for a in (best_split([(x, y) for x, y in cows]), best_split([(y, x) for x, y in cows])) if a is not None]
        return max(0, whole - min(options)) if options else 0

    def brute(cows):
        n = len(cows)
        xs, ys = [x for x, _ in cows], [y for _, y in cows]
        whole, best = (max(xs) - min(xs)) * (max(ys) - min(ys)), None

        def box(group):
            gx, gy = [x for x, _ in group], [y for _, y in group]
            return min(gx), max(gx), min(gy), max(gy)

        for m in range(1, (1 << n) - 1):
            a = [cows[i] for i in range(n) if m >> i & 1]
            b = [cows[i] for i in range(n) if not m >> i & 1]
            A, B = box(a), box(b)
            apart = A[1] < B[0] or B[1] < A[0] or A[3] < B[2] or B[3] < A[2]
            if apart:
                area = (A[1] - A[0]) * (A[3] - A[2]) + (B[1] - B[0]) * (B[3] - B[2])
                best = area if best is None else min(best, area)
        return 0 if best is None else max(0, whole - best)

    def gen(rng, big):
        n, V = (50000, 10**9) if big else (rng.randint(2, 7), 6)
        return ([[rng.randint(1, V), rng.randint(1, V)] for _ in range(n)],)


@problem
class Deforestation:
    title = "Selective Logging"
    difficulty = "Hard"
    func = "maxCut"
    statement = """
<p>Trees stand at positions <code>trees</code> (several trees can share a position). Each rule <code>[l, r, t]</code> says
at least <code>t</code> trees with positions in <code>[l, r]</code> must remain standing. Return the most trees you can cut
down while obeying every rule. The rules can always be satisfied.</p>
<ul><li><code>1 &lt;= trees.length, rules.length &lt;= 5 * 10^4</code></li><li>positions between <code>-10^9</code> and <code>10^9</code></li></ul>"""
    hint = dict(pattern="Decide which trees to KEEP: process rules by right end; keep extra trees as far right as possible (they help later rules most), using sorted lists",
                module="Silver: Priority Queues", url="https://usaco.guide/silver/priority-queues", similar="USACO Deforestation ★")
    examples = [([1, 2, 3, 4, 5, 6, 7], [[1, 4, 2], [3, 7, 3]]),]
    edges = [([5], [[5, 5, 1]]), ([1, 1, 1], [[0, 2, 1]])]

    def ref(trees: List[int], rules: List[List[int]]) -> int:
        from bisect import bisect_right, insort
        free = sorted(trees)  # trees not yet kept
        kept = []
        for l, r, t in sorted(rules, key=lambda x: x[1]):
            have = bisect_right(kept, r) - bisect_left(kept, l)
            i = bisect_right(free, r) - 1
            while have < t:  # keep the rightmost free trees inside [l, r]
                insort(kept, free.pop(i))
                i -= 1
                have += 1
        return len(trees) - len(kept)

    def brute(trees, rules):
        n, best = len(trees), 0
        for m in range(1 << n):
            keep = [trees[i] for i in range(n) if m >> i & 1]
            if all(sum(l <= x <= r for x in keep) >= t for l, r, t in rules):
                best = max(best, n - len(keep))
        return best

    def gen(rng, big):
        n, k, V = (50000, 50000, 10**9) if big else (rng.randint(1, 8), rng.randint(1, 4), 8)
        trees = sorted(rng.randint(-V, V) for _ in range(n))
        rules = []
        for _ in range(k):
            l, r = sorted((rng.randint(-V, V), rng.randint(-V, V)))
            inside = bisect_left(trees, r + 1) - bisect_left(trees, l)
            rules.append([l, r, rng.randint(0, min(inside, 3 if not big else inside // 3 + 1))])
        rng.shuffle(trees)
        return trees, rules


@problem
class SurvivalWeakest:
    title = "Survival of the Smallest"
    difficulty = "Hard"
    func = "lastNumber"
    tl = 3.0
    statement = """
<p>Start with the list <code>nums</code> of length <code>n</code>. Repeat until one number is left: form all sums of two
elements at different positions, sort them, and keep only the smallest <code>(current length) - 1</code> of them as the
new list. Return the final number modulo <code>10^9 + 7</code>.</p>
<ul><li><code>2 &lt;= nums.length &lt;= 300</code></li><li><code>0 &lt;= nums[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Don't build all n^2 sums: the k smallest pair sums of a sorted list come from a heap that walks each row i, i+1, i+2, ... (the numbers grow huge, which Python handles)",
                module="Silver: Priority Queues", url="https://usaco.guide/silver/priority-queues", similar="CF Survival of the Weakest (easy version) ★")
    examples = [([1, 2, 4, 5, 6],), ([3, 7],)]
    edges = [([0, 0],), ([1, 1, 1],)]

    def ref(nums: List[int]) -> int:
        a = sorted(nums)
        while len(a) > 1:
            L = len(a)
            heap = [(a[i] + a[i + 1], i, i + 1) for i in range(L - 1)]
            heapify(heap)
            nxt = []
            for _ in range(L - 1):
                s, i, j = heappop(heap)
                nxt.append(s)
                if j + 1 < L:
                    heappush(heap, (a[i] + a[j + 1], i, j + 1))
            a = nxt
        return a[0] % (10**9 + 7)

    def brute(nums):
        a = sorted(nums)
        while len(a) > 1:
            a = sorted(x + y for x, y in combinations(a, 2))[:len(a) - 1]
        return a[0] % MOD

    def gen(rng, big):
        n = 300 if big else rng.randint(2, 6)
        return ([rng.randint(0, 10**9 if big else 9) for _ in range(n)],)


@problem
class SushiBelt:
    title = "Sushi Belt"
    difficulty = "Hard"
    func = "maxDelight"
    statement = """
<p>Sushi plates pass by one per minute; plate <code>i</code> (minute <code>i</code>) has deliciousness
<code>plates[i]</code>. Each minute you either take the plate passing by (adding <code>k</code> pieces to your stack),
eat one piece from your stack, or do nothing. Every piece you take must be eaten by the end of the last minute. Return
the greatest total deliciousness of plates you can take.</p>
<ul><li><code>1 &lt;= plates.length &lt;= 2 * 10^5</code></li><li><code>1 &lt;= k &lt;= plates.length</code>, <code>1 &lt;= plates[i] &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Each plate needs k later minutes to eat, so the plates taken from minute i on can number at most (n - i) // (k + 1): scan from the end keeping chosen plates in a min-heap, dropping the cheapest whenever that limit is exceeded",
                module="Silver: Priority Queues", url="https://usaco.guide/silver/priority-queues", similar="CF Serval and Kaitenzushi Buffet ★")
    examples = [([3, 6, 4, 1, 2], 2), ([5, 1], 1)]
    edges = [([9], 1), ([1, 2, 3, 4], 4)]

    def ref(plates: List[int], k: int) -> int:
        heap, n = [], len(plates)  # min-heap of the plates currently chosen
        for i in range(n - 1, -1, -1):
            heappush(heap, plates[i])
            if len(heap) > (n - i) // (k + 1):  # too many plates from minute i on to finish eating
                heappop(heap)
        return sum(heap)

    def brute(plates, k):
        n, best = len(plates), 0
        for m in range(1 << n):
            pending, ok = 0, True
            for i in range(n):
                if m >> i & 1:
                    pending += k
                elif pending:
                    pending -= 1
            if pending == 0:
                best = max(best, sum(plates[i] for i in range(n) if m >> i & 1))
        return best

    def gen(rng, big):
        n = 200000 if big else rng.randint(1, 10)
        return [rng.randint(1, 10**9 if big else 9) for _ in range(n)], rng.randint(1, 3 if big else n)


@problem
class SkylinePhoto:
    title = "Skyline Photos"
    difficulty = "Hard"
    func = "maxBeauty"
    statement = """
<p>Buildings in a row have distinct <code>heights</code> and beauties <code>beauty</code> (possibly negative). Split the
row into one or more consecutive photos; a photo's beauty is the beauty of its <b>shortest</b> building. Return the
greatest possible total beauty.</p>
<ul><li><code>1 &lt;= n &lt;= 3 * 10^5</code></li><li><code>heights</code> is a permutation of <code>1..n</code>; <code>|beauty[i]| &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="DP over prefixes with a monotonic stack: building i either joins the photo of the previous shorter building (same value), or is the shortest of a new photo (best prefix in between + beauty[i])",
                module="Gold: Stacks", url="https://usaco.guide/gold/stacks", similar="CF Skyline Photo ★")
    examples = [([1, 2, 3, 5, 4], [1, 5, 3, 2, 4]), ([2, 1], [-2, -3])]
    edges = [([1], [-7]), ([1, 2], [5, -1])]

    def ref(heights: List[int], beauty: List[int]) -> int:
        n = len(heights)
        f = [0] * (n + 1)  # f[i]: best total for the first i buildings
        stack = []  # (index, best f over [previous shorter index, index - 1])
        for i in range(1, n + 1):
            h, b = heights[i - 1], beauty[i - 1]
            m = f[i - 1]
            while stack and heights[stack[-1][0] - 1] > h:
                m = max(m, stack.pop()[1])
            f[i] = m + b
            if stack:
                f[i] = max(f[i], f[stack[-1][0]])  # join the previous shorter building's photo
            stack.append((i, m))
        return f[n]

    def brute(heights, beauty):
        n = len(heights)

        @lru_cache(None)
        def f(i):  # best for buildings i..n-1
            if i == n:
                return 0
            best, low = None, None
            for j in range(i, n):
                if low is None or heights[j] < heights[low]:
                    low = j
                v = beauty[low] + f(j + 1)
                best = v if best is None else max(best, v)
            return best

        return f(0)

    def gen(rng, big):
        n = 300000 if big else rng.randint(1, 8)
        return rng.sample(range(1, n + 1), n), [rng.randint(-10**9 if big else -5, 10**9 if big else 5) for _ in range(n)]


@problem
class QueueComposite:
    title = "Function Queue"
    difficulty = "Hard"
    func = "processQueries"
    tl = 3.0
    statement = """
<p>A queue holds linear functions <code>f(x) = a*x + b</code>. Process <code>queries</code>:</p>
<ul><li><code>[0, a, b]</code>: push <code>a*x + b</code> to the back.</li><li><code>[1]</code>: pop the front function.</li>
<li><code>[2, x]</code>: apply every function in the queue to <code>x</code>, front first, and report the result modulo
<code>998244353</code> (with an empty queue, report <code>x</code>).</li></ul>
<p>Return all reported values.</p>
<ul><li><code>1 &lt;= queries.length &lt;= 2 * 10^5</code></li><li><code>0 &lt;= a, b, x &lt; 998244353</code>; pops never hit an empty queue</li></ul>"""
    hint = dict(pattern="Queue from two stacks, each storing prefix compositions; when the front stack empties, move everything over and rebuild its compositions",
                module="Gold: Sliding Window", url="https://usaco.guide/gold/sliding-window", similar="Library Checker Queue Operate All Composite ★")
    examples = [([[0, 1, 2], [0, 3, 0], [2, 5], [1], [2, 5]],),]
    edges = [([[2, 7]],), ([[0, 0, 4], [2, 9], [1], [2, 9]],)]

    def ref(queries: List[List[int]]) -> List[int]:
        M = 998244353
        front, back = [], []  # entries: (a, b, composed a, composed b)
        out = []

        def compose(f, g):  # g after f: g(f(x))
            return f[0] * g[0] % M, (f[1] * g[0] + g[1]) % M

        for q in queries:
            if q[0] == 0:
                a, b = q[1], q[2]
                agg = compose(back[-1][2:], (a, b)) if back else (a, b)
                back.append((a, b) + agg)
            elif q[0] == 1:
                if not front:
                    while back:
                        a, b = back.pop()[:2]
                        agg = compose((a, b), front[-1][2:]) if front else (a, b)  # front stack composes towards the back
                        front.append((a, b) + agg)
                front.pop()
            else:
                f = front[-1][2:] if front else (1, 0)
                g = back[-1][2:] if back else (1, 0)
                a, b = compose(f, g)
                out.append((a * q[1] + b) % M)
        return out

    def brute(queries):
        M, funcs, out = 998244353, deque(), []
        for q in queries:
            if q[0] == 0:
                funcs.append((q[1], q[2]))
            elif q[0] == 1:
                funcs.popleft()
            else:
                x = q[1]
                for a, b in funcs:
                    x = (a * x + b) % M
                out.append(x)
        return out

    def gen(rng, big):
        n, V = (200000, 998244352) if big else (rng.randint(1, 8), 5)
        qs, size = [], 0
        for _ in range(n):
            r = rng.random()
            if r < 0.45:
                qs.append([0, rng.randint(0, V), rng.randint(0, V)])
                size += 1
            elif r < 0.7 and size:
                qs.append([1])
                size -= 1
            else:
                qs.append([2, rng.randint(0, V)])
        return (qs,)


@problem
class SnowBoots:
    title = "Snow Boots"
    difficulty = "Hard"
    func = "canCross"
    statement = """
<p>A path of tiles has snow depths <code>depths</code> (the first and last tiles have depth 0). With boots
<code>[s, d]</code> you may stand only on tiles with depth at most <code>s</code>, and each step moves forward at most
<code>d</code> tiles. For each pair of boots, return <code>1</code> if you can walk from the first tile to the last, else
<code>0</code>.</p>
<ul><li><code>2 &lt;= depths.length, boots.length &lt;= 10^5</code></li><li><code>0 &lt;= depth, s &lt;= 10^9</code>, <code>1 &lt;= d &lt; depths.length</code></li></ul>"""
    hint = dict(pattern="Offline: sort boots by s descending and remove too-deep tiles from a linked list as s drops; track the largest gap between usable tiles",
                module="Gold: More Operations on Sorted Sets", url="https://usaco.guide/gold/intro-sorted-sets", similar="USACO Snow Boots ★ (Gold)")
    examples = [([0, 2, 8, 3, 6, 7, 5, 1, 4, 0], [[2, 4], [8, 1], [6, 3], [5, 2]]),]
    edges = [([0, 0], [[0, 1]]), ([0, 9, 0], [[5, 1], [5, 2]])]

    def ref(depths: List[int], boots: List[List[int]]) -> List[int]:
        n = len(depths)
        prv, nxt = list(range(-1, n - 1)), list(range(1, n + 1))
        tiles = sorted(range(1, n - 1), key=lambda i: -depths[i])
        out, gap, t = [0] * len(boots), 1, 0
        for bi in sorted(range(len(boots)), key=lambda i: -boots[i][0]):
            s, d = boots[bi]
            while t < len(tiles) and depths[tiles[t]] > s:  # this tile becomes unusable
                i = tiles[t]
                a, b = prv[i], nxt[i]
                nxt[a], prv[b] = b, a
                gap = max(gap, b - a)
                t += 1
            out[bi] = int(gap <= d)
        return out

    def brute(depths, boots):
        out = []
        for s, d in boots:
            last, ok = 0, True
            for i in range(1, len(depths)):
                if depths[i] <= s:
                    if i - last > d:
                        ok = False
                        break
                    last = i
            out.append(int(ok))
        return out

    def gen(rng, big):
        n, b, V = (100000, 100000, 10**9) if big else (rng.randint(2, 8), rng.randint(1, 4), 9)
        depths = [0] + [rng.randint(0, V) for _ in range(n - 2)] + [0]
        return depths, [[rng.randint(0, V), rng.randint(1, n - 1)] for _ in range(b)]


@problem
class RectangularPasture:
    title = "Fenced Herds"
    difficulty = "Hard"
    func = "countSubsets"
    statement = """
<p>Cows stand at points <code>cows[i] = [x, y]</code>; all x coordinates are distinct and all y coordinates are distinct.
Count the subsets of cows (including the empty one) that are exactly the cows inside some axis-aligned rectangle.</p>
<ul><li><code>1 &lt;= cows.length &lt;= 800</code></li><li><code>0 &lt;= x, y &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Fix the leftmost and rightmost cow (O(n^2) pairs); the subset is then set by how far the rectangle extends below and above them: count cows below/above with 2-D prefix sums",
                module="Silver: Custom Comparators and Coordinate Compression", url="https://usaco.guide/silver/sorting-custom",
                similar="USACO Rectangular Pasture (focus problem)")
    examples = [([[0, 2], [1, 0], [2, 3], [3, 5]],),]
    edges = [([[5, 5]],), ([[0, 0], [1, 1]],)]

    def ref(cows: List[List[int]]) -> int:
        pts = sorted(cows)
        n = len(pts)
        ys = sorted(y for _, y in pts)
        rank = [bisect_left(ys, y) for _, y in pts]
        below = [[0] * (n + 1) for _ in range(n + 1)]  # below[i][r]: cows among the first i (by x) with y-rank < r
        for i in range(n):
            row, prev = below[i + 1], below[i]
            for r in range(n + 1):
                row[r] = prev[r] + (rank[i] < r)
        total = 1  # the empty subset
        for i in range(n):
            for j in range(i, n):
                lo, hi = min(rank[i], rank[j]), max(rank[i], rank[j])
                under = below[j + 1][lo] - below[i][lo]
                over = (j - i + 1) - (below[j + 1][hi + 1] - below[i][hi + 1])
                total += (under + 1) * (over + 1)
        return total

    def brute(cows):
        xs = sorted({x for x, _ in cows})
        ys = sorted({y for _, y in cows})
        subsets = set()
        for x1 in range(len(xs)):
            for x2 in range(x1, len(xs)):
                for y1 in range(len(ys)):
                    for y2 in range(y1, len(ys)):
                        subsets.add(frozenset(i for i, (x, y) in enumerate(cows) if xs[x1] <= x <= xs[x2] and ys[y1] <= y <= ys[y2]))
        subsets.add(frozenset())
        return len(subsets)

    def gen(rng, big):
        n, V = (800, 10**9) if big else (rng.randint(1, 6), 20)
        return ([[x, y] for x, y in zip(rng.sample(range(V), n), rng.sample(range(V), n))],)


@problem
class StaticRangeQueries:
    title = "Sparse Range Sums"
    difficulty = "Hard"
    func = "rangeTotals"
    statement = """
<p>An array indexed <code>0 .. 10^9</code> starts all zero. First apply every update <code>[l, r, v]</code>, which adds
<code>v</code> to every index in <code>[l, r)</code>. Then, for each query <code>[l, r]</code>, return the sum of the
array over indices <code>[l, r)</code>.</p>
<ul><li><code>1 &lt;= updates.length, queries.length &lt;= 10^5</code></li><li><code>0 &lt;= l &lt; r &lt;= 10^9</code>, <code>1 &lt;= v &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Coordinate-compress every endpoint; difference array over the compressed points, then prefix sums of (value x segment length)",
                module="Silver: Custom Comparators and Coordinate Compression", url="https://usaco.guide/silver/sorting-custom",
                similar="CF Gym Static Range Queries (focus problem)")
    examples = [([[1, 3, 1], [2, 4, 2]], [[0, 5], [3, 4], [1, 2]]),]
    edges = [([[0, 1, 5]], [[0, 1], [1, 2]])]

    def ref(updates: List[List[int]], queries: List[List[int]]) -> List[int]:
        pts = sorted({p for l, r, _ in updates for p in (l, r)} | {p for l, r in queries for p in (l, r)})
        idx = {p: i for i, p in enumerate(pts)}
        diff = [0] * (len(pts) + 1)
        for l, r, v in updates:
            diff[idx[l]] += v
            diff[idx[r]] -= v
        upto, run = [0] * len(pts), 0  # upto[i]: array sum over [0, pts[i])
        for i in range(len(pts) - 1):
            run += diff[i]
            upto[i + 1] = upto[i] + run * (pts[i + 1] - pts[i])
        return [upto[idx[r]] - upto[idx[l]] for l, r in queries]

    def brute(updates, queries):
        arr = Counter()
        for l, r, v in updates:
            for i in range(l, r):
                arr[i] += v
        return [sum(arr[i] for i in range(l, r)) for l, r in queries]

    def gen(rng, big):
        n, q, V = (100000, 100000, 10**9) if big else (rng.randint(1, 4), rng.randint(1, 4), 12)
        upd = [sorted(rng.sample(range(V + 1), 2)) + [rng.randint(1, 10**9 if big else 5)] for _ in range(n)]
        return upd, [sorted(rng.sample(range(V + 1), 2)) for _ in range(q)]


@problem
class WireLayers:
    title = "Wire Layers"
    difficulty = "Hard"
    func = "minLayers"
    statement = """
<p>A circuit board has two parallel rails. Wire <code>[a, b]</code> connects point <code>a</code> on the top rail to point
<code>b</code> on the bottom rail; all top points are distinct and all bottom points are distinct. Two wires cross if their
order on the top rail differs from their order on the bottom rail. Wires on the same layer may not cross. Return the
fewest layers needed.</p>
<ul><li><code>1 &lt;= wires.length &lt;= 10^5</code></li><li><code>0 &lt;= a, b &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Sort by top point; a layer is an increasing sequence of bottom points, so (Dilworth) the answer is the longest decreasing subsequence",
                module="Gold: Longest Increasing Subsequence", url="https://usaco.guide/gold/lis", similar="Baltic OI PCB (focus problem)")
    examples = [([[1, 3], [2, 1], [3, 2], [4, 0]],), ([[0, 0], [1, 1]],)]
    edges = [([[5, 5]],), ([[0, 2], [1, 1], [2, 0]],)]

    def ref(wires: List[List[int]]) -> int:
        tails = []  # longest strictly decreasing subsequence via negated LIS
        for _, b in sorted(wires):
            x = -b
            i = bisect_left(tails, x)
            if i == len(tails):
                tails.append(x)
            else:
                tails[i] = x
        return len(tails)

    def brute(wires):
        n = len(wires)
        cross = [[(wires[i][0] - wires[j][0]) * (wires[i][1] - wires[j][1]) < 0 for j in range(n)] for i in range(n)]
        for k in range(1, n + 1):
            color = [-1] * n

            def place(v):
                if v == n:
                    return True
                for c in range(k):
                    if all(not cross[v][u] or color[u] != c for u in range(v)):
                        color[v] = c
                        if place(v + 1):
                            return True
                return False

            if place(0):
                return k

    def gen(rng, big):
        n, V = (100000, 10**9) if big else (rng.randint(1, 7), 20)
        return ([[a, b] for a, b in zip(rng.sample(range(V), n), rng.sample(range(V), n))],)


@problem
class HaybaleDistribution:
    title = "Depot Placement"
    difficulty = "Hard"
    tl = 4.0  # ~2 log-n searches per query, each with two bisects
    func = "minCosts"
    statement = """
<p>Farms sit at positions <code>farms</code> on a line. A depot will be built at some integer position <code>y</code>.
Delivering to a farm at <code>x &lt; y</code> costs <code>a * (y - x)</code>, and to a farm at <code>x &gt; y</code> costs
<code>b * (x - y)</code>. For each query <code>[a, b]</code>, return the minimum total delivery cost over all choices of
<code>y</code>.</p>
<ul><li><code>1 &lt;= farms.length &lt;= 10^5</code>, <code>1 &lt;= queries.length &lt;= 5 * 10^4</code></li><li><code>0 &lt;= farms[i] &lt;= 10^6</code>, <code>0 &lt;= a, b &lt;= 10^6</code></li></ul>"""
    hint = dict(pattern="The cost is convex and piecewise linear with corners at farm positions: binary/ternary search the best farm index, evaluating each candidate with prefix sums",
                module="Gold: Optimizing Unimodal Functions", url="https://usaco.guide/gold/ternary-search", similar="USACO Haybale Distribution (focus problem)")
    examples = [([1, 4, 2, 3, 10], [[1, 1], [2, 1], [1, 2], [0, 5], [5, 0]]),]
    edges = [([7], [[3, 4]]), ([0, 0], [[1, 1]])]

    def ref(farms: List[int], queries: List[List[int]]) -> List[int]:
        from bisect import bisect_right
        x = sorted(farms)
        n = len(x)
        pre = [0]
        for v in x:
            pre.append(pre[-1] + v)
        spots = sorted(set(x))  # candidate depot positions; duplicates would make the search see flat steps

        def cost(y, a, b):
            lo, hi = bisect_left(x, y), bisect_right(x, y)  # farms left of y: [0, lo); right of y: [hi, n)
            return a * (lo * y - pre[lo]) + b * ((pre[n] - pre[hi]) - (n - hi) * y)

        out = []
        for a, b in queries:
            lo, hi = 0, len(spots) - 1
            while lo < hi:  # cost is convex in y: find where moving right stops helping
                mid = (lo + hi) // 2
                if cost(spots[mid], a, b) <= cost(spots[mid + 1], a, b):
                    hi = mid
                else:
                    lo = mid + 1
            out.append(cost(spots[lo], a, b))
        return out

    def brute(farms, queries):
        return [min(sum(a * (y - x) if x < y else b * (x - y) for x in farms) for y in range(min(farms), max(farms) + 1))
                for a, b in queries]

    def gen(rng, big):
        n, q, V = (100000, 50000, 10**6) if big else (rng.randint(1, 6), rng.randint(1, 4), 12)
        return [rng.randint(0, V) for _ in range(n)], [[rng.randint(0, V if big else 4), rng.randint(0, V if big else 4)] for _ in range(q)]


@problem
class SubtreeQueries:
    title = "Subtree Totals"
    difficulty = "Hard"
    func = "processQueries"
    tl = 3.0
    statement = """
<p>A tree has <code>n</code> nodes (root <code>0</code>), <code>edges</code>, and node values <code>values</code>. Process
<code>queries</code>: <code>[1, v, x]</code> sets node <code>v</code>'s value to <code>x</code>; <code>[2, v]</code> reports the
sum of values in <code>v</code>'s subtree. Return the reported sums.</p>
<ul><li><code>1 &lt;= n, queries.length &lt;= 10^5</code></li><li><code>1 &lt;= values, x &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Euler tour: number nodes in DFS order so every subtree is a contiguous range, then a Fenwick tree handles point updates and range sums",
                module="Gold: Euler Tour Technique", url="https://usaco.guide/gold/tree-euler", similar="CSES Subtree Queries (focus problem)")
    examples = [(5, [[0, 1], [0, 2], [2, 3], [2, 4]], [4, 2, 5, 2, 1], [[2, 2], [1, 4, 10], [2, 2], [2, 0]]),]
    edges = [(1, [], [7], [[2, 0], [1, 0, 3], [2, 0]]),]

    def ref(n: int, edges: List[List[int]], values: List[int], queries: List[List[int]]) -> List[int]:
        adj = [[] for _ in range(n)]
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        tin, order, seen, stack = [0] * n, [], [False] * n, [0]
        seen[0] = True
        parent = [0] * n
        while stack:
            u = stack.pop()
            tin[u] = len(order)
            order.append(u)
            for v in adj[u]:
                if not seen[v]:
                    seen[v], parent[v] = True, u
                    stack.append(v)
        size = [1] * n
        for u in reversed(order[1:]):
            size[parent[u]] += size[u]
        tree, val = [0] * (n + 1), values[:]

        def add(i, v):
            i += 1
            while i <= n:
                tree[i] += v
                i += i & -i

        def prefix(i):
            s = 0
            while i > 0:
                s += tree[i]
                i -= i & -i
            return s

        for v in range(n):
            add(tin[v], val[v])
        out = []
        for q in queries:
            if q[0] == 1:
                add(tin[q[1]], q[2] - val[q[1]])
                val[q[1]] = q[2]
            else:
                out.append(prefix(tin[q[1]] + size[q[1]]) - prefix(tin[q[1]]))
        return out

    def brute(n, edges, values, queries):
        adj = defaultdict(list)
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        parent, order = {0: None}, [0]
        for u in order:
            for v in adj[u]:
                if v not in parent:
                    parent[v] = u
                    order.append(v)
        val, out = values[:], []
        for q in queries:
            if q[0] == 1:
                val[q[1]] = q[2]
            else:
                total = 0
                for u in range(n):
                    w = u
                    while w is not None and w != q[1]:
                        w = parent[w]
                    total += val[u] if w == q[1] else 0
                out.append(total)
        return out

    def gen(rng, big):
        n, q = (100000, 100000) if big else (rng.randint(1, 7), rng.randint(1, 5))
        label = list(range(n))
        rng.shuffle(label)
        edges = [[label[i - 1 if big and rng.random() < 0.5 else rng.randrange(i)], label[i]] for i in range(1, n)]
        qs = [[1, rng.randrange(n), rng.randint(1, 10**9)] if rng.random() < 0.5 else [2, rng.randrange(n)] for _ in range(q)]
        return n, edges, [rng.randint(1, 10**9 if big else 9) for _ in range(n)], qs


@problem
class ZeroTriples:
    title = "Zero Triples"
    difficulty = "Hard"
    func = "countTriples"
    statement = """
<p>For each query <code>[l, r]</code>, count the index triples <code>l &lt;= i &lt; j &lt; k &lt;= r</code> with
<code>nums[i] + nums[j] + nums[k] == 0</code>.</p>
<ul><li><code>1 &lt;= nums.length &lt;= 800</code></li><li><code>1 &lt;= queries.length &lt;= 10^5</code></li><li><code>|nums[i]| &lt;= 10^6</code></li></ul>"""
    hint = dict(pattern="For every pair (i, k), count middle indices j with nums[j] = -(nums[i] + nums[k]) (a hash map swept per i); then 2-D prefix sums over (i, k) answer each query",
                module="Gold: Hashmaps", url="https://usaco.guide/gold/hashmaps", similar="USACO Farmer John Solves 3SUM (focus problem)")
    examples = [([2, 0, -1, 1, -2, 3, 3], [[0, 6], [1, 4], [1, 3]]),]
    edges = [([0, 0, 0], [[0, 2], [1, 2]]),]

    def ref(nums: List[int], queries: List[List[int]]) -> List[int]:
        n = len(nums)
        ans = [[0] * n for _ in range(n)]  # ans[i][k]: triples with both ends inside [i, k]
        for i in range(n - 1, -1, -1):
            seen = {}
            row_next = ans[i + 1] if i + 1 < n else None
            row = ans[i]
            for k in range(i + 1, n):
                w = seen.get(-(nums[i] + nums[k]), 0)  # middles strictly between i and k
                row[k] = w + (row[k - 1] if k - 1 > i else 0) + (row_next[k] if row_next else 0) - (row_next[k - 1] if row_next and k - 1 > i else 0)
                seen[nums[k]] = seen.get(nums[k], 0) + 1
        return [ans[l][r] for l, r in queries]

    def brute(nums, queries):
        return [sum(nums[i] + nums[j] + nums[k] == 0 for i, j, k in combinations(range(l, r + 1), 3)) for l, r in queries]

    def gen(rng, big):
        n, q, V = (800, 100000, 50) if big else (rng.randint(1, 7), rng.randint(1, 4), 3)
        nums = [rng.randint(-V, V) for _ in range(n)]
        return nums, [sorted((rng.randrange(n), rng.randrange(n))) for _ in range(q)]


@problem
class BestSubsequence:
    title = "Best Bit Subsequence"
    difficulty = "Hard"
    func = "bestValues"
    statement = """
<p>A bit string of length <code>n</code> starts as all zeros. Each flip <code>[l, r]</code> inverts bits <code>l..r</code>.
After all flips, answer each query <code>[l, r, k]</code>: choose <code>k</code> bits from positions <code>l..r</code>
(keeping their order) to form the largest possible binary number, and return it modulo <code>10^9 + 7</code>.</p>
<ul><li><code>1 &lt;= n &lt;= 10^9</code></li><li><code>1 &lt;= flips.length, queries.length &lt;= 2 * 10^4</code></li><li><code>1 &lt;= k &lt;= r - l + 1</code></li></ul>"""
    hint = dict(pattern="With X ones in range: if X >= k the answer is all ones; otherwise take every 1 before, then the shortest suffix holding the needed k - X zeros. Bits form O(flips) runs, so count and evaluate with prefix data over runs",
                module="Gold: Modular Arithmetic", url="https://usaco.guide/gold/modular", similar="USACO The Best Subsequence ★ (Gold Feb 2025)")
    examples = [(10, [[0, 3], [2, 6]], [[0, 9, 4], [1, 5, 3], [4, 9, 6]]),]
    edges = [(1, [], [[0, 0, 1]]), (3, [[0, 2]], [[0, 2, 2]])]

    def ref(n: int, flips: List[List[int]], queries: List[List[int]]) -> List[int]:
        M = 10**9 + 7
        cuts = Counter()
        for l, r in flips:
            cuts[l] ^= 1
            cuts[r + 1] ^= 1
        pts = sorted({0, n} | {p for p in cuts if p < n})
        starts, bits, bit = [], [], 0  # runs [pts[i], pts[i+1]) with a constant bit
        for i in range(len(pts) - 1):
            bit ^= cuts.get(pts[i], 0)
            starts.append(pts[i])
            bits.append(bit)
        R = len(starts)
        ends = starts[1:] + [n]
        ones_before, value_at = [0] * (R + 1), [0] * (R + 1)  # value_at[i]: bits [0, starts[i]) as a number mod M
        for i in range(R):
            length = ends[i] - starts[i]
            ones_before[i + 1] = ones_before[i] + length * bits[i]
            value_at[i + 1] = (value_at[i] * pow(2, length, M) + (pow(2, length, M) - 1) * bits[i]) % M

        def run_of(x):  # index of the run containing position x (0 <= x < n)
            return bisect_left(starts, x + 1) - 1

        def ones(x):  # ones in [0, x)
            if x <= 0:
                return 0
            i = run_of(x - 1)
            return ones_before[i] + (x - starts[i]) * bits[i]

        def value(x):  # bits [0, x) as a number mod M
            if x <= 0:
                return 0
            i = run_of(x - 1)
            k = x - starts[i]
            return (value_at[i] * pow(2, k, M) + (pow(2, k, M) - 1) * bits[i]) % M

        out = []
        for l, r, k in queries:
            hi = r + 1
            X = ones(hi) - ones(l)
            if X >= k:
                out.append((pow(2, k, M) - 1) % M)
                continue
            need = k - X  # zeros to include: take the suffix [s, hi) holding exactly `need` zeros
            lo_s, hi_s = l, hi - 1
            while lo_s < hi_s:  # largest s with zeros in [s, hi) >= need
                mid = (lo_s + hi_s + 1) // 2
                if (hi - mid) - (ones(hi) - ones(mid)) >= need:
                    lo_s = mid
                else:
                    hi_s = mid - 1
            s = lo_s
            lead = ones(s) - ones(l)  # every 1 before the suffix
            suffix = (value(hi) - value(s) * pow(2, hi - s, M)) % M
            out.append(((pow(2, lead, M) - 1) * pow(2, hi - s, M) + suffix) % M)
        return out

    def brute(n, flips, queries):
        b = [0] * n
        for l, r in flips:
            for i in range(l, r + 1):
                b[i] ^= 1
        out = []
        for l, r, k in queries:
            seg, pick, start = b[l:r + 1], [], 0
            for t in range(k):  # greedy: biggest bit that still leaves room for the rest, earliest occurrence
                window = seg[start:len(seg) - (k - t - 1)]
                j = window.index(max(window)) + start
                pick.append(seg[j])
                start = j + 1
            out.append(int("".join(map(str, pick)), 2) % MOD)
        return out

    def gen(rng, big):
        n, f, q = (10**9, 20000, 20000) if big else (rng.randint(1, 12), rng.randint(0, 3), rng.randint(1, 4))
        flips = [sorted((rng.randrange(n), rng.randrange(n))) for _ in range(f)]
        qs = []
        for _ in range(q):
            l, r = sorted((rng.randrange(n), rng.randrange(n)))
            qs.append([l, r, rng.randint(1, r - l + 1)])
        return n, flips, qs


@problem
class CircularBarn:
    title = "Circular Barn Doors"
    difficulty = "Hard"
    func = "minWalking"
    statement = """
<p>A circular barn has <code>n</code> rooms; room <code>i</code> must end up holding <code>cows[i]</code> cows. You unlock
exactly <code>k</code> of the rooms' outer doors. Cows enter through unlocked doors and walk clockwise (from room
<code>i</code> to room <code>i + 1</code>, and from the last room to room 0) to their rooms; walking past one room boundary
costs 1. Return the smallest total walking distance.</p>
<ul><li><code>1 &lt;= k &lt;= n &lt;= 40</code></li><li><code>0 &lt;= cows[i] &lt;= 10^6</code></li></ul>"""
    hint = dict(pattern="Fix where one door is (n choices) to break the circle, then DP over (rooms covered, doors used) with a precomputed cost for each block of rooms served by one door",
                module="Gold: Introduction to DP", url="https://usaco.guide/gold/intro-dp", similar="USACO Circular Barn Revisited ★")
    examples = [([2, 5, 7, 3, 4, 1], 2),]
    edges = [([5], 1), ([1, 1], 2)]

    def ref(cows: List[int], k: int) -> int:
        n, best = len(cows), None
        for s in range(n):
            r = cows[s:] + cows[:s]
            cost = [[0] * (n + 1) for _ in range(n + 1)]  # cost[a][b]: one door at a serving rooms a..b-1
            for a in range(n):
                c = 0
                for b in range(a, n):
                    c += r[b] * (b - a)
                    cost[a][b + 1] = c
            INF = float("inf")
            dp = [[INF] * (k + 1) for _ in range(n + 1)]  # dp[i][j]: rooms 0..i-1 served with j doors
            dp[0][0] = 0
            for i in range(n):
                for j in range(k):
                    if dp[i][j] == INF:
                        continue
                    for b in range(i + 1, n + 1):
                        v = dp[i][j] + cost[i][b]
                        if v < dp[b][j + 1]:
                            dp[b][j + 1] = v
            v = min(dp[n][1:])
            best = v if best is None else min(best, v)
        return best

    def brute(cows, k):
        n, best = len(cows), None
        for doors in combinations(range(n), k):
            total = 0
            for room in range(n):
                dist = min((room - d) % n for d in doors)
                total += cows[room] * dist
            best = total if best is None else min(best, total)
        return best

    def gen(rng, big):
        n = 40 if big else rng.randint(1, 7)
        return [rng.randint(0, 10**6 if big else 5) for _ in range(n)], rng.randint(1, 7 if big else n)


@problem
class PairCancellation:
    title = "Pair Cancellation"
    difficulty = "Hard"
    func = "minInsertions"
    statement = """
<p>A string can be erased by repeatedly deleting two <b>adjacent equal</b> letters. You may first insert extra letters
anywhere. Return the fewest insertions that make <code>s</code> fully erasable.</p>
<ul><li><code>1 &lt;= s.length &lt;= 150</code>, lowercase letters</li></ul>"""
    hint = dict(pattern="An erasable string is a non-crossing matching of equal letters; range DP: s[i] is either matched with an inserted copy, or with some equal s[k], splitting the range",
                module="Gold: Range DP", url="https://usaco.guide/gold/dp-ranges", similar="SAPO Space Jazz (focus problem; adapted)")
    examples = [("abba",), ("abab",), ("aab",)]
    edges = [("a",), ("aa",)]

    def ref(s: str) -> int:
        n = len(s)
        dp = [[0] * (n + 1) for _ in range(n + 1)]  # dp[i][j]: insertions for s[i:j]
        for length in range(1, n + 1):
            for i in range(n - length + 1):
                j = i + length
                best = 1 + dp[i + 1][j]
                for k in range(i + 1, j):
                    if s[k] == s[i]:
                        v = dp[i + 1][k] + dp[k + 1][j]
                        if v < best:
                            best = v
                dp[i][j] = best
        return dp[0][n]

    def brute(s):
        letters = sorted(set(s))
        dist, dq = {s: 0}, deque([s])
        while dq:  # 0-1 BFS: deleting a pair is free, inserting a letter costs 1
            t = dq.popleft()
            if not t:
                return dist[t]
            d = dist[t]
            for i in range(len(t) - 1):
                if t[i] == t[i + 1]:
                    u = t[:i] + t[i + 2:]
                    if dist.get(u, 99) > d:
                        dist[u] = d
                        dq.appendleft(u)
            if len(t) < 8:
                for i in range(len(t) + 1):
                    for ch in letters:
                        u = t[:i] + ch + t[i:]
                        if dist.get(u, 99) > d + 1:
                            dist[u] = d + 1
                            dq.append(u)

    def gen(rng, big):
        if big:
            return ("".join(rng.choice("abc") for _ in range(150)),)
        return ("".join(rng.choice("ab") for _ in range(rng.randint(1, 6))),)


@problem
class CandyCarts:
    title = "Candy Carts"
    difficulty = "Hard"
    func = "assignCarts"
    statement = """
<p>Candy <code>i</code> falls at position <code>candies[i][0]</code> at time <code>candies[i][1]</code>. Carts move along
the line at speed at most 1 and can start anywhere; a cart catches a candy by being at its position at its time. Assign
every candy to a cart using as few carts as possible, and return the cart number (from 0) of each candy. Any optimal
assignment is accepted.</p>
<ul><li><code>1 &lt;= candies.length &lt;= 10^5</code></li><li><code>0 &lt;= position, time &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Rotate coordinates: u = t - p, v = t + p. Candy j can follow i iff u and v both don't decrease, so carts are chains: sort, then greedily extend the chain with the largest end <= v (bisect)",
                module="Gold: Longest Increasing Subsequence", url="https://usaco.guide/gold/lis", similar="Baltic OI Candy ★")
    examples = [([[0, 0], [1, 1], [0, 2], [5, 1]],),]
    edges = [([[3, 3]],), ([[0, 5], [0, 5]],)]

    def ref(candies: List[List[int]]) -> List[int]:
        from bisect import bisect_right
        order = sorted(range(len(candies)), key=lambda i: (candies[i][1] - candies[i][0], candies[i][1] + candies[i][0]))
        tails, cart_of_tail, out = [], [], [0] * len(candies)  # tails sorted ascending (v of each cart's last candy)
        carts = 0
        for i in order:
            v = candies[i][1] + candies[i][0]
            j = bisect_right(tails, v) - 1
            if j >= 0:
                cart = cart_of_tail.pop(j)
                tails.pop(j)
            else:
                cart, carts = carts, carts + 1
            out[i] = cart
            k = bisect_right(tails, v)
            tails.insert(k, v)
            cart_of_tail.insert(k, cart)
        return out

    def brute(candies):
        n = len(candies)
        ok = lambda a, b: abs(candies[b][0] - candies[a][0]) <= candies[b][1] - candies[a][1]
        order = sorted(range(n), key=lambda i: candies[i][1])
        for k in range(1, n + 1):
            last, assign = [None] * k, [0] * n

            def place(t):
                if t == n:
                    return True
                i = order[t]
                for c in range(k):
                    if last[c] is None or ok(last[c], i):
                        prev, last[c], assign[i] = last[c], i, c
                        if place(t + 1):
                            return True
                        last[c] = prev
                return False

            if place(0):
                return assign

    def check(args, out, expected):
        candies = args[0]
        if not isinstance(out, list) or len(out) != len(candies) or not all(type(c) is int and c >= 0 for c in out):
            return False
        if len(set(out)) > len(set(expected)):
            return False
        by_cart = defaultdict(list)
        for i, c in enumerate(out):
            by_cart[c].append(candies[i])
        for cs in by_cart.values():
            cs.sort(key=lambda pt: pt[1])
            if any(abs(b[0] - a[0]) > b[1] - a[1] for a, b in zip(cs, cs[1:])):
                return False
        return True

    def gen(rng, big):
        n, V = (100000, 10**9) if big else (rng.randint(1, 6), 6)
        return ([[rng.randint(0, V), rng.randint(0, V)] for _ in range(n)],)


# ================================================================ stretch S3a: graphs

@problem
class WheresBessie:
    title = "Two-Color Patches"
    difficulty = "Hard"
    func = "countPatches"
    statement = """
<p>An image is a grid of uppercase letters (colors). A rectangle is a <b>patch</b> if it contains exactly two colors,
one of which forms exactly one connected region inside the rectangle (up/down/left/right) while the other forms two or
more. Count the patches that are not contained in any other, larger patch.</p>
<ul><li><code>1 &lt;= rows, cols &lt;= 12</code></li></ul>"""
    hint = dict(pattern="Complete search over all O(n^4) rectangles with a flood fill each, then drop patches that sit inside another patch",
                module="Silver: Flood Fill", url="https://usaco.guide/silver/flood-fill", similar="USACO Where's Bessie? ★")
    examples = [(["ABBBC", "AAAAA", "ABABA", "AAAAA"],), (["AB", "BA"],)]
    edges = [(["A"],), (["AAB", "BAB"],)]

    def ref(grid: List[str]) -> int:
        m, n = len(grid), len(grid[0])

        def is_patch(r1, c1, r2, c2):
            regions = Counter()
            seen = set()
            for i in range(r1, r2 + 1):
                for j in range(c1, c2 + 1):
                    if (i, j) in seen:
                        continue
                    color = grid[i][j]
                    regions[color] += 1
                    if len(regions) > 2:
                        return False
                    seen.add((i, j))
                    stack = [(i, j)]
                    while stack:
                        a, b = stack.pop()
                        for x, y in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                            if r1 <= x <= r2 and c1 <= y <= c2 and (x, y) not in seen and grid[x][y] == color:
                                seen.add((x, y))
                                stack.append((x, y))
            return len(regions) == 2 and sorted(regions.values())[0] == 1 and sorted(regions.values())[1] >= 2

        patches = [(r1, c1, r2, c2) for r1 in range(m) for r2 in range(r1, m) for c1 in range(n) for c2 in range(c1, n)
                   if is_patch(r1, c1, r2, c2)]
        inside = lambda a, b: a != b and b[0] <= a[0] and b[1] <= a[1] and a[2] <= b[2] and a[3] <= b[3]
        return sum(not any(inside(p, q) for q in patches) for p in patches)

    def brute(grid):
        m, n = len(grid), len(grid[0])
        found = []
        for r1, r2 in combinations(range(m + 1), 2):
            for c1, c2 in combinations(range(n + 1), 2):
                cells = [(i, j) for i in range(r1, r2) for j in range(c1, c2)]
                parent = {c: c for c in cells}

                def find(x):
                    while parent[x] != x:
                        x = parent[x]
                    return x

                for i, j in cells:
                    for x, y in ((i + 1, j), (i, j + 1)):
                        if (x, y) in parent and grid[x][y] == grid[i][j]:
                            parent[find((i, j))] = find((x, y))
                per_color = Counter(grid[i][j] for (i, j) in {find(c) for c in cells})
                if len(per_color) == 2 and min(per_color.values()) == 1 and max(per_color.values()) >= 2:
                    found.append((r1, c1, r2, c2))
        return sum(not any(q != p and q[0] <= p[0] and q[1] <= p[1] and p[2] <= q[2] and p[3] <= q[3] for q in found) for p in found)

    def gen(rng, big):
        m, n = (12, 12) if big else (rng.randint(1, 4), rng.randint(1, 4))
        return (["".join(rng.choice("AB" if not big else "ABC") for _ in range(n)) for _ in range(m)],)


@problem
class EvenOutdegree:
    title = "Even Outflows"
    difficulty = "Hard"
    func = "orientRoads"
    statement = """
<p>A road network has <code>n</code> towns and two-way <code>roads</code> <code>[a, b]</code> (no road from a town to
itself, no repeated pairs). Make every road one-way so that every town has an <b>even</b> number of roads leaving it.
Return a list with one entry per road: <code>0</code> to direct it from <code>a</code> to <code>b</code>, <code>1</code> for
<code>b</code> to <code>a</code>. Return an empty list if it is impossible. Any valid answer is accepted.</p>
<ul><li><code>1 &lt;= n &lt;= 10^5</code></li><li><code>1 &lt;= roads.length &lt;= 2 * 10^5</code></li></ul>"""
    hint = dict(pattern="Possible iff each component has an even number of roads. Orient non-tree roads anyway, then fix parities bottom-up along a DFS tree: each node uses its parent road to become even",
                module="Silver: Introduction to Tree Algorithms", url="https://usaco.guide/silver/intro-tree", similar="CSES Even Outdegree Edges ★")
    examples = [(4, [[0, 1], [1, 2], [2, 3], [3, 0]]), (3, [[0, 1], [1, 2], [2, 0]])]
    edges = [(2, [[0, 1]]), (4, [[0, 1], [2, 3]])]

    def ref(n: int, roads: List[List[int]]) -> List[int]:
        adj = [[] for _ in range(n)]
        for i, (a, b) in enumerate(roads):
            adj[a].append((b, i))
            adj[b].append((a, i))
        out = [-1] * len(roads)
        deg = [0] * n  # current out-degree
        seen, up = [False] * n, [-1] * n  # up[v]: index of the tree road to v's parent
        for s in range(n):
            if seen[s]:
                continue
            seen[s], order, stack = True, [], [s]
            while stack:
                u = stack.pop()
                order.append(u)
                for v, i in adj[u]:
                    if not seen[v]:
                        seen[v], up[v] = True, i
                        stack.append(v)
            tree = {up[v] for v in order if up[v] != -1}
            for u in order:  # non-tree roads: any direction
                for v, i in adj[u]:
                    if i not in tree and out[i] == -1:
                        out[i] = 0
                        deg[roads[i][0]] += 1
            for v in reversed(order[1:]):  # fix v using its parent road
                i = up[v]
                a, b = roads[i]
                p = a if b == v else b
                if deg[v] % 2:
                    out[i] = 0 if a == v else 1
                    deg[v] += 1
                else:
                    out[i] = 0 if a == p else 1
                    deg[p] += 1
            if deg[s] % 2:
                return []
        return out

    def brute(n, roads):
        for mask in range(1 << len(roads)):
            deg = [0] * n
            for i, (a, b) in enumerate(roads):
                deg[b if mask >> i & 1 else a] += 1
            if all(d % 2 == 0 for d in deg):
                return [mask >> i & 1 for i in range(len(roads))]
        return []

    def check(args, out, expected):
        n, roads = args
        if not expected:
            return out == []
        if not isinstance(out, list) or len(out) != len(roads) or any(x not in (0, 1) or type(x) is not int for x in out):
            return False
        deg = [0] * n
        for (a, b), x in zip(roads, out):
            deg[b if x else a] += 1
        return all(d % 2 == 0 for d in deg)

    def gen(rng, big):
        n, m = (100000, 200000) if big else (rng.randint(2, 6), rng.randint(1, 8))
        pairs = set()
        while len(pairs) < min(m, n * (n - 1) // 2):
            pairs.add(tuple(sorted(rng.sample(range(n), 2))))
        roads = [list(p) for p in pairs]
        if big and len(roads) % 2:
            roads.pop()
        return n, roads


@problem
class PalindromeWalk:
    title = "Palindrome Walk"
    difficulty = "Hard"
    func = "shortestPalindrome"
    statement = """
<p>A graph has <code>n</code> nodes and two-way edges <code>[a, b, letter]</code> (an edge may connect a node to itself;
there may be several edges between two nodes). Find the shortest walk from node <code>0</code> to node <code>n - 1</code>
whose edge letters read the same forwards and backwards, and return its number of edges, or <code>-1</code> if there is
none. Edges and nodes may be reused.</p>
<ul><li><code>2 &lt;= n &lt;= 300</code></li><li><code>1 &lt;= edges.length &lt;= 600</code></li></ul>"""
    hint = dict(pattern="BFS over pairs (front node, back node) starting at (0, n-1): extend both ends with edges of the same letter; stop when the ends meet (even length) or are joined by one edge (odd length)",
                module="Gold: Shortest Paths with Unweighted Edges", url="https://usaco.guide/gold/unweighted-shortest-paths", similar="AtCoder Construct a Palindrome ★")
    examples = [(8, [[0, 1, "a"], [0, 2, "b"], [1, 7, "a"], [2, 3, "b"], [3, 7, "c"]]), (3, [[0, 1, "a"], [1, 2, "b"]])]
    edges = [(2, [[0, 1, "z"]]), (2, [[0, 0, "a"]])]

    def ref(n: int, edges: List[list]) -> int:
        adj = [defaultdict(list) for _ in range(n)]
        for a, b, ch in edges:
            adj[a][ch].append(b)
            adj[b][ch].append(a)
        linked = {(a, b) for a, b, _ in edges} | {(b, a) for a, b, _ in edges}
        dist = {(0, n - 1): 0}
        q = deque([(0, n - 1)])
        best = float("inf")
        while q:
            u, v = q.popleft()
            d = dist[(u, v)]
            if 2 * d >= best:
                break
            if u == v:
                best = min(best, 2 * d)
                continue
            if (u, v) in linked:
                best = min(best, 2 * d + 1)
            for ch, xs in adj[u].items():
                for y in adj[v].get(ch, ()):
                    for x in xs:
                        if (x, y) not in dist:
                            dist[(x, y)] = d + 1
                            q.append((x, y))
        return -1 if best == float("inf") else best

    def brute(n, edges):
        pairs = [(a, b, ch) for a, b, ch in edges] + [(b, a, ch) for a, b, ch in edges]
        INF = float("inf")
        dist = {(u, v): INF for u in range(n) for v in range(n)}
        dist[(0, n - 1)] = 0
        changed = True
        while changed:  # relax pair-steps until nothing improves
            changed = False
            for (u, v), d in list(dist.items()):
                if d == INF:
                    continue
                for a, x, c1 in pairs:
                    if a != u:
                        continue
                    for b, y, c2 in pairs:
                        if b == v and c1 == c2 and dist[(x, y)] > d + 1:
                            dist[(x, y)] = d + 1
                            changed = True
        best = min([2 * dist[(u, u)] for u in range(n)] + [2 * dist[(a, b)] + 1 for a, b, _ in pairs])
        return -1 if best == INF else best

    def gen(rng, big):
        n, m = (300, 600) if big else (rng.randint(2, 5), rng.randint(1, 6))
        return n, [[rng.randrange(n), rng.randrange(n), rng.choice("ab" if not big else "abc")] for _ in range(m)]


@problem
class SmallMultiple:
    title = "Small Digit Sum Multiple"
    difficulty = "Hard"
    func = "minDigitSum"
    statement = """
<p>Return the smallest possible digit sum of a positive multiple of <code>k</code>.</p>
<ul><li><code>2 &lt;= k &lt;= 10^5</code></li></ul>"""
    hint = dict(pattern="Shortest path over remainders: from r, '+1' goes to r+1 at cost 1 and 'x10' goes to 10r at cost 0; 0-1 BFS from 1 to 0",
                module="Gold: Shortest Paths with Unweighted Edges", url="https://usaco.guide/gold/unweighted-shortest-paths", similar="AtCoder Small Multiple ★")
    examples = [(6,), (41,), (79992,)]
    edges = [(2,), (10,)]

    def ref(k: int) -> int:
        dist = [None] * k
        dq = deque([(1, 1)])
        while dq:
            d, r = dq.popleft()
            if dist[r] is not None:
                continue
            dist[r] = d
            if dist[r * 10 % k] is None:
                dq.appendleft((d, r * 10 % k))
            if dist[(r + 1) % k] is None:
                dq.append((d + 1, (r + 1) % k))
        return dist[0]

    def brute(k):
        dist = {}  # Dijkstra on remainders: appending digit d costs d (an independent formulation)
        heap = [(d, d % k) for d in range(1, 10)]
        while heap:
            c, r = heappop(heap)
            if r in dist:
                continue
            dist[r] = c
            for d in range(10):
                if (r * 10 + d) % k not in dist:
                    heappush(heap, (c + d, (r * 10 + d) % k))
        return dist[0]

    def gen(rng, big):
        return (10**5 - rng.randint(0, 50) if big else rng.randint(2, 120),)


@problem
class FavoriteColors:
    title = "Favorite Colors"
    difficulty = "Hard"
    func = "assignColors"
    statement = """
<p>There are <code>n</code> cows; <code>[a, b]</code> in <code>admires</code> means cow <code>a</code> admires cow
<code>b</code>. Every cow gets a color, and if a cow admires two cows, those two must have the same color. Use as many
different colors as possible. Return each cow's color, numbering colors 1, 2, 3, ... in order of the lowest-numbered cow
that has each color (so cow 0 always has color 1).</p>
<ul><li><code>1 &lt;= n &lt;= 2 * 10^5</code></li><li><code>0 &lt;= admires.length &lt;= 2 * 10^5</code></li></ul>"""
    hint = dict(pattern="Union-find: a cow's admired set must collapse into one group. Merge adjacency lists small-to-large and keep a queue of groups that still admire 2+ different groups",
                module="Gold: Disjoint Set Union", url="https://usaco.guide/gold/dsu", similar="USACO Favorite Colors ★")
    examples = [(9, [[0, 1], [4, 2], [3, 5], [1, 2], [8, 2], [7, 5], [0, 7]]),]
    edges = [(1, []), (3, [[0, 1], [0, 2]])]

    def ref(n: int, admires: List[List[int]]) -> List[int]:
        parent = list(range(n))
        adj = [[] for _ in range(n)]
        for a, b in admires:
            adj[a].append(b)

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        q = deque(i for i in range(n) if len(adj[i]) > 1)
        while q:
            x = find(q.popleft())
            while len(adj[x]) > 1:
                a, b = find(adj[x].pop()), find(adj[x][-1])
                if a == b:
                    continue
                if len(adj[a]) < len(adj[b]):
                    a, b = b, a
                parent[b] = a  # merge b into a, along with everyone b admires
                adj[a].extend(adj[b])
                adj[b] = []
                if len(adj[a]) > 1:
                    q.append(a)
                if find(x) != x:  # x itself was merged; its group was queued above
                    break
        color, out = {}, []
        for i in range(n):
            r = find(i)
            if r not in color:
                color[r] = len(color) + 1
            out.append(color[r])
        return out

    def brute(n, admires):
        label = list(range(n))
        changed = True
        while changed:
            changed = False
            for a in range(n):  # everyone admired by a cow in group of a... applies per group
                targets = {label[b] for x, b in admires if label[x] == label[a]}
                if len(targets) > 1:
                    keep = min(targets)
                    label = [keep if l in targets else l for l in label]
                    changed = True
        color, out = {}, []
        for i in range(n):
            color.setdefault(label[i], len(color) + 1)
            out.append(color[label[i]])
        return out

    def gen(rng, big):
        n, m = (200000, 200000) if big else (rng.randint(1, 7), rng.randint(0, 6))
        return n, [[rng.randrange(n), rng.randrange(n)] for _ in range(m)]


@problem
class QuantumPaths:
    title = "Quantum Paths"
    difficulty = "Hard"
    func = "reachableTotals"
    statement = """
<p>Two networks with no cycles are given: <code>n1</code> nodes with one-way <code>edges1</code>, and <code>n2</code>
nodes with <code>edges2</code>. A particle travels from node 0 to the last node of the first network, then from node 0
to the last node of the second. For each total length <code>q</code> in <code>queries</code>, return <code>1</code> if the
two trips can use exactly <code>q</code> edges in total, otherwise <code>0</code>.</p>
<ul><li><code>2 &lt;= n1, n2 &lt;= 1000</code></li><li><code>edges &lt;= 2000</code> each</li><li><code>1 &lt;= queries.length &lt;= 2000</code>, <code>1 &lt;= q &lt;= 2000</code></li></ul>"""
    hint = dict(pattern="DP in topological order where each node keeps the SET of reachable path lengths as a bitset (Python int, shift by 1 per edge); then combine the two sets",
                module="Gold: Topological Sort", url="https://usaco.guide/gold/toposort", similar="Kattis Quantum Superposition ★")
    examples = [(3, [[0, 1], [1, 2], [0, 2]], 2, [[0, 1]], [1, 2, 3, 4]),]
    edges = [(2, [], 2, [[0, 1]], [1, 2])]

    def ref(n1: int, edges1: List[List[int]], n2: int, edges2: List[List[int]], queries: List[int]) -> List[int]:
        def lengths(n, edges):
            adj, indeg = [[] for _ in range(n)], [0] * n
            for a, b in edges:
                adj[a].append(b)
                indeg[b] += 1
            bits = [0] * n  # bit L set: some path from 0 has length L
            bits[0] = 1
            order = [i for i in range(n) if indeg[i] == 0]
            for u in order:
                for v in adj[u]:
                    bits[v] |= bits[u] << 1
                    indeg[v] -= 1
                    if indeg[v] == 0:
                        order.append(v)
            return bits[n - 1]

        a, b = lengths(n1, edges1), lengths(n2, edges2)
        total, shift = 0, 0
        while a:
            if a & 1:
                total |= b << shift
            a >>= 1
            shift += 1
        return [total >> q & 1 for q in queries]

    def brute(n1, edges1, n2, edges2, queries):
        def lengths(n, edges):
            found = set()

            def dfs(u, d):
                if u == n - 1:
                    found.add(d)
                for a, b in edges:
                    if a == u:
                        dfs(b, d + 1)

            dfs(0, 0)
            return found

        A, B = lengths(n1, edges1), lengths(n2, edges2)
        return [int(any(q - a in B for a in A)) for q in queries]

    def gen(rng, big):
        def dag(n, m):
            order = [0] + rng.sample(range(1, n - 1), n - 2) + [n - 1]
            out = []
            for _ in range(m):
                i, j = sorted(rng.sample(range(n), 2))
                out.append([order[i], order[j]])
            return out

        if big:
            return 1000, dag(1000, 2000), 1000, dag(1000, 2000), [rng.randint(1, 2000) for _ in range(2000)]
        n1, n2 = rng.randint(2, 5), rng.randint(2, 5)
        return n1, dag(n1, rng.randint(0, 6)), n2, dag(n2, rng.randint(0, 6)), [rng.randint(1, 8) for _ in range(rng.randint(1, 4))]


@problem
class RangedTopoSort:
    title = "Ranged Ordering"
    difficulty = "Hard"
    tl = 3.0
    func = "placeAll"
    statement = """
<p>Place <code>n</code> tasks in positions <code>1..n</code> (one task per position). Task <code>i</code> must go in a
position between <code>ranges[i][0]</code> and <code>ranges[i][1]</code>, and each <code>[a, b]</code> in
<code>before</code> means task <code>a</code> must get a smaller position than task <code>b</code>. Return each task's
position, or an empty list if it is impossible. Any valid answer is accepted.</p>
<ul><li><code>1 &lt;= n &lt;= 2 * 10^5</code></li><li><code>0 &lt;= before.length &lt;= 4 * 10^5</code></li></ul>"""
    hint = dict(pattern="Tighten deadlines backwards along the DAG (R[a] <= R[b] - 1) and releases forwards; then fill positions 1..n greedily with the released task of earliest deadline (min-heap)",
                module="Gold: Topological Sort", url="https://usaco.guide/gold/toposort", similar="AtCoder Constrained Topological Sort ★")
    examples = [(3, [[1, 3], [1, 3], [3, 3]], [[0, 1]]), (2, [[1, 1], [1, 2]], [[1, 0]])]
    edges = [(1, [[1, 1]], []), (2, [[1, 2], [1, 2]], [[0, 1], [1, 0]])]

    def ref(n: int, ranges: List[List[int]], before: List[List[int]]) -> List[int]:
        adj, rev, indeg = [[] for _ in range(n)], [[] for _ in range(n)], [0] * n
        for a, b in before:
            adj[a].append(b)
            rev[b].append(a)
            indeg[b] += 1
        order = [i for i in range(n) if indeg[i] == 0]
        for u in order:
            for v in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    order.append(v)
        if len(order) < n:
            return []
        lo, hi = [r[0] for r in ranges], [r[1] for r in ranges]
        for u in order:  # releases forward
            for v in adj[u]:
                lo[v] = max(lo[v], lo[u] + 1)
        for u in reversed(order):  # deadlines backward
            for a in rev[u]:
                hi[a] = min(hi[a], hi[u] - 1)
        by_release = sorted(range(n), key=lambda i: lo[i])
        heap, pos, j = [], [0] * n, 0
        for p in range(1, n + 1):
            while j < n and lo[by_release[j]] <= p:
                heappush(heap, (hi[by_release[j]], by_release[j]))
                j += 1
            if not heap:
                return []
            h, i = heappop(heap)
            if h < p:
                return []
            pos[i] = p
        return pos

    def brute(n, ranges, before):
        from itertools import permutations
        for perm in permutations(range(1, n + 1)):
            if all(l <= p <= r for p, (l, r) in zip(perm, ranges)) and all(perm[a] < perm[b] for a, b in before):
                return list(perm)
        return []

    def check(args, out, expected):
        n, ranges, before = args
        if not expected:
            return out == []
        return (isinstance(out, list) and sorted(out) == list(range(1, n + 1))
                and all(l <= p <= r for p, (l, r) in zip(out, ranges)) and all(out[a] < out[b] for a, b in before))

    def gen(rng, big):
        n = 200000 if big else rng.randint(1, 6)
        perm = rng.sample(range(1, n + 1), n)  # a hidden valid answer, usually
        ranges = [[max(1, p - rng.randint(0, 3)), min(n, p + rng.randint(0, 3))] for p in perm]
        before = []
        for _ in range(rng.randint(0, 2 * n if big else 5)):
            a, b = rng.sample(range(n), 2) if n > 1 else (0, 0)
            if n > 1:
                before.append([a, b] if perm[a] < perm[b] else [b, a])
        if not big and rng.random() < 0.3 and n > 1:
            before.append(rng.sample(range(n), 2))  # may break it
        return n, ranges, before


@problem
class CommuterPass:
    title = "Commuter Pass"
    difficulty = "Hard"
    tl = 3.0  # four Dijkstras in Python
    func = "cheapestTrip"
    statement = """
<p>A city has <code>n</code> stations and two-way rail lines <code>[a, b, fare]</code>. You buy a commuter pass for one
<b>cheapest</b> route between stations <code>s</code> and <code>t</code> (you pick which one); lines on that route become
free. Return the cheapest fare from station <code>u</code> to station <code>v</code> afterwards. All stations are connected.</p>
<ul><li><code>2 &lt;= n &lt;= 5 * 10^4</code></li><li><code>1 &lt;= lines.length &lt;= 10^5</code></li><li><code>1 &lt;= fare &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Dijkstra from s, t, u and v. Lines on some cheapest s-t route form a DAG; along it, carry the best dist-from-u seen so far and pair it with dist-to-v (and the other way round)",
                module="Gold: Shortest Paths with Non-Negative Edge Weights", url="https://usaco.guide/gold/shortest-paths", similar="JOI Commuter Pass ★")
    examples = [(6, [[0, 1, 1], [1, 2, 1], [2, 4, 1], [0, 3, 2], [3, 4, 2], [3, 5, 1], [4, 5, 1]], 0, 5, 1, 3),]
    edges = [(2, [[0, 1, 5]], 0, 1, 0, 1), (3, [[0, 1, 2], [1, 2, 2]], 0, 1, 1, 2)]

    def ref(n: int, lines: List[List[int]], s: int, t: int, u: int, v: int) -> int:
        adj = [[] for _ in range(n)]
        for a, b, w in lines:
            adj[a].append((b, w))
            adj[b].append((a, w))

        def dijkstra(src):
            dist = [float("inf")] * n
            dist[src] = 0
            heap = [(0, src)]
            while heap:
                d, x = heappop(heap)
                if d > dist[x]:
                    continue
                for y, w in adj[x]:
                    if d + w < dist[y]:
                        dist[y] = d + w
                        heappush(heap, (d + w, y))
            return dist

        ds, dt, du, dv = dijkstra(s), dijkstra(t), dijkstra(u), dijkstra(v)
        best = du[v]
        on_route = [x for x in range(n) if ds[x] + dt[x] == ds[t]]
        on_route.sort(key=lambda x: ds[x])
        mu, mv = {}, {}  # best du / dv over route nodes from s up to x
        for x in on_route:
            mu[x], mv[x] = du[x], dv[x]
            for y, w in adj[x]:
                if y in mu and ds[y] + w == ds[x]:  # y comes right before x on some cheapest route
                    mu[x] = min(mu[x], mu[y])
                    mv[x] = min(mv[x], mv[y])
            best = min(best, mu[x] + dv[x], mv[x] + du[x])
        return best

    def brute(n, lines, s, t, u, v):
        adj = defaultdict(list)
        for i, (a, b, w) in enumerate(lines):
            adj[a].append((b, w, i))
            adj[b].append((a, w, i))

        def shortest(src, dst, free):
            dist, heap = {src: 0}, [(0, src)]
            while heap:
                d, x = heappop(heap)
                if d > dist[x]:
                    continue
                for y, w, i in adj[x]:
                    nd = d + (0 if i in free else w)
                    if nd < dist.get(y, float("inf")):
                        dist[y] = nd
                        heappush(heap, (nd, y))
            return dist[dst]

        target, routes = shortest(s, t, set()), []

        def dfs(x, cost, used, seen):
            if cost > target:
                return
            if x == t:
                if cost == target:
                    routes.append(set(used))
                return
            for y, w, i in adj[x]:
                if y not in seen:
                    dfs(y, cost + w, used + [i], seen | {y})

        dfs(s, 0, [], {s})
        return min(shortest(u, v, r) for r in routes)

    def gen(rng, big):
        n, m, W = (50000, 100000, 3) if big else (rng.randint(2, 6), rng.randint(0, 6), 3)
        lines = [[rng.randrange(i), i, rng.randint(1, W)] for i in range(1, n)]  # connected
        pairs = {(min(a, b), max(a, b)) for a, b, _ in lines}
        for _ in range(m):
            a, b = sorted(rng.sample(range(n), 2))
            if (a, b) not in pairs:
                pairs.add((a, b))
                lines.append([a, b, rng.randint(1, W)])
        s, t = rng.sample(range(n), 2)
        u, v = rng.sample(range(n), 2)
        return n, lines, s, t, u, v


# ================================================================ stretch S3b: olympiad graphs, trees, strings

@problem
class RecolorRobot:
    title = "Recolor Robot"
    difficulty = "Hard"
    func = "minRecolorCost"
    tl = 3.0
    statement = """
<p>A graph has <code>n</code> nodes and <code>m</code> two-way edges <code>[a, b, color, cost]</code> with colors in
<code>1..m</code> (no loops, no repeated pairs). A robot starts at node 0. It can move along an edge only if no other edge
touching its current node has the same color. Before any move you may repaint any edge to any color in <code>1..m</code>,
paying that edge's <code>cost</code> each time. Return the cheapest total cost to get the robot to node <code>n - 1</code>,
or <code>-1</code> if it is impossible.</p>
<ul><li><code>2 &lt;= n &lt;= 3 * 10^4</code></li><li><code>1 &lt;= m &lt;= 6 * 10^4</code></li><li><code>1 &lt;= cost &lt;= 10^9</code></li></ul>"""
    hint = dict(pattern="Leaving u along a c-colored edge costs min(its own cost, total cost of the other c-colored edges at u). Add states (node, color just used) so the repaint of the edge you arrived on is not paid twice",
                module="Gold: Shortest Paths with Non-Negative Edge Weights", url="https://usaco.guide/gold/shortest-paths", similar="JOI Robot ★")
    examples = [(4, [[0, 1, 1, 1], [0, 2, 1, 4], [1, 3, 2, 2], [2, 3, 1, 3], [1, 2, 3, 1]]),]
    edges = [(2, [[0, 1, 1, 7]]), (3, [[1, 2, 1, 1]])]

    def ref(n: int, edges: List[List[int]]) -> int:
        by_color = [defaultdict(list) for _ in range(n)]
        total = [defaultdict(int) for _ in range(n)]
        for a, b, c, p in edges:
            by_color[a][c].append((b, p))
            by_color[b][c].append((a, p))
            total[a][c] += p
            total[b][c] += p
        INF = float("inf")
        dist, dist2 = [INF] * n, {}
        dist[0] = 0
        heap = [(0, 0, 0)]  # (cost, node, color just used; 0 = plain state)
        while heap:
            d, u, c = heappop(heap)
            if c:
                if d > dist2.get((u, c), INF):
                    continue
                for v, p in by_color[u][c]:  # repaint the other c-edges here, which includes the one we came on
                    nd = d + total[u][c] - p
                    if nd < dist[v]:
                        dist[v] = nd
                        heappush(heap, (nd, v, 0))
                continue
            if d > dist[u]:
                continue
            for color, lst in by_color[u].items():
                for v, p in lst:
                    nd = d + min(p, total[u][color] - p)
                    if nd < dist[v]:
                        dist[v] = nd
                        heappush(heap, (nd, v, 0))
                    if d < dist2.get((v, color), INF):
                        dist2[(v, color)] = d
                        heappush(heap, (d, v, color))
        return -1 if dist[n - 1] == INF else dist[n - 1]

    def brute(n, edges):
        m = len(edges)
        start = (0, tuple(c for _, _, c, _ in edges))
        best, heap = {start: 0}, [(0, start)]
        while heap:
            d, (u, cols) = heappop(heap)
            if d > best[(u, cols)]:
                continue
            if u == n - 1:
                return d
            for i, (a, b, _, p) in enumerate(edges):
                if u in (a, b):  # move along edge i if its color is unique at u
                    if sum(1 for j, (x, y, _, _) in enumerate(edges) if u in (x, y) and cols[j] == cols[i]) == 1:
                        st = (b if u == a else a, cols)
                        if d < best.get(st, float("inf")):
                            best[st] = d
                            heappush(heap, (d, st))
                for col in range(1, m + 1):  # repaint edge i
                    if col != cols[i]:
                        st = (u, cols[:i] + (col,) + cols[i + 1:])
                        if d + p < best.get(st, float("inf")):
                            best[st] = d + p
                            heappush(heap, (d + p, st))
        return -1

    def gen(rng, big):
        n, m = (30000, 60000) if big else (rng.randint(2, 4), rng.randint(1, 3))
        pairs = set()
        while len(pairs) < min(m, n * (n - 1) // 2):
            pairs.add(tuple(sorted(rng.sample(range(n), 2))))
        m = len(pairs)
        return n, [[a, b, rng.randint(1, max(1, m // 3 if big else m)), rng.randint(1, 10**9 if big else 5)] for a, b in pairs]


@problem
class DetourCosts:
    title = "Detour Costs"
    difficulty = "Hard"
    func = "detours"
    statement = """
<p>A city has <code>n</code> junctions and two-way roads <code>[a, b, length]</code> (no repeated pairs). The list
<code>route</code> is a shortest route from <code>route[0]</code> to <code>route[-1]</code>. For each road on that route
(in order), return the shortest distance between the two ends if only that road is closed, or <code>-1</code> if they
become disconnected.</p>
<ul><li><code>2 &lt;= n &lt;= 2000</code></li><li><code>1 &lt;= roads.length &lt;= 10^4</code></li><li><code>1 &lt;= length &lt;= 10^6</code></li></ul>"""
    hint = dict(pattern="Shortest-path trees from both ends that contain the route: every junction hangs off the route at some index. A non-route road (x, y) gives dA[x] + w + dB[y] for all route roads between x's and y's hanging indices",
                module="Gold: Shortest Paths with Non-Negative Edge Weights", url="https://usaco.guide/gold/shortest-paths", similar="Balkan OI Shortest Paths ★")
    examples = [(5, [[0, 1, 1], [1, 2, 1], [2, 4, 1], [0, 3, 2], [3, 4, 2], [1, 3, 1]], [0, 1, 2, 4]),]
    edges = [(2, [[0, 1, 5]], [0, 1]),]

    def ref(n: int, roads: List[List[int]], route: List[int]) -> List[int]:
        adj = [[] for _ in range(n)]
        for a, b, w in roads:
            adj[a].append((b, w))
            adj[b].append((a, w))
        INF = float("inf")

        def dijkstra(src):
            dist = [INF] * n
            dist[src] = 0
            heap = [(0, src)]
            while heap:
                d, x = heappop(heap)
                if d > dist[x]:
                    continue
                for y, w in adj[x]:
                    if d + w < dist[y]:
                        dist[y] = d + w
                        heappush(heap, (d + w, y))
            return dist

        k = len(route) - 1
        index = {v: i for i, v in enumerate(route)}

        def hang(dist):  # route index where each junction's tree path leaves the route
            at = [-1] * n
            for v in sorted(range(n), key=lambda v: dist[v]):
                if dist[v] == INF:
                    continue
                if v in index:
                    at[v] = index[v]
                    continue
                for u, w in adj[v]:
                    if dist[u] + w == dist[v] and at[u] != -1:
                        at[v] = at[u]
                        break
            return at

        dA, dB = dijkstra(route[0]), dijkstra(route[-1])
        left, right = hang(dA), hang(dB)
        on_route = {(route[i], route[i + 1]) for i in range(k)} | {(route[i + 1], route[i]) for i in range(k)}
        ans = [INF] * k
        for a, b, w in roads:
            if (a, b) in on_route:
                continue
            for x, y in ((a, b), (b, a)):
                if dA[x] < INF and dB[y] < INF and left[x] < right[y]:
                    c = dA[x] + w + dB[y]
                    for i in range(left[x], right[y]):
                        if c < ans[i]:
                            ans[i] = c
        return [-1 if a == INF else a for a in ans]

    def brute(n, roads, route):
        out = []
        for i in range(len(route) - 1):
            cut = {route[i], route[i + 1]}
            adj = defaultdict(list)
            for a, b, w in roads:
                if {a, b} != cut:
                    adj[a].append((b, w))
                    adj[b].append((a, w))
            dist, heap = {route[0]: 0}, [(0, route[0])]
            while heap:
                d, x = heappop(heap)
                if d > dist[x]:
                    continue
                for y, w in adj[x]:
                    if d + w < dist.get(y, float("inf")):
                        dist[y] = d + w
                        heappush(heap, (d + w, y))
            out.append(dist.get(route[-1], -1))
        return out

    def gen(rng, big):
        n, m, W = (2000, 10000, 10**6) if big else (rng.randint(2, 6), rng.randint(0, 5), 4)
        pairs = {}
        for i in range(1, n):
            pairs[(rng.randrange(i), i)] = rng.randint(1, W)
        for _ in range(m):
            a, b = sorted(rng.sample(range(n), 2))
            pairs.setdefault((a, b), rng.randint(1, W))
        roads = [[a, b, w] for (a, b), w in pairs.items()]
        A, B = rng.sample(range(n), 2)
        adj = defaultdict(list)
        for a, b, w in roads:
            adj[a].append((b, w))
            adj[b].append((a, w))
        dist, par, heap = {A: 0}, {A: None}, [(0, A)]
        while heap:
            d, x = heappop(heap)
            if d > dist[x]:
                continue
            for y, w in adj[x]:
                if d + w < dist.get(y, float("inf")):
                    dist[y], par[y] = d + w, x
                    heappush(heap, (d + w, y))
        route = [B]
        while par[route[-1]] is not None:
            route.append(par[route[-1]])
        return n, roads, route[::-1]


@problem
class PatrolRoads:
    title = "Patrol Shortcuts"
    difficulty = "Hard"
    func = "shortestPatrol"
    statement = """
<p><code>n</code> villages are joined by <code>n - 1</code> roads <code>edges</code> forming a tree, each of length 1. You
will build exactly <code>k</code> new roads of length 1 (each between any two villages, or even a loop at one village).
A patrol starts and ends at village 0, must use every old road at least once and every new road exactly once. Return the
shortest possible patrol length.</p>
<ul><li><code>3 &lt;= n &lt;= 10^5</code></li><li><code>k</code> is 1 or 2</li></ul>"""
    hint = dict(pattern="Without new roads the patrol is 2(n-1). One new road saves (longest path - 1): use the diameter. For the second, weight the first diameter's edges -1 (using them again costs) and take the best path again",
                module="Silver: Introduction to Tree Algorithms", url="https://usaco.guide/silver/intro-tree", similar="APIO Patrol ★")
    examples = [(8, [[0, 1], [1, 2], [2, 3], [2, 4], [1, 5], [5, 6], [5, 7]], 1), (8, [[0, 1], [1, 2], [2, 3], [2, 4], [1, 5], [5, 6], [5, 7]], 2)]
    edges = [(3, [[0, 1], [1, 2]], 2),]

    def ref(n: int, edges: List[List[int]], k: int) -> int:
        adj = [[] for _ in range(n)]
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)

        def bfs(s):
            dist, par = [-1] * n, [-1] * n
            dist[s], q = 0, [s]
            for u in q:
                for v in adj[u]:
                    if dist[v] == -1:
                        dist[v], par[v] = dist[u] + 1, u
                        q.append(v)
            far = max(range(n), key=dist.__getitem__)
            return far, dist[far], par

        a, _, _ = bfs(0)
        b, d1, par = bfs(a)
        answer = 2 * (n - 1) - d1 + 1
        if k == 1:
            return answer
        on_path = set()
        x = b
        while x != a:
            on_path.add((x, par[x]))
            on_path.add((par[x], x))
            x = par[x]
        parent, order = [-1] * n, [0]
        parent[0] = 0
        for u in order:
            for v in adj[u]:
                if parent[v] == -1:
                    parent[v] = u
                    order.append(v)
        down, d2 = [0] * n, 0  # down[v]: best path weight going down from v (>= 0: may stop at v)
        for u in reversed(order):
            top1 = top2 = 0
            for v in adj[u]:
                if v == parent[u] and u != 0 or v == u:
                    continue
                if parent[v] != u:
                    continue
                w = -1 if (u, v) in on_path else 1
                val = down[v] + w
                if val > top1:
                    top1, top2 = val, top1
                elif val > top2:
                    top2 = val
            down[u] = top1
            d2 = max(d2, top1 + top2)
        return answer - d2 + 1

    def brute(n, edges, k):
        adj = defaultdict(list)
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        parent, order = {0: None}, [0]
        for u in order:
            for v in adj[u]:
                if v not in parent:
                    parent[v] = u
                    order.append(v)
        best = None
        roads = [(u, v) for u in range(n) for v in range(u, n)]
        for chosen in (combinations(roads, 1) if k == 1 else [(r1, r2) for i, r1 in enumerate(roads) for r2 in roads[i:]]):
            odd = [0] * n
            for u, v in chosen:
                odd[u] ^= 1
                odd[v] ^= 1
            for a, b in edges:
                odd[a] ^= 1
                odd[b] ^= 1
            sub = odd[:]  # odd vertices below each node: a tree edge is doubled iff that count is odd
            extra = 0
            for u in reversed(order[1:]):
                if sub[u] % 2:
                    extra += 1
                sub[parent[u]] += sub[u]
            cost = (n - 1) + k + extra
            best = cost if best is None else min(best, cost)
        return best

    def gen(rng, big):
        n = 100000 if big else rng.randint(3, 7)
        return n, [[rng.randrange(i), i] for i in range(1, n)], rng.randint(1, 2)


@problem
class LevelBlockers:
    title = "Level Blockers"
    difficulty = "Hard"
    func = "canBlock"
    statement = """
<p>A tree rooted at node 0 has <code>n</code> nodes and <code>edges</code>. You may place at most one blocker on a node at
each depth <code>1, 2, ..., k</code> (the root has depth 0). Return <code>true</code> if you can place blockers so that
every node at depth exactly <code>k</code> has a blocker on itself or on one of its ancestors.</p>
<ul><li><code>2 &lt;= n &lt;= 100</code></li><li><code>1 &lt;= k &lt;= n</code></li></ul>"""
    hint = dict(pattern="If k*k >= n the answer is always yes. Otherwise order depth-k nodes by DFS; each node covers a contiguous range of them, so bitmask DP over the depths used, tracking how long a prefix is covered",
                module="Gold: Bitmask DP", url="https://usaco.guide/gold/dp-bitmasks", similar="COCI Burza ★ (adapted: the game reduces to this covering question)")
    examples = [(6, [[0, 1], [0, 2], [1, 3], [1, 4], [2, 5]], 2), (4, [[0, 1], [0, 2], [0, 3]], 1)]
    edges = [(2, [[0, 1]], 1), (3, [[0, 1], [1, 2]], 3)]

    def ref(n: int, edges: List[List[int]], k: int) -> bool:
        if k * k >= n:
            return True
        adj = [[] for _ in range(n)]
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        depth, lo, hi, leaves = [-1] * n, [0] * n, [-1] * n, 0
        depth[0] = 0
        stack = [(0, iter(adj[0]))]
        lo[0] = 0
        while stack:  # DFS assigning each node the range of depth-k nodes below it
            u, it = stack[-1]
            for v in it:
                if depth[v] == -1 and depth[u] < k:
                    depth[v] = depth[u] + 1
                    lo[v] = leaves
                    if depth[v] == k:
                        leaves += 1
                    stack.append((v, iter(adj[v])))
                    break
            else:
                hi[u] = leaves - 1
                stack.pop()
        if leaves == 0:
            return True
        covering = defaultdict(list)  # leaf index p -> nodes (depth, hi) whose range starts at p
        for v in range(1, n):
            if 1 <= depth[v] <= k and lo[v] <= hi[v]:
                covering[lo[v]].append((depth[v] - 1, hi[v]))
        reach = [-1] * (1 << k)  # reach[mask]: longest covered prefix of leaves using those depths
        reach[0] = 0
        for mask in range(1 << k):
            p = reach[mask]
            if p < 0:
                continue
            if p == leaves:
                return True
            for d, h in covering[p]:
                if not mask >> d & 1 and h + 1 > reach[mask | 1 << d]:
                    reach[mask | 1 << d] = h + 1
        return False

    def brute(n, edges, k):
        adj = defaultdict(list)
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        parent, depth, order = {0: None}, {0: 0}, [0]
        for u in order:
            for v in adj[u]:
                if v not in parent:
                    parent[v], depth[v] = u, depth[u] + 1
                    order.append(v)
        targets = [v for v in range(n) if depth[v] == k]
        levels = [[None] + [v for v in range(n) if depth[v] == d] for d in range(1, k + 1)]
        from itertools import product
        for pick in product(*levels):
            chosen = {v for v in pick if v is not None}
            ok = True
            for t in targets:
                x = t
                while x is not None and x not in chosen:
                    x = parent[x]
                if x is None:
                    ok = False
                    break
            if ok:
                return True
        return False

    def gen(rng, big):
        n = 100 if big else rng.randint(2, 9)
        return n, [[rng.randrange(i), i] for i in range(1, n)], rng.randint(1, 9 if big else 4)


@problem
class TrainingRoutes:
    title = "Training Routes"
    difficulty = "Hard"
    func = "minBlockCost"
    tl = 3.0
    statement = """
<p><code>n</code> towns are joined by paved roads forming a tree; the first <code>n - 1</code> entries of
<code>roads</code> are paved (<code>[a, b, 0]</code>) and the rest are unpaved (<code>[a, b, cost]</code>). No town has more
than 10 paved roads. You must block some unpaved roads, paying their costs, so that the remaining network has <b>no
cycle of even length</b> (a cycle visits no town and uses no road twice). Return the minimum total cost.</p>
<ul><li><code>2 &lt;= n &lt;= 200</code></li><li><code>roads.length &lt;= 1000</code>; unpaved roads never repeat a paved pair</li></ul>"""
    hint = dict(pattern="An unpaved road whose tree path has odd length closes an even cycle: always block it. Kept roads must have edge-disjoint tree paths; maximize kept cost with a tree DP over subsets of children (degree <= 10)",
                module="Gold: Bitmask DP", url="https://usaco.guide/gold/dp-bitmasks", similar="IOI 2007 Training ★")
    examples = [(5, [[0, 1, 0], [1, 2, 0], [2, 3, 0], [3, 4, 0], [0, 2, 3], [1, 3, 4], [2, 4, 5], [0, 4, 6]]),]
    edges = [(2, [[0, 1, 0]]), (3, [[0, 1, 0], [1, 2, 0], [0, 2, 7]])]

    def ref(n: int, roads: List[List[int]]) -> int:
        tree = roads[:n - 1]
        adj = [[] for _ in range(n)]
        for a, b, _ in tree:
            adj[a].append(b)
            adj[b].append(a)
        parent, depth, order = [-1] * n, [0] * n, [0]
        parent[0] = 0
        for u in order:
            for v in adj[u]:
                if parent[v] == -1:
                    parent[v], depth[v] = u, depth[u] + 1
                    order.append(v)
        kids = [[v for v in adj[u] if parent[v] == u and v != 0] for u in range(n)]
        slot = [0] * n  # slot[v]: index of v among its parent's children
        for u in range(n):
            for i, v in enumerate(kids[u]):
                slot[v] = i

        def lca(a, b):
            while depth[a] > depth[b]:
                a = parent[a]
            while depth[b] > depth[a]:
                b = parent[b]
            while a != b:
                a, b = parent[a], parent[b]
            return a

        total, at = 0, defaultdict(list)  # candidate kept roads grouped by their LCA
        for a, b, c in roads[n - 1:]:
            total += c
            w = lca(a, b)
            if (depth[a] + depth[b] - 2 * depth[w]) % 2 == 0:
                at[w].append((a, b, c))
        dp = [None] * n  # dp[v][mask]: best kept cost in v's subtree with children in mask already used

        def climb(x, top):  # value of a path from x up to (not including) top, and the child of top it enters through
            val, prev = dp[x][0], x
            x2 = parent[x]
            while x2 != top:
                val += dp[x2][1 << slot[prev]]
                prev, x2 = x2, parent[x2]
            return val, prev

        for v in reversed(order):
            d = len(kids[v])
            full = (1 << d) - 1
            options = []
            for a, b, c in at[v]:
                val, used = c, 0
                for x in (a, b):
                    if x != v:
                        part, child = climb(x, v)
                        val += part
                        used |= 1 << slot[child]
                options.append((used, val))
            best = [0] * (1 << d)
            for mask in range(full, -1, -1):
                b = sum(dp[kids[v][i]][0] for i in range(d) if not mask >> i & 1)
                for used, val in options:
                    if not used & mask:
                        b = max(b, val + best[mask | used])
                best[mask] = b
            dp[v] = best
        return total - dp[0][0]

    def brute(n, roads):
        tree, extra = roads[:n - 1], roads[n - 1:]

        def has_even_cycle(edge_list):
            adj = defaultdict(list)
            for i, (a, b, _) in enumerate(edge_list):
                adj[a].append((b, i))
                adj[b].append((a, i))
            found = False

            def dfs(start, u, used_nodes, length):
                nonlocal found
                for v, i in adj[u]:
                    if found:
                        return
                    if v == start and length + 1 >= 3 and (length + 1) % 2 == 0:
                        found = True
                        return
                    if v not in used_nodes and v > start:
                        dfs(start, v, used_nodes | {v}, length + 1)

            for s in range(n):
                dfs(s, s, {s}, 0)
                if found:
                    return True
            return False

        best = None
        for mask in range(1 << len(extra)):
            kept = [extra[i] for i in range(len(extra)) if mask >> i & 1]
            if not has_even_cycle(tree + kept):
                cost = sum(c for i, (_, _, c) in enumerate(extra) if not mask >> i & 1)
                best = cost if best is None else min(best, cost)
        return best

    def gen(rng, big):
        n = 200 if big else rng.randint(2, 7)
        tree, deg = [], [0] * n
        for i in range(1, n):
            p = rng.choice([u for u in range(i) if deg[u] < 10])
            deg[p] += 1
            deg[i] += 1
            tree.append([p, i, 0])
        pairs = {(min(a, b), max(a, b)) for a, b, _ in tree}
        extra = []
        for _ in range(800 if big else rng.randint(0, 5)):
            a, b = sorted(rng.sample(range(n), 2))
            if (a, b) not in pairs:
                pairs.add((a, b))
                extra.append([a, b, rng.randint(1, 10000 if big else 9)])
        return n, tree + extra


@problem
class SmallestRotation:
    title = "Smallest Rotation"
    difficulty = "Hard"
    func = "smallestShift"
    statement = """
<p>A satellite photo is a grid of <code>'*'</code> and <code>'.'</code>. It can be shifted cyclically: move some number of
rows from the top to the bottom and some number of columns from the left to the right. Return the shifted photo that is
smallest when read row by row, left to right, with <code>'*'</code> smaller than <code>'.'</code>.</p>
<ul><li><code>1 &lt;= rows, cols &lt;= 150</code></li></ul>"""
    hint = dict(pattern="Compare two candidate shifts fast with 2-D polynomial hashing of the doubled grid: binary search for the first differing row, then the first differing column",
                module="Gold: Hashing", url="https://usaco.guide/gold/hashing", similar="COCI Sateliti ★")
    examples = [([".**", "*..", ".*."],), (["..", ".*"],)]
    edges = [(["*"],), ([".*.*"],)]

    def ref(grid: List[str]) -> List[str]:
        m, n = len(grid), len(grid[0])
        M, BR, BC = (1 << 61) - 1, 911382323, 972663749
        G = [[1 if ch == "*" else 2 for ch in row * 2] for row in grid * 2]
        H = [[0] * (2 * n + 1) for _ in range(2 * m + 1)]  # 2-D prefix hash of the doubled grid
        for i in range(2 * m):
            row, Hi, Hn = G[i], H[i], H[i + 1]
            run = 0
            for j in range(2 * n):
                run = (run * BC + row[j]) % M
                Hn[j + 1] = (Hi[j + 1] * BR + run) % M
        pr, pc = [1] * (2 * m + 1), [1] * (2 * n + 1)
        for i in range(2 * m):
            pr[i + 1] = pr[i] * BR % M
        for j in range(2 * n):
            pc[j + 1] = pc[j] * BC % M

        def block(r, c, h, w):  # hash of rows r..r+h-1, columns c..c+w-1
            return (H[r + h][c + w] - H[r][c + w] * pr[h] - H[r + h][c] * pc[w] + H[r][c] * pr[h] % M * pc[w]) % M

        def less(a, b):  # is shift a lexicographically smaller than shift b?
            (r1, c1), (r2, c2) = a, b
            lo, hi = 0, m  # number of equal leading rows
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if block(r1, c1, mid, n) == block(r2, c2, mid, n):
                    lo = mid
                else:
                    hi = mid - 1
            if lo == m:
                return False
            row = lo
            lo, hi = 0, n
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if block(r1 + row, c1, 1, mid) == block(r2 + row, c2, 1, mid):
                    lo = mid
                else:
                    hi = mid - 1
            return G[r1 + row][c1 + lo] < G[r2 + row][c2 + lo]

        best = (0, 0)
        for r in range(m):
            for c in range(n):
                if less((r, c), best):
                    best = (r, c)
        r, c = best
        return ["".join(grid[(r + i) % m][(c + j) % n] for j in range(n)) for i in range(m)]

    def brute(grid):
        m, n = len(grid), len(grid[0])
        key = lambda rows: "".join(rows).replace("*", "0").replace(".", "1")
        cands = [[grid[(r + i) % m][c:] + grid[(r + i) % m][:c] for i in range(m)] for r in range(m) for c in range(n)]
        return min(cands, key=key)

    def gen(rng, big):
        m, n = (150, 150) if big else (rng.randint(1, 4), rng.randint(1, 4))
        return (["".join(rng.choice("*.") for _ in range(n)) for _ in range(m)],)


@problem
class OddOneOut:
    title = "Odd Genome Out"
    difficulty = "Hard"
    func = "findUnique"
    statement = """
<p>All strings in <code>genomes</code> have the same length and use letters A, C, G, T. Exactly one of them differs from
<b>every</b> other genome in exactly <code>k</code> positions. Return its index.</p>
<ul><li><code>3 &lt;= genomes.length &lt;= 1000</code>, <code>1 &lt;= length &lt;= 1000</code></li><li><code>1 &lt;= k &lt;= length</code></li></ul>"""
    hint = dict(pattern="Give each genome a random weight. For each column and letter, sum the weights of genomes with that letter; then genome i's weighted total of differences is one pass, and it equals k * (sum of the others' weights) only for the answer (with high probability)",
                module="Gold: Hashing", url="https://usaco.guide/gold/hashing", similar="Baltic OI Genetics ★")
    examples = [(["ACC", "CCA", "ACA", "AAA"], 1),]
    edges = [(["A", "C", "G"], 1),]

    def ref(genomes: List[str], k: int) -> int:
        import random as rnd
        r = rnd.Random(12345)
        n, m = len(genomes), len(genomes[0])
        w = [r.getrandbits(48) for _ in range(n)]
        W = sum(w)
        col = [Counter() for _ in range(m)]
        for g, wi in zip(genomes, w):
            for p, ch in enumerate(g):
                col[p][ch] += wi
        for i, g in enumerate(genomes):
            diff = sum(W - col[p][ch] for p, ch in enumerate(g))  # weight of genomes differing, column by column
            if diff == k * (W - w[i]):
                return i

    def brute(genomes, k):
        return next(i for i, g in enumerate(genomes)
                    if all(sum(a != b for a, b in zip(g, h)) == k for j, h in enumerate(genomes) if j != i))

    def gen(rng, big):
        n, m = (1000, 1000) if big else (rng.randint(3, 5), rng.randint(2, 6))
        while True:  # plant the special genome, then make every other one differ from it in exactly k positions
            k = m // 4 if big else rng.randint(1, m)
            special = [rng.choice("ACGT") for _ in range(m)]
            genomes = []
            for _ in range(n - 1):
                g = special[:]
                for p in rng.sample(range(m), k):
                    g[p] = rng.choice([c for c in "ACGT" if c != special[p]])
                genomes.append("".join(g))
            genomes.insert(rng.randrange(n), "".join(special))
            if big:  # others differ from each other in ~1.5k positions, so the planted one is unique (w.h.p.)
                return genomes, k
            hits = [i for i, g in enumerate(genomes)
                    if all(sum(a != b for a, b in zip(g, h)) == k for j, h in enumerate(genomes) if j != i)]
            if len(hits) == 1:
                return genomes, k


@problem
class PilingPapers:
    title = "Piling Digits"
    difficulty = "Hard"
    func = "countPiles"
    statement = """
<p>Digits <code>digits</code> (each 1 to 9) arrive in order. For a query <code>[l, r]</code>, take <code>digits[l..r]</code>
in order; each digit is either put on top of a pile, put at the bottom, or thrown away (3 choices each, so 3^(r-l+1) ways
in total; putting the first digit on top or at the bottom counts as two ways). Read the pile top to bottom as a number.
Count the ways that produce a number from <code>a</code> to <code>b</code> (an empty pile does not count), modulo
<code>10^9 + 7</code>.</p>
<ul><li><code>1 &lt;= digits.length &lt;= 30</code></li><li><code>1 &lt;= a &lt;= b &lt;= 10^12</code></li><li><code>1 &lt;= queries.length &lt;= 500</code></li></ul>"""
    hint = dict(pattern="Count piles <= X (then subtract). DP for each start l over (i, j, cmp): the pile matches positions i..j of X's digits and compares less/equal/greater; top adds at i - 1, bottom at j + 1",
                module="Gold: Digit DP", url="https://usaco.guide/gold/digit-dp", similar="USACO Piling Papers ★ (Gold)")
    examples = [([1, 2, 3, 4, 5], 13, 327, [[0, 1], [0, 4], [1, 4]]),]
    edges = [([7], 7, 7, [[0, 0]]), ([1, 1], 1, 100, [[0, 1]])]

    def ref(digits: List[int], a: int, b: int, queries: List[List[int]]) -> List[int]:
        M, n = 10**9 + 7, len(digits)

        def table(X):  # cnt[l][r]: ways for digits[l..r] giving a non-empty number <= X
            cnt = [[0] * n for _ in range(n)]
            if X <= 0:
                return cnt
            s = [int(ch) for ch in str(X)]
            D = len(s)
            cmp = lambda d, t: 0 if d < t else 1 if d == t else 2
            for l in range(n):
                dp = {}  # (i, j, c) -> ways
                for r in range(l, n):
                    d = digits[r]
                    nxt = dict(dp)  # throw the digit away
                    for (i, j, c), w in dp.items():
                        if i > 0:  # on top: the new digit decides unless equal
                            c2 = cmp(d, s[i - 1])
                            key = (i - 1, j, c if c2 == 1 else c2)
                            nxt[key] = (nxt.get(key, 0) + w) % M
                        if j + 1 < D:  # at the bottom: earlier digits decide unless equal so far
                            key = (i, j + 1, cmp(d, s[j + 1]) if c == 1 else c)
                            nxt[key] = (nxt.get(key, 0) + w) % M
                    for p in range(D):  # start a new pile here: top or bottom, two ways
                        key = (p, p, cmp(d, s[p]))
                        nxt[key] = (nxt.get(key, 0) + 2) % M
                    dp = nxt
                    total = 0
                    for (i, j, c), w in dp.items():
                        if j == D - 1 and (i > 0 or c < 2):  # shorter piles are always smaller; full length must be <= X
                            total += w
                    cnt[l][r] = total % M
            return cnt

        hi, lo = table(b), table(a - 1)
        return [(hi[l][r] - lo[l][r]) % M for l, r in queries]

    def brute(digits, a, b, queries):
        from itertools import product
        out = []
        for l, r in queries:
            ways = 0
            for choice in product(range(3), repeat=r - l + 1):
                pile = deque()
                for d, ch in zip(digits[l:r + 1], choice):
                    if ch == 0:
                        pile.appendleft(d)
                    elif ch == 1:
                        pile.append(d)
                if pile and a <= int("".join(map(str, pile))) <= b:
                    ways += 1
            out.append(ways % MOD)
        return out

    def gen(rng, big):
        n = 30 if big else rng.randint(1, 6)
        digits = [rng.randint(1, 9) for _ in range(n)]
        hi = 10**12 if big else 10**rng.randint(1, 5)
        a = rng.randint(1, hi)
        b = rng.randint(a, hi)
        qs = []
        for _ in range(500 if big else rng.randint(1, 3)):
            l, r = sorted((rng.randrange(n), rng.randrange(n)))
            qs.append([l, r])
        return digits, a, b, qs


# Broad topics (they name the area, not the trick), easiest first within each group.
GROUPS = {
    "Arrays & Prefix Sums": ["RangeSums", "BestStreak", "Attendance", "RectangleSums", "CountSubarrays", "FairStretches",
                             "DivisibleStreaks", "EvenDigits", "ScenicRun", "LayeredUpdates", "PaintLayers", "PrefixSetEquality"],
    "Two Pointers & Sliding Window": ["TwoGifts", "ReadingMarathon", "FerrisWheel", "ThreeGifts", "GenreStretch", "TwoShowcases",
                                      "WindowPeaks", "StableReadings", "AnagramWindows"],
    "Sorting, Searching & Greedy": ["StudyPlan", "LampPosts", "FilmFestival", "AssignmentRush", "ReadingPlan", "MedianBoost",
                                    "BakeryOvens", "SkylineTowers", "MountainSkyline", "PeakOccupancy", "HotelDesk", "TastingLine",
                                    "DairyDecisions", "HighLow", "StreetLights", "PackingRanges", "Deadlines", "ScreeningRooms"],
    "Graphs": ["CountingRooms", "UnionQueries", "IceRegions", "TwoTeams", "Rewiring", "DoubleVisit", "PlanetCycles", "HerdFence",
               "RadioRelay", "FencedFields", "RouteAudit", "MergeAccounts", "GrowingKingdom", "PortalSort", "SkiTrail", "VideoRecs",
               "CableNetwork", "CoursePlanner", "GameRoutes", "RoundTrip", "LongestFlight", "ProjectTime", "PriorityCourses"],
    "Shortest Paths": ["PacketRoute", "MazeRunner", "NearestCharger", "GraphGirth", "ShortestRoutes", "AllPairsRoutes", "FastestRoutes",
                       "RouteInvestigation", "BreakWalls", "LaserRelay", "TravelVoucher"],
    "Stacks & Range Queries": ["PreviousCheaper", "SumOfMinimums", "TeamStrength", "LiveScoreboard", "BulkDiscounts", "PriceTracker",
                               "SmallerAfter", "DistinctQueries", "BitRuns"],
    "Dynamic Programming": ["DiceSums", "FewestCoins", "ChangeCombinations", "OrderedChange", "TugOfWar", "Bookshop", "TreasureWalk",
                            "CommonThread", "TypoFixer", "CoinLineDuel", "RisingPrices", "NestingBoxes", "MatchingPlaylists",
                            "ProfitTour", "ContractPicker", "GrandTour"],
    "Trees": ["OrgChart", "FlowerBeds", "NetworkSpan", "TasteRoute", "TreeMatching", "FarthestFromEach", "CourierDistances",
              "OfficeParty", "SumDistances", "TreeEdgeUpdates", "ConnectedPaintings"],
    "Math": ["FastPower", "DivisorCounts", "BinomialQueries"],
    "Fundamentals": ["DistinctNumbers", "AssociativeArray", "FencePainting", "BlockedBillboard", "ShellGame", "MixingMilk",
                     "SpeedingTicket", "BlockGame", "BubbleSortStats", "WhereAmI", "DontBeLast", "MaxDistance", "CowGymnastics",
                     "GenomeClues", "AllArrangements", "MadScientist", "MilkFactory", "CrossingPairs", "OutOfPlace", "SleepyHerding",
                     "Kayaking", "PhotoLineup", "LoadBalancing", "BlockedQueens", "LivestockLineup", "CoolingPlan", "BlockedBillboard2",
                     "GenomeTriples", "SleepingInClass", "CowCheckups", "ThreeLogos", "RaceFinish", "ContactTracing"],
    "Stretch": ["TotientQueries", "DistributingApples", "Derangements", "EqualHeights", "DigitSumRange", "ArrangementCount",
                "PrimeMultiples", "BestPairGcd", "ExponentTower", "PermutationRounds", "NonCoprimePairs", "XorPaths", "SubsetCount",
                "MaxGcdBySize", "SegmentComponents", "GcdSum", "DivisorSumPower", "DivisorAnalysis",
                "SushiBelt", "WireLayers", "StaticRangeQueries", "SubtreeQueries", "HaybaleDistribution", "SnowBoots", "WindyVoyage",
                "ResidueAlign", "SplittingField", "Deforestation", "SurvivalWeakest", "SkylinePhoto", "QueueComposite", "ForestComponents",
                "RectangularPasture", "ZeroTriples", "CircularBarn", "PairCancellation", "CandyCarts", "BestSubsequence",
                "SmallMultiple", "QuantumPaths", "WheresBessie", "EvenOutdegree", "FavoriteColors", "PalindromeWalk", "RangedTopoSort",
                "CommuterPass", "OddOneOut", "SmallestRotation", "PatrolRoads", "LevelBlockers", "DetourCosts", "RecolorRobot",
                "PilingPapers", "TrainingRoutes"],
}
# Problems modeled on a usaco.guide starred (recommended) original; the app shows them with a star, first.
STARRED = {
    "Attendance": "SPOJ Haybale Stacking", "ReadingPlan": "CSES Array Division", "IceRegions": "USACO Icy Perimeter",
    "TwoTeams": "USACO The Great Revegetation", "MazeRunner": "CSES Labyrinth", "SmallerAfter": "USACO Haircut",
    "OrderedChange": "CSES Coin Combinations", "OfficeParty": "AtCoder Independent Set",
    # Silver / Gold starred originals
    "FairStretches": "CF Good Subarrays", "ScenicRun": "CF Running Miles", "PaintLayers": "USACO Painting the Barn",
    "ThreeGifts": "CSES Sum of Three Values", "TwoShowcases": "USACO Diamond Collector", "DairyDecisions": "USACO Rental Service",
    "MountainSkyline": "USACO Mountain View", "AssignmentRush": "CSES Tasks & Deadlines", "HighLow": "USACO High Card Low Card",
    "TastingLine": "USACO Convention II", "RadioRelay": "USACO Moocast", "HerdFence": "USACO Fence Planning",
    "RouteAudit": "CSES Flight Routes Check", "PortalSort": "USACO Wormhole Sort", "SkiTrail": "USACO Cross Country Skiing",
    "FencedFields": "USACO Why Did the Cow Cross the Road III", "VideoRecs": "USACO MooTube", "TasteRoute": "USACO Milk Visits",
    "FlowerBeds": "USACO Grass Planting", "NetworkSpan": "CSES Tree Diameter", "PlanetCycles": "CSES Planets Cycles",
    "EvenDigits": "AtCoder Three Days Ago", "ProfitTour": "USACO Time is Mooney", "FewestCoins": "CSES Minimizing Coins",
    "ChangeCombinations": "CSES Coin Combinations II", "TypoFixer": "CSES Edit Distance",
    "MatchingPlaylists": "CF LCS on Permutations", "GraphGirth": "CSES Graph Girth", "LaserRelay": "USACO Lasers and Mirrors",
    "GameRoutes": "CSES Game Routes", "PriorityCourses": "CSES Course Schedule II", "RouteInvestigation": "CSES Investigation",
    "StreetLights": "CSES Traffic Lights", "SkylineTowers": "CSES Towers", "ScreeningRooms": "CSES Movie Festival II",
    "TeamStrength": "CF Mike and Feet", "BulkDiscounts": "CSES Range Update Queries",
    # Bronze starred originals
    "SpeedingTicket": "USACO Speeding Ticket", "BlockGame": "USACO Block Game", "BlockedBillboard2": "USACO Blocked Billboard II",
    "CowGymnastics": "USACO Cow Gymnastics", "GenomeClues": "USACO Bovine Genomics (Bronze)",
    "GenomeTriples": "USACO Bovine Genomics (Silver)", "CrossingPairs": "USACO Why Did the Cow Cross the Road II",
    "LoadBalancing": "USACO Load Balancing", "SleepingInClass": "USACO Sleeping in Class", "CowCheckups": "USACO Cow Checkups",
    "ContactTracing": "USACO Cowntact Tracing", "CoolingPlan": "USACO Air Cownditioning II",
    "LivestockLineup": "USACO Livestock Lineup", "ThreeLogos": "CF Three Logos", "OutOfPlace": "USACO Out of Place",
    "PhotoLineup": "USACO Photoshoot", "RaceFinish": "USACO Race", "MilkFactory": "USACO Milk Factory",
    "WhereAmI": "USACO Where Am I?", "DontBeLast": "USACO Don't Be Last!", "DistinctNumbers": "CSES Distinct Numbers",
    "Kayaking": "CF Kayaking",
    "PackingRanges": "AtCoder Packing Under Range Regulations", "DistinctQueries": "CSES Distinct Values Queries",
    "ConnectedPaintings": "AtCoder Subtree", "TreeEdgeUpdates": "AtCoder Distance Queries on a Tree",
    # stretch: contest-level starred originals
    "PrimeMultiples": "CSES Prime Multiples", "ArrangementCount": "CSES Creating Strings II", "SegmentComponents": "USACO Help Yourself",
    "DigitSumRange": "SPOJ Digit Sum", "PermutationRounds": "CSES Permutation Rounds", "NonCoprimePairs": "SPOJ Playing with GCD",
    "BestPairGcd": "CSES Common Divisors", "MaxGcdBySize": "CodeChef Maximum of GCDs", "ExponentTower": "CSES Exponentiation II",
    "DivisorSumPower": "Kilonova Sumdiv", "DivisorAnalysis": "CSES Divisor Analysis", "XorPaths": "CF Xor-Paths",
    "EqualHeights": "SPOJ Building Construction",
    "ResidueAlign": "USACO Farmer John's Favorite Operation", "ForestComponents": "AtCoder Nuske vs Phantom Thnook",
    "WindyVoyage": "CF Magic Ship", "SplittingField": "USACO Splitting the Field", "Deforestation": "USACO Deforestation",
    "SurvivalWeakest": "CF Survival of the Weakest (easy)", "SushiBelt": "CF Serval and Kaitenzushi Buffet",
    "SkylinePhoto": "CF Skyline Photo", "QueueComposite": "Library Checker Queue Operate All Composite",
    "SnowBoots": "USACO Snow Boots", "BestSubsequence": "USACO The Best Subsequence", "CircularBarn": "USACO Circular Barn Revisited",
    "CandyCarts": "Baltic OI Candy",
    "WheresBessie": "USACO Where's Bessie?", "EvenOutdegree": "CSES Even Outdegree Edges",
    "PalindromeWalk": "AtCoder Construct a Palindrome", "SmallMultiple": "AtCoder Small Multiple",
    "FavoriteColors": "USACO Favorite Colors", "QuantumPaths": "Kattis Quantum Superposition",
    "RangedTopoSort": "AtCoder Constrained Topological Sort", "CommuterPass": "JOI Commuter Pass",
    "RecolorRobot": "JOI Robot", "DetourCosts": "Balkan OI Shortest Paths", "PatrolRoads": "APIO Patrol",
    "LevelBlockers": "COCI Burza", "TrainingRoutes": "IOI Training", "SmallestRotation": "COCI Sateliti",
    "OddOneOut": "Baltic OI Genetics", "PilingPapers": "USACO Piling Papers",
}
# A 4-week path through the core interview patterns: one problem per pattern, easiest pattern first in each week.
# Rare-in-interviews topics (Fenwick trees, bitmask and rerooting DP) are left to the topic tree.
# Pair each week with the NeetCode 150 topics named in `neetcode` (do those first, then these).
ROADMAP = [
    dict(title="Week 1 · Arrays, windows, binary search and backtracking", neetcode="Arrays & Hashing, Two Pointers, Sliding Window, Binary Search, Backtracking",
         ids=["RangeSums", "CountSubarrays", "DivisibleStreaks", "Attendance", "RectangleSums", "TwoGifts", "FerrisWheel",
              "ThreeGifts", "ReadingMarathon", "GenreStretch", "WindowPeaks", "LampPosts", "ReadingPlan", "BakeryOvens", "MedianBoost",
              "AllArrangements"]),
    dict(title="Week 2 · Greedy, heaps and stacks", neetcode="Stack, Heap / Priority Queue, Intervals, Greedy",
         ids=["FilmFestival", "AssignmentRush", "PeakOccupancy", "HotelDesk", "Deadlines", "SkylineTowers", "StreetLights",
              "PreviousCheaper", "SumOfMinimums", "TeamStrength", "StableReadings"]),
    dict(title="Week 3 · Graphs", neetcode="Graphs, Advanced Graphs",
         ids=["CountingRooms", "IceRegions", "TwoTeams", "Rewiring", "UnionQueries", "MergeAccounts", "PacketRoute",
              "NearestCharger", "BreakWalls", "CoursePlanner", "ProjectTime", "ShortestRoutes", "FastestRoutes", "TravelVoucher",
              "CableNetwork"]),
    dict(title="Week 4 · Trees and dynamic programming", neetcode="Trees, 1-D Dynamic Programming, 2-D Dynamic Programming",
         ids=["OrgChart", "NetworkSpan", "OfficeParty", "CourierDistances", "DiceSums", "FewestCoins",
              "ChangeCombinations", "OrderedChange", "Bookshop", "TugOfWar", "TreasureWalk", "CommonThread", "TypoFixer",
              "RisingPrices", "CoinLineDuel", "ContractPicker"]),
]
# NeetCode-style topic tree. Each node is one or more usaco.guide modules (the slug after usaco.guide/ in a
# problem's hint url); `after` draws the arrows (suggested order); `row` is the tree level. DP is split by type.
TREE = [
    dict(id="search", row=0, title="Complete Search", after=[],
         modules=["bronze/simulation", "bronze/intro-complete", "bronze/complete-rec", "bronze/rect-geo", "bronze/ad-hoc"]),
    dict(id="hashing", row=1, title="Sets, Maps & Hashing", after=["search"],
         modules=["bronze/intro-sets", "gold/hashmaps", "gold/hashing"]),
    dict(id="sorting", row=1, title="Sorting & Greedy", after=["search"],
         modules=["bronze/intro-sorting", "bronze/intro-greedy", "silver/sorting-custom", "silver/greedy-sorting"]),
    dict(id="prefix", row=2, title="Prefix Sums", after=["hashing"], modules=["silver/prefix-sums", "silver/more-prefix-sums"]),
    dict(id="twoptr", row=2, title="Two Pointers", after=["sorting"], modules=["silver/two-pointers"]),
    dict(id="binsearch", row=2, title="Binary Search", after=["sorting"],
         modules=["silver/binary-search", "silver/binary-search-sorted-array", "gold/ternary-search"]),
    dict(id="heaps", row=2, title="Heaps & Sorted Sets", after=["sorting"], modules=["silver/priority-queues", "gold/intro-sorted-sets"]),
    dict(id="stack", row=3, title="Monotonic Stack", after=["prefix"], modules=["gold/stacks"]),
    dict(id="rangeq", row=3, title="Range Queries", after=["prefix"], modules=["gold/PURS"]),
    dict(id="window", row=3, title="Sliding Window", after=["twoptr"], modules=["gold/sliding-window"]),
    dict(id="graphs", row=3, title="Graph Traversal", after=["binsearch"],
         modules=["bronze/intro-graphs", "silver/graph-traversal", "silver/flood-fill", "silver/func-graphs"]),
    dict(id="bits", row=3, title="Bitmasks", after=["heaps"], modules=["silver/intro-bitwise", "gold/meet-in-the-middle"]),
    dict(id="dp", row=4, title="DP Basics", after=["window"], modules=["gold/intro-dp"]),
    dict(id="trees", row=4, title="Trees", after=["graphs"], modules=["silver/intro-tree", "gold/tree-euler", "gold/lca-euler"]),
    dict(id="bfs", row=4, title="BFS Shortest Paths", after=["graphs"], modules=["gold/unweighted-shortest-paths"]),
    dict(id="dsu", row=4, title="Union-Find & MST", after=["graphs"], modules=["gold/dsu", "gold/mst"]),
    dict(id="topo", row=4, title="Topological Sort", after=["graphs"], modules=["gold/toposort"]),
    dict(id="modular", row=4, title="Modular & Combinatorics", after=["bits"], modules=["gold/modular", "gold/combo"]),
    dict(id="knapsack", row=5, title="Knapsack DP", after=["dp"], modules=["gold/knapsack"]),
    dict(id="grids", row=5, title="Grid DP", after=["dp"], modules=["gold/paths-grids"]),
    dict(id="lis", row=5, title="LIS DP", after=["dp"], modules=["gold/lis"]),
    dict(id="dijkstra", row=5, title="Weighted Shortest Paths", after=["bfs"], modules=["gold/shortest-paths"]),
    dict(id="numtheory", row=5, title="Number Theory", after=["modular"], modules=["gold/divisibility"]),
    dict(id="bitdp", row=6, title="Bitmask DP", after=["knapsack"], modules=["gold/dp-bitmasks"]),
    dict(id="rangedp", row=6, title="Range DP", after=["grids"], modules=["gold/dp-ranges"]),
    dict(id="digitdp", row=6, title="Digit DP", after=["lis"], modules=["gold/digit-dp"]),
    dict(id="treedp", row=6, title="Tree DP", after=["trees"], modules=["gold/dp-trees"]),
    dict(id="reroot", row=7, title="Rerooting DP", after=["treedp"], modules=["gold/all-roots"]),
]


def module_of(p):
    return p.hint["url"].split("usaco.guide/")[-1].split("#")[0]


BY_ID = {p.id: p for p in PROBLEMS}
assert sorted(sum(GROUPS.values(), [])) == sorted(BY_ID), "every problem must be in exactly one group"
_mods = [m for n in TREE for m in n["modules"]]
assert len(_mods) == len(set(_mods)) and {module_of(p) for p in PROBLEMS} == set(_mods), "TREE must cover every module once"
assert all(a in {n["id"] for n in TREE[:i]} for i, n in enumerate(TREE) for a in n["after"]), "TREE: `after` must name an earlier node"
assert set(STARRED) <= set(BY_ID), "STARRED names an unknown problem"
_road = [i for week in ROADMAP for i in week["ids"]]
assert set(_road) <= set(BY_ID) and len(_road) == len(set(_road)), "ROADMAP names an unknown or repeated problem"
PROBLEMS = [BY_ID[i] for ids in GROUPS.values() for i in ids]
for g, ids in GROUPS.items():
    for i in ids:
        BY_ID[i].group = g

if __name__ == "__main__":
    # Self-check: reference must match brute force on every small case; time the large ones.
    # `python problems.py Id1 Id2` checks only those problems.
    import sys
    unknown = set(sys.argv[1:]) - set(BY_ID)
    assert not unknown, f"unknown problem ids: {unknown}"
    for p in [BY_ID[i] for i in sys.argv[1:]] or PROBLEMS:
        rng = random.Random("check" + p.id)
        small = list(p.examples) + list(getattr(p, "edges", [])) + [p.gen(rng, False) for _ in range(300)]
        for args in small:
            r, b = p.ref(*args), p.brute(*args)
            if hasattr(p, "check"):  # several valid answers: each must be accepted against the other
                assert p.check(args, r, b) is True and p.check(args, b, r) is True, (p.id, args, r, b)
            else:
                assert p.norm(r) == p.norm(b), (p.id, args, r, b)
        slowest = 0
        for _ in range(p.big):
            args = p.gen(rng, True)
            s = time.perf_counter()
            p.ref(*args)
            slowest = max(slowest, time.perf_counter() - s)
        print(f"ok  {p.id:16} 300 small cases match brute; large ref {slowest:.2f}s (limit {p.tl}s)")
    print(starter(PROBLEMS[0]))
