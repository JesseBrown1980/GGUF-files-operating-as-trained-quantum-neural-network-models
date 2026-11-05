import sys
sys.path.insert(0,'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
for q in ('1/50','2/25','8/25','32/25','128/25','512/25'):
    print(q, dec(mathieu_f(F(q)),6))
