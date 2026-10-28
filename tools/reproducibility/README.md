# Research artifact preservation

These standard-library tools preserve **documentary evidence**, not an executable copy of a cluster environment.
The collectors never import the research package, run a numerical calculation, or modify a frozen bundle.
The separately named deployment/staging helpers can submit preservation jobs through the existing shared admission gate.
Run inventory collection, archive creation, and acceptance tests in a PBS job submitted through the project's current physical-node admission gate.
Do not run a large source/data scan on the local HDD or bypass the two-node limit.

## Inventory request (private)

Create a JSON request outside the tracked tree with `schema: 1`, canonical absolute `roots`, explicit `seeds`, `relative_bases`, `required_scopes`, and `limits`.
For example, replace every placeholder below before use:

```json
{
  "schema": 1,
  "roots": {"workspace": "/ABSOLUTE/PRIVATE/WORKSPACE"},
  "seeds": [{"scope": "controller", "path": "/ABSOLUTE/PRIVATE/WORKSPACE/flow-config.json", "sha256": "ACTUAL_64_CHARACTER_SHA256"}],
  "relative_bases": {},
  "required_scopes": ["controller", "worker", "merge", "tail", "science", "seeds", "acceptance", "final_proofs"],
  "limits": {"file_bytes": 2097152, "total_bytes": 33554432, "files": 2000}
}
```

`seeds` are independently pinned root documents or supplemental files, not directory globs.
Supply a separate explicit base in `relative_bases` for each JSON document containing relative path/hash references.
Discovery follows explicit `{path, sha256}` objects and filename/path-keyed hash maps.
Missing files, inconsistent hashes, symlinked paths, unresolved relative references, and collection-limit failures are blockers.
Large JSON and non-text files are external inputs: their declared hash and size are indexed, their content is not read, and references inside them are not discovered.
Inventory JSON is private because it contains real paths and potentially exception details.

```sh
python archive.py discover --request private-request.json --inventory private-inventory.json
```

Review every discovered entry and supplement the root list with actual imported source, bootstrap/entrypoint helpers, acceptance tests, seed-generating rules, requirements/lockfiles, and immutable submission scripts not reached through JSON pins.
Bare hashes, dynamic imports, Python import search paths, source code containing embedded paths, and repository-level dependencies are **not** automatically resolved.
Do not label the source closure reviewed until these have been checked against actual environment `import_origins`, `resolved_sources`, and `source_sha256` maps.
Inventory completion is not evidence of successful production completion.

Before actual collection, classify references as **current execution dependencies**, **upstream historical evidence**, or **external raw/native inputs**.
An old provenance document may mention unavailable Windows paths even when its current cluster replacement is complete.
Do not silently drop those references or invent a replacement hash, but do not claim that every historical machine must be reconstructed to inspect the current code either.
Record the original reference, its role, its current substitute (if any), and the accepted relocation/provenance evidence in a supplemental audit.
The initial collector fails closed on unavailable references; a reviewed, separately versioned boundary policy is needed before omitting historical-only edges from an actual archive inventory.
Do not mutate the original pinned document to make discovery succeed.

## Public policy and archive

Create a separate private policy with `schema: 1`, `replacements` (each `{private, public}`), `forbidden_literals`, `external_access`, `source_closure_manually_reviewed`, and `scope_review`.
Map every root to a public token such as `${WORKSPACE}`; explicitly map usernames, hostnames, scheduler server suffixes, and any remaining machine identifiers.
Replacement values must not reintroduce a private token.
Inspect source and metadata for credentials or other sensitive information before packaging; a literal redaction list is not an automatic secret detector.

Every external artifact identity, for example `workspace/raw/trace.npz`, needs `format`, `custodian`, `availability`, `retrieval`, and `retention` strings in `external_access`.
Use honest values such as `unconfirmed` or `not publicly available` when appropriate; do not imply durable preservation or public access from a private path alone.
The tool refuses missing access terms and marks external hashes as **not reverified by this collection**.

```sh
python archive.py build --inventory private-inventory.json --policy private-policy.json --archive public-sources.zip
python archive.py verify --archive public-sources.zip
```

Store the printed archive SHA-256 and manifest SHA-256 in an independently published receipt.
`verify` checks internal byte/hash and edge consistency; it does not authenticate an archive whose manifest and contents were both replaced.
Verification accepts at most 4,002 ZIP members, 16 MiB per member, and 128 MiB total uncompressed bytes.
Review the complete public ZIP for identifiers before distribution.
Do not publish private request, policy, or inventory files.

The manifest records both original and public SHA-256 values and whether explicit redaction changed a file.
Embedded original metadata pins continue to identify original private bytes.
They are **not** silently rewritten to assert that the public bytes were the bytes used in production.
`execution_ready` and `scientific_reproduction_verified` remain false.

