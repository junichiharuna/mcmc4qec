"""Package fingerprints cover nested circuit implementation sources."""
from mcmc4qec import BinaryLinearModel, CallableDecoder, IndependentBitFlip, Problem
from mcmc4qec import results


def test_fingerprint_includes_subpackages(monkeypatch, tmp_path):
    (tmp_path / "results.py").write_text("# root source\n", encoding="utf-8")
    nested = tmp_path / "circuit"
    nested.mkdir()
    source = nested / "model.py"
    source.write_text("# circuit version one\n", encoding="utf-8")
    monkeypatch.setattr(results, "__file__", str(tmp_path / "results.py"))
    problem = Problem(BinaryLinearModel([[1]], [[1]]), IndependentBitFlip(1),
                      CallableDecoder(lambda s: [0], identifier="zero"))
    first = results.metadata(problem, 0.1, {})
    source.write_text("# circuit version two\n", encoding="utf-8")
    second = results.metadata(problem, 0.1, {})
    assert first["package_source_sha256"] != second["package_source_sha256"]
    assert second["source_commit"] is None
    assert "not been committed" not in second["source_commit_reason"]
    source.rename(nested / "other.py")
    third = results.metadata(problem, 0.1, {})
    assert third["package_source_sha256"] != second["package_source_sha256"]
