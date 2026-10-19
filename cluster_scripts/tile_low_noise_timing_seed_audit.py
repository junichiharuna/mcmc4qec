"""Connect new fixed timing allocations to the entire previous seed catalog.

These are pure planning and numerical gates, not PBS/native approval. The caller
must separately pin accepted baseline evidence and result bytes, bind sources and
input files, run the full combined census, and verify its completed PBS job.
"""
from pathlib import Path

import calibration as c
import tile_seed_audit as old
import tile_low_noise_timing_plan as plans

BASELINE_TOTAL=3963562
BASELINE_NAMESPACES=56
INTENTIONAL_SHARED=8448


def entries(plan):
    """Enumerate allocated RNG seeds, including explicitly unconsumed purposes."""
    role=plans._role(plan)
    for task in plans.tasks(plan):
        if ".mc." in role:
            yield old.Entry(role+".sample",plans.seed_coordinates(plan,task,0,0,0),0)
            continue
        for purpose,label in ((0,"anchor"),(3,"bootstrap")):
            yield old.Entry(role+"."+label,plans.seed_coordinates(plan,task,0,0,purpose),purpose)
        row=next(row for row in plan["rows"] if (row["case"],row["target_index"],row["epsilon_index"])==task[:3])
        for rung in range(len(row["rungs"])):
            for chain in range(row["condition"]["chains"]):
                for purpose,label in ((1,"initialization"),(2,"sample")):
                    yield old.Entry(role+"."+label,plans.seed_coordinates(plan,task,rung,chain,purpose),purpose)


def planned_counts(plan):
    """Independent formula count; does not enumerate or generate RNG seeds."""
    role=plans._role(plan);rep=plan["replicates"]
    ready=[row for row in plan["rows"] if row["planning_status"]=="ready"]
    if ".mc." in role:return {role+".sample":rep*len(ready)}
    pairs=sum(len(row["rungs"])*row["condition"]["chains"] for row in ready)
    return {role+".anchor":rep*len(ready),role+".bootstrap":rep*len(ready),
            role+".initialization":rep*pairs,role+".sample":rep*pairs}


def _full_result(result,total,role_counts,shared):
    numbers={"planned_entries":total,"checked_entries":total,"unchecked_entries":0,
        "unexpected_collisions":0,"intentional_shared_entries":shared,"unique_seeds":total-shared}
    if any(type(result.get(k)) is not int or result[k]!=v for k,v in numbers.items()):
        raise ValueError("complete census counts/collisions differ")
    actual=result.get("checked_counts")
    if (result.get("complete") is not True or not isinstance(actual,dict) or
            any(type(v) is not int or v<0 for v in actual.values()) or
            {k:v for k,v in actual.items() if v}!={k:v for k,v in role_counts.items() if v}):
        raise ValueError("full census role counts differ")
    plans.require_hash(result.get("stream_sha256"))


