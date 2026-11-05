# Byte difference of two PE files, with the bytes grouped into runs and each run placed in its section. Reads only.
import struct
import sys

a = open(sys.argv[1], "rb").read()
b = open(sys.argv[2], "rb").read()
print("PE_DIFF|size_a=%d|size_b=%d|json=0" % (len(a), len(b)))


def sections(data):
    pe = struct.unpack_from("<I", data, 0x3c)[0]
    count = struct.unpack_from("<H", data, pe + 6)[0]
    stamp = struct.unpack_from("<I", data, pe + 8)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    start = pe + 24 + opt
    out = []
    for i in range(count):
        name = data[start + 40 * i: start + 40 * i + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, vaddr, rsize, rptr = struct.unpack_from("<IIII", data, start + 40 * i + 8)
        out.append((name, rptr, rsize, vaddr, vsize))
    return pe, stamp, out


pe, stamp_a, sec = sections(a)
_, stamp_b, sec_b = sections(b)
print("PE_STAMP|a=%d|b=%d|json=0" % (stamp_a, stamp_b))
for s in sec:
    print("PE_SECTION|name=%s|raw_ptr=%d|raw_size=%d|va=%d|vsize=%d|json=0" % s)
print("PE_SAME_SECTIONS|%d|json=0" % int(sec == sec_b))


def where(off):
    if off < sec[0][1]:
        return "headers"
    for name, ptr, size, _, _ in sec:
        if ptr <= off < ptr + size:
            return name
    return "tail"


n = min(len(a), len(b))
runs = []
i = 0
total = 0
while i < n:
    if a[i] != b[i]:
        j = i
        while j < n and (a[j] != b[j] or (j + 8 < n and a[j:j + 8] != b[j:j + 8])):
            j += 1
        runs.append((i, j))
        total += sum(1 for k in range(i, j) if a[k] != b[k])
        i = j
    else:
        i += 1
print("PE_DIFF_TOTAL|bytes_different=%d|runs=%d|json=0" % (total, len(runs)))
for i, j in runs[:60]:
    print("PE_RUN|off=%d|len=%d|in=%s|a=%s|b=%s|a_text=%r|b_text=%r|json=0" % (i, j - i, where(i), a[i:min(j, i + 24)].hex(), b[i:min(j, i + 24)].hex(), a[max(0, i - 8):j + 8][:120], b[max(0, i - 8):j + 8][:120]))
# Every path-looking string with .pdb in each.
for label, data in (("a", a), ("b", b)):
    k = 0
    while True:
        k = data.find(b".pdb", k)
        if k < 0:
            break
        s = k
        while s > 0 and 32 <= data[s - 1] < 127:
            s -= 1
        print("PE_PDB|file=%s|off=%d|text=%s|json=0" % (label, s, data[s:k + 4].decode("ascii", "replace")))
        k += 4
