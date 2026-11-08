# Problem plan

A running list of usaco.guide problems worth importing, in batches. usaco.guide modules link to
CSES, AtCoder, Codeforces and USACO problems; each problem here is modeled on one of those originals,
with its own statement and hidden tests. Only problems whose pattern shows up in SWE interviews make the list.

**Status:** ✅ imported · 🔜 next batch · 📋 backlog · 🧗 stretch (contest/olympiad level; now imported into the **Stretch** group, except the six left out below) · ⛔ out of scope

In the tables below, every 📋 import, 📋 later and 🧗 stretch row has since been imported (batches 4–7), apart from the
six problems that need new judge features.

## Imported

| Batch | Problems |
|---|---|
| 1 ✅ | Venue Attendance, Orchard Rectangles, Balanced Ledger Windows, Reading Plan, Freelancer Deadlines, Ice Survey, Two Teams, Merge Customer Profiles, Counting Fastest Routes, Build Pipeline, Demolition Path, Weakest Link Total, Later Underdogs, Nesting Boxes, Total Commute in a Tree Network |
| 2 ✅ | Gondola Rides (CSES Ferris Wheel), Playlist Variety (CSES Playlist), Stable Readings (LC 1438), Peak Occupancy (CSES Restaurant Customers), Ordered Change (CSES Coin Combinations I), Tug of War (CSES Apple Division), Bookshop Budget (CSES Book Shop), Treasure Walk (CSES Grid Paths), Cable Network (CSES Road Reparation), Office Party (AtCoder DP P) |
| 3 ✅ | Contract Picker (CSES Projects), Nearest Charger (LC 542 multi-source BFS), Travel Voucher (CSES Flight Discount), Rewiring the Lab (CSES Building Roads / LC 1319), Packet Route (CSES Message Route), Hotel Desk (CSES Room Allocation), Coin Line Duel (CSES Removal Game), Divisible Streaks (CSES Subarray Divisibility), Bakery Ovens (CSES Factory Machines), Growing Kingdom (CSES Road Construction) |

| 4 ✅ | Batch 4 warm-ups (Course Planner, Rising Prices, Film Festival, Live Scoreboard, Org Chart, Maze Runner) and Batch 6 (Layered Updates, Lamp Posts, Median Boost, Round Trip, Price Tracker, Grand Tour, Courier Distances) |
| 5 ✅ | Every **📋 import** row in the Starred, Focus and Bronze tables below (98 problems; new topic groups **Shortest Paths**, **Math**, **Fundamentals**). Problems modeled on a starred original are listed in `STARRED` in `problems.py` and shown with ★ |

| 6 ✅ | All 📋 later rows (12 + AtCoder Distance Queries on a Tree) and 38 🧗 stretch problems (number theory, combinatorics, greedy, data structures, DP) in the **Stretch** group |
| 7 ✅ | The last 16 🧗 stretch problems (graphs, trees, strings): Where's Bessie, Even Outdegree Edges, Construct a Palindrome, Small Multiple, Favorite Colors, Quantum Superposition, Constrained Topological Sort, JOI Commuter Pass, JOI Robot, Balkan Shortest Paths, APIO Patrol, COCI Burza (as a covering problem), IOI Training, COCI Sateliti, Baltic Genetics, USACO Piling Papers |

**Status 2026-11-07:** 199 problems. Every starred and focus problem from usaco.guide's Bronze–Gold modules is
imported, except the six that need new judge features (listed below). Each is checked against a brute force.
Left out because they need new judge features: USACO Angry Cows, CF The Meeting Place Cannot Be Changed, CSES Candy
Lottery and AtCoder Erasing Vertices (non-integer answers), and CF Take a Guess and CF Cooperative Game (interactive).

Problems with more than one correct answer (Packet Route, Hotel Desk) define a `check(args, out, expected)`
validator in `problems.py` instead of being compared to the reference output exactly.

## Batch 4 🔜: warm-ups for the Hard problems

Each one is the plain Medium pattern, placed just before its Hard problem so the twist is the only new idea.

| Warm-up (plain pattern) | Original | Leads into |
|---|---|---|
| Topological order of courses | CSES Course Schedule ★ · LC 210 | Build Pipeline (adds DP on finish times) |
| Plain LIS, O(n log n) | CSES Increasing Subsequence · LC 300 | Nesting Boxes (adds 2-D sort trick) |
| Interval greedy by end time | CSES Movie Festival · LC 435 | Freelancer Deadlines (adds heap "undo") |
| Fenwick tree: point update, range sum | CSES Dynamic Range Sum Queries · LC 307 | Later Underdogs (adds coordinate compression) |
| Sum of distances from **one** node + subtree sizes | CSES Subordinates | Total Commute (adds rerooting to every node) |
| Grid BFS shortest path | CSES Labyrinth ★ (Packet Route already covers this) | Demolition Path (adds 0/1 edge weights) |

