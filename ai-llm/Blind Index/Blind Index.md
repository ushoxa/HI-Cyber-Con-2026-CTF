# Blind Index

**Category:** AI / LLM (embedding oracle), per-instance dynamic  **Flag (my instance `blind-index-1d830d29ece3`):** `hiCTF{1726950438}`

> The platform team runs an internal similarity lookup service. You give it a text and it tells you how close that text sits, in the house embedding space, to a fixed reference direction. Ten reference records are filed under your team… the service will not look a reference record up directly, it never shows you an embedding…

**This flag is instance-specific.** Every instance gets its own 10 random records, so this answer only worked for my instance. To solve a fresh instance, run `python3 solve/solve.py https://blind-index-<id>.chall.hiddeninvestigations.net`.

## My instance's results

Second-difference estimates (median of 12 disjoint position pairs `(i, i+12)` per record, 36 lookups per record, 360 lookups in total out of ~400). An additive ridge model fitted on every scored text, which cost no extra lookups, gave exactly the same ordering.

| /records order | record | estimated score | rank |
|---|---|---|---|
| 0 | `517dd591a03c02a8ded1893b` | -0.4164 | **1** |
| 1 | `a2c16097501047437c0a8375` | +0.0196 | **7** |
| 2 | `5eada38cd20b5073965f0d53` | -0.3664 | **2** |
| 3 | `9c51bb7dd67efc8ce08e8a90` | -0.0275 | **6** |
| 4 | `2f4395416b295fb7d3ebb2a9` | +0.0280 | **9** |
| 5 | `6cf7093681cbecf33b2ede1a` | -0.0328 | **5** |
| 6 | `fe773709d5accbbfa8d304fd` | -0.4709 | **0** |
| 7 | `58a3df67b3bc0af7c385f9ff` | -0.0759 | **4** |
| 8 | `727618b716ce44ac2a173d58` | -0.2667 | **3** |
| 9 | `71853b150a7c793b07ecbf9e` | +0.0273 | **8** |

ranks in /records order → 1726950438  (solver result: 1726950438)
lookups logged: 360

## Notes from the run
- `/lookup` rate-limits with HTTP 429 on rapid batches, so use smaller chunks with `time.sleep` backoff.
- First-order additive extrapolation over all 24 positions was off by 0.2 or more, because of the L2 normalization. The second-difference trick cancels that normalization residual.
- Don't try to reconstruct the full embedding; it doesn't fit in the lookup budget.

---

## Method writeup (general, no instance data)

## 1. What the service is

The instance exposes a tiny HTTP API — a "blind index" similarity lookup:

- `GET /records` — the 10 reference record IDs filed under your team (24-char hex each).
- `GET /status` — your remaining lookup allowance (fixed total, never resets).
- `POST /lookup` — `{"text": "..."}` or `{"texts": [...]}` (<=64 per request);
  returns a float **score** = how close the text sits to a fixed reference
  direction in the house embedding space.

Constraints that define the puzzle:
- Reference records **cannot be looked up directly** (`/lookup` on a record -> `403`).
- You never see an embedding, only a scalar score.
- The lookup budget is small (a few hundred total), so brute force is out.

**Goal:** report where each of your 10 records falls on the score scale.

## 2. The key observation

The score is a **linear-ish blind index**: `score(t) = <E(t), d>` where the
embedding `E` is (to first order) **additive per character position**, and `d`
is a fixed direction. Practically:

> `score(t) ~= b + sum_i f_i(t_i)`

Two things worth confirming cheaply, because they shape the whole approach:

- **The model is fixed across instances.** Score a constant probe (e.g.
  all-zeros) on any instance — it returns the *same* value every time. The
  embedding and reference direction are global.
- **Only the 10 records are per-instance.** `/records` returns a fresh random
  set each spin-up. => **Every team's scores, ranking, and final token are
  different.** Nothing in this writeup can leak another team's answer; each
  solver must run the procedure on their own live instance.

