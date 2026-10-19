"""Independent weight-stratum primitives with explicit statistical and tail bounds.

The caller fixes the decoder prior. Nothing here permits reuse across different
decoder priors or infers correctable weights from a code-distance claim.
"""
import math
import operator
import numpy as np


def class_size(n,w,noise):
    n,w=operator.index(n),operator.index(w)
    if n<1 or not 0<=w<=n or noise not in ("bit","depolarizing"):
        raise ValueError("invalid stratum")
    return math.comb(n,w)*(3**w if noise=="depolarizing" else 1)


def _unrank_support(n,w,rank):
    support=[]
    start=0
    for remaining in range(w,0,-1):
        for value in range(start,n-remaining+1):
            count=math.comb(n-value-1,remaining-1)
            if rank<count:
                support.append(value)
                start=value+1
                break
            rank-=count
    return support


def enum_patterns(n,w,noise,start=0,stop=None):
    """Enumerate a half-open range of all support/type patterns exactly once."""
    total=class_size(n,w,noise)
    stop=total if stop is None else operator.index(stop)
    start=operator.index(start)
    if not 0<=start<=stop<=total:
        raise ValueError("invalid enumeration range")
    multiplier=3**w if noise=="depolarizing" else 1
    for index in range(start,stop):
        rank,labels=divmod(index,multiplier)
        support=_unrank_support(n,w,rank)
        state=np.zeros(n,dtype=np.uint8)
        if noise=="bit":
            state[support]=1
        else:
            for location in reversed(support):
                labels,label=divmod(labels,3)
                state[location]=label+1
        yield state


def draw_patterns(n,w,noise,samples,rng):
    """Independent uniform supports, and uniform non-I labels for Pauli noise."""
    class_size(n,w,noise)
    samples=operator.index(samples)
    if samples<1:
        raise ValueError("positive sample count required")
    states=np.zeros((samples,n),dtype=np.uint8)
    for state in states:
        support=rng.choice(n,size=w,replace=False)
        state[support]=1 if noise=="bit" else rng.integers(1,4,size=w,dtype=np.uint8)
    return states


def binomial_mass(n,w,p):
    if not 0<=w<=n or n<1 or not 0<=p<=1:
        raise ValueError("invalid binomial parameters")
    if p==0:
        return float(w==0)
    if p==1:
        return float(w==n)
    return math.exp(math.lgamma(n+1)-math.lgamma(w+1)-math.lgamma(n-w+1)+w*math.log(p)+(n-w)*math.log1p(-p))


def clopper_pearson(failures,trials,alpha):
    from scipy.stats import beta
    if trials<1 or not 0<=failures<=trials or not 0<alpha<1:
        raise ValueError("invalid binomial confidence parameters")
    lower=0. if failures==0 else float(beta.ppf(alpha/2,failures,trials-failures+1))
    upper=1. if failures==trials else float(beta.isf(alpha/2,failures+1,trials-failures))
    return lower,upper


def synthesize(n,noise,p,strata,alpha=.001):
    """Combine complete recorded layers; unobserved higher mass stays explicit.

The partial estimate is unbiased for the truncated sum when MC budgets are
fixed independently of these samples. The simultaneous interval adds the
entire omitted mass to its upper endpoint, not to a statistical standard error.
"""
    if not strata or not 0<alpha<1:
        raise ValueError("nonempty strata and confidence level required")
    weights=[operator.index(row["w"]) for row in strata]
    if len(set(weights))!=len(weights) or set(weights)!=set(range(max(weights)+1)):
        raise ValueError("every layer from zero to w_max required exactly once")
    mc_count=sum(row["mode"]=="mc" for row in strata)
    components=[]
    for row in sorted(strata,key=lambda entry:entry["w"]):
        w=row["w"]
        total=class_size(n,w,noise)
        trials,failures=operator.index(row["trials"]),operator.index(row["failures"])
        if trials<1 or not 0<=failures<=trials:
            raise ValueError("invalid stratum counts")
        rate=failures/trials
        if row["mode"]=="enum":
            if trials!=total:
                raise ValueError("incomplete enumeration")
            lower=upper=rate
            variance=0.
        elif row["mode"]=="mc":
            lower,upper=clopper_pearson(failures,trials,alpha/mc_count)
            variance=rate*(1-rate)/trials
        else:
            raise ValueError("unsupported stratum mode")
        mass=binomial_mass(n,w,p)
        components.append(dict(w=w,mass=mass,failure_rate=rate,interval=[lower,upper],
                               mc_variance_plugin=variance,mode=row["mode"],trials=trials,failures=failures))
    tail=math.fsum(binomial_mass(n,w,p) for w in range(max(weights)+1,n+1))
    partial=min(1.,max(0.,math.fsum(row["mass"]*row["failure_rate"] for row in components)))
    weighted=math.fsum(row["w"]*row["mass"]*row["failure_rate"] for row in components)
    lower=math.fsum(row["mass"]*row["interval"][0] for row in components)
    upper=math.fsum(row["mass"]*row["interval"][1] for row in components)+tail
    return dict(partial_estimate=partial,omitted_mass_upper=tail,
                partial_conditional_weight=weighted/partial if partial>0 else None,
                mc_standard_error_plugin=math.sqrt(math.fsum(row["mass"]**2*row["mc_variance_plugin"] for row in components)),
                interval=[min(1.,max(0.,lower)),min(1.,upper)],confidence_level=1-alpha,
                interval_method="Clopper-Pearson per MC stratum, Bonferroni, plus omitted-mass bound",
                strata=components,warning="Fixed decoder prior required. A zero plug-in SE for zero failures does not imply exact zero. The partial estimate omits the explicitly bounded tail.")