## Starred on usaco.guide ★

Every problem usaco.guide stars in the Silver and Gold modules used here (scraped 2026-11-06).
★ in the app = an Ascend problem modeled on a starred original; do those first.

Verified 2026-11-06 against the site's source (`cpinitiative/usaco-guide`, `content/**/*.problems.json`, field
`isStarred`) and spot-checked on the live site. The JSON also marks each module's **focus problems** as starred;
the site shows those as "Focus Problem" blocks, not starred rows, so they are tracked in their own table below.

| Module | Starred problem | Status |
|---|---|---|
| Prefix Sums | CF Good Subarrays · CF Running Miles | 📋 import |
| | USACO Farmer John's Favorite Operation | 🧗 stretch |
| More Prefix Sums | SPOJ Haybale Stacking | ✅ Venue Attendance ★ |
| | USACO Painting the Barn (2-D difference array) | 📋 import |
| | AtCoder Nuske vs Phantom Thnook | 🧗 stretch |
| Two Pointers | CSES Sum of Three Values · USACO Diamond Collector | 📋 import |
| Binary Search | CSES Array Division | ✅ Reading Plan ★ |
| | USACO Angry Cows | 📋 import |
| | CF Magic Ship · CF The Meeting Place Cannot Be Changed | 🧗 stretch (Meeting Place needs a floating-point answer checker) |
| Custom Comparators | USACO Rental Service · USACO Mountain View | 📋 import |
| | USACO Splitting the Field | 🧗 stretch |
| Greedy with Sorting | CSES Tasks & Deadlines · USACO High Card Low Card | 📋 import |
| Priority Queues | USACO Convention II | 📋 import |
| | AtCoder Packing Under Range Regulations | 📋 later |
| | USACO Deforestation · CF Survival of the Weakest · CF Serval and Kaitenzushi Buffet | 🧗 stretch |
| Graph Traversal | USACO The Great Revegetation | ✅ Two Teams ★ |
| | USACO Moocast · USACO Fence Planning · CSES Flight Routes Check · USACO Wormhole Sort | 📋 import |
| Flood Fill | USACO Icy Perimeter | ✅ Ice Survey ★ |
| | USACO Cross Country Skiing · USACO Why Did the Cow Cross the Road III | 📋 import |
| | USACO Where's Bessie? | 🧗 stretch |
| Intro to Trees | USACO MooTube · USACO Milk Visits · USACO Grass Planting · CSES Tree Diameter | 📋 import |
| | CSES Even Outdegree Edges | 🧗 stretch (many valid answers, needs a checker) |
| Functional Graphs | CSES Planets Cycles | 📋 import |
| Bitwise | AtCoder Three Days Ago (prefix XOR) | 📋 import |
| | CSES Prime Multiples | 🧗 stretch |
| Intro DP | USACO Time is Mooney | 📋 import |
| | USACO Circular Barn Revisited | 🧗 stretch |
| Knapsack | CSES Coin Combinations (ordered) | ✅ Ordered Change ★ |
| | CSES Minimizing Coins · CSES Coin Combinations (unordered) | 📋 import |
| Paths on Grids | CSES Edit Distance | 📋 import |
| LIS | CF LCS on Permutations (LCS → LIS trick) | 📋 import |
| | Baltic OI Candy | 🧗 stretch |
| Bitmask DP | COCI Burza · IOI Training | 🧗 stretch (olympiad) |
| Unweighted Shortest Paths | CSES Labyrinth (grid BFS, return the path) | 📋 import (similar to Packet Route + Nearest Charger) |
| | CSES Graph Girth · USACO Lasers and Mirrors | 📋 import |
| | AtCoder Construct a Palindrome · AtCoder Small Multiple | 🧗 stretch |
| DSU | USACO MooTube (Gold) · USACO Wormhole Sort | 📋 import (with the Silver versions) |
| | USACO Favorite Colors | 🧗 stretch |
| Topological Sort | CSES Game Routes · CSES Course Schedule II (smallest-first order) | 📋 import |
| | Kattis Quantum Superposition · AtCoder Constrained Topological Sort | 🧗 stretch |
| Shortest Paths | CSES Investigation | 📋 import |
| | JOI Commuter Pass · JOI Robot · Balkan OI Shortest Paths | 🧗 stretch (olympiad) |
| Sorted Sets | CSES Traffic Lights · CSES Towers · CSES Movie Festival II | 📋 import |
| | USACO Snow Boots | 🧗 stretch |
| Stacks | CF Mike and Feet | 📋 import |
| | CF Skyline Photo | 🧗 stretch |
| Sliding Window | USACO Painting the Barn | 📋 (listed above) |
| | Library Checker Queue Composite | 🧗 stretch (also starred in Modular Arithmetic) |
| Point Update Range Sum | USACO Haircut (inversions) | ✅ Later Underdogs ★ |
| | CSES Range Update Queries | 📋 import |
| | CSES Distinct Values Queries | 📋 later |
| DP on Trees | AtCoder Independent Set | ✅ Office Party ★ |
| | IOI Training | 🧗 stretch (olympiad; also starred in Bitmask DP) |
| All Roots | AtCoder Subtree | 📋 later |
| | APIO Patrol | 🧗 stretch (olympiad) |
| Hashing | COCI Sateliti · Baltic OI Genetics | 🧗 stretch (olympiad) |
| LCA with Euler Tour | AtCoder Distance Queries on a Tree (LCA + edge updates) | 📋 later (after the Batch 5 LCA problem) |
| Combinatorics | CSES Creating Strings II · USACO Help Yourself | 🧗 stretch |
| Digit DP | SPOJ Digit Sum · USACO Piling Papers | 🧗 stretch |
| Divisibility | CSES Permutation Rounds · SPOJ Playing with GCD · CSES Common Divisors · CodeChef Maximum of GCDs | 🧗 stretch |
| Modular Arithmetic | CSES Exponentiation II · Kilonova Sumdiv · CSES Divisor Analysis · USACO The Best Subsequence (+ Queue Composite, listed above) | 🧗 stretch |
| Meet in the Middle | CF Xor-Paths | 🧗 stretch |
| Ternary Search | SPOJ Building Construction | 🧗 stretch |
| MST, Range DP, Hashmaps, Euler Tour, Custom STL | (no starred problems) | |

