"""Physical fault baseline with a midpoint rotated-surface logical idle."""
from mcmc4qec.circuit import surface_logical_idle_problem
from mcmc4qec.sampling import direct_mc


def main():
    p = .01
    problem = surface_logical_idle_problem(distance=3, decoder_p=p, basis="Z")
    result = direct_mc(problem, p, trials=500, seed=2026)
    print(f"locations={problem.model.n}; detectors={problem.model.H.shape[0]}")
    print(f"midpoint logical-Z failure={result.estimate:.5f}; "
          f"Wilson 95% interval={result.interval}; trials={result.trials}")


if __name__ == "__main__":
    main()