## Relocation to another local or cluster workspace

1. Verify the outer archive against the independently stored receipt, then run the internal verifier and extract under a new empty workspace.
2. Obtain every external input under its stated access terms and verify its **original** hash before use.
   Preserve raw immutable input content; record unavailable inputs as blockers.
3. Install the recorded Python and package versions, preserve the original platform/binary records, and record hashes of the **new** interpreter and native modules separately.
   Equal package versions do not imply equal BP-OSD binaries or equal trajectories across platforms.
4. Review the public path tokens and source-code path literals before mapping them to the new workspace.
   Do not perform a blind global replacement followed by execution, and do not import the archived original controller automatically.
5. Generate **new** environment records (`python`, native binary pins, `pythonpath`, `import_origins`, `resolved_sources`, source hash maps), then new reader/worker manifests, resource plans, configurations, scripts, and submission ledgers in dependency order.
   Rehash modified source and configuration bytes; preserve original hashes as historical provenance.
   Never rewrite historical PBS receipts or accepted-result records as though the new run were the old run.
6. Rerun meaningful acceptance checks for the relocated setup: code/failure semantics, exact approved source deltas, actual CLI import origins, metadata selection/census, scheduler resources and physical-node gate, and a small end-to-end canary.
   New scientific runs use the recorded seed and parameter definitions; resulting outputs and terminal receipts are new evidence.
7. Submit cluster work using `qsub`, with no more than two physical nodes.
   A local installation must use a separately reviewed local execution entrypoint; archived PBS controllers are not a local runner.

An automated relocation/re-pinning runner is **not implemented here**.
The exact archived workflow has site-specific immutable validators; modifying them to support a new workspace requires a small specification and acceptance tests.
Until that work and raw-input retrieval are complete, this archive supports source inspection and provenance review, not an exact replay guarantee.

## Fixture acceptance

The 23 small tests use temporary fixture files only.
Stage `archive.py`, `test_archive.py`, and `pbs_tests.py` under a fresh directory, pin all three in a request with purpose `reproduction_archive_fixture_acceptance`, and execute `pbs_tests.py --request ... --sha256 ... --result ...` in PBS.
The wrapper requires `PBS_JOBID`, verifies the sources before and after testing, and records stdout/stderr and a receipt.
Requested acceptance resources: one allowed vnode, one CPU, 1 GiB, five minutes.
Use the existing physical-node gate; these are not instructions to submit directly without admission.

## Finite private snapshots (v2)

`snapshot_v2.py` adds a separate, explicitly scoped preservation step without modifying the accepted recursive inventory tool.
It takes exact source declarations, a finite list of current JSON documents, import/alias bindings, external binary declarations, and the complete sealed-envelope index.
It writes **private** source and metadata ZIPs, their original hashes, a one-hop reference index, and an external index.
It does not perform public redaction or publish any output.

Source aliases retain both their declaration path and the expected canonical target.
Both target identity and byte hash are checked before and after capture; retargeting to another file with identical contents still fails.
Native and raw files are never opened: external entries record declared hashes, stat/alias information when available, and `original_hash_verified=false`.
Same-path conflicting pins across source, metadata, envelope, and external tables are rejected.

The one-hop scanner records recognized pins, malformed pins, unbound hashes, import-origin maps, resolved-source maps, and unpaired `*_path` fields.
A malformed entry does not hide its siblings.
Unrecognized dynamic conventions and source-code strings still require manual review; this is not an arbitrary-program dependency resolver.
Historical references outside the explicit metadata list remain visible external edges, without recursive collection.
The result separately reports explicit source/metadata byte preservation and keeps full dependency closure, final proofs, public distributability, and scientific reproduction false.

The v2 acceptance consists of 25 small fixtures, including direct content-open traps for native/raw files and source alias retargeting.
The production request builder is tied to a specific recorded run; later recovery flows require a separate, pinned request version.
Never relabel a snapshot of the earlier flow as the current flow's snapshot.

`collect_tile_v5_snapshot.py` preserves the actual request builder used for the fixed flow v5 evidence.
Its byte hash matches the successful PBS collector; it requires that run's private pinned inputs and the accepted fixture library location.
It is a record of the collection procedure, not a portable replacement for the scientific runner.
The collected source scope has 1,016 baseline declarations plus 15 explicitly attributed current-validation supplements.
The source declaration count includes aliases and does not silently deduplicate them by physical target or content hash.

