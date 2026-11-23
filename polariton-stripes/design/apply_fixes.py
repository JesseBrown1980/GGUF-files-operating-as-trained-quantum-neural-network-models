# apply_fixes.py HBP: apply the critic's FIX_FIRST repairs to the stripe-phase draft in place; each old text must occur once.
import sys
p = sys.argv[1]
t = open(p).read()
def rep(old, new):
    global t
    n = t.count(old)
    assert n == 1, (n, old[:80])
    t = t.replace(old, new)
def row(rid):
    for ln in t.split('\n'):
        if ln.startswith('STRIPES_PREDICT|id=%s|' % rid):
            return ln
    raise KeyError(rid)
def field(rid, name, new=None, append=None):
    ln = row(rid)
    parts = ln.split('|')
    for i, f in enumerate(parts):
        if f.startswith(name + '='):
            parts[i] = name + '=' + (new if new is not None else f[len(name) + 1:] + append)
            break
    else:
        raise KeyError((rid, name))
    rep(ln, '|'.join(parts))

rep('judges_qo-review_and_referee;_every_row_a_judge_rejected_is_dropped_or_repaired_(STRIPES_REPAIR)',
    'judges_qo-review_and_referee;_every_row_a_judge_rejected_is_dropped_or_repaired_(STRIPES_REPAIR);_the_final_critic_FIX_FIRST_findings_applied_(RP15-RP23)')
rep('rows=26_PREDICT_rows,_Q01-Q07_quantum_and_E01-E19_ensemble;_10_DERIVED,_16_CONJECTURE;_every_CONJECTURE_row_can_read_NOT_MET,',
    'rows=26_PREDICT_rows,_Q01-Q07_quantum_and_E01-E19_ensemble;_8_DERIVED,_18_CONJECTURE;_reads_of_frozen_values_at_exposed_(delta,abs(s),t)_are_read-and-report_(rule_EXPOSED,_X08),_E17_wholly;_every_other_CONJECTURE_row_keeps_scored_reads_and_can_read_NOT_MET,')
# rules
rep('if_none_completes,_its_4096_indices_are_NOT_MEASURED_and_reads_state_the_loss;',
    'if_none_completes,_its_4096_indices_are_NOT_MEASURED_and_reads_state_the_loss;_a_twens_run_batch_(R1-R4)_exiting_4_prints_nothing_too:_it_is_rerun_with_the_same_keys_and_its_last_record_(and_that_record_ctrl_entry)_dropped_until_it_completes,_the_point_keeps_only_the_records_all_64_batches_reached_and_the_rest_are_NOT_MEASURED;')
g = [ln for ln in t.split('\n') if ln.startswith('STRIPES_RULE|id=GUARD|')][0]
rep(g, g + '\nSTRIPES_RULE|id=EXPOSED|rule=a_triple_(delta,abs(s),t),_s=y_sqrt(N),_is_exposed_when_a_receipt_at_4a97736_files_quantum_B,_C2_or_f_there_at_any_N_(X08):_the_linear_law_fixes_every_leading-order_value_by_(delta,s,t)_alone,_so_moving_a_point_in_N_protects_its_samples_and_finite-N_values,_not_those;_at_an_exposed_triple_with_s!=0_every_read_scored_against_a_frozen_value_or_a_frozen_verdict_is_read-and-report_(its_frozen_value_kept_beside,_no_verdict);_exact_identity_and_symmetry_reads_(H8,_SIGNFLIP,_parity,_exchange_atoms,_equalities,_the_iid_identity),_comparisons_of_two_variants_on_the_same_samples_with_no_frozen_value_(E06,_E15_order,_E16),_and_values_fixed_by_the_start_lattice_alone_(atom_counts,_E07_q_k)_are_scored_at_every_point;_the_demoted_reads_are_listed_in_X08_and_in_each_row|json=0')
rep('so_points_moved_in_N_at_fixed_(delta,s)_keep_their_values;',
    'so_points_moved_in_N_at_fixed_(delta,s)_keep_their_values,_and_a_receipt_at_any_N_at_the_same_(delta,s,t)_exposes_them_(rule_EXPOSED);')
