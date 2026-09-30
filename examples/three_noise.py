"""Tiny categorical/spacetime examples with one fixed failure rule per ladder.

These deterministic reference decoders demonstrate contracts; they are not
claimed to be optimal. Short runs and their diagnostics do not prove mixing.
The bit-flip-only static example is in bit_flip.py.
"""
import numpy as np

from mcmc4qec import (
    CSSCode, CallableDecoder, DepolarizingModel, DepolarizingNoise,
    PhenomenologicalModel, PhenomenologicalNoise, Problem,
    KernelConfig, SamplingConfig, exact, direct_mc, sample_faulty,
    estimate_logical_error,
)
from mcmc4qec.adapter_composition import HistoryDecoder, SectorDecoder


def problems():
    code = CSSCode(np.zeros((0, 2), dtype=int), [[1, 1]], [[1, 1]], [[1, 0]])
    # X correction is assigned to qubit 0 when the parity check is one.
    # No Z syndrome exists for this repetition code; predict zero Z observable.
    sectors = SectorDecoder(
        CallableDecoder(lambda s: [int(s[0])], identifier="x-parity-to-qubit0-v1"),
        CallableDecoder(lambda s: [0], identifier="zero-z-observable-v1"),
        x_syndrome_size=1, identifier="independent-sectors-reference-v1",
    )
    yield "static depolarizing", Problem(DepolarizingModel(code), DepolarizingNoise(2), sectors), [0.3, 0.15]

    for data_noise in ("bit_flip", "depolarizing"):
        model = PhenomenologicalModel(
            code, 2, data_noise=data_noise, initial_boundary="clean",
            final_boundary="perfect", representation="history",
        )
        # Use every round: assign X correction to qubit 0 only when a strict
        # majority of recorded check outcomes are one. This deliberately simple
        # fixed rule is independent of data and measurement probabilities.
        def reference(history, kind=data_noise):
            x_prediction = int(np.count_nonzero(history) > history.size / 2)
            return [x_prediction] if kind == "bit_flip" else [x_prediction, 0]

        decoder = HistoryDecoder(
            CallableDecoder(reference, identifier=f"history-majority-{data_noise}-v1"),
            layout="history", identifier=f"all-rounds-{data_noise}-v1",
        )
        ladder = [{"data": 0.25, "measurement": 0.1}, {"data": 0.12, "measurement": 0.04}]
        yield f"phenomenological {data_noise}", Problem(model, PhenomenologicalNoise(model), decoder), ladder


def main():
    config = SamplingConfig(samples=500, burn_in=50, kernels=KernelConfig(cluster_k=1))
    for index, (name, problem, ladder) in enumerate(problems()):
        target = ladder[-1]
        reference = exact(problem, target)
        mc = direct_mc(problem, target, trials=2_000, seed=10 + index)
        conditional = sample_faulty(problem, target, config=config, seed=20 + index)
        bar = estimate_logical_error(
            problem, ladder, anchor=exact(problem, ladder[0]), config=config,
            bootstrap_replicates=20, seed=30 + index,
        )
        occupancy = np.count_nonzero(conditional.states, axis=-1).mean()
        print(f"{name}: target={target}")
        print(f"  Exact P_L={reference.estimate:.6f}; direct MC={mc.estimate:.6f}; Wilson95={mc.interval}")
        print(f"  E[occupied coordinates | faulty]: exact={reference.conditional_weight:.6f}, MCMC={occupancy:.6f}")
        print(f"  Fixed-failure BAR P_L={bar.estimate:.6f}; approximate interval={bar.interval}")
        print("  BAR uncertainty assumes mixing; 20 bootstrap replicates are only a smoke demonstration.")


if __name__ == "__main__":
    main()
