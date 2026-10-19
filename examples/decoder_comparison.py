"""Compare fixed-prior CSS decoders with bounded direct MC and small-code exact.

Requires mcmc4qec[bposd]; toric also requires [codes], and --mwpm [matching].
Standalone Union-Find currently requires ldpc==2.4.1. This is a usage example,
not a decoder ranking, performance benchmark, or interval-coverage study.
"""
import argparse
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import platform
import tempfile

import numpy as np

from mcmc4qec import IndependentBitFlip, Problem, direct_mc, exact
from mcmc4qec.codes import make_steane_code, make_tile_code, make_toric_code
from mcmc4qec.decoders import bposd_decoder, mwpm_decoder
from mcmc4qec.bplsd_decoders import bplsd_decoder
from mcmc4qec.belief_find_decoders import belief_find_decoder
from mcmc4qec.union_find_decoders import union_find_decoder


def output_dir(value):
    """Keep generated results outside the read-only research checkout."""
    path = Path(value).expanduser().resolve()
    roots = [Path("A:/dev/RIMC"), Path("C:/dev/RIMC")]
    roots.extend(Path(os.environ[key]) for key in ("RIMC_RESEARCH_ROOT", "RESEARCH_ROOT")
                 if os.environ.get(key))
    for root in roots:
        resolved = root.resolve()
        if path == resolved or resolved in path.parents:
            raise ValueError("output directory cannot be inside the research repository")
    path.mkdir(parents=True, exist_ok=True)
    return path


class CheckedBposdBaseline:
    """Check physical BP-OSD corrections before assigning a logical outcome."""

    def __init__(self, code, prior):
        adapter = bposd_decoder(
            code, prior, osd_method="osd_0", osd_order=0, max_iter=100,
            bp_method="min_sum", ms_scaling_factor=1., schedule="parallel",
            omp_thread_count=1, random_schedule_seed=0,
            input_vector_type="syndrome")
        self.decoder = adapter.decoder
        self.decoder.random_serial_schedule = False
        if self.decoder.random_serial_schedule:
            raise ValueError("BP-OSD backend did not disable random scheduling")
        self.code = code
        self._metadata = adapter.metadata()
        self._metadata["settings"]["random_serial_schedule"] = False

    def predict(self, syndrome):
        # Problem supplies realizable binary syndromes from this fixed code.
        syndrome = np.asarray(syndrome)
        correction = np.asarray(self.decoder.decode(syndrome.copy()))
        if (correction.shape != (self.code.n,) or
                not np.all((correction == 0) | (correction == 1))):
            raise ValueError("BP-OSD returned an invalid binary correction")
        correction = correction.astype(np.uint8)
        if not np.array_equal(self.code.hz @ correction % 2, syndrome):
            raise ValueError("BP-OSD correction does not reproduce syndrome")
        return self.code.lz @ correction % 2

    def metadata(self):
        return {**self._metadata, "example_syndrome_consistency_checked": True,
                "invalid_correction_policy": "raise"}


def make_decoders(code, code_name, prior, *, mwpm=False):
    """Build each fixed decoder once; no sampling parameter changes its prior."""
    decoders = {
        "bp_osd_0": CheckedBposdBaseline(code, prior),
        "bp_lsd_0": bplsd_decoder(code, prior),
        "belief_find_inversion": belief_find_decoder(code, prior),
    }
    if code_name == "toric":
        decoders["union_find_peeling"] = union_find_decoder(code, method="peeling")
        if mwpm:
            decoders["mwpm"] = mwpm_decoder(code)
    return decoders


def run(code_name="steane", *, quick=False, seed=20261018, mwpm=False):
    """Return a JSON-compatible report without writing files."""
    if mwpm and code_name != "toric":
        raise ValueError("--mwpm is supported only with --code toric")
    factories = {"steane": make_steane_code, "toric": lambda: make_toric_code(3),
                 "tile72": lambda: make_tile_code(6, 6)}
    code = factories[code_name]()
    p = prior = .08
    trials = 64 if quick else 512
    rows = []
    for name, decoder in make_decoders(code, code_name, prior, mwpm=mwpm).items():
        problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), decoder)
        reference = exact(problem, p) if code_name == "steane" else None
        # Shared seed gives common physical errors across decoder comparisons.
        mc = direct_mc(problem, p, trials=trials, seed=seed)
        rows.append(dict(name=name, planned_trials=trials,
                         direct_mc=json.loads(mc.to_json()),
                         exact=None if reference is None else json.loads(reference.to_json())))
    packages = {}
    for name in ("numpy", "scipy", "ldpc", "bposd", "pymatching", "mcmc4qec"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    return dict(schema_version=1, code=code_name, n=code.n, k=len(code.lz),
                noise="independent-bit-flip", sampling_p=p, decoder_prior=prior,
                seed=seed, common_random_numbers=True, decoders=rows,
                environment=dict(python=platform.python_version(), platform=platform.platform(),
                                 packages=packages),
                failure_definition="nonzero residual logical X after syndrome-consistent correction",
                limitations=["Short fixed-trial example; no decoder ranking or BAR calibration.",
                             "Same seed couples decoder comparisons; they are not independent experiments.",
                             "No cross-platform or all-input determinism guarantee.",
                             "Exact enumeration is restricted to Steane; other references are unavailable."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", choices=("steane", "toric", "tile72"), default="steane")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--seed", type=int, default=20261018)
    parser.add_argument("--mwpm", action="store_true")
    parser.add_argument("--out", type=Path,
                        default=Path(tempfile.gettempdir()) / "mcmc4qec" / "decoder_comparison")
    args = parser.parse_args()
    if args.mwpm and args.code != "toric":
        parser.error("--mwpm requires --code toric")
    out = output_dir(args.out)
    report = run(args.code, quick=args.quick, seed=args.seed, mwpm=args.mwpm)
    destination = out / "summary.json"
    destination.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for row in report["decoders"]:
        mc = row["direct_mc"]
        reference = row["exact"]
        print(f'{row["name"]}: failures={mc["failures"]}/{mc["trials"]}, '
              f'P_L={mc["estimate"]:.6g}, Wilson95%={mc["interval"]}, '
              f'exact={None if reference is None else reference["estimate"]}')
    print("Short usage example: no ranking, coverage, or cross-platform guarantee.")
    print(f"Output: {destination}")
    summary = {key: report[key] for key in ("code", "n", "k", "sampling_p", "decoder_prior", "seed")}
    summary["decoders"] = [dict(name=row["name"], trials=row["direct_mc"]["trials"],
                                failures=row["direct_mc"]["failures"],
                                pl=row["direct_mc"]["estimate"])
                           for row in report["decoders"]]
    print("SUMMARY " + json.dumps(summary, allow_nan=False))


if __name__ == "__main__":
    main()
