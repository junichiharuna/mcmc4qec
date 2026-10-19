"""Stream a finite planned-seed census, retaining incomplete namespace evidence.

This does not execute samplers or certify RNG-stream independence. Run the
default bounded pilot before --full; long censuses require a larger explicit
--max-seconds budget on the authorized execution environment.
"""
from dataclasses import dataclass
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import itertools
import json
from pathlib import Path
import sqlite3
import struct
import tempfile
import time

import calibration as c
import tile_study as t
import tile_bar_study as bar
import tile_reference as reference
import tile_weight_pilot as wp
import tile_weight_reference as wr
import tile_mc_time_benchmark as mc
import tile_low_noise_study as low


@dataclass(frozen=True)
class Entry:
    role: str
    coordinates: tuple
    purpose: int


def bootstrap_entries(plan, *, synthetic=False):
    """Mirror the pinned tile_bar_analysis.analyze_group coordinate loops."""
    role="synthetic.bootstrap" if synthetic else "calibration.bootstrap"
    for case,spec in enumerate(plan["cases"]):
        pairs=[(0,0)] if synthetic else itertools.product(range(2),range(2))
        for kernel,init in pairs:
            for rep,chains,burn,samples,ladder in itertools.product(
                    range(plan["replicates"]),sorted({4,spec["chains"]}),
                    plan["burns"],spec["windows"],range(2)):
                blocks=[v for v in plan["blocks"] if v<=samples and (v!=1024 or samples>=6000)]+[None]
                for block in blocks:
                    yield Entry(role,(33,case,kernel,init,rep,chains,burn,samples,ladder,block or 0),0)


def low_entries(plan, *, include_analysis=True):
    prefix=plan["purpose"]
    for task in low.tasks(plan):
        for purpose,label in ((0,"init"),(1,"sample")):
            yield Entry(prefix+"."+label,(plan["stages"]["sample"],*task),purpose)
    for task in low.tasks(plan,"anchors"):
        yield Entry(prefix+".anchor",(plan["stages"]["anchors"],*task),0)
    if include_analysis and plan["purpose"]=="low_noise_production":
        import tile_low_noise_analysis as analysis
        for kernel,init,rep in itertools.product(range(2),range(2),range(plan["replicates"])):
            group=(plan["case"],plan["target_index"],kernel,init,rep)
            for chains,burn,samples,ladder,label,values,block in analysis.analysis_settings(plan):
                coordinates=(plan["stages"]["analysis"],*group,chains,burn,samples,ladder,block or 0)
                # The source helper is checked on bounded witnesses by catalog().
                yield Entry(prefix+".bootstrap",coordinates,0)


def low_capacity_entries(plan):
    import tile_low_noise_analysis_capacity as capacity
    import tile_low_noise_analysis as analysis
    compute=capacity.compute_plan(plan)
    spec=compute["condition"]
    for group in capacity.groups(plan):
        for rung,chain in itertools.product(range(len(spec["rungs"])),range(spec["chains"])):
            yield Entry("low.synthetic.data",(plan["seed_stage"],*group,rung,chain),2)
        for chains,burn,samples,ladder,_,_,block in analysis.analysis_settings(compute):
            yield Entry("low.synthetic.bootstrap",(compute["stages"]["analysis"],*group,chains,burn,samples,ladder,block or 0),0)


def round_robin(streams):
    active=[iter(stream) for stream in streams]
    while active:
        following=[]
        for stream in active:
            item=next(stream,None)
            if item is not None:
                yield item
                following.append(stream)
        active=following


