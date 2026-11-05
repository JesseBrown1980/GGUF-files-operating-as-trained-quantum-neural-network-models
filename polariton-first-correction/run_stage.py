# Runs one stage of PLAN.hbp with the engine, several points at a time, and writes its rows in plan order, so the receipt is the same bytes at any parallelism.
# Elapsed time and peak memory go to a separate file, since they differ from machine to machine.
#
# usage: run_stage.py ENGINE PLAN STAGE RECEIPT_OUT COST_OUT PARALLEL [sabotage=NAME]
import os
import subprocess
import sys
import threading

sys.dont_write_bytecode = True


def fields(line):
    out = {}
    for part in line.strip().split("|")[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            out[key] = value
    return out


def peak_working_set_kb(process):
    """Peak memory of a finished process on Windows, where the engine's own read of /proc says CANNOT_SEE. The handle stays open until the Popen object goes."""
    if os.name != "nt":
        return "not_windows"
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(Counters)
    get_info = ctypes.WinDLL("psapi").GetProcessMemoryInfo
    get_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    get_info.restype = wintypes.BOOL
    if not get_info(wintypes.HANDLE(int(process._handle)), ctypes.byref(counters), counters.cb):
        return "CANNOT_SEE"
    return str(counters.PeakWorkingSetSize // 1024)


def run_one(engine, run, sabotage, slot, results, failures):
    command = [engine, "point", run["N"], run["K"], run["delta"], run["y"], run["W"], run["times"]]
    if sabotage:
        command.append(sabotage)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    peak = peak_working_set_kb(process)
    if process.returncode != 0:
        failures.append("%s exit %d %s" % (" ".join(command), process.returncode, err.decode("utf-8", "replace")[-300:]))
    cost = [line.removesuffix("|json=0") + "|peak_working_set_kB=%s|json=0" % peak for line in err.decode("utf-8").splitlines() if line.startswith("POLARITON_FIRST_CORRECTION_COST|")]
    results[slot] = (out.decode("utf-8").replace("\r\n", "\n"), cost)


def main():
    engine, plan, stage, receipt_out, cost_out, parallel = sys.argv[1:7]
    sabotage = sys.argv[7] if len(sys.argv) > 7 else ""
    runs = [fields(line) for line in open(plan, encoding="utf-8", newline="") if line.startswith("FC_RUN|") and fields(line)["stage"] == stage]
    if not runs:
        sys.stderr.write("no runs at stage %s\n" % stage)
        sys.exit(2)
    results = [None] * len(runs)
    failures = []
    gate = threading.Semaphore(int(parallel))

    def worker(slot, run):
        with gate:
            run_one(engine, run, sabotage, slot, results, failures)

    threads = [threading.Thread(target=worker, args=(i, run)) for i, run in enumerate(runs)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    if failures:
        sys.stderr.write("\n".join(failures) + "\n")
        sys.exit(1)
    with open(receipt_out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("POLARITON_FIRST_CORRECTION_STAGE|stage=%s|runs=%d|json=0\n" % (stage, len(runs)))
        for out, _ in results:
            handle.write(out)
        handle.write("POLARITON_FIRST_CORRECTION_STAGE_DONE|stage=%s|runs=%d|json=0\n" % (stage, len(runs)))
    with open(cost_out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("POLARITON_FIRST_CORRECTION_COST_STAGE|stage=%s|runs=%d|parallel=%s|json=0\n" % (stage, len(runs), parallel))
        for _, cost in results:
            for line in cost:
                handle.write(line + "\n")
    print("STAGE_DONE|stage=%s|runs=%d|json=0" % (stage, len(runs)))


main()
