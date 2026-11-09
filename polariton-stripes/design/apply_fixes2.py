# apply_fixes2.py HBP: the second review's repairs on top of apply_fixes.py; each old text must occur once.
import sys
p = sys.argv[1]
t = open(p).read()
def rep(old, new):
    global t
    n = t.count(old)
    assert n == 1, (n, old[:90])
    t = t.replace(old, new)
def row(kind_id):
    for ln in t.split('\n'):
        if ln.startswith(kind_id + '|'):
            return ln
    raise KeyError(kind_id)
def field(rid, name, new=None, append=None, kind='STRIPES_PREDICT'):
    ln = row('%s|id=%s' % (kind, rid))
    parts = ln.split('|')
    for i, f in enumerate(parts):
        if f.startswith(name + '='):
            parts[i] = name + '=' + (new if new is not None else f[len(name) + 1:] + append)
            break
    else:
        raise KeyError((rid, name))
    rep(ln, '|'.join(parts))

# B1: falsifiers limited to scored reads
field('Q03', 'falsifier', new='a_scored_interval_wholly_outside_the_band_(MISS);_powers_1,_3,_4_miss_by_over_0.1')
field('Q04', 'falsifier', new='a_scored_ratio_outside_[1/5,3/10]_or_D(1/8)_outside_(0,1/20)')
field('Q05', 'falsifier', new='R-1/4<=0_or_outside_its_band_at_a_scored_ratio_(t=1)')
field('Q06', 'falsifier', new='B_e18<=0_or_c_outside_[1/2,3/2]_at_a_scored_read_(t=1/2,_1)_(c_near_0:_no_correction;_near_2:_the_dropped_ansatz)')
field('Q07', 'falsifier', new='a_scored_ratio_outside_its_band;_at_t=2_Q_W_at_or_above_the_law_read_and_report')
field('E04', 'falsifier', new='a_flag_or_a_scored_ratio_outside_[1/4-1/100-4SE,1/4+1/100+4SE]_(powers_1,_3_give_1/2,_1/8)')
field('E13', 'falsifier', new='a_MISS,_or_a_scored_band_verdict_(P02_t=2,_P08_t=1)_reversed')
field('E15', 'falsifier', new='a_MISS,_a_scored_order_claim_not_as_stated,_or_a_scored_cross-read_(P08_t=1)_other_than_predicted')
rep('read-and-report_items_have_no_verdict|json=0',
    'read-and-report_items_have_no_verdict,_and_falsifiers_are_evaluated_on_scored_reads_only|json=0')
# E15: the thinnest order link rests on an exposed VNC value
rep('scored:_the_order_claims_at_P05_and_P08_(t=1,_2;_comparisons_on_common_samples)_and_the_value_and_cross_reads_at_P08_t=1',
    'scored:_the_order_claims_among_variants_on_common_samples_at_P05_and_P08_(t=1,_2),_except_VNC>LOCK_at_P05_t=1_(a_7.6_percent_margin_on_an_exposed_VNC_value),_read_and_report,_and_the_value_and_cross_reads_at_P08_t=1')
# one criterion for s=0 second moments (Q07 y=0 t=2 and E18 (0,2))
rep('field_values_fixed_by_the_start_lattice_alone_(atom_counts,_E07_q_k)_are_scored_at_every_point;' if False else 'and_values_fixed_by_the_start_lattice_alone_(atom_counts,_E07_q_k)_are_scored_at_every_point;',
    'and_values_fixed_by_the_start_lattice_alone_(atom_counts,_E07_q_k)_are_scored_at_every_point;_at_s=0_every_value_read_is_fixed_by_exact_symmetry_except_the_second_moments_Q_W_and_E[abs(B_W)^2],_which_are_exposed_at_(delta,0,t)_when_a_receipt_files_C2_and_f_at_the_same_(delta,t)_with_abs(s)<=1/4,_since_they_move_by_O(s^2)_only_(Q07_y=0_t=2_and_E18_(0,2));_the_triple_test_runs_at_any_N_and_any_u,_since_the_linear_law_depends_on_u_only_through_delta=x+u;')
rep('a_triple_(delta,abs(s),t),_s=y_sqrt(N),_is_exposed_when_a_receipt_at_4a97736_files_quantum_B,_C2_or_f_there_at_any_N_(X08)',
    'a_triple_(delta,abs(s),t),_s=y_sqrt(N),_is_exposed_when_a_receipt_at_4a97736_files_quantum_B,_C2_or_f_there_at_any_N_or_u_(X08)')
