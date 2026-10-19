"""Compare accepted saved mixing summaries, without opening JSONL or raw traces."""
import argparse
import copy
import csv
import hashlib
import importlib.util
import io
import itertools
import json
import math
from pathlib import Path, PurePosixPath

import tile_mixing_inventory as inventory

STAT_FIELDS = ('expected_values', 'finite_values', 'null_values', 'nonfinite_values',
               'sum', 'min', 'max', 'mean', 'available_only_mean')
STATUS = ('stored', 'missing_recorded_sampling_failure', 'missing_unexpected')
LIMITS = ('Summary marginal counts do not identify seed-level unions, correlations, paired differences, '
          'or 96/96 initialization strata. Saved diagnostics are descriptive, not convergence, '
          'ergodicity, bias or coverage guarantees. JSONL/NPZ/native/ACF are not rechecked. '
          'Historical consumed-input hashes were not recorded by the original analysis.')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Evidence:
    def __init__(self):
        self.files = {}

    def read(self, path, expected=None):
        path = Path(path).absolute()
        target = str(path.resolve())
        raw = path.read_bytes()
        digest = sha(raw)
        require(expected is None or digest == expected, 'input pin mismatch: ' + str(path))
        value = dict(resolved_path=target, sha256=digest, bytes=len(raw))
        require(self.files.setdefault(str(path), value) == value, 'input changed during read')
        return raw

    def json(self, path, expected=None):
        return json.loads(self.read(path, expected))

    def pin(self, item):
        require(set(item) == {'path', 'sha256'}, 'path/hash pin required')
        return self.json(item['path'], item['sha256'])

    def finish(self):
        for path, value in self.files.items():
            require(str(Path(path).resolve()) == value['resolved_path'] and
                    sha(Path(path).read_bytes()) == value['sha256'], 'input/source changed before completion')


def expected_keys(plan, case):
    diagnostics = inventory.expected_diagnostics(plan, case)
    templates = [('diagnostic', *key) for key in diagnostics]
    templates += [('sector', *key, 'sector') for key in
                  sorted({key[:4] for key in diagnostics if '_bennett_edge_' not in key[4]})]
    return [(kind, case, kernel, init, chains, burn, samples, rung, name)
            for kernel, init in itertools.product(plan['kernels'], plan['initializations'])
            for kind, chains, burn, samples, rung, name in templates]


def normalize(saved, plan, case, collector):
    """Validate shape and retain all stored numerical values; no diagnostic estimation."""
    expected = expected_keys(plan, case)
    collector.validate_report(saved, case, expected, len(expected)*192)
    result = []
    spec = plan['cases'][case]
    for original in saved['records']:
        row = copy.deepcopy(original)
        stored = row['status_counts'].get('stored', 0)
        flags = row['stored_flag_counts']
        if row['kind'] == 'sector':
            require(flags == {}, 'sector screen flags are not applicable')
        else:
            if stored == 0 and flags == {}:
                flags = row['stored_flag_counts'] = dict.fromkeys(inventory.FLAGS, 0)
            require(set(flags) == set(inventory.FLAGS) and all(type(v) is int and 0 <= v <= stored
                    for v in flags.values()), 'invalid stored flag counts')
        for metric in row['metrics'].values():
            require(set(metric) == set(STAT_FIELDS), 'invalid metric fields')
            for field in STAT_FIELDS[4:]:
                value = metric[field]
                require(value is None or (type(value) in (int, float) and math.isfinite(value)),
                        'metric must be finite or explicit null')
        row['status_counts'] = {key: row['status_counts'].get(key, 0) for key in STATUS}
        row.update(p=spec['rungs'][row['rung']], target_p=spec['target'],
                   target_rung=spec['rungs'][row['rung']] == spec['target'],
                   noise=spec['noise'], tile_n=2*spec['size']**2,
                   maximum_chains=spec['chains'], longest_samples=max(spec['windows']),
                   stored_flags_applicability='not_applicable' if row['kind']=='sector' else 'applicable',
                   stored_flags_absent=None if row['kind']=='sector' else 192-stored)
        if '_bennett_edge_' in row['observable']:
            label, edge = row['observable'].split('_bennett_edge_')
            ladder = spec['coarse'] if label == 'coarse' else spec['rungs']
            row['bennett_endpoints'] = ladder[int(edge):int(edge)+2]
        else:
            row['bennett_endpoints'] = None
        result.append(row)
    return sorted(result, key=lambda row: tuple(row[k] for k in inventory.KEY))


