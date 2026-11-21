#!/usr/bin/env python3
# float_scan.py -- float_used=0 of the engine, by a static and two dynamic scans (the round-1 review's float_scan_rv.py
# and the build lane's check_int.py trace, in one file):
#  (1) static: tokenize every NUMBER token with '.', an exponent or 'j'; ast: the names float/complex, math attributes
#      and imports other than its integer functions, every import;
#  (2) dynamic, rewrite: every true division and power of the module becomes a checked call that counts int/int true
#      divisions and any float or complex operand or result;
#  (3) dynamic, trace: every line and return event in the engine's frames, every local and return value (through tuples,
#      lists, dicts, sets) classified by type, float or complex counted.
# The dynamic runs are at allowed points only (reserved.clear first): (1/2, 1/27) bound on, 3 steps, obs, bound_row,
# obs_bound_row(729), a half-step read and its rows; (3/4, 4/81) bound off to 3/32, obs(81); the guard's checks on refused
# values, predicate only (fx, taylor_step and obs on tripwires there).
# usage: float_scan.py ENGINE [OUTDIR [LABEL]]   (exit 0 when every count is 0)
import ast, hashlib, io, os, sys, tokenize
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reserved import clear

INT_MATH = {'isqrt', 'lcm', 'gcd', 'comb', 'perm', 'factorial', 'prod'}
rows = []


def static(path, src):
    lits = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.NUMBER:
            s = tok.string.lower()
            if not s.startswith(('0x', '0o', '0b')) and ('.' in s or 'e' in s or 'j' in s):
                lits.append(tok.start[0])
    tree = ast.parse(src)
    names = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id in ('float', 'complex')]
    mattr = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
             and n.value.id == 'math' and n.attr not in INT_MATH]
    imps = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imps += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            imps += ['%s.%s' % (n.module, a.name) for a in n.names]
    from_math = [i for i in imps if i.startswith('math.') and i.split('.', 1)[1] not in INT_MATH]
    ndiv = sum(1 for n in ast.walk(tree) if (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div))
               or (isinstance(n, ast.AugAssign) and isinstance(n.op, ast.Div)))
    npow = sum(1 for n in ast.walk(tree) if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Pow))
    rows.append('FLOAT_STATIC|sha256=%s|float_or_complex_number_tokens=%d|names_float_complex=%d|math_non_integer_attributes=%d|'
                'math_non_integer_imports=%d|imports=%s|true_divisions=%d|powers=%d|json=0' % (
                    hashlib.sha256(src.encode('utf-8')).hexdigest(), len(lits), len(names), len(mattr), len(from_math),
                    ','.join(sorted(set(imps))), ndiv, npow))
    return len(lits) + len(names) + len(mattr) + len(from_math)


STATS = {'div': 0, 'div_int_int': 0, 'pow': 0, 'float_seen': 0}


def _cdiv(a, b):
    STATS['div'] += 1
    if type(a) is int and type(b) is int:
        STATS['div_int_int'] += 1
    r = a / b
    STATS['float_seen'] += sum(1 for v in (a, b, r) if isinstance(v, (float, complex)))
    return r


def _cpow(a, b):
    STATS['pow'] += 1
    r = a ** b
    STATS['float_seen'] += sum(1 for v in (a, b, r) if isinstance(v, (float, complex)))
    return r


class Rewrite(ast.NodeTransformer):
    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Div):
            return ast.copy_location(ast.Call(ast.Name('_cdiv', ast.Load()), [node.left, node.right], []), node)
        if isinstance(node.op, ast.Pow):
            return ast.copy_location(ast.Call(ast.Name('_cpow', ast.Load()), [node.left, node.right], []), node)
        return node

    def visit_AugAssign(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Div) and isinstance(node.target, ast.Name):
            call = ast.Call(ast.Name('_cdiv', ast.Load()), [ast.Name(node.target.id, ast.Load()), node.value], [])
            return ast.copy_location(ast.Assign([ast.Name(node.target.id, ast.Store())], call), node)
        return node


