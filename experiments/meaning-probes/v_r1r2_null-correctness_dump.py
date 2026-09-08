import json, io, os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results', 'r1r2.json')
d = json.load(io.open(P, encoding='utf-8'))
prim = d['runs']['ZL3b_comma_split_true']
for k in ('recipesB_TEST_even','recipesB_FIT_odd','recipesB_ALL','herbal_ALL','f58_langA_oos'):
    st = prim['R1'][k]
    bc = st['bc']; a = st['a']
    print('==',k,'paras',st['n_paragraphs'])
    print('  a: pi_rate',a['rate_para_initial'],'n',a['n_para_initial'],
          'nil',a['rate_nonpara_line_initial'],'n',a['n_nonpara_line_initial'],
          'all',a['rate_all_words'],'n',a['n_all_words'])
    print('  a vs line:',a['vs_line_initial'])
    print('  a vs all :',a['vs_all_words'])
    print('  b: n_pi',bc['n_para_initial'],'n_gallows',bc['n_para_initial_gallows'],
          'n_match',bc['n_matchable'],'dropped',bc['n_unmatched_dropped'])
    print('     obs_all',bc['obs_attest_rate_all_gallows'],'obs_match',bc['obs_attest_rate_matchable'],
          'obs_dropped',bc['obs_attest_rate_dropped_unmatched'])
    print('     ctrl',bc['control_attest_rate_mean'],'sd',bc['control_attest_rate_sd'],
          'z',bc['b_sd_units'],'p',bc['b_p_two_sided'])
    print('     mdd',bc['b_min_detectable_abs_diff_at_p05'],'q025',bc['control_null_q025'],'q975',bc['control_null_q975'])
    print('     relaxed',bc.get('b_relaxed_match_SUPPLEMENTARY'))
    print('     word stats',bc['obs_word_stats'])
    print('     res  stats',bc['obs_residue_stats'])
    print('     c word_top1',bc['c']['word_top1'])
    print('     c res_top1 ',bc['c']['residue_top1'])
    print('     c word_H   ',bc['c']['word_entropy'])
    print('     top10 openers',bc['top10_opener_words'][:6])
    print('     gate',st['gate'])
r2 = prim['R2']['recipes_TEST_even']
print('== R2 TEST', {k:r2[k] for k in ('n_star_paragraphs','n_tests_run','bonferroni_threshold_actual_tests','bonferroni_threshold_protocol_53','permutation_p_floor','n_uncorrected_p_lt_0.05','expected_false_positives_at_0.05')})
print('  top10:'); [print('   ',t) for t in r2['largest_uncorrected_effects_top10']]
print('  supp:'); [print('   ',t) for t in r2['SUPPLEMENTARY_page_stratified_null_top10']]
print('  clustering:'); [print('   ',k,{kk:vv for kk,vv in v.items() if kk!='per_page_rate'}) for k,v in r2['page_clustering_of_star_attributes'].items()]
print('  star_summary', r2['star_summary'])