## 3. The attack: estimate a blocked record's score from neighbours

You can't query a record `r`, but you *can* query strings that differ from it.
Use the inclusion-exclusion (second-difference) identity. Pick two positions
`i`, `j`; let `r^i` be `r` with a single nibble changed at `i`, `r^j` at `j`,
and `r^{i,j}` at both:

> **score(r) ~= score(r^i) + score(r^j) - score(r^{i,j})**

Under a purely additive model this is **exact** — every term cancels except
`score(r)`. With a real (L2-normalized) embedding there's a tiny residual: the
second-difference of the *interaction* between positions `i` and `j`. So:

- **Use two far-apart, single-nibble substitutions** to keep each estimate clean.
- **Average several disjoint position-pairs per record and take the median** to
  cancel the residual. ~8-15 pairs/record drives the error to a few thousandths
  — far inside any sane checker tolerance.

Each record then costs: a handful of single-mutations (reused across pairs) +
one double-mutation per pair. Batch everything through `texts` (<=64), and reuse
the singles across many pairs to stay well inside budget.

### Sketch

```python
# r = a record id; H = "0123456789abcdef"
def sub(t, p, c): return t[:p] + c + t[p+1:]

# pick spread-out positions, one alt nibble each
singles = {p: sub(r, p, alt[p]) for p in POS}
ests = []
for (i, j) in disjoint_pairs(POS):
    ab = sub(sub(r, i, alt[i]), j, alt[j])
    ests.append(S[singles[i]] + S[singles[j]] - S[ab])   # S = scored lookups
score_r = median(ests)
```

*(Cross-check: fit a global additive ridge model
`score ~= b + sum onehot(position,char)` on everything you've scored and predict
each record — it should agree with the pair estimates.)*

## 4. Budget discipline

- One `/status` up front; never waste lookups on malformed input (validation
  errors are free but round-trips aren't).
- Batch 64/request; **reuse single-mutations** so each new pair costs only its
  one double-mutation lookup.
- A full 10-record reconstruction fits comfortably in the allowance with margin
  to break near-ties.

## 5. From scores to the submission token

The checker wants the **ordering**, encoded deterministically — robust to small
reconstruction error:

1. Sort the 10 records by estimated score, **low -> high**.
2. Give each record its **0-indexed scale position** (0 = lowest ... 9 = highest).
3. Read those positions back **in the API's original `/records` order** and
   concatenate -> a **10-digit permutation of 0-9**.
4. Wrap it: `hiCTF{<that 10-digit string>}`.

Because the records are per-instance, this digit string is unique to your
instance — submit it while that same instance is the one bound to your account.

## 6. Robustness checklist

- Median over many pairs; add a few more pairs for any two records whose scores
  are within your error bar (don't let a near-tie flip two adjacent ranks).
- Confirm invariance: position matters (a cyclic shift changes the score a lot),
  so your single-nibble deltas are genuine per-position signal.
- Keep a log of every `text -> score`; it doubles as the training set for the
  additive-model cross-check and costs nothing extra.

## 7. TL;DR

Linear blind index -> recover each blocked record's score via
`score(r) ~= score(r^i)+score(r^j)-score(r^{i,j})` with far-apart nibble flips,
median over pairs -> rank the records -> read 0-indexed ranks in original order
-> `hiCTF{<permutation>}`. Model is global; records (and therefore the answer)
are per-instance.

## Files
- `solve/solve.py` is the full live solver (pass the instance URL as the argument): it pulls `/records`, runs the pair lookups, takes medians, ranks and prints the flag
- `solve/tiebreak.py` runs extra pairs or a different nibble scheme for near-tied records, plus the additive-ridge cross-check
- `artifacts/solve_result.json` has my instance's per-record estimates, the 10-digit answer and the full `text → score` log (360 lookups)
- `artifacts/validate.json` holds the validation lookups from the run