def exercise(ns):
    """the allowed-point runs and the predicate-only guard calls; returns every value produced"""
    out = []
    a = ns['Traj'](Fr(1, 2), Fr(1, 27), bound=True)
    for _ in range(3):
        a.taylor_step()
    out += list(a.obs(729).values()) + [a.bound_row(), a.obs_bound_row(729), a.berr, a.bR, a.bsum]
    r = a.read_at(Fr(7, 64))
    out += list(r.obs(81).values()) + [r.bound_row(), r.obs_bound_row(81), r.berr]
    b = ns['Traj'](Fr(3, 4), Fr(4, 81))
    b.advance_to(Fr(3, 32))
    out += list(b.obs(81).values())
    for q in (Fr(0), Fr(12345), Fr(9999, 1000), Fr(1, 3)):
        out.append(ns['_sci_up'](q))

    def trip(*x, **k):
        raise RuntimeError('TRIPWIRE')
    saved = (ns['fx'], ns['Traj'].taylor_step, ns['Traj'].obs)
    ns['fx'] = trip; ns['Traj'].taylor_step = trip; ns['Traj'].obs = trip
    try:
        for d, y, kw in ((Fr(3, 5), Fr(1, 27), {}), (Fr(1, 2), Fr(2, 27) + Fr(1, 1 << 300), {}), (Fr(1, 4), '0.0740740740740741', {}),
                         (Fr(3, 5), Fr(2, 27), {'allow_reserved': True}), (Fr(1, 10), Fr(1, 27), {})):
            out.append(ns['guard_checks'](d, y, **kw))
    finally:
        ns['fx'], ns['Traj'].taylor_step, ns['Traj'].obs = saved
    return out


def main():
    path = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else None
    label = sys.argv[3] if len(sys.argv) > 3 else 'engine'
    src = open(path, encoding='utf-8').read()
    total = static(path, src)
    rows.append(clear('float_scan_a', '1/2', ['1/27']))
    rows.append(clear('float_scan_b', '3/4', ['4/81']))
    # (2) rewrite
    tree = ast.fix_missing_locations(Rewrite().visit(ast.parse(src)))
    ns = {'_cdiv': _cdiv, '_cpow': _cpow, '__name__': 'traj_scan_rewrite'}
    exec(compile(tree, path, 'exec'), ns)
    vals = exercise(ns)
    bad_vals = sum(1 for v in vals if isinstance(v, (float, complex)))
    rows.append('FLOAT_DYNAMIC_REWRITE|true_divisions_run=%d|int_over_int_divisions=%d|powers_run=%d|float_or_complex_operands_or_results=%d|'
                'float_values_returned=%d|json=0' % (STATS['div'], STATS['div_int_int'], STATS['pow'], STATS['float_seen'], bad_vals))
    total += STATS['div_int_int'] + STATS['float_seen'] + bad_vals
    # (3) trace
    target = os.path.abspath(path)
    ns2 = {'__name__': 'traj_scan_trace', '__file__': target}
    code = compile(src, target, 'exec')
    exec(code, ns2)
    seen = {}; bad = []; events = [0, 0]

    def classify(v, depth, where):
        events[1] += 1
        t = type(v)
        seen[t.__name__] = seen.get(t.__name__, 0) + 1
        if t is float or t is complex:
            bad.append(where)
            return
        if depth < 4 and t in (tuple, list, set, frozenset):
            for x in v:
                classify(x, depth + 1, where)
        elif depth < 4 and t is dict:
            for k, x in v.items():
                classify(k, depth + 1, where); classify(x, depth + 1, where)

    def local_tracer(frame, event, arg):
        if event in ('line', 'return'):
            events[0] += 1
            where = '%s:%d' % (frame.f_code.co_name, frame.f_lineno)
            for name, v in frame.f_locals.items():
                classify(v, 0, where + ':' + name)
            if event == 'return':
                classify(arg, 0, where + ':<return>')
        return local_tracer

    def global_tracer(frame, event, arg):
        return local_tracer if frame.f_code.co_filename == target else None

    sys.settrace(global_tracer)
    try:
        vals2 = exercise(ns2)
    finally:
        sys.settrace(None)
    bad_vals2 = sum(1 for v in vals2 if isinstance(v, (float, complex)))
    rows.append('FLOAT_DYNAMIC_TRACE|events=%d|values_classified=%d|float_or_complex_values=%d|first=%s|types_seen=%s|json=0' % (
        events[0], events[1], len(bad) + bad_vals2, bad[0] if bad else 'none', ','.join('%s:%d' % (k, seen[k]) for k in sorted(seen))))
    total += len(bad) + bad_vals2
    rows.append('FLOAT_SUMMARY|engine=%s|float_findings=%d|float_used=%d|verdict=%s|json=0' % (
        label, total, 0 if total == 0 else 1, 'MEASURED_PASS' if total == 0 else 'MEASURED_FAIL'))
    body = '\n'.join(rows) + '\n'
    if outdir:
        name = os.path.join(outdir, 'float_scan_%s.hbp' % label)
        with open(name, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(body)
        with open(name + '.sha256', 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('%s  %s\n' % (hashlib.sha256(body.encode('utf-8')).hexdigest(), os.path.basename(name)))
    print(body, end='')
    return 1 if total else 0


if __name__ == '__main__':
    raise SystemExit(main())