`collect_tile_v8_snapshot.py` and `deploy_tile_v8_snapshot.py` define a separate finite preservation run for the fixed v8 flow, front v6, parallel merge v6, and tail v3/config v8.
They preserve the earlier snapshot's 1,031 source declarations as a historical baseline and add sources referenced by the explicitly listed current authority documents.
That latter count includes historical validation inputs and unused slots in retained workers' complete manifests; it is not a count of files actually executed by the twelve active workers.
Current worker-to-prepared-to-job bindings are recorded separately.
The collector reads no mutable observation log and saves its own one-time PBS worker observation instead.
Native/raw bytes remain external, and final production proofs remain incomplete.
The deployer uses the existing shared physical-node admission gate and `qsub` for one CPU, 2 GiB, ten minutes.
These scripts remain tied to original private paths and pins; use the relocation procedure above before attempting a new scientific run elsewhere.

The separate v9 collection preserves the switched controller and finite PBS tail without changing either v8 artifact.
PBS job 265646 completed the new nine scope-builder fixtures and the actual collection: 1,336 source declarations, 179 metadata documents, and 30,484,980 original text bytes.
Its private receipt hash is `efe1892730e2c2e75d9d97e9798418dcae7f35ed89101ec12f79d80b43809aa5`.
The first attempt, job 265645, passed seven fixtures but failed its final acceptance because a redundant source-attribution document exceeded 4 MiB; it remains a failed attempt with its original outputs preserved.
The successful revision groups attribution by source path and document role while preserving every recognized declaration pointer in the unchanged snapshot library's one-hop index.
It also bounds the PBS wrapper's source/authority reads; the original 4 MiB limit is retained.

`collect_tile_v9_snapshot.py`, `test_tile_v9_snapshot_scope.py`, `pbs_tile_v9_snapshot.py`, and `deploy_tile_v9_snapshot.py` preserve the exact successful helper bytes.
Their original staging names were respectively `collect.py`, `test_collect.py`, `run.py`, and `deploy.py`; the wrapper and fixture imports require those names in a separate staging directory.
They are records of the fixed private run, not commands to rerun against existing stage names.
The collector adds only explicit current metadata, one authority-request layer, declared source/import bindings, actual launch/cutover records, native job terminal observations, and a point-in-time observation of the unchanged twelve scientific workers.
No raw/native content, large scientific result, or mutable controller log is opened.
The v9 snapshot is private; a v9 sharing candidate, identifier review, exact scientific replay, and final scientific proof remain unperformed.
See the [v9 collection acceptance](../../docs/wp/finite_flow_v9_snapshot_acceptance_2026-10-25_ja.md).

## Sharing candidates from a private v2 snapshot

`share_snapshot_v2.py` is a separate format and exporter for the two ZIP files and five indexes produced by `snapshot_v2.py`.
It does not use the v1 inventory format accepted by `archive.py`; the earlier 23 archive fixtures do not validate this exporter.
Its dedicated 26 fixtures passed in PBS job 265618 on 2026-10-25.
The first actual build then rejected eight saved-source strings because the drive-path detector also matched SCP paths, POSIX path lists, and an escaped newline.
That failed build is preserved separately; it is not a successful archive export.
`share_snapshot_v2_revision2.py` retains the initial accepted source and changes only this detector's word-boundary rule, with dedicated URL/path regression fixtures.
Its separate 29 fixtures passed in PBS job 265622, including preservation of public URLs/SCP/POSIX paths and rejection of unredacted Windows paths and private identifiers inside URLs.
Use the separately accepted revision2 source and its receipt for the candidate build; the 26-test initial receipt alone does not establish that revision's acceptance.
The v2 exporter checks an externally supplied private receipt hash, every declared private artifact, and each included source/metadata member before redaction.
It rejects unsafe or duplicate ZIP members, unsupported compression/encryption, oversized inputs, duplicate JSON keys, and inconsistent original pins.
It never follows the external declarations into raw or native files, even for a stat.

The private policy supplies literal path prefixes, account/host identifiers, and additional residual patterns.
JSON keys and values are redacted structurally, with key collisions rejected.
Embedded original SHA-256 values stay unchanged and continue to identify private bytes; the sharing manifest records separate hashes for the public bytes.
This is a documentary review candidate, with `execution_ready`, `scientific_reproduction_verified`, and `publicly_distributable` remaining false.
Unknown or encoded identifiers and sensitive content still require an independent review before distribution.

Run build and verification inside a PBS allocation admitted by the shared physical-node gate:

```sh
python -B share_snapshot_v2_revision2.py build \
  --snapshot PRIVATE_SNAPSHOT_DIRECTORY \
  --receipt-sha256 ORIGINAL_RECEIPT_SHA256 \
  --policy PRIVATE_REDACTION_POLICY_JSON \
  --archive NEW_SHARING_CANDIDATE_ZIP
python -B share_snapshot_v2_revision2.py verify \
  --archive NEW_SHARING_CANDIDATE_ZIP --sha256 RETURNED_ARCHIVE_SHA256
```

