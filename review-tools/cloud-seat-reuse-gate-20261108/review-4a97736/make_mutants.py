# make_mutants.py -- the cloud seat's five planted reuse faults in twens 0.4.0 (main.rs 1d768fa9), one copy each.
# usage: python3 -I make_mutants.py PATH/TO/engines/ensemble/src/main.rs OUT_DIR
import os, shutil, sys

MUTS = {
    'N1_k4_reused_weight_plus1': ('ens_accumulate_w(job, smp, rec, w, &mp.k4, &mp.k4_pairs);',
                                  'ens_accumulate_w(job, smp, rec, w + u64::from(w >= 2), &mp.k4, &mp.k4_pairs);'),
    'N2_k2_reused_weight_plus1': ('ens_accumulate_w(job, smp, rec, w, &sel_lock, &[false; NPAIR]);',
                                  'ens_accumulate_w(job, smp, rec, w + u64::from(w >= 2), &sel_lock, &[false; NPAIR]);'),
    'N5_k4_count_dropped': ('if c4.map(|ct| ct.inc(i)).unwrap_or(false) {',
                            'if idx % 4096 != 0 && c4.map(|ct| ct.inc(i)).unwrap_or(false) {'),
    'N6_k4_key_c3_sign': ('let g = [c0 << s, c1 << s, c2 << s, c3 << s, 0, 0];',
                          'let g = [c0 << s, c1 << s, c2 << s, (-c3) << s, 0, 0];'),
    'N7_k2_count_dropped': ('ct[i].fetch_add(1, Ordering::Relaxed);',
                            'if idx % 4096 != 0 { ct[i].fetch_add(1, Ordering::Relaxed); }'),
}
src_path, out = sys.argv[1], sys.argv[2]
src = open(src_path, encoding='utf-8').read()
crate = os.path.dirname(os.path.dirname(src_path))
for name, (a, b) in MUTS.items():
    if src.count(a) != 1:
        raise SystemExit('MUT_FAIL|name=%s|pattern_count=%d|json=0' % (name, src.count(a)))
    d = os.path.join(out, name)
    shutil.copytree(crate, d, ignore=shutil.ignore_patterns('target'))
    open(os.path.join(d, 'src', 'main.rs'), 'w', encoding='utf-8').write(src.replace(a, b))
    print('MUT|name=%s|json=0' % name)
