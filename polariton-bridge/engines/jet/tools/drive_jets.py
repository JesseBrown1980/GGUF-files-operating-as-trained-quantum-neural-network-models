# drive_jets.py -- the guarded driver of PLAN-JETS.hbp. Lane jet-plan-20261106 (opus55, a lane of the second seat for
# ACER-CLAUDE-FABLE5). Exact rationals only (float_used=0).
#
# usage: python3 -I -B -X utf8 drive_jets.py MODE --plan=PATH --plan-sha256=HEX --root=DIR --binary=PATH
#            --prediction=PATH --amendment=PATH [--jobs=1|2] [--opt-in=TEXT] [--timeout-min=45]
#   MODE  dry-run : verifies every byte the plan names, the resume state and every launch's guard; launches nothing
#         analog  : the plan's proof: each launch at its analog (an allowed delta; y = 2/27 -> 1/18), the guard checked
#                   in this file before each launch; the reads at the analog rows
#         blind   : the seat's run of the reserved points; refused unless --opt-in=RUN_THE_RESERVED_JETS_FOR_THE_SEAT
#   Fails closed: the plan's sha256 must equal --plan-sha256; the binary, PREDICTION.hbp, the amendment, this driver,
#   the reader and its modules must carry the sha256 the plan names, re-checked before every launch and every read;
#   every completed output must still carry the sha256 its LAUNCH_DONE or READ_DONE row logged. Any changed byte stops
#   the driver with a DRV_FAIL row before anything further starts.
#   Resumable: ROOT/<MODE>/DRIVER-LOG.hbp is append-only; a rerun skips what it logged as done (after re-hashing it),
#   relaunches what it logged as started and never finished (its .part file is removed, inside ROOT), and refuses an
#   output it never logged.
import hashlib
import os
import subprocess
import sys
import time
from fractions import Fraction as Fr

OPT_IN = 'RUN_THE_RESERVED_JETS_FOR_THE_SEAT'
RESERVED_DELTA = (Fr(3, 5), Fr(-3, 5))
ALLOWED_DELTA = (Fr(0), Fr(1, 4), Fr(-1, 4), Fr(1, 2), Fr(-1, 2), Fr(3, 4), Fr(-3, 4))
Y227 = Fr(2, 27)
TOOLS = os.path.dirname(os.path.abspath(__file__))


def fields(line):
    out = {}
    for part in line.rstrip('\n').split('|')[1:]:
        if '=' in part:
            k, v = part.split('=', 1)
            out[k] = v
    return out


def sha_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%S%z')


class Log:
    def __init__(self, path):
        self.path = path

    def row(self, text):
        with open(self.path, 'a', newline='\n') as fh:
            fh.write(text + '\n')
        print(text, flush=True)


def guard_reason(delta, y):
    """The analog guard: None if this driver may launch a jet at (delta, y) without the opt-in; else the reason.
    A jet does not depend on N, so the y band is refused at every N."""
    delta, y = Fr(delta), Fr(y)
    for r in RESERVED_DELTA:
        if delta == r:
            return 'reserved_delta'
        if abs(delta - r) <= Fr(1, 20):
            return 'reserved_delta_neighbourhood_1/20'
    if delta not in ALLOWED_DELTA:
        return 'delta_not_in_the_allowed_list'
    if abs(y) == Y227:
        return 'reserved_y'
    if abs(abs(y) - Y227) <= Fr(1, 81):
        return 'reserved_y_neighbourhood_1/81_at_every_N'
    return None


def parse_args(argv):
    if not argv:
        raise SystemExit('DRV_FAIL|reason=usage|json=0')
    mode = argv[0]
    opts = {}
    for a in argv[1:]:
        if not a.startswith('--') or '=' not in a:
            raise SystemExit('DRV_FAIL|reason=bad_option:%s|json=0' % a)
        k, v = a[2:].split('=', 1)
        if k in opts:
            raise SystemExit('DRV_FAIL|reason=duplicate_option:%s|json=0' % k)
        opts[k] = v
    for k in ('plan', 'plan-sha256', 'root', 'binary', 'prediction', 'amendment'):
        if k not in opts:
            raise SystemExit('DRV_FAIL|reason=missing_option:%s|json=0' % k)
    if mode not in ('dry-run', 'analog', 'blind'):
        raise SystemExit('DRV_FAIL|reason=mode_dry-run_analog_or_blind|json=0')
    jobs = int(opts.get('jobs', '1'))
    if jobs not in (1, 2):
        raise SystemExit('DRV_FAIL|reason=jobs_1_or_2|json=0')
    return mode, opts, jobs