def census(entries, planned_count, database, *, limit=None, seed_function=t.seed):
    """Use an on-disk unique index; bound retained collision examples to 20."""
    database=Path(database)
    if database.exists():
        raise ValueError("new census database required")
    if planned_count<0 or (limit is not None and limit<1):
        raise ValueError("nonnegative planned count and positive limit required")
    started=time.perf_counter()
    checked=unexpected=shared=unique=0
    counts=Counter()
    examples=[]
    digest=hashlib.sha256()
    allowed={"calibration.bootstrap","synthetic.bootstrap"}
    with closing(sqlite3.connect(database)) as db:
        db.execute("PRAGMA journal_mode=OFF")
        db.execute("PRAGMA synchronous=OFF")
        db.execute("CREATE TABLE seeds (seed BLOB PRIMARY KEY, entropy TEXT, role TEXT) WITHOUT ROWID")
        db.execute("CREATE TABLE uses (seed BLOB, role TEXT, PRIMARY KEY(seed,role)) WITHOUT ROWID")
        for entry in itertools.islice(entries,limit):
            entropy=json.dumps([*entry.coordinates,entry.purpose],separators=(",",":"))
            seed=int(seed_function(entry.coordinates,entry.purpose))
            key=struct.pack("<Q",seed)
            old=db.execute("SELECT entropy,role FROM seeds WHERE seed=?",(key,)).fetchone()
            repeated=db.execute("SELECT 1 FROM uses WHERE seed=? AND role=?",(key,entry.role)).fetchone()
            if old is None:
                db.execute("INSERT INTO seeds VALUES (?,?,?)",(key,entropy,entry.role))
                unique+=1
            elif not repeated and old[0]==entropy and {old[1],entry.role}==allowed:
                shared+=1
            else:
                unexpected+=1
                if len(examples)<20:
                    examples.append(dict(seed=seed,first_role=old[1],role=entry.role,
                        first_input=json.loads(old[0]),input=json.loads(entropy),
                        kind="same_input_different_role" if old[0]==entropy and old[1]!=entry.role else
                             "duplicate_entry" if old[0]==entropy else "different_input_same_seed"))
            checked+=1
            db.execute("INSERT OR IGNORE INTO uses VALUES (?,?)",(key,entry.role))
            counts[entry.role]+=1
            digest.update(c.canonical([entry.role,*entry.coordinates,entry.purpose,seed])+b"\n")
            if checked%1000==0:
                db.commit()
        if checked>planned_count or (limit is None and checked!=planned_count):
            raise ValueError("stream does not match planned count")
        db.commit()
    return dict(planned_entries=planned_count,checked_entries=checked,
                unchecked_entries=planned_count-checked,complete=checked==planned_count,
                unique_seeds=unique,intentional_shared_entries=shared,unexpected_collisions=unexpected,
                checked_counts=dict(counts),collision_examples=examples,stream_sha256=digest.hexdigest(),
                seconds=time.perf_counter()-started,recorded_sampling_metadata_audited=False,
                warning="Finite planned seed uniqueness is not statistical independence or executed-metadata validation.")