# exposure rows
rep('handling=P03-P06_moved_to_N=1296_at_the_same_(delta,s);_P03_found_by_this_seat,_P04-P06_by_both_judges|',
    'handling=P03-P06_moved_to_N=1296_at_the_same_(delta,s);_P03_found_by_this_seat,_P04-P06_by_both_judges;_the_move_protects_samples_and_finite-N_values_only,_so_their_value_reads_are_read-and-report_(X08)|')
rep('handling=P01,_P09,_P10_moved_to_N=1296_and_N=121|',
    'handling=P01,_P09,_P10_moved_to_N=1296_and_N=121;_P01_and_P09_sit_at_y=0_(symmetry,_identity_and_lattice_reads,_scored);_P10_value_reads_are_read-and-report_(X08)|')
rep('seen=twens_runs_and_first-correction_receipts|handling=not_row_points|',
    'seen=twens_runs_and_first-correction_receipts|handling=not_row_points,_but_(6561,-1/4,1/81,_1/162,_1/324)_share_(delta,s)_with_the_N=729_rows_at_y=1/27,_1/54,_1/108:_see_X08|')
rep('seen=no_repo_row_at_N=1296,_324_or_121;',
    'seen=no_repo_row_at_N=1296_or_324;_at_N=121_only_static_u-scans_of_the_spectrum_(CROSS_U,_MARGIN,_LARGE_PARTIAL_rows_in_polariton/second-seat/recheck-ce44be7/window/out/t3_boundary.hbp,_t3_margin.hbp,_t3_partial_large.hbp;_u_varies,_no_B_dynamics);')
x7 = [ln for ln in t.split('\n') if ln.startswith('STRIPES_EXPOSURE|id=X07|')][0]
rep(x7, x7 + '\nSTRIPES_EXPOSURE|id=X08|point=exposed_triples_(delta,abs(s),t)|seen=(a)_polariton-first-correction/RECEIPT-GRID.hbp_with_READ-GRID.hbp:_QE_READ_rows_(B,_D2,_C2,_f)_at_N=6561,_K=1200_and_1600,_t=2:_delta=-1/4,_y=1/81,_1/162,_1/324_(s=1,_1/2,_1/4)_and_delta=1/2,_y=1/162,_1/324_(s=1/2,_1/4);_(b)_polariton-bridge/reviews/opus55-engine-quantum-20261106/dyadic/BRIDGE-ENGINE-QUANTUM.hbp:_FOCK_CERT_READ_at_(6561,-1/4,1/81)_and_(6561,1/2,1/324),_t=1/2,_3/2;_(c)_polariton/second-seat/recheck-ce44be7/contact/out/TRACE-N729.hbp:_B,_C2,_f_at_N=729,_delta_in_{-1,-1/2,0,1/2},_y=1/216_to_4/27_(s=1/8_to_4),_every_t=k/4_to_12;_(d)_the_N=81,_delta=1/2_grid_at_s=1;_found_by_the_final_critic_by_key-only_scans,_rechecked_key-only_by_this_seat_at_4a97736;_no_value_read|triples=delta=-1/4:_(s,t)=(1,1/2),_(1,3/2),_(1,2),_(1/2,2),_(1/4,2);_delta=1/2:_s_in_{1/8,1/4,1/2,1}_at_every_t|handling=read-and-report_(rule_EXPOSED):_Q03_(729,_1/27->1/54,_t=1/2),_Q03_t=2_(R(1/108->1/216)_and_L);_Q04_D(1/4)/D(1/2)_at_N=729;_Q05_t=1/2_and_both_t=2_ratios;_Q06_both_t=2_reads_with_their_sign;_Q07_t=1/2_at_y=1/27_and_every_t=2_band_(y=0_included:_the_s=1/4_receipts_reach_it_to_O(s^2));_E04_t=2_ratio;_E09,_E10_and_E13_at_P03-P06_(every_record)_and_P08_t=2;_E10_ratios;_E14_at_t=2;_E15_value_and_cross_reads_at_P05_(every_record)_and_P08_t=2;_E17_wholly_(P10:_(1/2,_s=1));_E18_at_(1/54,2)_and_(1/108,2)_(both_sides_filed_at_N=6561,_X05)|still_scored=identity_and_symmetry_reads_everywhere_(Q01,_Q02,_E01-E03,_E04_sign-flip,_E05,_E07,_E08,_E12),_comparisons_on_common_samples_(E06,_E15_order,_E16),_and_every_value_read_at_QR5_(N=81),_P01,_P02,_P07,_P09,_P11,_P12,_R4_and_at_t<=1_at_P08,_P13,_P14,_R1-R3,_QR3_except_s=1_at_t=1/2|json=0')
# smoke rows
s7 = [ln for ln in t.split('\n') if ln.startswith('STRIPES_SMOKE|id=SM7|')][0]
rep(s7, s7 + '\nSTRIPES_SMOKE|id=SM8|seat=final_critic|calls=own_float_exact_evolution_(numpy,_dense_eigh;_not_a_repo_engine)_at_N=81,_delta_in_{1/3,1/4},_y_in_{1/54,1/108},_t=0_to_4_by_quarters:_B/(N_y^2)_about_t^2_at_t=1/4,_positive_throughout,_peak_about_27.5_near_t=3.25,_19.6_to_22.2_at_t=4;_key-only_scans_of_the_repo|excluded=delta=1/3_and_delta=1/4_at_every_N;_no_twens_or_QE_run,_no_value_read_at_a_row_point|json=0'
       '\nSTRIPES_SMOKE|id=SM9|seat=this_seat|calls=key-only_rechecks_of_the_X08_receipts_and_the_N=121_files_at_4a97736;_two_ratios_of_frozen_values_(E13_band_at_P08_t=1,_E14_at_t=1)|excluded=no_engine_run,_no_value_read|json=0')
