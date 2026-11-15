#!/usr/bin/env python3
"""Independent finite checks for role-bounded quad (standard library only).

Bisection is compared with enumeration of every coordinate/total active face;
the latter does not use the scalar-response implementation. Gradients are
checked only inside smooth branches, not at nondifferentiable boundaries.
"""
from itertools import product
import math
import random


def in_description_space(description, role, k, beta=0, alpha=1, gamma_max=2):
    """Membership in the fixed role's D_v, before any regional optimization."""
    w, mu, score, lo, hi = description
    if not all(math.isfinite(x) for x in description) or not 0 <= w <= mu <= 1 or mu > gamma_max*w:
        return False
    expected = {'ordinary': (0, mu), 'pass': (mu, mu),
                'floor_cap': (beta*mu, min(mu, alpha*k))}[role]
    return (lo, hi) == expected and 0 <= lo <= hi <= mu


def bounds(mu, lower, upper, k, received=None):
    if len(mu) != len(lower) or len(mu) != len(upper):
        raise ValueError('shape mismatch')
    if any(not 0 <= a <= b <= m <= 1 for m, a, b in zip(mu, lower, upper)):
        raise ValueError('infeasible coordinate bounds')
    total_upper = min(k, sum(upper))
    if sum(lower) > total_upper + 1e-12:
        raise ValueError('infeasible regional floor')
    old_floor = min(1, sum(mu if received is None else received))
    return max(sum(lower), min(old_floor, total_upper)), total_upper


def allocate(scores, lower, upper, low_total, high_total, tau):
    if tau <= 0 or not 0 <= low_total <= high_total:
        raise ValueError('invalid temperature or total range')
    if sum(lower) > low_total + 1e-12 or high_total > sum(upper) + 1e-12:
        raise ValueError('infeasible total range')
    if not scores:
        return []
    def response(lam):
        return [min(hi, max(lo, (s - lam) / tau))
                for s, lo, hi in zip(scores, lower, upper)]
    initial = response(0)
    if low_total <= sum(initial) <= high_total:
        return initial
    target = low_total if sum(initial) < low_total else high_total
    if abs(target - sum(lower)) < 1e-14:
        return list(lower)
    if abs(target - sum(upper)) < 1e-14:
        return list(upper)
    left = min(s - tau * hi for s, hi in zip(scores, upper))
    right = max(s - tau * lo for s, lo in zip(scores, lower))
    for _ in range(100):
        middle = (left + right) / 2
        if sum(response(middle)) > target:
            left = middle
        else:
            right = middle
    return response((left + right) / 2)


def enumerate_faces(scores, lower, upper, lo_total, hi_total, tau):
    candidates = []
    for statuses in product((-1, 0, 1), repeat=len(scores)):
        fixed = {i: lower[i] if status == -1 else upper[i]
                 for i, status in enumerate(statuses) if status}
        free = [i for i, status in enumerate(statuses) if not status]
        for total in (None, lo_total, hi_total):
            c = [fixed.get(i, 0) for i in range(len(scores))]
            if total is None:
                for i in free:
                    c[i] = scores[i] / tau
            elif free:
                shift = (sum(scores[i] for i in free) -
                         tau * (total - sum(fixed.values()))) / len(free)
                for i in free:
                    c[i] = (scores[i] - shift) / tau
            elif abs(sum(c) - total) > 1e-10:
                continue
            if not lo_total - 1e-10 <= sum(c) <= hi_total + 1e-10:
                continue
            if any(not a - 1e-10 <= x <= b + 1e-10 for x, a, b in zip(c, lower, upper)):
                continue
            objective = sum(s * x - tau * x * x / 2 for s, x in zip(scores, c))
            candidates.append((objective, c))
    assert candidates
    return max(candidates, key=lambda x: x[0])[1]


def close(a, b, tol=1e-8):
    assert len(a) == len(b) and all(math.isclose(x, y, abs_tol=tol, rel_tol=tol)
                                    for x, y in zip(a, b)), (a, b)