def read_plan(path):
    with open(path, 'rb') as fh:
        data = fh.read()
    if b'\r' in data:
        raise SystemExit('DRV_FAIL|reason=CR_in_the_plan|json=0')
    head, launches, rows, check = None, [], [], None
    for ln in data.decode('utf-8').split('\n'):
        if ln.startswith('PLAN_JETS_HEAD|'):
            head = fields(ln)
        elif ln.startswith('JET_LAUNCH|'):
            launches.append(fields(ln))
        elif ln.startswith('JET_ROW|'):
            rows.append(fields(ln))
        elif ln.startswith('PLAN_JETS_CHECK|'):
            check = fields(ln)
    if head is None or check is None:
        raise SystemExit('DRV_FAIL|reason=plan_without_head_or_check|json=0')
    return head, launches, rows, check


def want_hashes(head, opts):
    """(label, path, sha256 the plan names) for every byte the driver depends on."""
    first = lambda v: v.split('(')[0]
    return [
        ('plan', opts['plan'], opts['plan-sha256']),
        ('binary', opts['binary'], first(head['binary_sha256'])),
        ('PREDICTION.hbp', opts['prediction'], head['PREDICTION.hbp_sha256']),
        ('AMENDMENT', opts['amendment'], head['AMENDMENT_sha256']),
        ('drive_jets.py', os.path.join(TOOLS, 'drive_jets.py'), first(head['driver'].split('=', 1)[1])),
        ('jetread.py', os.path.join(TOOLS, 'jetread.py'), first(head['reader'].split('=', 1)[1])),
        ('jetcmp.py', os.path.join(TOOLS, 'jetcmp.py'), first(head['jetcmp.py_sha256'])),
        ('cf.py', os.path.join(TOOLS, 'cf.py'), first(head['cf.py_sha256'])),
    ]


def verify_inputs(hashes, log):
    for label, path, want in hashes:
        if not os.path.exists(path):
            log.row('DRV_FAIL|reason=missing_input|what=%s|path=%s|json=0' % (label, path))
            sys.exit(5)
        got = sha_file(path)
        if got != want:
            log.row('DRV_FAIL|reason=changed_byte|what=%s|path=%s|want=%s|got=%s|json=0' % (label, path, want, got))
            sys.exit(5)


def read_log(path):
    started, done, reads = {}, {}, {}
    if os.path.exists(path):
        with open(path, 'rb') as fh:
            for raw in fh.read().decode('ascii').split('\n'):
                if raw.startswith('LAUNCH_START|'):
                    f = fields(raw)
                    started[f['id']] = f
                elif raw.startswith('LAUNCH_DONE|'):
                    f = fields(raw)
                    done[f['id']] = f
                elif raw.startswith('READ_DONE|'):
                    f = fields(raw)
                    reads[f['row']] = f
    return started, done, reads


def verify_done(root, done, reads, log):
    for d in list(done.values()) + list(reads.values()):
        p = os.path.join(root, d['output'])
        if not os.path.exists(p):
            log.row('DRV_FAIL|reason=logged_output_missing|output=%s|json=0' % d['output'])
            sys.exit(5)
        got = sha_file(p)
        if got != d['sha256']:
            log.row('DRV_FAIL|reason=changed_byte_in_a_completed_output|output=%s|want=%s|got=%s|json=0' % (
                d['output'], d['sha256'], got))
            sys.exit(5)