# repair rows
r14 = [ln for ln in t.split('\n') if ln.startswith('STRIPES_REPAIR|id=RP14|')][0]
rp = [
 ('RP15', 'all_value_reads', 'final_critic_blocking_1:_exposure_is_by_(delta,abs(s),t),_since_the_leading-order_values_depend_on_it_alone;_rule_EXPOSED_and_X08_added;_exposed_value_reads_demoted_to_read-and-report_with_their_frozen_values_kept;_the_critic_list_extended_to_P03-P06_and_P10_(TRACE-N729_covers_delta=1/2,_s=1/8_to_1,_at_every_t)_and_to_Q04_N=729_t=1/2_ratio;_E16_and_E15_order_claims_stay_scored_as_comparisons_on_common_samples_with_no_frozen_value'),
 ('RP16', 'E13,_E14', 'to_keep_the_plateau_and_the_crossover_scored_at_unexposed_points:_E13_band_added_at_P08_t=1_from_its_frozen_rho_(1+(n-1)rho);_E14_rescored_at_t=1_from_Q07_frozen_n*_lin_(574.30/46.527=12.343),_t=2_(10.280)_read_and_report;_E14_lower_edge_widened_to_4(1-4SE_rel)'),
 ('RP17', 'Q02', 'final_critic_blocking_2:_B(+-y)>0_removed;_at_N=81,_t=2,_4_the_linear_law_has_n_f_about_12_and_613_against_N=81,_deep_saturation,_where_no_symmetry_or_algebra_fixes_the_sign;_the_signs_are_read_and_report'),
 ('RP18', 'Q03,_E04', 'final_critic_blocking_2:_retagged_CONJECTURE:_their_limits_are_derived,_the_size_of_the_quantum_or_ensemble_y^4_term_inside_their_finite-y_bands_is_not_(as_RP04_for_Q04);_E04_paired_sign-flip_read_remains_an_exact-symmetry_read;_DERIVED_8,_CONJECTURE_18'),
 ('RP19', 'STOP', 'twens_run_batch_exit_4_handling_frozen_(same_keys,_last_record_and_its_ctrl_entry_dropped,_records_reached_by_all_64_batches_kept)'),
 ('RP20', 'X07', 'the_claim_of_no_repo_row_at_N=121_corrected:_static_u-scans_exist,_harmless'),
 ('RP21', 'Q03,_Q05', 't=2_values_relabelled_two-term_series;_full_noiseless_trajectory_R-1/4=+2.4268e-3_(1/54->1/108),_+6.0702e-4_(1/108->1/216)_frozen_beside,_L-1/4_about_+4e-7;_bands_unchanged'),
 ('RP22', 'E04,_E12', 'the_CLT_basis_of_their_SE_thresholds_stated_in_each_row_(rule_SE)'),
 ('RP23', 'STRIPES_SMOKE', 'SM8_(final_critic_float_check_at_excluded_points)_and_SM9_(this_seat_key-only_rechecks)_added'),
]
rep(r14, r14 + ''.join('\nSTRIPES_REPAIR|id=%s|rows=%s|action=%s|json=0' % x for x in rp))
# Q02
field('Q02', 'predicted', new='abs(B(y)-B(-y))<=e_B(y)+e_B(-y)_and_abs(A(y)+A(-y))<=(N/2)(A1_err(y)+A1_err(-y))+2*10^-18_at_all_7;_the_signs_of_B(+-y)_read_and_report_(RP17)')
field('Q02', 'falsifier', new='a_difference_above_its_bound')
# Q03
field('Q03', 'statement', append=';_the_limit_1/4_is_DERIVED,_the_finite-y_band_is_conjectured_(the_size_of_the_quantum_y^4_term_is_not_derived;_RP18)')
rep('predicted=every_read_interval_inside_[99/400,101/400];_classical_R-1/4_from_3.77e-6_to_6.09e-4,_L-1/4=-8.0e-6;',
    'predicted=every_read_interval_inside_[99/400,101/400];_two-term-series_R-1/4_from_3.77e-6_to_6.09e-4,_L-1/4=-8.0e-6_(the_full_noiseless_trajectory_gives_R-1/4=+2.4268e-3,_+6.0702e-4_at_t=2_for_1/54->1/108,_1/108->1/216,_so_L-1/4_about_+4e-7);_read-and-report_(X08):_(729,_1/27->1/54,_t=1/2),_R(1/108->1/216)_and_L_at_t=2,_so_11_of_14_reads_scored;')