def main():
    rng = random.Random(20261115)
    comparisons = 0
    for _ in range(200):
        n = rng.randrange(1, 6)
        mu = [rng.random() for _ in range(n)]
        lower = [m * rng.uniform(0, .2) for m in mu]
        upper = [rng.uniform(a, m) for a, m in zip(lower, mu)]
        k = max(1, math.ceil(sum(lower)))
        L, U = bounds(mu, lower, upper, k)
        scores = [rng.uniform(-2, 3) for _ in mu]
        tau = rng.uniform(.05, 2)
        for A, B in [(L, U), ((L + U) / 2, (L + U) / 2)]:
            c = allocate(scores, lower, upper, A, B, tau)
            close(c, enumerate_faces(scores, lower, upper, A, B, tau))
            comparisons += 1
    # Hand calculation, absence, zero neutrality, and fixed passing.
    close(allocate([-2, 1, .8], [.25, 0, 0], [1, 1, 1], 1, 2, 1), [.25, .975, .775])
    close(allocate([1, .8], [0, 0], [1, 1], 1, 2, 1), [1, .8])
    close(allocate([-2, 1, .8, 100], [.25, 0, 0, 0], [1, 1, 1, 0], 1, 2, 1), [.25, .975, .775, 0])
    close(allocate([-100], [.03], [.03], .03, .03, 1), [.03])
    close(allocate([], [], [], 0, 0, 1), [])
    close(allocate([100], [0], [0], 0, 0, 1), [0])
    # The old constrained low-total branch has no score dependence.
    mu = [.1, .2, .3]
    L, U = bounds(mu, [0] * 3, mu, 1)
    close(allocate([-2, 50, 4], [0] * 3, mu, L, U, .2), mu)
    # Four-hub floors are feasible for every corner of the receipt cube.
    for mu in product((0, 1), repeat=4):
        lower = [m / 4 for m in mu]
        upper = [min(m, .5 * 2) for m in mu]
        bounds(mu, lower, upper, 2)
    # The old inequality-only D_v admitted this tuple at every hub, although
    # four copies have no feasible regional allocation with k=2.
    invalid = (1, 1, 0, 1, 1)
    assert not in_description_space(invalid, 'floor_cap', 2, beta=.25, alpha=.5)
    assert in_description_space((1, 1, 0, .25, 1), 'floor_cap', 2, beta=.25, alpha=.5)
    # Check a product of the corrected role-specific spaces, including missing
    # candidates, capped hubs, fixed passing and weak/zero receipt coordinates.
    role_specs = [('pass', 1, 1), ('floor_cap', .25, .2), ('ordinary', 0, 1)]
    for mu in product((0, .125, .5, 1), repeat=3):
        for present in product((False, True), repeat=3):
            ds = []
            for m, active, (kind, beta, alpha) in zip(mu, present, role_specs):
                if not active:
                    continue
                lo = m if kind == 'pass' else beta*m
                hi = min(m, alpha*2) if kind == 'floor_cap' else m
                d = (m/2, m, -1, lo, hi)
                assert in_description_space(d, kind, 2, beta=beta, alpha=alpha)
                ds.append(d)
            L, U = bounds([d[1] for d in ds], [d[3] for d in ds], [d[4] for d in ds], 2)
            c = allocate([d[2] for d in ds], [d[3] for d in ds], [d[4] for d in ds], L, U, 1)
            assert L-1e-10 <= sum(c) <= U+1e-10
    try:
        bounds([1, 1], [1, 1], [1, 1], 1)
    except ValueError:
        pass
    else:
        raise AssertionError('invalid all-pass budget was accepted')
    # Smooth equality branch: one lower, two free, one upper coordinate.
    t, lo, hi, B, tau = [-.5, .8, 1.1, 3], [.15, .05, .1, .02], [.7, .8, .9, .5], 1.7, .7
    c = allocate(t, lo, hi, B, B, tau)
    assert c[0] == lo[0] and c[3] == hi[3] and all(lo[i] < c[i] < hi[i] for i in (1, 2))
    errors = []
    for _ in range(40):
        dt, dl, du = ([rng.uniform(-.1, .1) for _ in t] for _ in range(3))
        dB, dtau = rng.uniform(-.1, .1), rng.uniform(-.1, .1)
        dlam = (sum(dt[i] - c[i] * dtau for i in (1, 2)) + tau * (dl[0] + du[3] - dB)) / 2
        expected = [dl[0], (dt[1] - dlam - c[1] * dtau) / tau,
                    (dt[2] - dlam - c[2] * dtau) / tau, du[3]]
        eps = 1e-5
        def moved(sign):
            return allocate([x + sign * eps * dx for x, dx in zip(t, dt)],
                            [x + sign * eps * dx for x, dx in zip(lo, dl)],
                            [x + sign * eps * dx for x, dx in zip(hi, du)],
                            B + sign * eps * dB, B + sign * eps * dB, tau + sign * eps * dtau)
        plus, minus = moved(1), moved(-1)
        actual = [(a - b) / (2 * eps) for a, b in zip(plus, minus)]
        close(actual, expected, tol=2e-8)
        errors.append(max(abs(a - b) for a, b in zip(actual, expected)))
    print(f'PASS: {comparisons} independent face comparisons; role-domain counterexample and 512 product/subset checks; '
          'zero/absence/pass/feasibility/reduction checks; '
          f'40 smooth derivative directions, max error {max(errors):.3g}')


if __name__ == '__main__':
    main()