def source_paths():
    """Conservatively pin local analysis/core trees, including source additions."""
    root = Path(__file__).resolve().parents[1]
    return sorted({*root.joinpath('cluster_scripts').glob('*.py'),
                   *root.joinpath('src/mcmc4qec').rglob('*.py')})


def load_collector(pin, evidence):
    raw = evidence.read(pin['path'], pin['sha256'])
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader('accepted_mixing_collector', loader=None))
    module.__file__ = str(Path(pin['path']).absolute())
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    return module


def load_inputs(config_path, config_sha, evidence):
    config = evidence.json(config_path, config_sha)
    require(config['schema'] == 1 and [r['case'] for r in config['cases']] == list(range(4)),
            'four ordered completed cases required')
    collector = load_collector(config['collector'], evidence)
    prep = evidence.pin(config['preparation'])
    require(config['preparation']['sha256'] == collector.PREPARATION_SHA and
            [r['case'] for r in prep['cases']] == list(range(4)), 'accepted preparation differs')
    plan = evidence.pin(config['production_plan'])
    context = evidence.pin(config['analysis_context'])
    require(plan['purpose']=='calibration' and plan['replicates']==192 and
            len(plan['kernels'])==len(plan['initializations'])==2, 'fixed production plan required')
    require(context['sampling_manifest']==inventory.c.digest(plan) and context['runtime']==plan['runtime'],
            'analysis context sampling/runtime differs')
    rows, proofs = [], []
    for entry in config['cases']:
        case = entry['case']; prepared = prep['cases'][case]
        verification = evidence.pin(entry['verification'])
        root = Path(entry['root']).absolute()
        require(verification['case']==case and verification['root']==prepared['full_root'] and
                verification['local_all_files_hash_verified'] is True and
                verification['collector_sha256']==config['collector']['sha256'] and
                verification['preparation_sha256']==config['preparation']['sha256'] and
                verification['qsub_executed'] is False and
                verification['scientific_diagnostics_recomputed'] is False, 'unaccepted collection')
        require(set(verification['files'])==set(collector.FILES), 'collected file census differs')
        data = {}
        for name in collector.FILES:
            item = verification['files'][name]
            require(item['resolved_path']==str(PurePosixPath(prepared['full_root'])/name) and
                    type(item['bytes']) is int and item['bytes']>=0 and
                    isinstance(item['sha256'], str) and len(item['sha256'])==64, 'saved artifact metadata differs')
            if name == 'inventory/rows.jsonl':
                continue
            path = root/'full'/name
            require(path.resolve().is_relative_to(root.resolve()), 'collection file escaped root')
            raw = evidence.read(path,item['sha256'])
            require(len(raw)==item['bytes'], 'collected size differs')
            if name.endswith('.json'): data[name]=json.loads(raw)
        parent = evidence.json(root/'accepted_parent_receipt.json', verification['parent_receipt_sha256'])
        full = data['manifest.json']; dry = data['dry_run.json']; execution = data['summary.json']
        intent = data['execution-intent.json']; summary = data['inventory/summary.json']
        require(full['mode']=='full' and full['case']==case and full['replicates']==192 and full['planned_groups']==768 and
                inventory.c.digest(full)==prepared['full_manifest'], 'fixed full manifest differs')
        for name, digest in prepared['full_files_sha256'].items():
            require(verification['files'][name]['sha256']==digest, 'prepared file differs')
        job = verification['job_id']
        require(parent==data['submission.json'] and parent['job_id']==job and
                {k:v for k,v in parent.items() if k not in ('job_id','upstream_completion_sha256')} ==
                {k:v for k,v in dry.items() if k!='job_id'}, 'parent submission differs')
        require(data['submission-intent.json']=={k:v for k,v in parent.items() if k!='job_id'}, 'submission intent differs')
        require(parent['upstream_completion_sha256']==verification['files']['upstream-completion-at-submit.json']['sha256'],
                'upstream completion differs')
        require(verification['bundle_binding']==parent['bundle_binding']==dry['bundle_binding'], 'saved source/native binding differs')
        require(execution['complete'] is True and execution['terminal_binding_valid'] is True and execution['mode']=='full' and
                execution['case']==case and execution['pbs_job_id']==intent['pbs_job_id']==job and
                execution['manifest']==intent['manifest']==prepared['full_manifest'] and
                execution['submission_binding']==intent['submission_binding'] and execution['hostname']==intent['hostname'] and
                execution['execution_intent_sha256']==verification['files']['execution-intent.json']['sha256'], 'execution binding differs')
        stable = collector.validate_pbs(verification['pbs'], prepared['full_root']+'/inventory.sh', prepared['resource'], intent['hostname'])
        require(stable==verification['pbs_stable'], 'terminal receipt differs')
        state=full['snapshot']
        production_manifest=str(PurePosixPath(state['production_root'])/'manifest.json')
        require(state['input_files'][production_manifest][1]==config['production_plan']['sha256'] and
                summary['input_sha256'][production_manifest]==config['production_plan']['sha256'] and
                summary['sampling_manifest']==inventory.c.digest(plan), 'production plan binding differs')
        context_path=str(PurePosixPath(state['production_root'])/'analysis_manifest.json')
        require(state['input_files'][context_path][1]==config['analysis_context']['sha256'] and
                summary['input_sha256'][context_path]==config['analysis_context']['sha256'] and
                summary['analysis_context']==inventory.c.digest(context) and
                context['analysis_source_sha256']==verification['bundle_binding']['source_sha256']['tile_bar_analysis.py'],
                'analysis context binding differs')
        require(summary['audited_results_sha256']==state['input_files'][state['audited_results']][1] and
                summary['analysis_verification_sha256']==state['input_files'][state['analysis_verification']][1], 'upstream report differs')
        expected_source={k:verification['bundle_binding']['source_sha256'][name] for k,name in
                         (('inventory','tile_mixing_inventory.py'),('audited_results','tile_audited_results.py'),
                          ('calibration','calibration.py'),('archive','artifact_archive.py'))}
        require(summary['source_sha256']==expected_source, 'saved inventory source differs')
        require(execution['inventory_summary_sha256']==verification['files']['inventory/summary.json']['sha256'] and
                execution['rows_sha256']==summary['rows_sha256']==verification['files']['inventory/rows.jsonl']['sha256'] and
                all(execution[k]==summary[k] for k in ('rows','replicates','groups','inventory_complete')), 'inventory output binding differs')
        keys=expected_keys(plan,case)
        census=collector.validate_report(summary,case,keys,len(keys)*192)
        require(census==verification['census'], 'saved census differs')
        rows.extend(normalize(summary,plan,case,collector))
        proofs.append(dict(case=case, job_id=job, collection_root=str(root), groups=summary['groups'], replicates=192, rows=summary['rows'],
            inventory_complete=summary['inventory_complete'], failed_sampling=summary['failed_sampling'],
            verification=entry['verification'], census=census,
            rows_reference=verification['files']['inventory/rows.jsonl'] | {'path':str(root/'full/inventory/rows.jsonl')},
            postprocessing_measurement={k:execution[k] for k in ('wall_seconds','cpu_seconds','peak_rss_mb')},
            native_scope=verification['native_provenance']))
    return rows, proofs