def catalog(data, bar_timing_manifests=()):
    """Bind stored manifests and source; return fresh iterators, not sampled data."""
    data=Path(data)
    files={}
    sources={}
    plans={}
    reservations={140:"BAR timing selection manifest not supplied",141:"BAR timing capacity selection not supplied",
                  155:"Low-noise analysis capacity cohort undefined"}
    factories={}
    def read(name):
        path=data/name
        files[str(path.resolve())]=c.file_hash(path)
        return json.loads(path.read_text())
    def bind(module):
        sources[str(Path(module.__file__).resolve())]=c.file_hash(module.__file__)
    for module in (t,bar,reference,wp,wr,mc,low):
        bind(module)
    import tile_bar_analysis as analysis
    import tile_analysis_capacity as ac
    bind(analysis)
    bind(ac)
    def add(name,plan,factory):
        plans[name]=plan
        factories[name]=lambda:factory(plan)
    prod=read("production_manifest.json")
    cap=read("capacity_manifest.json")
    ref=read("reference_manifest.json")
    syn=read("analysis_capacity_manifest.json")
    pilot=read("pilot_manifest.json")
    weightpilot=read("weight_pilot_v2_manifest.json")
    weight=read("weight_reference_manifest_v4.json")["reference"]
    # Seed-defining sources must still match the frozen execution manifests.
    for plan,module,key in ((prod,t,"tile_driver_sha256"),(prod,bar,"bar_sampler_sha256"),
                            (cap,bar,"bar_sampler_sha256"),(ref,reference,"reference_driver_sha256")):
        if plan["runtime"][key]!=c.file_hash(module.__file__):
            raise ValueError("frozen seed producer changed: "+module.__name__)
    for plan,module in ((weightpilot,wp),(weight,wr)):
        if plan["driver_sha256"]!=c.file_hash(module.__file__):
            raise ValueError("frozen weight seed producer changed")
    if syn["analysis_source_sha256"]!=c.file_hash(analysis.__file__):
        raise ValueError("frozen analysis coordinate producer changed")
    for plan in (prod,cap,ref,syn,pilot,weight):
        if plan["master_seed"]!=t.MASTER:
            raise ValueError("master seed differs")
        if plan["runtime"]["tile_driver_sha256"]!=c.file_hash(t.__file__):
            raise ValueError("frozen seed generator changed")
    def traces(p):
        for task in bar.tasks(p):
            for purpose,label in ((0,"init"),(1,"sample")):
                yield Entry(p["purpose"]+"."+label,(99 if p["purpose"]=="capacity" else 31,*task),purpose)
    add("calibration",prod,traces)
    add("capacity",cap,traces)
    add("reference",ref,lambda p:(Entry("reference",(21,*task),0) for task in reference.tasks(p)))
    add("anchors",prod,lambda p:(Entry("calibration.anchor",(32,case,rep),0)
        for case,rep in itertools.product(range(len(p["cases"])),range(p["replicates"]))))
    add("bootstrap",prod,bootstrap_entries)
    add("synthetic.bootstrap",syn,lambda p:bootstrap_entries(p,synthetic=True))
    add("synthetic.data",syn,lambda p:(Entry("synthetic.data",(100,case,rep),0)
        for case,rep in itertools.product(range(len(p["cases"])),range(p["replicates"]))))
    add("pilot",pilot,lambda p:(Entry("pilot",task,purpose) for task in itertools.product(
        range(len(p["cases"])),range(len(p["probabilities"])),range(p["replicates"]))
        for purpose in (1,2,10,11,100,101,110,111)))
    add("weight.pilot",weightpilot,lambda p:(Entry("weight.pilot",(110,*task),0) for task in wp.tasks(p)))
    add("weight.reference",weight,lambda p:(Entry("weight.reference",(130,*task),0)
        for task in wr.tasks(p) if p["conditions"][task[0]]["layers"][task[1]]["mode"]=="mc"))
    for name in ("capacity","benchmark"):
        plan=read(f"mc_timing_{name}_manifest_v3.json")
        if plan["runtime"]["mc_timing_driver_sha256"]!=c.file_hash(mc.__file__):
            raise ValueError("frozen MC timing seed producer changed")
        add("mc."+name,plan,lambda p:(Entry(p["purpose"],(p["seed_stage"],*task),0) for task in mc.tasks(p)))
    if bar_timing_manifests:
        import tile_bar_time_benchmark as bt
        bind(bt)
        def bar_timing_entries(p):
            for task in bt.tasks(p):
                row=p["conditions"][task[0]]
                for purpose,label in ((0,"anchor"),(3,"bootstrap")):
                    yield Entry(p["purpose"]+"."+label,(p["seed_stage"],*task,0,0),purpose)
                for rung,chain in itertools.product(range(len(row["rungs"])),range(row["condition"]["chains"])):
                    for purpose,label in ((1,"init"),(2,"sample")):
                        yield Entry(p["purpose"]+"."+label,(p["seed_stage"],*task,rung,chain),purpose)
        for index,path in enumerate(bar_timing_manifests):
            path=Path(path).resolve()
            files[str(path)]=c.file_hash(path)
            p=json.loads(path.read_text())
            if (p["master_seed"]!=t.MASTER or p["seed_stage"] not in (140,141)
                    or p["sources"]["benchmark"]!=c.file_hash(bt.__file__)):
                raise ValueError("BAR timing seed source/stage differs")
            reservations.pop(p["seed_stage"],None)
            add("bar.timing."+str(index),p,bar_timing_entries)
    try:
        import tile_low_noise_analysis as low_analysis
        has_analysis=all(hasattr(low_analysis,name) for name in ("analysis_settings","bootstrap_seed"))
    except ImportError:
        has_analysis=False
    if has_analysis:
        bind(low_analysis)
    else:
        reservations[153]="Low-noise bootstrap helper unavailable"
    for case,target,capacity in itertools.product(range(4),range(3),(True,False)):
        plan=low.make_plan(case,target,capacity=capacity)
        if has_analysis and not capacity:
            setting=next(iter(low_analysis.analysis_settings(plan)))
            chains,burn,samples,ladder,_,_,block=setting
            group=(case,target,0,0,0)
            if low_analysis.bootstrap_seed(plan,group,chains,burn,samples,ladder,block)!=t.seed(
                    (153,*group,chains,burn,samples,ladder,block or 0),0):
                raise ValueError("low bootstrap coordinate helper mismatch")
        add(f"low.{case}.{target}.{capacity}",plan,lambda p:low_entries(p,include_analysis=has_analysis))
    if has_analysis:
        try:
            import tile_low_noise_analysis_capacity as low_capacity
            has_capacity=all(hasattr(low_capacity,key) for key in ("make_plan","groups","compute_plan","synthetic_seed"))
        except ImportError:
            has_capacity=False
        if has_capacity:
            bind(low_capacity)
            reservations.pop(155)
            for case,target in itertools.product(range(4),range(3)):
                plan=low_capacity.make_plan(case,target)
                compute=low_capacity.compute_plan(plan)
                group=next(iter(low_capacity.groups(plan)))
                if low_capacity.synthetic_seed(plan,group,0,0)!=t.seed((155,*group,0,0),2):
                    raise ValueError("synthetic array coordinate helper mismatch")
                chains,burn,samples,ladder,_,_,block=next(iter(low_analysis.analysis_settings(compute)))
                if low_analysis.bootstrap_seed(compute,group,chains,burn,samples,ladder,block)!=t.seed(
                        (155,*group,chains,burn,samples,ladder,block or 0),0):
                    raise ValueError("synthetic bootstrap coordinate helper mismatch")
                add(f"low.synthetic.{case}.{target}",plan,low_capacity_entries)
    counts={name:sum(1 for _ in factory()) for name,factory in factories.items()}
    import numpy as np
    import platform
    return factories,dict(planned_counts=counts,planned_total=sum(counts.values()),
        master_seed=t.MASTER,numpy=np.__version__,python=platform.python_version(),
        input_sha256=files,source_sha256=sources,plan_sha256={name:c.digest(plan) for name,plan in plans.items()},
        generated_candidate_plans={name:plan for name,plan in plans.items() if name.startswith("low.")},
        reserved_unenumerated_stages=reservations,all_goal_namespaces_complete=False,
        note="Low-noise plans are current candidate grids, not submitted jobs. Stage 33 is intentionally reused only by synthetic resource profiling.")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data",type=Path,default=Path(__file__).resolve().parents[1]/"docs/wp/data_tile_validation_2026-10-17")
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--full",action="store_true")
    parser.add_argument("--max-seconds",type=float,default=60.)
    parser.add_argument("--bar-timing-manifest",type=Path,action="append",default=[])
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError("preserve existing evidence")
    factories,evidence=catalog(args.data,args.bar_timing_manifest)
    total=evidence["planned_total"]
    def stream():
        return round_robin([factory() for factory in factories.values()])
    with tempfile.TemporaryDirectory(prefix="tile-seed-audit-") as temporary:
        pilot=census(stream(),total,Path(temporary)/"pilot.sqlite",limit=min(1000,total))
        predicted=2*pilot["seconds"]*total/pilot["checked_entries"]
        result=None
        if args.full and predicted<=args.max_seconds:
            result=census(stream(),total,Path(temporary)/"full.sqlite")
    for path,digest in {**evidence["input_sha256"],**evidence["source_sha256"]}.items():
        if c.file_hash(path)!=digest:
            raise ValueError("input/source changed during audit")
    output=dict(schema=1,evidence=evidence,pilot=pilot,full=result,
                predicted_full_seconds_with_factor2=predicted,
                full_deferred_reason=None if result is not None else "Full census not requested or exceeds explicit time budget",
                auditor_sha256=c.file_hash(__file__))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("xb") as handle:
        handle.write(c.canonical(output)+b"\n")
    print(json.dumps(dict(planned=total,pilot_checked=pilot["checked_entries"],predicted_seconds=predicted,
                          full_complete=result is not None and result["complete"],
                          reserved=evidence["reserved_unenumerated_stages"])))


if __name__=="__main__":
    main()
