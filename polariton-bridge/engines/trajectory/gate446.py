#!/usr/bin/env python3
# gate446.py -- the byte-for-byte gate that PREDICTION.hbp line 446 names for the trajectory integrator: s2_validate.py
# at delta = 1/2, -1/2, 3/4 (KMAX 4, TMAX 10), three processes, each output's sha256 against the value line 446 names.
# PREDICTION.hbp is read at its frozen sha256 and line 446 is parsed; the harness s2_validate.py and the exact series
# exact.py are read at their pinned sha256 (the design lane's files, the harness with its two path lines pointed here);
# the engine traj_int.py beside them is hashed into the receipt. Every run passes reserved.clear() first.
# The receipt holds the runs' values and hashes; the wall times go to standard output.
# usage: python3 -I -B -X utf8 gate446.py OUTDIR     (the runs use this interpreter; exit 0 when 3 of 3 reproduce)
import hashlib, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reserved import clear

PRED = os.path.join(HERE, '..', '..', 'PREDICTION.hbp')
PRED_SHA = 'fadd84122e820cc03e9a4d6d5dd47fe7118ab4b16e1d4db93a601fb44c90b892'
HARNESS_SHA = '3d7dd17558ff9477769757a3ccd19eadac666d61c0b718bb34901c28692aad0c'   # design lane 69c19c27..., lines 6 and 11 only
EXACT_SHA = 'cb4c69367764a0f0ce4d2ee56adfb1d1089fbeaf4fa6abc6b80a01a754236a19'     # design lane exact.py, byte copy
RUNS = [('1/2', 'd1o2'), ('-1/2', 'dm1o2'), ('3/4', 'd3o4')]
YS = ['1/27', '4/27', '1/81', '4/81', '1/243']


def sha(path):
    with open(path, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    outdir = sys.argv[1]
    py = sys.executable
    os.makedirs(outdir, exist_ok=True)
    pred = open(PRED, 'rb').read()
    if hashlib.sha256(pred).hexdigest() != PRED_SHA:
        raise SystemExit('GATE446_REFUSED|reason=PREDICTION.hbp_differs_from_the_frozen_file|json=0')
    line446 = pred.decode('utf-8').split('\n')[445]
    if not line446.startswith('BRIDGE_ENGINE_CHANGE|engine=the_trajectory_integrator'):
        raise SystemExit('GATE446_REFUSED|reason=line_446_is_not_the_trajectory_row|json=0')
    want = dict(re.findall(r's2_validate_(d1o2|dm1o2|d3o4)\.txt_sha256=([0-9a-f]{64})', line446))
    if len(want) != 3:
        raise SystemExit('GATE446_REFUSED|reason=line_446_names_%d_hashes|json=0' % len(want))
    harness = os.path.join(HERE, 's2_validate.py')
    if sha(harness) != HARNESS_SHA or sha(os.path.join(HERE, 'exact.py')) != EXACT_SHA:
        raise SystemExit('GATE446_REFUSED|reason=harness_or_exact_series_differs_from_its_pinned_sha256|json=0')
    rows = ['GATE446|prediction_sha256=%s|line=446|line_446_hashes=%s|engine=traj_int.py_sha256=%s|harness=s2_validate.py_sha256=%s|'
            'exact=exact.py_sha256=%s|python=%s|flags=-I_-B_-X_utf8|json=0' % (
                PRED_SHA, ','.join('%s:%s' % kv for kv in sorted(want.items())), sha(os.path.join(HERE, 'traj_int.py')),
                HARNESS_SHA, EXACT_SHA, sys.version.split()[0])]
    for d, tag in RUNS:
        rows.append(clear('s2_validate_%s' % tag, d, YS, 'any(N_for_C1=729)'))
    procs = []
    t0 = time.monotonic()
    for d, tag in RUNS:
        log = open(os.path.join(outdir, 's2_run_%s.log' % tag), 'w', encoding='utf-8', newline='\n')
        p = subprocess.Popen([py, '-I', '-B', '-X', 'utf8', harness, d, '4', '10'], stdout=log, stderr=subprocess.STDOUT, cwd=outdir)
        procs.append((d, tag, p, log))
    ok_all = True
    for d, tag, p, log in procs:
        rc = p.wait()
        log.close()
        print('GATE446_TIME|delta=%s|wall_s_since_launch=%d' % (d, int(time.monotonic() - t0)), flush=True)
        out = os.path.join(outdir, 's2_validate_%s.txt' % tag)
        a = open(out, 'rb').read() if os.path.exists(out) else b''
        got = hashlib.sha256(a).hexdigest()
        ok = rc == 0 and got == want[tag] and b'\r' not in a
        ok_all = ok_all and ok
        rows.append('GATE446_RUN|delta=%s|file=s2_validate_%s.txt|exit=%d|bytes=%d|CR_bytes=%d|sha256=%s|line_446_sha256=%s|'
                    'verdict=%s|json=0' % (d, tag, rc, len(a), a.count(b'\r'), got, want[tag], 'MEASURED_PASS' if ok else 'MEASURED_FAIL'))
    rows.append('GATE446_SUMMARY|files=3|passed=%d|verdict=%s|json=0' % (
        sum(1 for r in rows if r.startswith('GATE446_RUN') and 'MEASURED_PASS' in r), 'MEASURED_PASS' if ok_all else 'MEASURED_FAIL'))
    body = '\n'.join(rows) + '\n'
    name = os.path.join(outdir, 'gate446.hbp')
    with open(name, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(body)
    with open(name + '.sha256', 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('%s  gate446.hbp\n' % hashlib.sha256(body.encode('utf-8')).hexdigest())
    print(body, end='')
    return 0 if ok_all else 1


if __name__ == '__main__':
    raise SystemExit(main())