def csv_text(rows):
    flat=[]
    for row in rows:
        item={k:row[k] for k in (*inventory.KEY,'p','target_p','replicates','undefined','nonfinite','stored_missing_fields',
                                'stored_flags_applicability','stored_flags_absent')}
        item['bennett_endpoints']=json.dumps(row['bennett_endpoints'])
        for name,value in row['status_counts'].items(): item['status_'+name]=value
        for name in inventory.FLAGS: item['stored_flag_'+name]=row['stored_flag_counts'].get(name)
        for name,metric in row['metrics'].items():
            for field,value in metric.items(): item[name+'_'+field]=value
        flat.append(item)
    stream=io.StringIO(newline=''); writer=csv.DictWriter(stream,fieldnames=list(dict.fromkeys(k for row in flat for k in row)))
    writer.writeheader();writer.writerows(flat)
    return stream.getvalue()


def render(rows, proofs):
    text=['# 主4条件の保存済み混合診断比較','', '## 受理範囲と分母','',
          '全4caseの正式回収証拠へ結合した保存summaryの比較であり、新しい数値診断や収束証明ではない。',
          '各観測量cohortの分母は192で、chain配列とsector統計の要素数は192×chainsである。','',
          '|case|実job|group|seed|inventory_complete|failed sampling|記録済みfailureによる欠測行|予期しない欠測行|inventory undefined行|', '|---|---|---:|---:|---|---:|---:|---:|---:|']
    for proof in proofs:
        census=proof['census'];counts=census['status_counts']
        text.append(f"|{proof['case']}|{proof['job_id']}|{proof['groups']}|192|{proof['inventory_complete']}|{proof['failed_sampling']}|{counts.get('missing_recorded_sampling_failure',0)}|{counts.get('missing_unexpected',0)}|{census['undefined']}|")
    text += ['', '欠測・undefined行は全observable-cohortとsector行の件数で、同じseedを重複して含み、192seed単位のORではない。',
             'inventory_completeは一覧の構造的な完全性であり、保存値のnullやscreen undefinedがあってもtrueになり得る。',
             '全予定条件と保存数値は[JSON](cohorts.json)・[CSV](cohorts.csv)、入力とJSONL回収hashは[証拠](provenance.json)に保持した。',
             'stored flagのundefinedと、missing/null/nonfiniteも含むinventory undefinedを区別する。',
             'missingのためflag自体が存在しないseedを警告なしへ読み替えない。','',
             '## target観測量と全rung/Bennettの違い','',
             '以下は最大chain・burn6000・最長保存長で、各kernel/initのtarget weightを固定した一覧である。',
             '全rung・全物理観測量・Bennett両端の個別値は全予定表に保持しており、target weightだけで全体の混合を判定しない。','',
             '|case|kernel|init|chains|samples|stored flag /192|screen undefined /192|inventory undefined /192|missing /192|',
             '|---|---|---|---:|---:|---:|---:|---:|---:|']
    fixed=[row for row in rows if row['chains']==row['maximum_chains'] and row['burn']==6000 and row['samples']==row['longest_samples']]
    for row in rows:
        if row['observable']=='weight' and row['target_rung'] and row['chains']==row['maximum_chains'] and row['burn']==6000 and row['samples']==row['longest_samples']:
            text.append('|'+ '|'.join(str(x) for x in (row['case'],row['kernel'],row['init'],row['chains'],row['samples'],
                row['stored_flag_counts']['flagged'],row['stored_flag_counts']['undefined'],row['undefined'],row['stored_flags_absent']))+'|')
    text += ['', '同じ固定windowの全rung・全observableの値は[rung/observable対比表](rung_observable_comparison.csv)に示す。',
             '次表の範囲は各observable/rungが持つflag件数の最小〜最大であり、seed集合の和集合ではない。',
             'missing合計は診断行の欠測数の和で、同じseedを複数回含み得る。','',
             '|case|kernel|init|observable family|診断cohort数|各cohort flag件数範囲 /192|missing診断行数|',
             '|---|---|---|---|---:|---|---:|']
    families={}
    for row in fixed:
        if row['kind']!='diagnostic':continue
        name=row['observable']
        family='logical_bit' if name.startswith('logical_bit_') else name.split('_bennett_edge_')[0]+'_bennett' if '_bennett_edge_' in name else name
        families.setdefault((row['case'],row['kernel'],row['init'],family),[]).append(row)
    for key, values in sorted(families.items()):
        counts=[r['stored_flag_counts']['flagged'] for r in values]
        text.append('|'+ '|'.join(map(str,(*key,len(values),f'{min(counts)}–{max(counts)}',sum(r['stored_flags_absent'] for r in values))))+'|')
    text += ['', '## kernel・初期化の比較','',
             '全予定表は同じcase/chains/burn/samples/rung/observableのZH・ZHSとrejection・logicalを対比できる。',
             '周辺件数と保存統計の比較に限り、同じreplicate番号の差・相関や共通乱数による効果は未評価である。','',
             '## chain数・burn-in・保存長の比較','',
             '4chainと最大chain、burn600と6000、各保存長を一つの軸ずつ対比する。',
             'この対比用の[target weight全window表](controls_target_weight.csv)は全kernel/initを保持する。',
             'windowは同じtraceを再利用し、4chainはprefixなので、設定数を独立試行数として扱わない。',
             '主meanがnullの場合も保持し、available_only_meanは有限値のみの補助平均である。','',
             '## logical sector移動','',
             'sector行はrung/window/chainsごとに一回で、screen flagはnot_applicableである。',
             'sector_transitionsとunique_sectorsは192×chains要素の集計であり、chain間の訪問集合の和集合や全支持の連結性を示さない。','',
             '固定windowの全rungの[sector対比表](sector_comparison.csv)を併記する。',
             '## BAR精度・被覆報告との対応と限界','',
             '主BARの既存flagは選択ladderの物理観測量とBennett診断をseed単位でORした別の受理済み集計である。',
             '本表の個別flagを足して主BARのflag数を復元しない。',
             '全rung/observableのseed単位OR、相関、対応差、depolarizingの96/96層別、median/quantileは本summaryでは未評価である。',
             'rows.jsonlは回収済みhash・sizeへの参照だけを保存し、今回JSONL/NPZ/ACF/raw trace/nativeを再読込・再監査していない。',
             '元解析にhistorical consumed-input hashが無い制限を引き継ぐ。',
             '警告の有無から収束・既約性・正しさ・bias・名目95%被覆を保証しない。',
             'wrapperのCPU/wall/RSSは保存診断の後処理時間であり、MCMCの計算効率やtime-to-accuracyではない。','']
    return '\n'.join(text)