def resolve(mode, L):
    """(argv, output) of a launch in this mode, with the checks of the mode; raises SystemExit on any refusal."""
    if mode == 'analog':
        argv, outp = L['analog_argv'].split('~'), L['analog_output']
        kv = dict(a.split('=', 1) for a in argv[1:])
        if 'lift_reserved_guard' in kv:
            raise SystemExit('DRV_FAIL|reason=analog_argv_lifts_the_guard|id=%s|json=0' % L['id'])
        r = guard_reason(kv['delta'], kv['y'])
        if r is not None:
            raise SystemExit('DRV_FAIL|reason=guard_refuses_the_analog:%s|id=%s|json=0' % (r, L['id']))
        for k in ('p', 'q', 'dtden', 'steps', 'for_n'):
            if kv[k] != L[k]:
                raise SystemExit('DRV_FAIL|reason=analog_differs_from_the_plan_in_%s|id=%s|json=0' % (k, L['id']))
    else:
        argv, outp = L['argv'].split('~'), L['output']
        kv = dict(a.split('=', 1) for a in argv[1:])
        if kv.get('lift_reserved_guard') != '1' or L['reserved'] != '1':
            raise SystemExit('DRV_FAIL|reason=blind_launch_without_the_lift|id=%s|json=0' % L['id'])
        if Fr(kv['delta']) != Fr(L['delta']) or Fr(kv['y']) != Fr(L['y']):
            raise SystemExit('DRV_FAIL|reason=blind_argv_differs_from_its_row|id=%s|json=0' % L['id'])
    if argv[0] != 'jet' or len(set(a.split('=', 1)[0] for a in argv[1:])) != len(argv) - 1:
        raise SystemExit('DRV_FAIL|reason=argv_shape|id=%s|json=0' % L['id'])
    return argv, outp


