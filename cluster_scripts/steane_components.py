"""Exact, post-hoc explanation of the fixed-prior Steane initialization effect."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from mcmc4qec.kernels import Zanella, ClusterExchange, StabilizerFlip
import calibration as c


def components(matrix):
    unseen, groups = set(range(len(matrix))), []
    while unseen:
        todo = [min(unseen)]
        group = set(todo)
        unseen.difference_update(group)
        while todo:
            i = todo.pop()
            for j in np.flatnonzero(matrix[i] > 0):
                if int(j) in unseen:
                    unseen.remove(int(j))
                    group.add(int(j))
                    todo.append(int(j))
        groups.append(sorted(group))
    return groups


def transition(probabilities, target, mixture, lazy=.05):
    matrix = np.zeros((len(target), len(target)))
    for weight, proposal in zip(mixture, probabilities):
        flux = np.minimum(target[:, None]*proposal, target[None, :]*proposal.T)
        matrix += (1-lazy)*weight*flux/target[:, None]
    # Include rejected moves to nonfailure states and all proposal self-loops.
    np.fill_diagonal(matrix, 0)
    matrix[np.diag_indices(len(target))] = 1-matrix.sum(axis=1)
    return matrix


def analyze():
    bank = c.enumerate_bank(2)
    _, problem = c.problem_for(2)
    states = c.unpack(bank["index"], 7)
    kernels = [Zanella(), ClusterExchange(2), StabilizerFlip()]
    checks, partition = [], None
    for p in (.1, .03, .0001):
        target = np.array([math.exp(problem.log_prob(state, p)) for state in states])
        target /= target.sum()
        probabilities = [np.array([[kernel.probability(a, b, problem, p) for b in states] for a in states]) for kernel in kernels]
        for name, mixture in [("Z0.7_H0.3", (.7, .3, 0.)), ("Z0.6_H0.3_S0.1", (.6, .3, .1))]:
            matrix = transition(probabilities, target, mixture)
            groups = components(matrix)
            flux = target[:, None]*matrix
            checks.append(dict(p=p, mixture=name, components=len(groups),
                               minimum_self_loop=float(np.diag(matrix).min()),
                               row_sum_error=float(np.abs(matrix.sum(1)-1).max()),
                               detailed_balance_error=float(np.abs(flux-flux.T).max()),
                               stationarity_error=float(np.abs(target@matrix-target).max())))
            if name == "Z0.7_H0.3":
                if partition is not None and partition != groups:
                    raise ValueError("support unexpectedly depends on positive noise rate")
                partition = groups
    partition = sorted(partition, key=lambda g: min(bank["weight"][g]))
    counts = [np.bincount(bank["weight"][group], minlength=8) for group in partition]
    component_records = [dict(size=len(group), indices=bank["index"][group].tolist(), weight_counts=count.tolist())
                         for group, count in zip(partition, counts)]
    starts = c.dispersed_indices(bank, 4)
    ids = [next(i for i, group in enumerate(partition) if start in bank["index"][group]) for start in starts]
    masses = []
    for p in sorted(set(sum([list(ladder) for ladder in c.LADDERS], [])), reverse=True):
        densities = p**np.arange(8)*(1-p)**(7-np.arange(8))
        total = c.failure_mass(bank, 7, p)
        masses.append(dict(p=p, conditional_component_mass=[float(np.dot(count, densities)/total) for count in counts]))
    limits = []
    for ladder in c.LADDERS:
        component_histograms, pooled = [], []
        for p in ladder:
            densities = p**np.arange(8)*(1-p)**(7-np.arange(8))
            normalized = [count*densities/np.dot(count, densities) for count in counts]
            component_histograms.append(normalized)
            pooled.append(np.mean([normalized[i] for i in ids], axis=0))
        edge = [float(c.histogram_bar(a, b, c.log_density_difference(7, p, q)))
                for a, b, p, q in zip(pooled, pooled[1:], ladder, ladder[1:])]
        estimate = c.failure_mass(bank, 7, ladder[0])*math.exp(sum(edge))
        truth = c.failure_mass(bank, 7, ladder[-1])
        chain_ratios = [[float(c.histogram_bar(a[i], b[i], c.log_density_difference(7, p, q)))
                         for a, b, p, q in zip(component_histograms, component_histograms[1:], ladder, ladder[1:])] for i in ids]
        covariance = np.atleast_2d(np.cov(chain_ratios, rowvar=False, ddof=1))/4
        se = math.sqrt(float(covariance.sum()))
        limits.append(dict(ladder=list(ladder), estimate=estimate, truth=truth, relative_bias=estimate/truth-1,
                           cross_chain_log_se=se,
                           cross_chain_interval=[estimate*math.exp(-1.959963984540054*se), min(1., estimate*math.exp(1.959963984540054*se))]))
    return dict(decoder=problem.decoder.metadata(), failure_weight_counts=np.bincount(bank["weight"], minlength=8).tolist(),
                components=component_records, dispersed_starts=starts, dispersed_component_ids=ids,
                component_masses=masses, checks=checks, dispersed_bar_limits=limits,
                interpretation="No weight-five faulty states separate weights 2-4 from 6-7. Z changes weight by one; H preserves it. Lazy ensures aperiodicity, not irreducibility. The stabilizer mixture is a finite-support candidate only; defaults remain unchanged.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = analyze()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(dict(components=[g["size"] for g in result["components"]], limits=result["dispersed_bar_limits"])))