field('Q03', 'tag', new='CONJECTURE')
# Q04
field('Q04', 'predicted', append=';_D(1/4)/D(1/2)_at_N=729_read-and-report_(X08:_s=1,_t=1/2),_the_other_3_ratios_and_both_D(1/8)_bands_scored')
# Q05
rep('R-1/4=+6.031e-5,_+4.912e-4,_+1.2255e-4,_+2.4604e-3,_+6.091e-4;',
    'R-1/4=+6.031e-5,_+4.912e-4,_+1.2255e-4,_+2.4604e-3,_+6.091e-4_(t=2:_two-term_series;_full_trajectory_+2.4268e-3,_+6.0702e-4);_read-and-report_(X08):_the_t=1/2_ratio_and_both_t=2_ratios,_so_the_two_t=1_ratios_are_scored;')
# Q06
field('Q06', 'predicted', append=';_read-and-report_(X08):_both_t=2_reads_with_their_sign,_so_4_reads_scored_(t=1/2,_1)')
# Q07
field('Q07', 'predicted', append=';_read-and-report_(X08):_t=1/2_at_y=1/27_and_every_t=2_band;_scored:_t=1/2_at_y=1/54_and_t=1_at_all_three_y;_n*_Q_infinite_at_y=0_scored_(it_follows_from_Q01)')
# E04
field('E04', 'statement', append=';_the_paired_sign-flip_read_rests_on_an_exact_symmetry,_the_ratio_band_is_conjectured_(the_ensemble_y^4_term_is_not_derived;_RP18);_its_SE_thresholds_are_CLT-based_(rule_SE)')
field('E04', 'predicted', append=';_the_t=2_ratio_(1/54->1/108)_read-and-report_(X08)')
field('E04', 'tag', new='CONJECTURE')
# E09
field('E09', 'predicted', append=';_read-and-report_(X08):_P03-P06_at_every_record_and_P08_at_t=2;_scored:_P01,_P02_at_t=1,_2_and_P08_at_t=1')
field('E09', 'falsifier', new='a_flag_at_P01_or_P02_at_t=1_or_2,_or_none_at_P08_at_t=1')
# E10
field('E10', 'predicted', append=';_read-and-report_(X08):_P03-P06,_both_ratios_and_P08_t=2;_scored:_P02_(t=1,_2)_and_P08_t=1')
field('E10', 'falsifier', new='a_MISS_on_a_scored_read;_P02_not_resolved_above_0_at_3_SE')
# E12
field('E12', 'statement', append=';_the_identity_is_DERIVED,_its_verdicts_use_CLT_3SE_thresholds_(rule_SE),_not_a_certified_bound;_the_margins_are_wide')
# E13
field('E13', 'point', new='VNC_at_P02-P06,_P08;_t=1,_2;_band_scored_at_t=2_at_P02_and_at_t=1_at_P08')
field('E13', 'predicted', append=';_band_[3/4,5/4]_at_P08_t=1_(rho_2.1041e-2,_added_before_the_freeze,_RP16):_MET_at_n=4_(1.0631),_NOT_MET_from_n=16_(1.3156,_2.3256,_6.3655,_22.525_to_n=1024);_read-and-report_(X08):_P03-P06_at_every_record_and_P08_at_t=2,_their_frozen_rho,_n*_and_bands_kept_beside;_scored:_P02_(t=1,_2)_and_P08_t=1')
# E14
field('E14', 'point', new='P08,_P14,_VNC_2^20;_t=1_scored_(moved_from_t=2,_X08);_t=2_read_and_report')
field('E14', 'predicted', new='t=1:_n*_hat(P14)/n*_hat(P08)_in_(4(1-4SE_rel),16(1+4SE_rel)],_closed_form_574.30/46.527=12.343_(Q07_linear-law_values);_t=2:_closed_form_10.280,_read_and_report;_n*_hat=V/abs(Bbar)^2_u,_abs(Bbar)^2_u=(abs(Sum_B)^2-Sum_abs(B)^2)/(M(M-1));_first_2^k_(k=2..10)_with_K2(n)<=2abs(Bbar)^2_u_read_and_report_(law:_2^6,_2^10_at_t=1;_2^5,_2^8_at_t=2)')
field('E14', 'falsifier', new='the_t=1_ratio_outside_(4(1-4SE_rel),16(1+4SE_rel)]')
# E15
field('E15', 'predicted', append=';_read-and-report_(X08):_the_value_and_cross_reads_at_P05_(every_record)_and_P08_t=2;_scored:_the_order_claims_at_P05_and_P08_(t=1,_2;_comparisons_on_common_samples)_and_the_value_and_cross_reads_at_P08_t=1')
# E16
field('E16', 'predicted', append=';_a_comparison_on_common_samples_with_no_frozen_value,_scored_at_every_point_(rule_EXPOSED)')
# E17
field('E17', 'predicted', append=';_every_read_read-and-report_(X08:_P10_is_(delta,s)=(1/2,1),_exposed_at_every_t),_so_the_row_carries_no_verdict')
field('E17', 'falsifier', new='none_scored;_kept_for_the_report:_an_unflagged_test_or_Pi_hat<=0_anywhere,_a_MISS_at_t=1')
# E18
field('E18', 'predicted', append=';_read-and-report_(X08):_(1/54,2)_and_(1/108,2);_scored:_(0,2),_(1/27,1),_(1/54,1)')
field('E18', 'falsifier', new='abs(ratio-1)-(4SE_rel+read_error)>1/20_at_a_scored_point')
# END
lines = [ln for ln in t.split('\n') if ln]
kinds = []
for ln in lines:
    k = ln.split('|', 1)[0]
    if k not in kinds:
        kinds.append(k)
pred = [ln for ln in lines if ln.startswith('STRIPES_PREDICT|')]
der = sum(1 for ln in pred if '|tag=DERIVED|' in ln)
con = sum(1 for ln in pred if '|tag=CONJECTURE|' in ln)
assert der + con == len(pred) == 26 and der == 8, (der, con)
body = [ln for ln in lines if not ln.startswith('STRIPES_END|')]
cnt = ','.join('%s:%d' % (k, sum(1 for ln in body if ln.split('|', 1)[0] == k) + (1 if k == 'STRIPES_END' else 0)) for k in kinds)
end = 'STRIPES_END|rows=%d|predict_rows=%d|derived=%d|conjecture=%d|kinds=%d|counts=%s|json=0' % (len(body) + 1, len(pred), der, con, len(kinds), cnt)
old_end = [ln for ln in lines if ln.startswith('STRIPES_END|')][0]
rep(old_end, end)
open(p, 'w').write(t)
print(end)