def run(config, config_sha, output):
    output=Path(output).absolute()
    require(not output.exists(), 'preserve existing output')
    evidence=Evidence()
    sources=source_paths()
    for path in sources: evidence.read(path)
    rows,proofs=load_inputs(config,config_sha,evidence)
    require([r['case'] for r in proofs]==list(range(4)), 'all four accepted cases required')
    for path in evidence.files:
        require(not Path(path).resolve().is_relative_to(output.resolve()), 'separate output root required')
    for proof in proofs:
        root=Path(proof['collection_root']).resolve()
        require(not output.resolve().is_relative_to(root) and not root.is_relative_to(output.resolve()), 'separate collection output required')
    prose=render(rows,proofs); table=csv_text(rows)
    require(source_paths()==sources, 'source census changed')
    evidence.finish()
    result=dict(schema=1,purpose='saved_mixing_summary_comparison',cases=proofs,cohorts=len(rows),
        input_sha256=evidence.files,source_paths=[str(p) for p in sources],
        scientific_diagnostics_recomputed=False,jsonl_reread=False,raw_payloads_reaudited=False,
        seed_level_union_evaluated=False,paired_differences_evaluated=False,strata_96_evaluated=False,warning=LIMITS)
    output.mkdir(parents=True,exist_ok=False)
    (output/'cohorts.json').write_text(json.dumps(rows,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    (output/'cohorts.csv').write_text(table,encoding='utf-8',newline='')
    fixed=[row for row in rows if row['chains']==row['maximum_chains'] and row['burn']==6000 and row['samples']==row['longest_samples']]
    for name, selected in (
        ('rung_observable_comparison.csv',[r for r in fixed if r['kind']=='diagnostic']),
        ('controls_target_weight.csv',[r for r in rows if r['observable']=='weight' and r['target_rung']]),
        ('sector_comparison.csv',[r for r in fixed if r['kind']=='sector'])):
        (output/name).write_text(csv_text(selected),encoding='utf-8',newline='')
    require(source_paths()==sources, 'source census changed before publication')
    evidence.finish()
    created={}; output_target=output.resolve()
    try:
        for name,text in (('report_ja.md',prose),('provenance.json',json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')):
            path=output/name
            with path.open('xb'):pass
            stat=path.stat(); created[path]=(stat.st_dev,stat.st_ino)
            path.write_text(text,encoding='utf-8')
        require(source_paths()==sources, 'source census changed during publication')
        evidence.finish()
    except BaseException:
        # Only this invocation's exclusively created files at the original target.
        for path,identity in created.items():
            if output.resolve()==output_target and path.is_file() and not path.is_symlink() and path.resolve().parent==output_target:
                stat=path.stat()
                if (stat.st_dev,stat.st_ino)==identity:path.unlink()
        raise
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--config-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=run(args.config,args.config_sha256,args.output)
    print(json.dumps({'cohorts':result['cohorts'],'scientific_diagnostics_recomputed':False}))


if __name__=='__main__':main()