def extend_catalog(legacy_factories,legacy_evidence,bundle,*,baseline_evidence_sha256,
                   baseline_result,baseline_result_sha256,expected_registry_digest):
    """Preserve all old factories; caller supplies externally pinned baseline.

The baseline result is required for old role counts, which cannot be inferred
from catalog namespace totals. This function does not run those factories.
    Pin arguments are canonical JSON object SHA256 digests. The persisted caller
    must first pin the original file bytes; normalized copies are not authority.
"""
    if c.digest(legacy_evidence)!=plans.require_hash(baseline_evidence_sha256):
        raise ValueError("baseline catalog evidence pin differs")
    if c.digest(baseline_result)!=plans.require_hash(baseline_result_sha256):
        raise ValueError("baseline full result pin differs")
    counts=legacy_evidence.get("planned_counts",{})
    if (len(legacy_factories)!=BASELINE_NAMESPACES or set(legacy_factories)!=set(counts) or
            any(not callable(factory) for factory in legacy_factories.values()) or
            any(type(v) is not int or v<0 for v in counts.values()) or sum(counts.values())!=BASELINE_TOTAL or
            legacy_evidence.get("planned_total")!=BASELINE_TOTAL or
            legacy_evidence.get("master_seed")!=plans.t.MASTER or
            legacy_evidence.get("reserved_unenumerated_stages")!={} or
            set(legacy_evidence.get("plan_sha256",{}))!=set(counts)):
        raise ValueError("entire fixed 56 namespace baseline required")
    for name in ("input_sha256","source_sha256","plan_sha256"):
        plans._pin_map(legacy_evidence[name])
    roles=baseline_result.get("checked_counts",{})
    if (not roles or any(type(v) is not int or v<0 for v in roles.values()) or
            sum(roles.values())!=BASELINE_TOTAL):raise ValueError("complete baseline role counts required")
    _full_result(baseline_result,BASELINE_TOTAL,roles,INTENTIONAL_SHARED)
    plans.validate_plans(bundle,expected_registry_digest=expected_registry_digest)
    factories=dict(legacy_factories);counts=dict(counts);role_counts=dict(roles)
    source=dict(legacy_evidence["source_sha256"])
    for path,digest in {str(Path(__file__).resolve()):c.file_hash(__file__),
                        str(Path(old.__file__).resolve()):c.file_hash(old.__file__)}.items():
        if path in source and source[path]!=digest:raise ValueError("baseline census source changed")
        source[path]=digest
    for role,plan in bundle["plans"].items():
        if role in factories:raise ValueError("duplicate new catalog namespace")
        pc=planned_counts(plan)
        if sum(pc.values())!=plan["planned_seed_entries"]:raise ValueError("planned allocation count differs")
        if set(pc)&set(role_counts):raise ValueError("new seed role already present")
        factories[role]=lambda plan=plan:entries(plan)
        counts[role]=sum(pc.values());role_counts.update(pc)
        for path,digest in plan["source_sha256"].items():
            if path in source and source[path]!=digest:raise ValueError("shared source hash differs")
            source[path]=digest
    proof=dict(schema=1,purpose="extended_low_noise_timing_seed_catalog",master_seed=plans.t.MASTER,
        baseline_evidence_sha256=baseline_evidence_sha256,baseline_result_sha256=baseline_result_sha256,
        baseline_input_sha256=legacy_evidence["input_sha256"],baseline_plan_sha256=legacy_evidence["plan_sha256"],
        source_sha256=source,selection_sha256=bundle["selection_sha256"],selection_digest=c.digest(bundle["selection"]),
        registry_digest=c.digest(bundle["registry"]),timing_bundle_digest=c.digest(bundle),
        new_plan_sha256={role:c.digest(plan) for role,plan in bundle["plans"].items()},
        new_planned_row_counts={role:{"/".join(str(row[key]) for key in ("case","target_index","epsilon_index")):row["planned_seed_entries"]
            for row in plan["rows"]} for role,plan in bundle["plans"].items()},
        planned_counts=counts,planned_role_counts=role_counts,planned_total=sum(counts.values()),
        expected_intentional_shared_entries=INTENTIONAL_SHARED,reserved_unenumerated_stages={},
        submission_authorized=False,raw_inputs_rehashed=False,warning=plans.WARNING)
    return factories,proof


def complete_census_gate(result,evidence,*,expected_evidence_sha256):
    """Check exact full combined numerical census; never authorize submission."""
    if c.digest(evidence)!=plans.require_hash(expected_evidence_sha256):
        raise ValueError("combined census evidence pin differs")
    if (evidence.get("purpose")!="extended_low_noise_timing_seed_catalog" or
            len(evidence.get("planned_counts",{}))!=60 or
            not set(plans.STAGES)<=set(evidence["planned_counts"]) or
            evidence.get("reserved_unenumerated_stages")!={} or
            evidence.get("expected_intentional_shared_entries")!=INTENTIONAL_SHARED):
        raise ValueError("combined complete catalog required")
    total=evidence["planned_total"]
    if (type(total) is not int or any(type(v) is not int or v<0 for v in evidence["planned_counts"].values()) or
            any(type(v) is not int or v<0 for v in evidence["planned_role_counts"].values()) or
            sum(evidence["planned_counts"].values())!=total or
            sum(evidence["planned_role_counts"].values())!=total):
        raise ValueError("planned census counts differ")
    _full_result(result,total,evidence["planned_role_counts"],INTENTIONAL_SHARED)
    return dict(full_allocation_census_consistent=True,evidence_sha256=expected_evidence_sha256,
        result_digest=c.digest(result),submission_authorized=False,
        terminal_native_source_input_verification_required=True,warning=plans.WARNING)