**Rule:** every starred problem gets imported, even when NeetCode 150 already covers the same idea, or when it is a
contest or olympiad problem. Overlap is useful practice: the same pattern in a different setting. 🧗 **stretch**
marks contest- and olympiad-level problems: they are imported, but in the last batches and in a **Stretch**
topic group, so they never block interview-core practice.

## Bronze ★ (all starred and focus problems)

All 22 starred table problems plus the 14 focus problems from usaco.guide's Bronze modules. They would make a new
**Fundamentals** topic group (complete search, simulation, sorting, sets, greedy, basic graphs) and are good warm-ups.

| Module | Starred problem | Focus problem | Status |
|---|---|---|---|
| Simulation | USACO Speeding Ticket (Easy) · USACO Block Game (Medium) | USACO Shell Game · USACO Mixing Milk | 📋 import |
| Rectangle Geometry | USACO Blocked Billboard II (Hard) | USACO Fence Painting · USACO Blocked Billboard | 📋 import |
| Basic Complete Search | USACO Cow Gymnastics · USACO Bovine Genomics · USACO Why Did the Cow Cross the Road II (Medium) · USACO Bovine Genomics, Silver version · USACO Load Balancing · USACO Sleeping in Class · USACO Cow Checkups (Hard) · USACO Cowntact Tracing (Very Hard) | CF Maximum Distance | 📋 import |
| Complete Search with Recursion | USACO Air Cownditioning II · USACO Livestock Lineup (Medium) · CF Three Logos (Hard) | CSES Apple Division (✅ Tug of War) · CSES Creating Strings I · CSES Chessboard and Queens | 📋 import (overlaps NeetCode: Permutations, N-Queens) |
| Ad Hoc / Casework | none | USACO Sleepy Cow Herding | 📋 import |
| Introduction to Sorting | CSES Distinct Numbers (Easy) · CF Kayaking (Medium) | HackerRank Bubble Sort | 📋 import |
| Introduction to Sets & Maps | USACO Where Am I? (Easy) · USACO Don't Be Last! (Medium) | CSES Distinct Numbers · Yosupo Associative Array | 📋 import (overlaps NeetCode: Contains Duplicate) |
| Introduction to Greedy | USACO Out of Place (Medium) · USACO Photoshoot (Hard) · USACO Race (Very Hard) | USACO Mad Scientist | 📋 import |
| Introduction to Graphs | USACO Milk Factory (Hard) | USACO Livestock Lineup | 📋 import |

## Focus problems (the worked example each module teaches with)

Status of every Silver/Gold focus problem. Focus problems are starred in usaco.guide's data, so each one is
imported even when it overlaps NeetCode 150.

