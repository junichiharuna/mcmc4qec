"""Pure low-noise timing plans; no persistence, execution or submission approval.

Saved selector bytes must be externally accepted. Reading a pinned selector does
not rescan its raw input census or replace terminal/native/PBS verification.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import itertools
import math
from pathlib import Path
import re

import calibration as c
import tile_study as t
import tile_low_noise_study as low
import tile_low_noise_summary as summary
import tile_low_noise_timing_selection as selector

STAGES={"low_timing.mc.benchmark":160,"low_timing.mc.capacity":161,
        "low_timing.bar.benchmark":162,"low_timing.bar.capacity":163}
KERNELS={"ZH":0,"ZHS":1}
INITIALIZATIONS={"logical_basis":0,"logical_combination":1}
HASH=re.compile(r"[0-9a-f]{64}")
WARNING=("Planning primitives only. No sampling, full seed census, terminal/native verification or submission authorization. "
         "Finite seed uniqueness does not prove stream independence. Capacity uses full estimator dimensions, not evaluation data.")


def require_hash(value):
    if not isinstance(value,str) or HASH.fullmatch(value) is None:
        raise ValueError("SHA256 required")
    return value


def _pin_map(value):
    if not isinstance(value,dict) or not value or any(not isinstance(k,str) or not k for k in value):
        raise ValueError("nonempty source/input pin mapping required")
    for digest in value.values():require_hash(digest)


def registry(selection_digest):
    """Reserve four stages for one immutable selection, not arbitrary revisions."""
    require_hash(selection_digest)
    return dict(schema=1,purpose="low_noise_timing_seed_registry",selection_digest=selection_digest,
        master_seed=t.MASTER,seed_version=1,stages=dict(STAGES),kernel_ids=dict(KERNELS),
        initialization_ids=dict(INITIALIZATIONS),mc_purposes={"sample":0},
        bar_purposes={"anchor":0,"initialization":1,"sample":2,"bootstrap":3},
        mc_coordinates=["stage","case","target_index","epsilon_index","replicate"],
        bar_coordinates=["stage","case","target_index","epsilon_index","replicate","kernel_id","init_id","rung","chain"],
        seed_source_sha256=c.file_hash(t.__file__),registry_source_sha256=c.file_hash(__file__),
        intentional_new_role_sharing=False)


def mc_budget(interval,epsilon_index):
    """Use exact decimal-spelling arithmetic, retaining huge integer budgets."""
    if type(epsilon_index) is not int or epsilon_index not in (0,1):
        raise ValueError("fixed epsilon index required")
    if (not isinstance(interval,(list,tuple)) or len(interval)!=2 or
            any(type(x) not in (int,float) or not math.isfinite(x) for x in interval) or
            not 0<interval[0]<=interval[1]<=1):
        raise ValueError("positive finite full reference interval required")
    lower=Fraction(str(interval[0]));epsilon=(Fraction(1,5),Fraction(1,10))[epsilon_index]
    rational=(1-lower)/(lower*epsilon**2)
    raw=-(-rational.numerator//rational.denominator)
    trials=64*((raw+63)//64)
    return dict(formula="lower_bound_bernoulli_rmse_64_v1",reference_interval=list(interval),
        epsilon_index=epsilon_index,epsilon=float(epsilon),lower_decimal=str(interval[0]),
        unrounded_trials=raw,trials=trials,
        planning_status="ready" if trials else "ineligible_degenerate_reference",
        conditional_population_budget=True,empirical_precision_guaranteed=False)


def read_selection(path,expected_sha256):
    """Read one externally pinned snapshot; do not scan large raw inputs."""
    import json
    path=Path(path).absolute();target=path.resolve()
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=require_hash(expected_sha256):
        raise ValueError("selection external SHA256 differs")
    report=json.loads(raw)
    if report.get("source_sha256")!=selector.source_hashes():
        raise ValueError("selector source closure differs")
    if path.resolve()!=target or c.file_hash(path)!=expected_sha256:
        raise ValueError("selection snapshot changed")
    return report,dict(selection_sha256=expected_sha256,selection_digest=c.digest(report),
        resolved_path=str(target),raw_inputs_rehashed=False,submission_authorized=False,warning=WARNING)


def _validate_selection(selection):
    if (selection.get("schema")!=1 or selection.get("purpose")!="low_noise_independent_timing_selection" or
            selection.get("conditions")!=24 or selection.get("production_selection_validated") is not True or
            any(selection.get(k) is not False for k in ("independent_timing_performed","population_rmse_certified","nominal_coverage_certified"))):
        raise ValueError("complete validated selector envelope required")
    require_hash(selection["input_manifest_sha256"])
    _pin_map(selection["input_sha256"]);_pin_map(selection["source_sha256"])
    if (set(selection.get("input_resolved",{}))!=set(selection["input_sha256"]) or
            any(not isinstance(v,str) or not v for v in selection["input_resolved"].values())):
        raise ValueError("selector input resolution bindings required")
    if selection["source_sha256"]!=selector.source_hashes():
        raise ValueError("selector source closure differs")
    rows=selection["rows"]
    expected=list(selector.identities())
    coordinates=[tuple(row.get(k) for k in ("case","target_index","epsilon_index")) for row in rows]
    if coordinates!=expected or any(type(x) is not int for coord in coordinates for x in coord):
        raise ValueError("exact ordered 24 selection identities required")
    bindings=selection["calibration_bindings"]
    if len(bindings)!=12:raise ValueError("all twelve calibration bindings required")
    plans={}
    for index,(case,target) in enumerate(itertools.product(range(4),range(3))):
        plan=low.make_plan(case,target,capacity=False)
        plans[(case,target)]=plan
        binding=bindings[index];pair=rows[2*index:2*index+2]
        if (binding.get("manifest")!=c.digest(plan) or
                c.canonical(binding.get("expected_conditions"))!=c.canonical(list(summary.expected_conditions(plan))) or
                binding.get("reference_interval")!=pair[0]["reference_interval"] or
                pair[0]["reference_interval"]!=pair[1]["reference_interval"]):
            raise ValueError("fixed calibration manifest/grid/reference binding differs")
        for key in ("analysis","reference_context","reference_audit_digest","audited_collection_digest"):
            require_hash(binding[key])
        if type(binding.get("reference_condition")) is not int or binding["reference_condition"]<0:
            raise ValueError("reference condition identity required")
        if not binding.get("terminals"):raise ValueError("upstream terminal evidence required")
        for terminal in binding["terminals"]:
            require_hash(terminal["ledger_sha256"])
            if (not isinstance(terminal.get("job_id"),str) or
                    re.fullmatch(r"\d+(?:\.[A-Za-z0-9_.-]+)?",terminal["job_id"]) is None or
                    type(terminal.get("exit_status")) is not int):
                raise ValueError("upstream terminal identity differs")
        for item in pair[0]["candidates"]:
            cfg=item["condition"]
            if (set(cfg)!=set(summary.CONDITION) or
                    any(type(cfg[key]) is not int for key in ("case","chains","burn","samples")) or
                    (cfg["block"] is not None and type(cfg["block"]) is not int)):
                raise ValueError("exact typed candidate condition required")
        compared=dict(replicates=192,reference_available=pair[0]["reference_interval"] is not None,
            reference=None if pair[0]["reference_interval"] is None else dict(interval=pair[0]["reference_interval"]),
            conditions=[dict(item["condition"],assessment=item["assessment"]) for item in pair[0]["candidates"]])
        rebuilt=selector.choose(plan,compared)
        for observed,wanted in zip(pair,rebuilt):
            if c.canonical({key:observed.get(key) for key in wanted})!=c.canonical(wanted):
                raise ValueError("selected setting, rank, cohort or status differs from full candidate policy")
    return plans


def make_plans(selection,*,selection_sha256):
    """Return four in-memory plans; external pin acceptance is a caller boundary."""
    require_hash(selection_sha256)
    production=_validate_selection(selection)
    reg=registry(c.digest(selection));rows=[]
    for original in selection["rows"]:
        case,target=original["case"],original["target_index"]
        source=production[(case,target)];spec=source["condition"]
        row={k:deepcopy(original[k]) for k in ("case","target_index","epsilon_index","epsilon","target_p","status","selected_condition","reference_interval")}
        row.update(selection_row_digest=c.digest(original),planning_status="not_selected")
        if original["status"]=="selected":
            budget=mc_budget(original["reference_interval"],original["epsilon_index"])
            cfg=deepcopy(original["selected_condition"])
            rungs=spec["coarse"] if cfg["ladder"]=="coarse" else spec["rungs"]
            row.update(planning_status=budget["planning_status"],condition=cfg,mc_budget=budget,
                size=spec["size"],noise=spec["noise"],rungs=list(rungs),fine_rung_indices=[spec["rungs"].index(v) for v in rungs],
                initialization_stride=spec["chains"],anchor_trials=source["anchor_trials"],
                bootstrap_replicates=source["bootstrap_replicates"],cache_cap=source["cache_cap"],
                decoder=deepcopy(source["decoder"]),kernels=deepcopy(source["kernels"]),
                production_manifest=c.digest(source),runtime=deepcopy(source["runtime"]),
                native_input_digests=deepcopy(source["native_input_digests"]),required_threads=deepcopy(source["required_threads"]))
        rows.append(row)
    plans={}
    for role,stage in STAGES.items():
        cap=role.endswith("capacity");replicates=2 if cap else 192
        number=0
        for row in rows:
            if row["planning_status"]=="ready":
                number+=replicates*(1 if ".mc." in role else 2+2*len(row["rungs"])*row["condition"]["chains"])
        role_rows=deepcopy(rows)
        for row in role_rows:
            factor=0 if row["planning_status"]!="ready" else (1 if ".mc." in role else 2+2*len(row["rungs"])*row["condition"]["chains"])
            row["planned_seed_entries"]=replicates*factor
        plans[role]=dict(schema=1,purpose=role,seed_stage=stage,master_seed=t.MASTER,seed_version=1,
            replicates=replicates,capacity_workers=2 if cap else None,rows=role_rows,
            selection_digest=c.digest(selection),selection_sha256=selection_sha256,registry_digest=c.digest(reg),
            source_sha256={str(Path(__file__).resolve()):c.file_hash(__file__),**selection["source_sha256"]},
            planned_seed_entries=number,warning=WARNING)
    if (selection["source_sha256"]!=selector.source_hashes() or
            reg["registry_source_sha256"]!=c.file_hash(__file__)):
        raise ValueError("source changed during plan construction")
    return dict(schema=1,purpose="low_noise_timing_plans",selection=deepcopy(selection),
        selection_sha256=selection_sha256,registry=reg,plans=plans,submission_authorized=False)


def validate_plans(bundle,*,expected_registry_digest):
    if c.digest(bundle["registry"])!=require_hash(expected_registry_digest):
        raise ValueError("externally fixed registry differs; stage reuse is forbidden")
    expected=make_plans(bundle["selection"],selection_sha256=bundle["selection_sha256"])
    if c.canonical(bundle)!=c.canonical(expected):
        raise ValueError("registry, scientific plan, or fixed selection changed")
    return expected


def _role(plan):
    role=plan["purpose"]
    if (role not in STAGES or type(plan["seed_stage"]) is not int or plan["seed_stage"]!=STAGES[role] or
            plan["master_seed"]!=t.MASTER or type(plan["seed_version"]) is not int or plan["seed_version"]!=1 or
            type(plan["replicates"]) is not int or plan["replicates"]!=(2 if role.endswith("capacity") else 192)):
        raise ValueError("unregistered role, stage, or replicate count")
    return role


def tasks(plan):
    """Yield stable identity tuples, independent of partition and worker count."""
    _role(plan)
    for row in plan["rows"]:
        if row["planning_status"]=="ready":
            for rep in range(plan["replicates"]):
                yield row["case"],row["target_index"],row["epsilon_index"],rep


def seed_coordinates(plan,task,rung,chain,purpose):
    role=_role(plan)
    if (len(task)!=4 or any(type(x) is not int or x<0 for x in (*task,rung,chain,purpose)) or
            task[0]>=4 or task[1]>=3 or task[2]>=2 or task[3]>=plan["replicates"]):
        raise ValueError("task outside fixed identity")
    rows=[row for row in plan["rows"] if (row["case"],row["target_index"],row["epsilon_index"])==tuple(task[:3])]
    if len(rows)!=1 or rows[0]["planning_status"]!="ready":raise ValueError("no unique selected task")
    if ".mc." in role:
        if any((rung,chain,purpose)):raise ValueError("MC uses purpose/rung/chain zero")
        return (plan["seed_stage"],*task)
    row=rows[0];cfg=row["condition"]
    if purpose not in range(4) or (purpose in (0,3) and (rung or chain)):
        raise ValueError("BAR reserved coordinate or purpose differs")
    if rung>=len(row["rungs"]) or chain>=cfg["chains"]:raise ValueError("rung/chain outside estimator")
    return (plan["seed_stage"],*task,KERNELS[cfg["kernel"]],INITIALIZATIONS[cfg["init"]],rung,chain)


def task_seed(plan,task,rung,chain,purpose):
    return t.seed(seed_coordinates(plan,task,rung,chain,purpose),purpose)


def logical_index(row,rep,chain):
    if (type(rep) is not int or not 0<=rep<192 or type(chain) is not int or
            not 0<=chain<row["condition"]["chains"] or row["initialization_stride"]!=(16 if row["case"]==0 else 8)):
        raise ValueError("fixed production logical index required")
    return rep*row["initialization_stride"]+chain
