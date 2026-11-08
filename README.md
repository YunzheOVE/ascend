# Ascend

An unofficial, local LeetCode-style judge for practicing problems built around usaco.guide modules,
picked for SWE interviews. Not affiliated with usaco.guide. See `plan.md` for the problem backlog.

```
python server.py        # then open http://localhost:8000
python problems.py      # self-check: every reference solution vs a brute force
```

- **Run examples** runs your `class Solution` on the visible examples. **Submit** runs ~30 hidden tests per problem,
  including large ones (n ≈ 10^5) that an O(n²) solution won't finish within the 2s limit.
- Your code is saved to `solutions/<id>.py` every time you run or submit it. Solved status is stored in `progress.json`.
- The usual LeetCode imports are already in scope (`typing`, `collections`, `heapq`, `bisect`, `functools`, `itertools`, `math`).
- Each problem has a hidden **Hint** (the pattern), a link to the usaco.guide module, and a spoiler reference solution.

**Adding a problem:** copy any class in `problems.py`. Give it a `ref` (the correct solution), a `brute` (a slow but
obviously correct solution), a `gen(rng, big)` that returns the arguments, and `examples`. Then run `python problems.py`.