The policy is private and must not be placed in the sharing directory.
Public verification checks public bytes against the supplied archive hash; it does not reverify private originals or external raw/native hashes.
Keep the private receipt, policy, original execution script, and build acceptance alongside the private operational records.

`share_policy_v2.py` proposes a deterministic literal policy from already-collected source/metadata text and explicit host/owner fields.
It is an aid for the fixed private collection, not a general privacy detector.
`build_share_snapshot_v2.py` pins that policy, runs three small policy fixtures in PBS, invokes the accepted exporter, verifies its output, and preserves generic builder sources in a separate sidecar ZIP.
The sidecar retains its original bytes and includes explicitly synthetic fixture identities; it needs a separate identifier review.
`deploy_share_snapshot_v2.py` submits this wrapper using the existing physical-node admission gate, requesting one CPU, 8 GiB, and fifteen minutes on one allowed vnode.
The generic builder, policy helper, tests, and deployer are preserved here as well as in the candidate sidecar; the private runtime policy is represented publicly only by its hash and creation procedure.
New controller or workflow versions require a new snapshot and candidate stage; never relabel the saved v8 collection as a later flow.

The actual v8 documentary candidate was built and byte-verified in PBS job 265624; it remains private and requires identifier review before distribution.
Its archive is 9,137,857 bytes with SHA-256 `aa2369d5d9bd106bc5568936cb6265ad709ebf82142ca97f01e9d52d2708bff8`.
The original seven-source builder sidecar is separate from a supplemental operational-source ZIP saved during the PBS audit.
`pbs_share_revision2_fixtures.py`, `deploy_share_revision2_fixtures.py`, and `diagnose_share_policy.py` preserve the exact fixture/diagnostic helper bytes used after snapshot collection.
The fixture staging names were `worker.py` and `deploy.py`; the repository names distinguish these historical entrypoints from the generic builders.
These helpers retain original fixed stage conventions and must not be rerun against an existing stage.
`audit_share_snapshot_v2.py` preserves the subsequent PBS-only whole-candidate scan and bounded review-sample procedure.
The private policy is excluded from both source ZIPs, and the supplement does not modify the original candidate or sidecar.
See the Japanese [acceptance record](../../docs/wp/share_snapshot_v2_acceptance_2026-10-25_ja.md) for the failed initial build, separate fixture acceptance, artifact pins, and limitations.

## v11 private control delta

`prepare_tile_v11_delta_snapshot.py`, `collect_tile_v11_delta_snapshot.py`, `test_tile_v11_delta_scope.py`, and `stage_tile_v11_delta_snapshot.py` preserve the exact source bytes used by PBS job 265662.
Their original staging names are `prepare.py`, `collect.py`, `test_collect.py`, and `stage.py`; retain those names when inspecting the historical imports and pinned request.
The fixed staging helper separates metadata preparation from submission and uses the existing physical-node gate after the original merge becomes terminal.
Do not rerun it against an existing stage or treat its historical fixed pins as a portable execution interface.
Eight dedicated fixtures and the actual delta collection passed in that job.
The delta contains explicitly bounded new source/control metadata and references the old v9 receipt without reopening its archives.
External raw/native declarations and scientific results remain outside this collection; the archives are private and execution readiness remains false.
See the [v11 delta acceptance record](../../docs/wp/finite_flow_v11_delta_snapshot_acceptance_2026-10-25_ja.md) for retrieval paths, original hashes, scope, and limitations.

## v12 private control delta

`prepare_tile_v12_delta_snapshot.py`, `collect_tile_v12_delta_snapshot.py`, `test_tile_v12_delta_scope.py`, and `stage_tile_v12_delta_snapshot.py` preserve the exact source bytes used by PBS job 265676.
Their staging names were `prepare.py`, `collect.py`, `test_collect.py`, and `stage.py`.
Ten dedicated fixtures and actual collection passed; the immutable v9 scope/snapshot library and the v11 delta scope behavior were reused.
Six explicitly selected source maps were checked completely, while older source pins outside the finite prefixes remained external declarations.
This delta adds namespace/observer/tail/flow control evidence and the original completed acceptance's small submission/terminal records.
It does not reopen result/selection payloads or previous archives, and does not establish completion of later scientific work.
The initial 105-document inventory was retained; a separate version added the original PBS start record before the final 106-document inventory was submitted.
The snapshot includes three additional collection records, yielding 109 metadata documents.
See the [v12 acceptance record](../../docs/wp/finite_flow_v12_delta_snapshot_acceptance_2026-10-25_ja.md) for pins and scope.
