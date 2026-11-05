# Blocks until the mutation log has at least K verdicts or holds its REMAIN row, or until SECONDS pass. It reads one local file every 20 s and starts nothing.
import sys
import time

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
k, secs = int(sys.argv[1]), int(sys.argv[2])
log = sys.argv[3] if len(sys.argv) > 3 else W + "/out/mut_run.log"
t0 = time.time()
while time.time() - t0 < secs:
    text = open(log, encoding="utf8", errors="replace").read()
    n = text.count("MUTANT|")
    if n >= k or "REMAIN|" in text or "Traceback" in text:
        break
    time.sleep(20)
print("WAIT|verdicts=%d|secs=%d|remain_row=%d|json=0" % (n, time.time() - t0, int("REMAIN|" in text)))