field('E18', 'predicted', new=row('STRIPES_PREDICT|id=E18').split('predicted=')[1].split('|')[0].replace(
    ';_read-and-report_(X08):_(1/54,2)_and_(1/108,2);_scored:_(0,2),_(1/27,1),_(1/54,1)',
    ';_read-and-report_(X08):_(1/54,2),_(1/108,2)_and_(0,2),_whose_quantum_side_Q_W_is_filed_at_t=2_(s=1/2,_1/4)_or_reached_from_s=1/4_to_O(s^2)_(rule_EXPOSED);_scored:_(1/27,1),_(1/54,1)'))
rep('E17_wholly_(P10:_(1/2,_s=1));_E18_at_(1/54,2)_and_(1/108,2)_(both_sides_filed_at_N=6561,_X05)',
    'E17_wholly_(P10:_(1/2,_s=1));_E18_at_(1/54,2),_(1/108,2)_and_(0,2)_(its_quantum_side_Q_W_exposed;_the_s=0_criterion_of_rule_EXPOSED);_E15_VNC>LOCK_at_P05_t=1')
rep(',_and_every_value_read_at_QR5_(N=81),_P01,_P02,_P07,_P09,_P11,_P12,_R4_and_at_t<=1_at_P08,_P13,_P14,_R1-R3,_QR3_except_s=1_at_t=1/2',
    ',_and_every_value_read_at_QR5_(N=81),_P01,_P02,_P07,_P09,_P11,_P12,_R4_and_at_t<=1_at_P08,_P13,_P14,_R1-R3,_QR3_except_s=1_at_t=1/2_(further_delta=1/2_receipts_found_by_the_second_review,_TRACE-N81,_the_GRID-band_files,_LAW-PREDICTIONS,_compare_receipt,_RECEIPT-BASELINE,_RECEIPT-DYADIC_at_(100,1/2,s=1/2),_lie_inside_the_listed_triples)')
# repair and smoke records
r23 = row('STRIPES_REPAIR|id=RP23')
rep(r23, r23 + '\nSTRIPES_REPAIR|id=RP24|rows=Q03-Q07,_E04,_E13,_E15,_READ3|action=second_review_blocking:_falsifiers_limited_to_scored_reads,_and_READ3_states_it|json=0'
    '\nSTRIPES_REPAIR|id=RP25|rows=EXPOSED,_X08,_E15,_E18|action=second_review_notes:_one_s=0_criterion_for_second_moments_(Q07_y=0_t=2_and_E18_(0,2)_both_read_and_report;_the_unsupported_N=6561_ensemble_reason_withdrawn);_the_triple_test_at_any_N_or_u;_X08_sources_completed;_E15_VNC>LOCK_at_P05_t=1_read_and_report|json=0')
s9 = row('STRIPES_SMOKE|id=SM9')
rep(s9, s9 + '\nSTRIPES_SMOKE|id=SM10|seat=second_review|calls=key-only_scans_at_4a97736_(git_grep_-l_by_field_family;_keys.py_with_tags_blanked;_triple_tests_against_every_scored_(delta,abs(s),t)_at_any_u);_its_first_contact/out_scan_printed_untagged_.txt_line_heads_(delta_values_and_the_non-row_(729,1/2,1/108)_at_t=3,_a_read-and-report_point);_keys.py_patched_to_blank_them|excluded=no_engine_run;_no_scored_read_affected|json=0')
# header and END
rep(',_E17_wholly;', ',_E17_wholly;_falsifiers_count_scored_reads_only;')
lines = [ln for ln in t.split('\n') if ln]
kinds = []
for ln in lines:
    k = ln.split('|', 1)[0]
    if k not in kinds:
        kinds.append(k)
pred = [ln for ln in lines if ln.startswith('STRIPES_PREDICT|')]
der = sum(1 for ln in pred if '|tag=DERIVED|' in ln)
con = sum(1 for ln in pred if '|tag=CONJECTURE|' in ln)
assert der == 8 and con == 18
body = [ln for ln in lines if not ln.startswith('STRIPES_END|')]
cnt = ','.join('%s:%d' % (k, sum(1 for ln in body if ln.split('|', 1)[0] == k) + (1 if k == 'STRIPES_END' else 0)) for k in kinds)
end = 'STRIPES_END|rows=%d|predict_rows=%d|derived=%d|conjecture=%d|kinds=%d|counts=%s|json=0' % (len(body) + 1, len(pred), der, con, len(kinds), cnt)
rep(row('STRIPES_END'), end)
open(p, 'w').write(t)
print(end)
