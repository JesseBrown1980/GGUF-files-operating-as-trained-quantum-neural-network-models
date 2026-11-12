#!/usr/bin/env python3
"""Independent spectral replay of the archived 2026-11-05 polariton hour-long run.

Source model: JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models
  src/bin/polariton_three_mode.rs, functions build/Space::sector/read.
Filed receipt: polariton/RECEIPT.hbp
Timing: polariton/TIMING-LOCAL-20261104.hbp
Hosted example: https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/actions/runs/42071602272

SciPy float64 diagonalization is independent from the repo's Rust fixed-point
integer-shear integrator. This checks numerical observables, not identical bytes.
Run: python3 polariton_6561_independent_replay.py
Needs numpy, scipy, threadpoolctl. No network calls.
"""
import csv
import hashlib
import io
import time
from pathlib import Path

import numpy as np
from scipy.linalg import eigh_tridiagonal
from threadpoolctl import threadpool_limits

N = 6561
T = (1, 2, 3, 4, 6, 8)
# Each tuple: delta, six filed jbar_ppb, six filed C1_ppm,
# six filed C2_ppm, historical local runtime in ms.
FILED = [
    ("-2",   [324216649,33879207,259981138,121728839,227790633,308882690], [593,61,475,222,416,565], [0,0,0,0,0,0], 19163),
    ("-1",   [998812703,3962693979,8652415264,14296293614,22644245334,21001613616], [1217,4830,10544,17416,27579,25586], [0,1,7,17,35,24], 19337),
    ("-1/2", [1275081998,9900622983,56040480334,249859618759,694349683827,130400800922], [1166,9045,50978,223919,610535,117001], [0,9,277,4610,24539,2267], 18321),
    ("0",    [1379923404,13054094865,94726714750,524243338996,1260511142858,130577601243], [841,7943,56966,299797,684946,75966], [0,16,793,19863,83658,3654], 19700),
    ("1/2",  [1275518058,9945377388,57838569396,292334751889,2132183876916,1300044130533], [388,3022,17328,82110,412622,291143], [0,9,304,7015,237433,105211], 19380),
    ("1",    [999482162,3990646207,8930298751,15678717110,33063500034,50593582693], [-1,-2,-8,-24,-96,-200], [0,1,7,23,95,199], 19484),
    ("2",    [324659214,33495857,261126810,120515911,226073541,307731208], [-198,-21,-160,-74,-138,-188], [0,0,0,0,0,0], 19811),
]

def independent_sector(n, delta):
    """Direct construction from the three-mode Hamiltonian, no Rust code reuse.

    |j> := |n_+=j,n_-=j,n_0=n-2j>.
    H_jj = x (2j) + u (n0*(2j)+j*j)/n with x=delta-1,u=1.
    H_j,j+1 = (j+1)*sqrt((n-2j)*(n-2j-1))/n.
    The above follows the Rust build() normalization and is not the
    modulo-prime circulant jump law.
    """
    k = np.arange(n // 2 + 1, dtype=np.float64)
    n0 = n - 2*k
    x = delta-1.0
    d = x*(2*k) + (n0*(2*k) + k*k)/n
    o = (k[:-1]+1)*np.sqrt((n-2*k[:-1])*(n-2*k[:-1]-1))/n
    return k, n0, d, o

def run_one(delta):
    k, n0, diagonal, coupling = independent_sector(N, delta)
    start = time.perf_counter()
    eigvals, eigvecs = eigh_tridiagonal(diagonal, coupling)
    coeffs = eigvecs[0, :]
    psi = eigvecs @ (coeffs[:, None]*np.exp(-1j*np.outer(eigvals,T)))
    prob = (psi.conj()*psi).real
    norm = prob.sum(axis=0)
    jbar = k @ prob
    np_nm = (k*k) @ prob
    n0pairs = (n0*2*k) @ prob
    pair_coeff = (k[:-1]+1)*np.sqrt((N-2*k[:-1])*(N-2*k[:-1]-1))
    re_p = (pair_coeff[:,None]*(psi[1:,:].conj()*psi[:-1,:]).real).sum(axis=0)
    c1_ppm = 2.0*(n0pairs + 2*re_p)/(N*(N-1))*1e6
    c2_ppm = 2.0*np_nm/(N*(N-1))*1e6
    return jbar*1e9,c1_ppm,c2_ppm,norm,time.perf_counter()-start

def main():
    records=[]
    total_cpu=0.0
    max_rel=0.0
    max_abs_c1=0.0
    max_abs_c2=0.0
    with threadpool_limits(limits=1):
        for name,ej,ec1,ec2,ms in FILED:
            delta = -0.5 if name == "-1/2" else 0.5 if name == "1/2" else float(name)
            obs=run_one(delta)
            total_cpu += obs[-1]
            for idx,t in enumerate(T):
                model_j,model_c1,model_c2 = (float(obs[q][idx]) for q in range(3))
                rel_j=abs(model_j-ej[idx])/max(abs(ej[idx]),1)
                err_c1=abs(model_c1-ec1[idx])
                err_c2=abs(model_c2-ec2[idx])
                max_rel=max(max_rel,rel_j)
                max_abs_c1=max(max_abs_c1,err_c1)
                max_abs_c2=max(max_abs_c2,err_c2)
                assert rel_j < 2e-8, (name,t,"jbar",rel_j)
                assert err_c1 < 1.0, (name,t,"c1",err_c1)
                assert err_c2 < 1.0, (name,t,"c2",err_c2)
                assert abs(float(obs[3][idx])-1.0) < 1e-12
                records.append([name,t,ej[idx],f"{model_j:.6f}",f"{rel_j:.12e}",ec1[idx],f"{model_c1:.8f}",ec2[idx],f"{model_c2:.8f}","PASS"])
            print(f"delta={name:>4}  spectral_seconds={obs[-1]:8.3f}  filed_local_seconds={ms/1000:6.3f}  reads=6  PASS")
    assert len(records)==42
    historical=sum(x[-1] for x in FILED)/1000
    print(f"TOTAL|rows={len(records)}|observables={len(records)*3}|independent_elapsed_seconds={total_cpu:.3f}|historical_local_seconds={historical:.3f}|speed_ratio_cross_machine={historical/total_cpu:.3f}|max_pair_relative={max_rel:.3e}|max_C1_absolute_ppm={max_abs_c1:.5f}|max_C2_absolute_ppm={max_abs_c2:.5f}|status=PASS")
    # Auditable fixed-order CSV. Floating results are independent numerical
    # values; the reference uses fixed-point integer shears, so don't hash-compare
    # the state and don't call it an exact byte-for-byte replay.
    out=Path(__file__).with_name("polariton_6561_independent_replay.csv")
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["delta","t","filed_jbar_ppb","spectral_jbar_ppb","relative_error_jbar","filed_C1_ppm","spectral_C1_ppm","filed_C2_ppm","spectral_C2_ppm","verdict"])
        w.writerows(records)
    print(f"CSV_SHA256|{hashlib.sha256(out.read_bytes()).hexdigest()}|path={out.name}")

if __name__=="__main__":
    main()
