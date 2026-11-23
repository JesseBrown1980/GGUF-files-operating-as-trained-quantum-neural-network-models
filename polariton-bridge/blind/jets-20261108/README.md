# The blind jets, filed by hash, November 8, 2026

The flow-map jet (jetens 0.2.0, binary `334dddec…`) ran on the 83 first-order rows of [`PLAN-JETS.hbp`](../../PLAN-JETS.hbp) at the frozen points, through `engines/jet/tools/drive_jets.py blind` with the explicit opt-in: 40 of 40 launches and 83 of 83 reads, every read `JET_READY`. These are the independent second answer beside the frozen Monte Carlo (the operator's decision of November 6, 2026), committed before the ensemble phase runs.

- [`DRIVER-LOG.hbp`](DRIVER-LOG.hbp): every launch and read with its output's bytes and sha256, its status and its timing.
- [`INDEX.hbi`](INDEX.hbi): one row per output file, 124 in all, with bytes, sha256, a 16-hex SH and a PID chained from the seat.
- [`SEAL.hbp`](SEAL.hbp): sha256 over `SHA256SUMS` then `INDEX.hbi`.

The output files themselves, 59 MB, stay on the seat's machine in `C:/tmp/opus55/bridge-blind-driver-20261106/out-blind/jets/blind/` until the frozen read. At the read they are compared with this index byte for byte, and any changed byte fails closed.