def main():
    mode, opts, jobs = parse_args(sys.argv[1:])
    root = opts['root']
    sub = 'dry-run' if mode == 'dry-run' else mode
    os.makedirs(os.path.join(root, sub), exist_ok=True)
    log = Log(os.path.join(root, sub, 'DRIVER-LOG.hbp'))
    head, launches, rows, check = read_plan(opts['plan'])
    hashes = want_hashes(head, opts)
    timeout_s = int(opts.get('timeout-min', '45')) * 60
    if timeout_s > 45 * 60:
        raise SystemExit('DRV_FAIL|reason=timeout_above_45_minutes|json=0')
    log.row('DRV_START|mode=%s|when=%s|plan=%s|plan_sha256=%s|binary=%s|jobs=%d|timeout_s=%d|opt_in=%s|json=0' % (
        mode, now(), opts['plan'], opts['plan-sha256'], opts['binary'], jobs, timeout_s,
        'given' if opts.get('opt-in') == OPT_IN else ('wrong_text' if 'opt-in' in opts else 'absent')))
    verify_inputs(hashes, log)
    for label, path, want in hashes:
        log.row('DRV_INPUT|what=%s|sha256=%s|equal_to_the_plan=1|json=0' % (label, want))
    if mode == 'blind' and opts.get('opt-in') != OPT_IN:
        log.row('DRV_FAIL|reason=blind_mode_needs_--opt-in=%s|launched=0|json=0' % OPT_IN)
        sys.exit(6)
    if mode != 'blind' and 'opt-in' in opts:
        log.row('DRV_FAIL|reason=the_opt-in_belongs_to_the_blind_mode_only|launched=0|json=0')
        sys.exit(6)
    # the plan's own structure
    ids = {L['id']: L for L in launches}
    if len(ids) != len(launches) or len(launches) != int(check['launches']) or len(rows) != int(check['plan_rows']):
        log.row('DRV_FAIL|reason=plan_counts|json=0')
        sys.exit(5)
    for r in rows:
        for k in ('jet', 'eint_jet'):
            if r[k] not in ids:
                log.row('DRV_FAIL|reason=row_names_an_unknown_jet|row=%s|json=0' % r['frozen_line'])
                sys.exit(5)
        for k, sk in (('jet', 'step64'), ('eint_jet', 'step128')):
            if r[sk] not in ids[r[k]]['steps'].split(','):
                log.row('DRV_FAIL|reason=row_step_not_in_its_jet|row=%s|json=0' % r['frozen_line'])
                sys.exit(5)
    resolved = {}
    for L in launches:
        try:
            resolved[L['id']] = resolve('analog' if mode == 'analog' else 'blind', L)
        except SystemExit as e:
            log.row(str(e))
            sys.exit(6)
    logpath = os.path.join(root, sub, 'DRIVER-LOG.hbp')
    started, done, reads = read_log(logpath)
    verify_done(root, done, reads, log)
    for L in launches:
        argv, outp = resolved[L['id']]
        p = os.path.join(root, outp)
        if L['id'] not in done and os.path.exists(p):
            log.row('DRV_FAIL|reason=output_present_but_never_logged_done|output=%s|json=0' % outp)
            sys.exit(5)
    for r in rows:
        rk = 'L%04d' % int(r['frozen_line'])
        rp = os.path.join(root, r['output'] if mode == 'blind' else r['analog_output'])
        if mode != 'dry-run' and rk not in reads and os.path.exists(rp):
            log.row('DRV_FAIL|reason=read_present_but_never_logged_done|output=%s|json=0' % rp)
            sys.exit(5)
    if mode == 'dry-run':
        # the resume state of each real mode, read only: its log's completed outputs re-hashed (fail closed if changed)
        state = {}
        for m in ('blind', 'analog'):
            mlog = os.path.join(root, m, 'DRIVER-LOG.hbp')
            _, mdone, mreads = read_log(mlog)
            verify_done(root, mdone, mreads, log)
            state[m] = (mdone, mreads)
        for L in launches:
            for m in ('blind', 'analog'):
                argv, outp = resolve(m, L)
                log.row('DRY_LAUNCH|mode=%s|order=%s|id=%s|role=%s|binary_sha256=%s|argv=%s|output=%s|reserved=%d|state=%s|json=0' % (
                    m, L['order'], L['id'], L['role'], hashes[1][2], '~'.join(argv), outp, int(m == 'blind'),
                    'done_and_verified' if L['id'] in state[m][0] else 'not_launched'))
        for r in rows:
            rk = 'L%04d' % int(r['frozen_line'])
            log.row('DRY_READ|row=%s|jet=%s|eint_jet=%s|output=%s|blind_state=%s|analog_output=%s|analog_state=%s|json=0' % (
                rk, r['jet'], r['eint_jet'], r['output'], 'read_and_verified' if rk in state['blind'][1] else 'not_read',
                r['analog_output'], 'read_and_verified' if rk in state['analog'][1] else 'not_read'))
        log.row('DRV_END|mode=dry-run|launches_listed=%d|reads_listed=%d|launched=0|read=0|blind_done=%d|blind_read=%d|analog_done=%d|analog_read=%d|json=0' % (
            2 * len(launches), len(rows), len(state['blind'][0]), len(state['blind'][1]), len(state['analog'][0]),
            len(state['analog'][1])))
        return
    # launches, at most `jobs` at a time, each after the inputs and every completed output are re-verified
    pending = [L for L in launches if L['id'] not in done]
    running = []
    n_launched = 0

    def finish(job):
        L, proc, part, outp, t0 = job
        rc = proc.wait()
        wall = (time.time_ns() - t0) // 1000000
        p = os.path.join(root, outp)
        ok = rc == 0 and os.path.exists(part)
        if ok:
            with open(part, 'rb') as fh:
                data = fh.read()
            lines = [x for x in data.split(b'\n') if x]
            hf = fields(lines[0].decode('ascii')) if lines else {}
            argv, _ = resolved[L['id']]
            ok = (bool(lines) and lines[-1].startswith(b'JET_DONE|') and hf.get('binary_sha256') == hashes[1][2]
                  and hf.get('args') == '~'.join(argv[1:]) and b'\r' not in data)
        if not ok:
            for other in running:
                other[1].kill()
                other[1].wait()
            log.row('DRV_FAIL|reason=launch_failed_or_output_unlike_the_plan|id=%s|rc=%d|wall_ms=%d|others_stopped=%d|json=0' % (
                L['id'], rc, wall, len(running)))
            sys.exit(7)
        os.replace(part, p)
        if os.path.exists(part + '.err') and os.path.getsize(part + '.err') == 0:
            os.remove(part + '.err')
        log.row('LAUNCH_DONE|id=%s|output=%s|bytes=%d|sha256=%s|rc=0|wall_ms=%d|when=%s|json=0' % (
            L['id'], outp, os.path.getsize(p), sha_file(p), wall, now()))
        done[L['id']] = {'output': outp, 'sha256': sha_file(p)}

    while pending or running:
        while pending and len(running) < jobs:
            L = pending.pop(0)
            verify_inputs(hashes, log)
            verify_done(root, done, reads, log)
            argv, outp = resolved[L['id']]
            if mode == 'analog':
                kv = dict(a.split('=', 1) for a in argv[1:])
                if guard_reason(kv['delta'], kv['y']) is not None or 'lift_reserved_guard' in kv:
                    log.row('DRV_FAIL|reason=guard_at_launch|id=%s|json=0' % L['id'])
                    sys.exit(6)
            p = os.path.join(root, outp)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            part = p + '.part'
            if os.path.exists(part):
                os.remove(part)
                log.row('LAUNCH_PART_REMOVED|id=%s|part=%s|json=0' % (L['id'], outp + '.part'))
            log.row('LAUNCH_START|id=%s|order=%s|role=%s|binary_sha256=%s|argv=%s|output=%s|reserved=%d|when=%s|json=0' % (
                L['id'], L['order'], L['role'], hashes[1][2], '~'.join(argv), outp, int(mode == 'blind'), now()))
            fo = open(part, 'wb')
            fe = open(part + '.err', 'wb')
            proc = subprocess.Popen([opts['binary']] + argv, stdout=fo, stderr=fe)
            fo.close()
            fe.close()
            running.append((L, proc, part, outp, time.time_ns()))
            n_launched += 1
        # wait for the first to finish, with the per-launch timeout
        while running:
            for job in list(running):
                L, proc, part, outp, t0 = job
                if proc.poll() is not None:
                    running.remove(job)
                    finish(job)
                    break
                if (time.time_ns() - t0) // 1000000000 > timeout_s:
                    for other in running:
                        other[1].kill()
                        other[1].wait()
                    log.row('DRV_FAIL|reason=launch_over_the_time_limit|id=%s|json=0' % L['id'])
                    sys.exit(7)
            else:
                time.sleep(1)
                continue
            break
    # the reads: one reader call per jet pair, after both jets are done
    by_jet = {}
    for i, r in enumerate(rows, start=1):
        by_jet.setdefault((r['jet'], r['eint_jet']), []).append(r)
    n_read = 0
    for (j64, j128), rs in by_jet.items():
        todo = [r for r in rs if 'L%04d' % int(r['frozen_line']) not in reads]
        if not todo:
            continue
        verify_inputs(hashes, log)
        verify_done(root, done, reads, log)
        cmd = [sys.executable, '-I', '-B', '-X', 'utf8', os.path.join(TOOLS, 'jetread.py'), mode, opts['plan'], root] + [
            r['order'] for r in todo]
        t0 = time.time_ns()
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        wall = (time.time_ns() - t0) // 1000000
        if res.returncode != 0:
            log.row('DRV_FAIL|reason=reader_failed|jets=%s,%s|rc=%d|stderr=%s|json=0' % (
                j64, j128, res.returncode, res.stderr.decode('ascii', 'replace').strip().replace('\n', ';')[:300]))
            sys.exit(8)
        for ln in res.stdout.decode('ascii').split('\n'):
            if ln.startswith('JR_DONE|'):
                f = fields(ln)
                log.row('READ_DONE|row=%s|output=%s|bytes=%s|sha256=%s|status=%s|failing=%s|reader_wall_ms_for_its_group=%d|json=0' % (
                    f['row'], f['output'], f['bytes'], f['sha256'], f['status'], f['failing'], wall))
                reads[f['row']] = {'output': f['output'], 'sha256': f['sha256']}
                n_read += 1
    verify_done(root, done, reads, log)
    log.row('DRV_END|mode=%s|when=%s|launched_this_call=%d|launches_done=%d_of_%d|reads_this_call=%d|reads_done=%d_of_%d|json=0' % (
        mode, now(), n_launched, len(done), len(launches), n_read, len(reads), len(rows)))


if __name__ == '__main__':
    main()