| Module | Focus problem | Status |
|---|---|---|
| Prefix Sums | YS Static Range Sum | 📋 import (warm-up for Venue Attendance / Orchard Rectangles) |
| More Prefix Sums | CSES Forest Queries | ✅ Orchard Rectangles |
| | CSES Max Subarray Sum | 📋 import (overlaps NeetCode: Maximum Subarray) |
| | CF Greg and Array (difference array applied twice) | 📋 **new candidate** |
| Two Pointers | CSES Sum of Two Values · CF Books | 📋 import (overlaps NeetCode: Two Sum II, sliding window) |
| Binary Search on a Sorted Array | USACO Counting Haybales (count points in ranges with bisect) | 📋 **new candidate** |
| Binary Search | CF Maximum Median (binary search on the answer) | 📋 **new candidate** |
| Custom Comparators | USACO Rectangular Pasture · CF Static Range Queries | 🧗 stretch (coordinate compression) |
| Greedy with Sorting | CSES Movie Festival | 🔜 Batch 4 |
| | CF Studying Algorithms | 📋 import (easy sort + greedy) |
| Priority Queues | CSES Room Allocation | ✅ Hotel Desk |
| Graph Traversal | CSES Building Roads · CSES Building Teams | ✅ Rewiring the Lab · Two Teams |
| Flood Fill | CSES Counting Rooms | 📋 import (overlaps NeetCode: Number of Islands) |
| Intro to Trees | CSES Subordinates | 🔜 Batch 4 |
| Functional Graphs | CF Badge · CF Cooperative Game (cycle finding) | 📋 import (overlaps NeetCode: Linked List Cycle, Find the Duplicate; Cooperative Game is interactive, so adapt it to a function) |
| Intro to Bitwise | CF Take a Guess (interactive) | 🧗 stretch (adapt: pass the hidden array's pair sums in, return the k-th smallest) |
| Intro DP | (none) | |
| Knapsack | CSES Dice Combinations | 📋 import (overlaps NeetCode: Climbing Stairs) |
| Paths on Grids | CSES Grid Paths | ✅ Treasure Walk |
| | LC Longest Common Subsequence | 📋 import (overlaps NeetCode: LCS) |
| LIS | CSES Increasing Subsequence | 🔜 Batch 4 |
| | Baltic OI PCB | 🧗 stretch |
| Bitmask DP | CSES Hamiltonian Flights (count paths over visited-sets) · AtCoder Close Group | 📋 **new candidate** (Batch 5) |
| Range DP | SAPO Space Jazz | 🧗 stretch (Coin Line Duel covers the easier range DP) |
| DP on Trees | CSES Tree Matching | 📋 later (same idea as Office Party) |
| All Roots | CSES Tree Distances I | 📋 later |
| Unweighted Shortest Paths | CSES Message Route | ✅ Packet Route |
| | Baltic OI Tracks in the Snow (0-1 BFS) | ✅ Demolition Path |
| DSU | YS Union Find | 📋 import (plain union-find warm-up) |
| Topological Sort | CSES Course Schedule | 🔜 Batch 4 |
| | CSES Round Trip II (find a directed cycle and return it) | 📋 **new candidate** |
| | CSES Longest Flight Route | 📋 later |
| Shortest Paths | CSES Shortest Routes I | 📋 import (overlaps NeetCode: Network Delay Time) |
| | CSES Shortest Routes II (Floyd-Warshall) | 📋 later |
| MST | CSES Road Reparation | ✅ Cable Network |
| Sorted Sets | CSES Bit Inversions | 📋 later (hard) |
| Stacks | CSES Nearest Smaller Values | 📋 import (overlaps NeetCode: Daily Temperatures) |
| Sliding Window | CSES Playlist | ✅ Playlist Variety |
| | LC Sliding Window Maximum | 📋 import (overlaps NeetCode: Sliding Window Maximum) |
| Point Update Range Sum | CSES Dynamic Range Sum Queries | 🔜 Batch 4 |
| | CSES Dynamic Range Minimum Queries (segment tree) | 📋 **new candidate** (pair with Batch 4's Fenwick tree) |
| | SPOJ Inversion Counting | ✅ Later Underdogs |
| LCA with Euler Tour | CSES Company Queries II | 📋 Batch 5 |
| | CSES Distance Queries (distance via LCA) | 📋 **new candidate** (Batch 5) |
| Hashing | CCC Searching For Strings · AtCoder Prefix Equality | 📋 later |
| Combinatorics | CSES Binomial Coefficients (nCr mod p) | 📋 later |
| | Yosupo Montmort Numbers · CSES Distributing Apples · CSES Candy Lottery · AtCoder Erasing Vertices | 🧗 stretch |
| Modular Arithmetic | CSES Exponentiation | 📋 import (overlaps NeetCode: Pow(x, n)) |
| Divisibility | CSES Counting Divisors | 📋 import (sieve-style counting) |
| | SPOJ GCD Extreme · SPOJ Euler Totient Function | 🧗 stretch |
| Meet in the Middle | CSES Meet in the Middle | 🧗 stretch |
| Ternary Search | USACO Haybale Distribution | 🧗 stretch |
| Euler Tour | CSES Subtree Queries (Euler tour + Fenwick tree) | 🧗 stretch |
| Hashmaps | USACO Farmer John Solves 3SUM | 🧗 stretch |

## Batch 6 📋: focus problems not yet planned

The interview-relevant **new candidates** from the table above.

| Pattern | Original | usaco.guide module | Why it matters |
|---|---|---|---|
| Difference array applied twice (operations of operations) | CF Greg and Array | Silver: More on Prefix Sums | Tests real understanding of difference arrays |
| Count points in ranges with binary search | USACO Counting Haybales | Silver: Binary Search on a Sorted Array | bisect_left / bisect_right fluency |
| Binary search on the answer (maximize median) | CF Maximum Median | Silver: Binary Search | Monotonic predicate that is not obvious |
| Find and return a directed cycle | CSES Round Trip II | Gold: Topological Sort | Cycle detection with the cycle itself as output |
| Segment tree: point update, range min | CSES Dynamic Range Minimum Queries | Gold: Point Update Range Sum | Fenwick trees can't do min; segment trees can |
| Bitmask DP over visited sets | CSES Hamiltonian Flights | Gold: Bitmask DP | Core bitmask-DP template (n ≤ 20) |
| Distance via LCA | CSES Distance Queries | Gold: LCA with Euler Tour | dist(u, v) = depth[u] + depth[v] − 2·depth[lca] |

## Batch 5 📋: harder but still interview-relevant

| Pattern | Original | usaco.guide module | Why it matters |
|---|---|---|---|
| BFS over (node, visited-mask) | LC 847 | Gold: Bitmask DP | Google favorite |
| Bitmask DP partitioning | CSES Elevator Rides · LC 1986 | Gold: Bitmask DP | Standard tool when n ≤ 20 |
| LCA / k-th ancestor (binary lifting) | CSES Company Queries II · LC 236 / 1483 | Gold: LCA with Euler Tour (and Platinum: Binary Jumping) | LCA is a top tree question |
| Sorted multiset lookups | CSES Concert Tickets | Gold: More Operations on Sorted Sets | Python has no TreeMap; learn bisect/heap workarounds |
| Interval booking | LC 729 / 731 | Gold: More Operations on Sorted Sets | Design question |
| Rolling hash + binary search | LC 1044 / 187 | Gold: Hashing | Shows up at Google-style companies |
| Longest cycle in a functional graph | LC 2360 | Silver: Introduction to Functional Graphs | Cycle detection on out-degree-1 graphs |
| Prefix XOR | LC 1442 / 1310 | Silver: Intro to Bitwise Operators | Prefix trick generalizes beyond sums |

## Later 📋: good practice, lower priority

- CSES Array Description (DP with neighbor constraints), CSES Rectangle Cutting (2D DP), CSES Two Sets II (counting subset sums)
- CSES Game Routes / Longest Flight Route (counting paths and reconstructing paths in a DAG)
- CSES Shortest Routes II (Floyd-Warshall, keep n ≤ 150 for Python)
- CSES Tree Distances I (farthest node from every node, rerooting)
- Sieve of Eratosthenes (LC 204), nCr mod p (Gold: Combinatorics)

## Out of scope ⛔

Platinum and Advanced modules. Within Bronze–Gold nothing starred is skipped: every starred and focus problem is
listed above, with contest- and olympiad-level ones marked 🧗 stretch. Unstarred problems in the number-theory,
Digit DP, Euler Tour and Meet in the Middle modules are not planned, since they rarely come up in SWE interviews.

## How to import a batch

1. Add a class per problem in `problems.py` (copy any existing one): `ref`, `brute`, `gen`, `examples`, `edges`, and a `hint` naming the original. If several answers are valid, add a `check` (see Hotel Desk).
2. Add its id to `GROUPS` (easiest first). For a new group, also add it to `STYLE` in `index.html`.
3. Run `python problems.py` (every reference must match its brute force), then restart `server.py`.
4. Move the rows from this file into **Imported**.
