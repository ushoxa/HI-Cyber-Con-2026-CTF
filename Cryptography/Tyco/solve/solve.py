import sys
from flint import fmpz_mod_poly_ctx

sys.setrecursionlimit(10000)

data = open(sys.argv[1]).read().strip().strip("'").split()
N, e, d, t1, t2 = map(int, data)

R = fmpz_mod_poly_ctx(N)
x = R([0, 1])
ONE, ZERO = R(1), R(0)


def split(p, m):
    # p = top * x^m + bot
    return p.right_shift(m), p.truncate(m)


def hgcd(a, b):
    if 2 * b.degree() <= a.degree() or a.degree() == 1:
        return ONE, ZERO, ZERO, ONE
    m = a.degree() // 2
    a_top, _ = split(a, m)
    b_top, _ = split(b, m)
    R00, R01, R10, R11 = hgcd(a_top, b_top)
    c = R00 * a + R01 * b
    dd = R10 * a + R11 * b
    if dd.is_zero():
        return R00, R01, R10, R11
    q, ee = divmod(c, dd)
    d_top, _ = split(dd, m // 2)
    e_top, _ = split(ee, m // 2)
    S00, S01, S10, S11 = hgcd(d_top, e_top)
    T0 = S00 - q * S01
    T1 = S10 - q * S11
    return (S01 * R00 + T0 * R10, S01 * R01 + T0 * R11,
            S11 * R00 + T1 * R10, S11 * R01 + T1 * R11)


def gcd(a, b):
    while True:
        print("deg", a.degree(), b.degree(), flush=True)
        if b.is_zero():
            return a.monic()
        q, r = divmod(a, b)
        if r.is_zero():
            return b.monic()
        R00, R01, R10, R11 = hgcd(a, b)
        c = R00 * a + R01 * b
        dd = R10 * a + R11 * b
        if dd.is_zero():
            return c.monic()
        q, r = divmod(c, dd)
        if r.is_zero():
            return dd.monic()
        a, b = dd, r


f1 = x**e - t1
f2 = (x + d)**e - t2
# reduce f2 mod f1 cheaply so degrees start strictly decreasing
f2 = f2 % f1

g = gcd(f1, f2)
print("gcd degree:", g.degree())
c0 = int(g.coeffs()[0])
r = (-c0) % N
assert pow(r, e, N) == t1 and pow(r + d, e, N) == t2
print(r.to_bytes((r.bit_length() + 7) // 8, "big"))

