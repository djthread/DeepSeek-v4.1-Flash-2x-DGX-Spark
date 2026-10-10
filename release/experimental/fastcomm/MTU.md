# Active MTU negotiation (candidate)

The shipped fastcomm library sets `IBV_MTU_4096` unconditionally. On two
GB10 systems with active RoCE MTU 1024, the original library reproduces
CUDA 719/Xid 43 without loading a model; bypassing its collectives through
PyNccl permits full model startup and short inference. See issues #4 and #5.

The candidate queries port 1's **active** MTU before CUDA allocation,
advertises it in the bootstrap record's former padding field, and configures
both QPs with the lower advertised MTU. Zero/unknown advertisements fail
before RTR with a diagnostic, including mixed old/new libraries. Record
size and the public C function signatures are unchanged, but both peers
must be rebuilt. Endpoint MTUs are not end-to-end path discovery: the fabric
must support the negotiated size; routed paths with lower limits need
additional configuration/path validation.

Build with `build.sh` into a fresh directory. `prepare_kit.py` includes the
new header and registers the new library/source hashes in a fresh candidate
kit and manifest. Do not replace the published runtime library, edit its
pins, or weaken verification to deploy this source change. This PR does not
modify the shipped runtime, lock, manifests, or verified kernel caches.

CPU regression: `python3 -B -m unittest discover -s tests -p test_fastcomm_mtu.py`.
The test covers every standard MTU pair, asymmetric endpoints, invalid
advertisements, and the old zero padding value. A CUDA compiler build is
also possible without exposing a GPU to the compiler container.

Hardware qualification remains pending. With both GPUs idle and the normal
memory watchdog active, build a separate candidate library/kit, verify its
manifest, and run the existing two-rank `bench_fc.py` exactness/graph tests
on both endpoints at active MTU 1024 and 4096, including asymmetric limits.
Confirm negotiated-MTU logs, correct sums/gathers, and absence of transport
retry errors/Xid. Then qualify full model startup/inference separately.
The external PyNccl workaround succeeded; that does not qualify this native
MTU patch. Do not interrupt an active serving pair to run these tests.
