"""rv_floatscan.py -- the review lane's own float scan (float_used=0).

Source: a Rust lexer strips line and nested block comments, string, raw string, byte string and char literals, then
counts in the code that remains: the type tokens f32 and f64; float literals (a decimal digit run followed by '.' and a
digit, or by '.' that is neither a second '.' nor an identifier start, or by an exponent, or a decimal literal with an
f32/f64 suffix); hex, octal and binary literals are taken whole first, so 0x...E... is never read as an exponent.
Comments and strings are counted separately for f32/f64 mentions (reported, never a code use).
Binary (optional): counts x86 floating-point arithmetic, conversion and compare mnemonics in an objdump listing.
usage: rv_floatscan.py src FILE.rs [...] | rv_floatscan.py bin OBJDUMP_LISTING | rv_floatscan.py selftest"""
import re
import sys

IDS = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789')


def strip(src):
    """Return (code with comments/literals blanked, comment+literal text)."""
    out, aside = [], []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if src.startswith('//', i):
            j = src.find('\n', i)
            j = n if j < 0 else j
            aside.append(src[i:j])
            out.append(' ' * (j - i))
            i = j
        elif src.startswith('/*', i):
            depth, j = 1, i + 2
            while j < n and depth:
                if src.startswith('/*', j):
                    depth, j = depth + 1, j + 2
                elif src.startswith('*/', j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            aside.append(src[i:j])
            out.append(re.sub(r'[^\n]', ' ', src[i:j]))
            i = j
        elif re.match(r'b?r#*"', src[i:i + 8]) and (i == 0 or src[i - 1] not in IDS):
            m = re.match(r'b?r(#*)"', src[i:])
            hashes = m.group(1)
            end = src.find('"' + hashes, i + m.end())
            j = n if end < 0 else end + 1 + len(hashes)
            aside.append(src[i:j])
            out.append(re.sub(r'[^\n]', ' ', src[i:j]))
            i = j
        elif ch == '"' or (ch == 'b' and src.startswith('b"', i) and (i == 0 or src[i - 1] not in IDS)):
            j = i + (2 if ch == 'b' else 1)
            while j < n and src[j] != '"':
                j += 2 if src[j] == '\\' else 1
            j += 1
            aside.append(src[i:j])
            out.append(re.sub(r'[^\n]', ' ', src[i:j]))
            i = j
        elif ch == "'":
            m = re.match(r"'(\\(x[0-9a-fA-F]{2}|u\{[0-9a-fA-F]+\}|.)|[^\\'])'", src[i:])
            if m:  # a char literal; otherwise a lifetime, left in the code
                aside.append(m.group(0))
                out.append(' ' * m.end())
                i += m.end()
            else:
                out.append(ch)
                i += 1
        else:
            out.append(ch)
            i += 1
    return ''.join(out), '\n'.join(aside)


NUM = re.compile(r'0[xX][0-9a-fA-F_]+|0[oO][0-7_]+|0[bB][01_]+|[0-9][0-9_]*')


def float_literals(code):
    found = []
    i, n = 0, len(code)
    while i < n:
        if code[i].isdigit() and (i == 0 or code[i - 1] not in IDS):
            m = NUM.match(code, i)
            j = m.end()
            tok = m.group(0)
            if tok[:2].lower() in ('0x', '0o', '0b'):
                i = j
                while i < n and code[i] in IDS:
                    i += 1
                continue
            is_float = False
            k = j
            if k < n and code[k] == '.':
                nxt = code[k + 1] if k + 1 < n else ''
                if nxt.isdigit():
                    is_float = True
                elif nxt != '.' and nxt not in IDS:
                    is_float = True
            if k < n and code[k] in 'eE' and re.match(r'[eE][+-]?[0-9]', code[k:k + 3]):
                is_float = True
            if re.match(r'_?f(32|64)\b', code[k:k + 4]):
                is_float = True
            if is_float:
                found.append(re.match(r'[0-9][0-9_]*(?:\.[0-9_]*)?(?:[eE][+-]?[0-9_]+)?(?:_?f(?:32|64))?', code[i:]).group(0))
            i = j
        else:
            i += 1
    return found


def scan_src(path):
    src = open(path, encoding='utf-8').read()
    code, aside = strip(src)
    types = re.findall(r'\bf(?:32|64)\b', code)
    lits = float_literals(code)
    calls = re.findall(r'\.(?:sqrt|powf|powi|ln|log10|log2|exp|sin|cos|tan|floor|ceil|round|trunc|fract|hypot|to_degrees)\s*\(', code)
    aside_mentions = re.findall(r'\bf(?:32|64)\b', aside)
    return dict(types=len(types), literals=len(lits), float_method_calls=len(calls), mentions_in_comments_or_strings=len(aside_mentions),
                examples=';'.join(lits[:3] + types[:3]))


FP = re.compile(r'\t(v?(?:add|sub|mul|div|sqrt|min|max)(?:sd|ss|pd|ps)|v?cvt\w*(?:sd|ss|pd|ps|si2sd|si2ss)\w*|v?u?comis[sd]|'
                r'v?round[sp][sd]|vfmadd\w+|f(?:ld|st|stp|add|sub|mul|div|sqrt|ild|istp|comi|ucomi)\w*)\s')


def scan_bin(listing):
    counts = {}
    for ln in open(listing, encoding='utf-8', errors='replace'):
        m = FP.search(ln)
        if m:
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    return counts


def selftest():
    sample = ('fn a() -> f64 { 1.5 }\nlet x = 2.;\nlet y = 3e5;\nlet z = 7f32;\nlet h = 0x9E37_79B9_7F4A_7C15;\n'
              'let r = 0..NV;\nlet s = x.0;\nlet t = 2.max(3);\n// f64 in a comment 1.0\nlet u = "f32 1.0";\nlet c = \'a\';\n'
              "fn l<'a>(v: &'a str) {}\nlet e = 1_000.0_1;\nlet w = 1E-3;\n")
    code, aside = strip(sample)
    lits = float_literals(code)
    types = re.findall(r'\bf(?:32|64)\b', code)
    print('RV_FLOATSCAN_SELFTEST|literals_found=%d|expected=6|types_found=%d|expected=1|literals=%s|json=0' % (
        len(lits), len(types), ';'.join(x.strip() for x in lits)))


def main():
    if sys.argv[1] == 'selftest':
        selftest()
    elif sys.argv[1] == 'src':
        tot = 0
        for p in sys.argv[2:]:
            d = scan_src(p)
            tot += d['types'] + d['literals'] + d['float_method_calls']
            print('RV_FLOATSCAN_SRC|file=%s|f32_f64_types_in_code=%d|float_literals_in_code=%d|float_method_calls=%d|'
                  'f32_f64_mentions_in_comments_or_strings=%d|examples=%s|json=0' % (
                      p, d['types'], d['literals'], d['float_method_calls'], d['mentions_in_comments_or_strings'], d['examples'] or 'none'))
        print('RV_FLOATSCAN_SRC_DONE|files=%d|code_uses=%d|float_used=%d|json=0' % (len(sys.argv) - 2, tot, int(tot > 0)))
    elif sys.argv[1] == 'bin':
        cnt = scan_bin(sys.argv[2])
        print('RV_FLOATSCAN_BIN|listing=%s|fp_instructions=%d|by_mnemonic=%s|json=0' % (
            sys.argv[2], sum(cnt.values()), ','.join('%s:%d' % kv for kv in sorted(cnt.items())) or 'none'))


if __name__ == '__main__':
    main()
