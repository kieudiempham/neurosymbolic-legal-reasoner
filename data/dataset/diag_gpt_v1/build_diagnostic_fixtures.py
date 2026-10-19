#!/usr/bin/env python3
"""Build isolated F1--F6 DIAGNOSTIC DRAFT from previously annotated 300 legal QAs.
The source labels are not independently adjudicated. This is a reproducible candidate/stress-test package.
No source QA gold is recalculated using an existing KB.
"""
import copy
import collections
import hashlib
import json
import random
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
if (ROOT/'crosslayer_300_DRAFT_SOURCE.jsonl').exists():
 SRC=ROOT
 DST=ROOT
 SRCNAME='crosslayer_300_DRAFT_SOURCE.jsonl'
else:
 SRC=Path('/mnt/data/crosslayer_full300_draft')
 DST=Path('/mnt/data/diagnostic_f1_f6_v1')
 SRCNAME='crosslayer_300_DRAFT.jsonl'
DST.mkdir(parents=True,exist_ok=True)
SEED=20261018
RNG=random.Random(SEED)
DATA=[json.loads(line) for line in open(SRC/SRCNAME,encoding='utf-8') if line.strip()]
BY_ID={x['id']:x for x in DATA}
DOMS=['bhxh','doanh_nghiep','thue','lao_dong','lien_nganh']
DOM_QUOTA={'bhxh':8,'doanh_nghiep':8,'thue':8,'lao_dong':8,'lien_nganh':8}
F1_QUOTA={'bhxh':9,'doanh_nghiep':9,'thue':8,'lao_dong':7,'lien_nganh':7}
BAD_F1={'BHXH-008','BHXH-036','BHXH-037','BHXH-054','BHXH-055','LN-030'}
RESTRICT_OLD=['Tôi chưa đề cập','tôi chưa đề cập']
CASES=[]
INPUTS=[]
GOLD=[]
INJECTIONS=[]
F5_CANDIDATES=[]
F6_OVERLAYS=[]


def clone(x):return copy.deepcopy(x)
def compact_fact(f):return {'pred':f['pred'],'value':f['value']}
def compact_facts(xs):return [compact_fact(f) for f in xs]
def citation_ids(q):return [{'doc':z.get('doc'), 'article':z.get('article'), 'clause':z.get('clause'), 'point':z.get('point')} for z in q['legal_basis']]
def stable(obj):return json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def clean_hash(q):return hashlib.sha256((q['question']+stable(q['goal'])+stable(compact_facts(q['facts']))).encode()).hexdigest()
def premise_predicates(q):
 text=' '.join(t.split('→')[0] for t in q['reasoning_chain'] if '→' in t)
 return set(re.findall(r'(?<![\w])~?([a-z][a-z0-9_]*)(?![\w])',text))

def primary_facts(q):
 used=premise_predicates(q)
 counter=collections.Counter(f['pred'] for f in q['facts'])
 f=[z for z in q['facts'] if z['pred'] in used and counter[z['pred']]==1]
 # More explicit proof participation is preferable. Prefer semantically consequential case facts.
 avoid={'foreign_citizen','is_vietnamese_citizen'}
 return sorted(f,key=lambda z:(z['pred'] in avoid, len(z['span']), z['pred']))

def add_record(q, mode, parsed_facts, defect, target, evidence, recovery, *, grade='controlled', fixture=None, notes=None, gold_applicability=None):
 n=sum(r['target_mode']==mode for r in CASES)+1
 idx=f'DX-{mode}-{n:03d}'
 inp={
  'id':idx,'source_question_id':q['id'],'domain':q['domain'],
  'original_question':q['question'], 'goal':clone(q['goal']),
  'parsed_facts':clone(parsed_facts),
  'oracle_goal_supplied':True,
  'kb_fixture':({'rules': [{'id':r['id'], 'if':clone(r['if']), 'then':clone(r['then'])} for r in fixture['rules']], 'exception_of':clone(fixture['exception_of']), 'priority_over':clone(fixture['priority_over']), 'kb_scope':'isolated_fixture'} if fixture is not None else None)
 }
 lab={
  'id':idx,'source_question_id':q['id'],'domain':q['domain'],
  'target_mode':mode,'label_status':grade,
  'target_proposition':clone(target),
  'expected_evidence':clone(evidence),
  'recommended_recovery':clone(recovery),
  'source_answer_expected_DRAFT':q['expected'],
  'source_legal_basis':citation_ids(q),
  'source_qa_gold_status':'DRAFT_UNREVIEWED',
  'diagnosis_conditions':clone(gold_applicability) if gold_applicability else {},
  'notes':notes or []
 }
 item={
  'id':idx,'source_question_id':q['id'],'domain':q['domain'],
  'target_mode':mode,'label_status':grade,
  'question':q['question'],'goal':clone(q['goal']),
  'original_annotated_facts':compact_facts(q['facts']),
  'observed_parsed_facts':clone(parsed_facts),
  'target_proposition':clone(target),'evidence':clone(evidence),
  'recovery':clone(recovery),'injection':clone(defect),
  'kb_fixture':clone(fixture) if fixture is not None else None,
  'source_qa_expected_DRAFT':q['expected'],
  'source_legal_basis':citation_ids(q),
  'source_references_pending_review':True,
  'notes':notes or []
 }
 man={
  'id':idx,'source_question_id':q['id'],'source_question_sha256':clean_hash(q),
  'target_mode':mode,'domain':q['domain'],'change':clone(defect),
  'source_gold_question_unchanged':True,
  'independence_group_id':q['id'],
  'source_qa_gold_status':'DRAFT_UNREVIEWED'
 }
 CASES.append(item);INPUTS.append(inp);GOLD.append(lab);INJECTIONS.append(man)
 return idx

# F1: natural unresolved user information, NOT a parser corruption. Under the annotation policy,
# an unmentioned relevant exception is not automatically insufficient.
f1=[]
for d,count in F1_QUOTA.items():
 pool=[q for q in DATA if q['domain']==d and q['expected']=='insufficient' and q.get('missing_facts') and
       q['id'] not in BAD_F1 and not any(z in q['question'] for z in RESTRICT_OLD) and
       all(m not in [f['pred'] for f in q['facts']] for m in q['missing_facts'])]
 # Unique question ids and diversity of the decisive missing predicate wherever possible.
 groups=collections.defaultdict(list)
 for q in pool:groups[q['missing_facts'][0]].append(q)
 for k in groups:RNG.shuffle(groups[k])
 ordered=[]
 for k in sorted(groups,key=lambda k:(len(groups[k]),k)):
  ordered.append(groups[k].pop())
 extras=[x for y in groups.values() for x in y]; RNG.shuffle(extras)
 chosen=(ordered+extras)[:count]
 assert len(chosen)==count,('F1 shortage',d,len(chosen),count)
 f1.extend(chosen)
for q in f1:
 targets=q['missing_facts']
 p=targets[0]
 add_record(q,'F1',compact_facts(q['facts']),
  {'operation':'no_injection_naturally_missing','missing_predicates':targets,'question_edited':False},
  {'pred':p,'polarity':'unknown'},
  {'pre_verification':['required('+p+')','not_parsed('+p+')'], 'expected_question_evidence':'neutral_or_explicitly_unknown',
   'verified_legal_label':'insufficient','missing_predicates':targets},
  {'action':'request_user_clarification','ask_about_predicates':targets,'recompute_from_answer':True},
  grade='candidate_legal_gold_pending_review',
  notes=['F1 is missing information in the ORIGINAL question. Lack of a parser fact alone is not F1.',
         'A missing predicate can be one of multiple unresolved premises; ask all relevant unknown premises.'])

# F2/F3/F4 paired corruption tests: pick 8 complete cases/domain with explicit proof-premise facts.
paired=[]
for d,k in DOM_QUOTA.items():
 pool=[q for q in DATA if q['domain']==d and q['expected'] in ('true','false') and primary_facts(q)]
 by_profile=collections.defaultdict(list)
 for q in pool:
  s=(q['goal']['pred'],q['expected'],tuple(sorted((f['pred'],f['value']) for f in q['facts'])))
  by_profile[s].append(q)
 for z in by_profile.values():RNG.shuffle(z)
 # De-duplicate exact fact signature as much as possible.
 keys=list(by_profile);RNG.shuffle(keys)
 chosen=[]
 for key in keys:
  if len(chosen)>=k:break
  chosen.append(by_profile[key].pop())
 if len(chosen)<k:
  extra=[v for vv in by_profile.values() for v in vv]
  RNG.shuffle(extra)
  chosen.extend(extra[:k-len(chosen)])
 assert len(chosen)==k
 paired.extend(chosen)

for i,q in enumerate(paired):
 originals=compact_facts(q['facts'])
 f=primary_facts(q)[0]
 target=compact_fact(f)
 # F2: omitted even though QUESTION entails it.
 omitted=[z for z in originals if z['pred']!=f['pred']]
 add_record(q,'F2',omitted,
  {'operation':'remove_parsed_fact','removed_fact':target,'original_question_preserved':True},
  target,
  {'pre_verification':['required('+f['pred']+')','not_parsed('+f['pred']+')'],
   'expected_question_evidence':'entailment','post_verification_mode':'parser_omission'},
  {'action':'restore_from_original_question','restore_fact':target,'rerun_reasoner':True},
  notes=['Gold question fact is explicitly grounded by span: '+f['span'],
         'Whether the reasoner marks the fact required needs proof/dependency verification.'])
 # F3: replace correct polarity with opposite, same predicate.
 flipped=clone(originals)
 for z in flipped:
  if z['pred']==f['pred']:z['value']=not f['value'];break
 add_record(q,'F3',flipped,
  {'operation':'replace_polarity','before':target,'after':{'pred':f['pred'],'value':not f['value']},'original_question_preserved':True},
  {'pred':f['pred'],'value':not f['value']},
  {'pre_verification':['parsed('+f['pred']+')'],
   'expected_question_evidence':'contradiction',
   'source_supported_fact':target,'post_verification_mode':'parser_misinterpretation'},
  {'action':'correct_parser_polarity','set_fact':target,'rerun_reasoner':True},
  notes=['A supported fact is REPLACED, not appended; this distinguishes F3 from F4.'])

# F4: More realistic neutral hallucination. Reuse F1's naturally incomplete
# questions but make the parser ADD the very missing decision-critical premise.
# This yields a paired F1/F4 control: question same, parser output changes only.
for q in f1:
 originals=compact_facts(q['facts'])
 p=q['missing_facts'][0]
 assert p not in [f['pred'] for f in originals]
 # Orient the hallucinated fact to the antecedent of an annotated legal rule.
 polarity_mentions=[]
 for line in q['reasoning_chain']:
  body=line.split('→')[0]
  for match in re.finditer(r'(?<![\w])(~?)'+re.escape(p)+r'(?![\w])',body):
   polarity_mentions.append(match.group(1)!='~')
 guessed_value=polarity_mentions[0] if polarity_mentions else True
 injected={'pred':p,'value':guessed_value}
 add_record(q,'F4',originals+[injected],
  {'operation':'append_unsupported_neutral_fact','added_fact':injected,
   'injection_variant':'hallucinated_decision_critical_missing_premise',
   'original_question_preserved':True,
   'polarity_selection':'antecedent_literal_from_QA_annotation' if polarity_mentions else 'positive_default_NEEDS_REVIEW'},
  injected,
  {'pre_verification':['parsed('+p+')','source_missing('+p+')'],
   'expected_question_evidence':'neutral_or_explicitly_unknown',
   'source_missing_predicates':q['missing_facts'],
   'post_verification_mode':'unsupported_extra_parsed_fact'},
  {'action':'deactivate_unsupported_fact','remove_appended_fact':injected,
   'after_removal_expected':'insufficient_until_user_clarifies',
   'ask_about_predicates':q['missing_facts'],'rerun_reasoner':True},
  grade='controlled_unsupported_neutral_fact_from_missing_QA_DRAFT',
  notes=['The added premise was absent/undetermined in the ORIGINAL question.',
         'This F4 is contrasted against an F1 case based on exactly the same question.',
         'Whether the added fact is used by the actual proof must be checked using the repository reasoner.'])

# F5: LEGAL-SOURCE ANCHORED, but provisional pairs until matching real KB rule ids + exception_of are exported.
# The fixtures are illustrative overlays, not assertions about the actual encoded KB.
F5_SPECS={
 'BHXH-010':(['signed_labor_contract','term_at_least_1_month'],['receiving_pension']),
 'BHXH-020':(['alternative_work_agreement','paid_wage','under_management','term_at_least_1_month'],['receiving_pension']),
 'BHXH-038':(['foreign_citizen','signed_labor_contract','term_at_least_12_months'],['intra_company_transfer']),
 'BHXH-039':(['foreign_citizen','signed_labor_contract','term_at_least_12_months'],['retirement_age_at_signing']),
 'BHXH-056':(['enterprise_manager'],['receiving_pension']),
 'BHXH-072':(['unpaid_14_days'],['unpaid_14_days','agreed_contribution']),
 'BHXH-078':(['multiple_contracts'],['first_contract_suspended','second_contract_active','agreed_contribution']),
 'DN-004':(['enterprise_name_state_body'],['enterprise_name_state_body','state_body_name_consent']),
 'DN-017':(['llc_company','llc_single_owner'],['converting_to_joint_stock']),
 'DN-044':(['founder_shareholding','founder_shares_within_first_3_years','buyer_is_nonfounder'],['founder_held_shares_from_registration']),
 'LD-009':(['probation_planned'],['contract_under_one_month']),
 'LD-016':(['wage_unpaid_or_late'],['wage_unpaid_or_late']),
 'LD-030':(['nursing_child_under_12_months'],['nursing_child_under_12_months','consented_to_night_work']),
 'THUE-013':(['tax_pays_under_deduction','input_used_for_taxable_sales'],['purchase_amount_at_least_5m','purchase_has_valid_vat_invoice']),
 'THUE-035':(['foreign_customer','consumed_outside_vietnam'],['outbound_technology_transfer']),
 'THUE-070':(['tax_debt_exists'],['tax_debt_offset_refund_processing']),
}

def select_preds(q, names):
 vals={f['pred']:f['value'] for f in q['facts']}
 assert all(p in vals for p in names),(q['id'],[p for p in names if p not in vals])
 return [{'pred':p,'value':vals[p]} for p in names]

for bid,(gen,exc) in F5_SPECS.items():
 q=BY_ID[bid]
 assert q['expected'] in ('true','false')
 goal=q['goal']['pred']; val=q['expected']=='true'
 general=select_preds(q,gen);except_body=select_preds(q,exc)
 n=sum(r['target_mode']=='F5' for r in CASES)+1
 rid='PAIR-'+hashlib.sha256(f'{SEED}:f5:{n}'.encode()).hexdigest()[:12]
 fixture={
  'fixture_id':rid,'scope':'isolated_provisional_pair',
  'rules':[
   {'id':rid+'_r1','if':general,'then':{'pred':goal,'value':not val},
    'nature':'abstracted_general_side_NOT_verified_source_rule'},
   {'id':rid+'_r2','if':except_body,'then':{'pred':goal,'value':val},
    'nature':'abstracted_exception_side_NOT_verified_source_rule'}
  ],
  'exception_of':[{'exception_rule_id':rid+'_r2','general_rule_id':rid+'_r1'}],
  'priority_over':[],
  'all_fixture_premises_explicitly_present_in_question':True,
  'real_kb_rule_ids':None,
  'claim_actual_kb_contains_pair':False,
  'review_required':'Map both fixture rules to actual encoded KB rules and verify genuine legal general/exception applicability.'
 }
 did=add_record(q,'F5',compact_facts(q['facts']),
  {'operation':'attach_provisional_rule_pair_fixture','fixture_id':rid,'natural_question_unchanged':True},
  {'rule_pair':[rid+'_r1',rid+'_r2'], 'resolved_by':'exception_of'},
  {'expected_kb_pair_observations':['applicable('+rid+'_r1'+')','applicable('+rid+'_r2'+')',
       'incompatible('+rid+'_r1'+','+rid+'_r2'+')','exception_of('+rid+'_r2'+','+rid+'_r1'+')'],
   'post_verification_mode':'resolvable_rule_overlap_if_verified'},
  {'action':'apply_existing_verified_exception_relation','do_not_invent_legal_priority':True,'rerun_reasoner':True},
  grade='provisional_F5_requires_real_KB_pair_and_legal_review',
  fixture=fixture,
  notes=['Legal citations copied from source QA; synthetic fixture uses abstract rule bodies.',
         'Do not score this case as genuine F5 before mapping to the real KB and verifying joint rule applicability.'])
 F5_CANDIDATES.append({'diagnostic_id':did,'source_question_id':bid, 'domain':q['domain'],
    'source_legal_basis':citation_ids(q),'possible_general_premises':general,
    'possible_exception_premises':except_body,'rule_pair_fixture_id':rid,
    'actual_kb_general_rule_id':None,'actual_kb_exception_rule_id':None,
    'actual_kb_exception_of_verified':False, 'status':'PENDING_REAL_KB_PAIR_AND_LEGAL_REVIEW'})

# F6: synthetic CONFLICT within a fully specified isolated micro-KB fixture. Zero legal-conflict claims.
# Two rule heads are incompatible. Both rules fire on the given input facts; no priority/exception edge.
per_domain=4
f6sources=[]
for d in DOMS:
 pool=[q for q in DATA if q['domain']==d and q['expected'] in ('true','false') and len(q['facts'])>=1 and primary_facts(q)]
 RNG.shuffle(pool)
 f6sources.extend(pool[:per_domain])
assert len(f6sources)==20
for i,q in enumerate(f6sources,1):
 chosen=primary_facts(q)[:2]
 assert chosen
 body=compact_facts(chosen)
 goal=q['goal']['pred'];val=q['expected']=='true'
 fxid='PAIR-'+hashlib.sha256(f'{SEED}:f6:{i}'.encode()).hexdigest()[:12]
 fixture={
  'fixture_id':fxid,'scope':'isolated_synthetic_micro_KB',
  'rules':[
   {'id':fxid+'_r1','if':body,'then':{'pred':goal,'value':val},'origin':'SYNTHETIC_DIAGNOSTIC_FIXTURE_ONLY'},
   {'id':fxid+'_r2','if':body,'then':{'pred':goal,'value':not val},'origin':'SYNTHETIC_CONFLICT_INJECTION_ONLY'}
  ],
  'exception_of':[], 'priority_over':[],
  'all_fixture_premises_explicitly_present_in_question':True,
  'base_kb_overlay_mode':'isolated_REPLACE_KB_with_fixture_not_merge',
  'asserts_real_Vietnamese_law_conflict':False
 }
 did=add_record(q,'F6',compact_facts(q['facts']),
  {'operation':'replace_with_synthetic_conflicting_micro_kb','fixture_id':fxid,
   'injected_rule_id':fxid+'_r2','injection_changes_KB_only':True},
  {'rule_pair':[fxid+'_r1',fxid+'_r2'], 'resolution':'none_in_fixture'},
  {'expected_kb_pair_observations':['applicable('+fxid+'_r1'+')','applicable('+fxid+'_r2'+')',
       'incompatible('+fxid+'_r1'+','+fxid+'_r2'+')','no_exception_or_priority_resolution'],
   'post_verification_mode':'unresolved_encoded_KB_conflict_IN_SYNTHETIC_FIXTURE'},
  {'action':'abstain_and_escalate_to_KB_curator','must_not_auto_insert_priority':True},
  grade='controlled_synthetic_KB_conflict',fixture=fixture,
  notes=['This conflict exists ONLY inside the isolated synthetic KB fixture.',
         'Do not claim Vietnamese statutes conflict or that the real KB contains either rule.'])
 F6_OVERLAYS.append({'diagnostic_id':did,'source_question_id':q['id'],'kb_fixture':fixture})

# No-fault controls: paired complete QA with preserved gold facts and no fixture alterations.
for q in paired[::2]:
 add_record(q,'CONTROL',compact_facts(q['facts']),
  {'operation':'identity_no_fault','original_question_preserved':True},
  {'pred':None},
  {'expected_question_evidence':'source_facts_are_entailments','post_verification_mode':'no_injected_fault'},
  {'action':'no_repair','reasoning_only':True},
  grade='controlled_no_fault_from_unreviewed_QA',
  notes=['This is a no-injection control, not a guarantee that the supplied QA gold is legally correct.'])

assert collections.Counter(x['target_mode'] for x in CASES)=={'F1':40,'F2':40,'F3':40,'F4':40,'F5':16,'F6':20,'CONTROL':20}
assert len(CASES)==216

# Opaque, randomly mixed public IDs: inference input must not reveal F1--F6 through IDs.
old_ids=[r['id'] for r in CASES]
order=old_ids[:]
RNG.shuffle(order)
new_id={old:f'DIAG-{i:04d}' for i,old in enumerate(order,1)}
for records in [CASES,INPUTS,GOLD,INJECTIONS]:
 for row in records:row['id']=new_id[row['id']]
for row in F5_CANDIDATES:row['diagnostic_id']=new_id[row['diagnostic_id']]
for row in F6_OVERLAYS:row['diagnostic_id']=new_id[row['diagnostic_id']]
for records in [CASES,INPUTS,GOLD,INJECTIONS]:
 records.sort(key=lambda z:z['id'])

# Output data separate from gold; no diagnostic target, expected evidence or injection mode in INPUTS.
def jsonl(path,rows):
 with open(path,'w',encoding='utf-8') as out:
  for row in rows:out.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
jsonl(DST/'diagnostic_cases_DRAFT.jsonl',CASES)
jsonl(DST/'diagnostic_model_inputs.jsonl',INPUTS)
jsonl(DST/'diagnostic_gold_labels_DRAFT.jsonl',GOLD)
jsonl(DST/'fault_injection_manifest.jsonl',INJECTIONS)
jsonl(DST/'f5_real_kb_mapping_QUEUE.jsonl',F5_CANDIDATES)
jsonl(DST/'f6_isolated_synthetic_kb_fixtures.jsonl',F6_OVERLAYS)

# Paired samples and near-paraphrases must never cross evaluation split boundaries.
# For source QA, treat BHXH as development-exposed. Other domains are NOT certified held-out.
SPLITS=[]
for bid in sorted(set(r['source_question_id'] for r in CASES)):
 q=BY_ID[bid]
 sig=(q['domain'],q['goal']['pred'],q['expected'],tuple(sorted((f['pred'],f['value']) for f in q['facts'])))
 sem_hash=hashlib.sha256(stable(sig).encode()).hexdigest()[:16]
 SPLITS.append({'source_question_id':bid,'domain':q['domain'],
                'semantic_signature_group':sem_hash,
                'use':'dev_exposed' if q['domain']=='bhxh' else 'candidate_pool_NOT_held_out',
                'case_ids':[r['id'] for r in CASES if r['source_question_id']==bid]})
jsonl(DST/'source_grouping_and_split_warnings.jsonl',SPLITS)

report={
 'status':'DRAFT_DIAGNOSTIC_FIXTURES_NOT_INDEPENDENT_GOLD',
 'seed':SEED,
 'total_diagnostic_cases':len(CASES),
 'counts_by_mode':dict(collections.Counter(x['target_mode'] for x in CASES)),
 'counts_by_domain':dict(collections.Counter(x['domain'] for x in CASES)),
 'by_mode_domain':{m:dict(collections.Counter(x['domain'] for x in CASES if x['target_mode']==m)) for m in ['F1','F2','F3','F4','F5','F6','CONTROL']},
 'source_QA_draft_count':len(DATA),
 'unique_source_question_ids':len(set(x['source_question_id'] for x in CASES)),
 'F5_real_KB_verified_count':0,
 'F6_real_KB_conflicts_claimed':0,
 'F4_requires_multiset_parser_facts':False,
 'human_legal_gold_review':'NOT_DONE',
 'actual_reasoner_MBD_executed':'NOT_DONE',
 'real_KB_rule_id_mapping':'NOT_AVAILABLE',
 'source_gold_independence_warning':'BHXH 90 used in KB development; no case claimed held-out.',
 'legal_gold_policy':'Gold independent of KB; absent general legal premise => insufficient; wholly unmentioned exceptions ignored by benchmark convention; partially triggered exception with decision-critical unknown => insufficient.',
}
(DST/'build_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

(DST/'README_VI.md').write_text('''# Diagnostic benchmark F1--F6 (BẢN NHÁP, KHÔNG PHẢI GOLD CHÍNH THỨC)

Bộ này **tách riêng thành file và nhãn chẩn đoán** so với 300 QA: 216 diagnostic fixtures gồm F1=40, F2=40, F3=40, F4=40, F5=16, F6=20, CONTROL=20.

**Đọc trước khi dùng kết quả trong paper:** Đây là bộ thí nghiệm có kiểm soát sinh từ 300 QA DRAFT chưa được thẩm định pháp lý độc lập; code reasoner/KB không được cung cấp, nên chưa có proof-grounded validation, không có kết quả đo accuracy/recovery. KHÔNG nêu 216 là 216 legal gold độc lập.

## Tập đầu vào và gold

- `diagnostic_model_inputs.jsonl`: input dành cho runner. Có `original_question`, oracle `goal`, `parsed_facts`, và `kb_fixture` (nếu là F5/F6). **Không chứa nhãn F1--F6**.
- `diagnostic_gold_labels_DRAFT.jsonl`: nhãn lỗi, target, NLI/evidence expectation, action recovery; **KHÔNG đưa cho parser / MBD**.
- `diagnostic_cases_DRAFT.jsonl`: file thuận tiện cho audit **có đáp án**; không đưa toàn bộ cho model.
- `fault_injection_manifest.jsonl`: log thao tác tiêm lỗi và SHA-256 fingerprint nguồn.
- `f5_real_kb_mapping_QUEUE.jsonl`: danh sách ca F5 cần map `rule_id` và `exception_of` thực tế.
- `f6_isolated_synthetic_kb_fixtures.jsonl`: 20 cặp rule **TỔNG HỢP** trong micro-KB; **KHÔNG phải** xung đột pháp luật thực.
- `source_grouping_and_split_warnings.jsonl`: nhóm theo QA gốc và signature để hạn chế leakage.
- `build_report.json`: báo cáo tổng hợp.

## Các chế độ

**F1**: Người dùng thực sự chưa cung cấp dữ kiện pháp lý quyết định. Lấy trực tiếp từ câu thiếu dữ kiện theo GOLD DRAFT, không chỉnh parser. NLI thường neutral/unknown. Không có "fault injection"; đây là một trạng thái đầu vào.

**F2**: Parser bỏ sót một fact thật, có nguyên văn span trong câu hỏi và được dùng trong annotated rule premise. Input xóa fact, câu hỏi không đổi. NLI theo gold: entailment. Recovery: bổ sung fact.

**F3**: Parser đảo cực tính một fact quan trọng (thay thế, không thêm). NLI theo gold: contradiction. Recovery: phục hồi cực tính ban đầu.

**F4**: Parser thêm một fact KHÔNG ĐƯỢC NÊU trong câu hỏi thiếu thông tin từ tập F1 (kiểu hallucination-neutral). Fact được chọn chính là một premise quyết định trong `missing_facts`. Gold NLI là `neutral_or_explicitly_unknown`. Source question giống hệt ca F1 ghép đôi; parser output có **thêm** một fact và vì vậy khác F1. Đây không phải ca xung đột polarity/multiset. Cần proof tracing xác nhận fact tiêm được dùng trong reasoning trước khi tính recovery end-to-end.

**F5**: 16 **ứng viên** general/exception. Có `kb_fixture` mô hình hóa hai phía theo gold, nhưng `real_kb_rule_ids=null`, và `exception_of` ở đây chỉ thuộc fixture. **Chưa được gọi là 16 F5 thực**. Map sang real KB, xác minh cả hai rule cùng áp dụng, kết luận xung khắc và quan hệ `exception_of`/priority được encode thật rồi mới đưa vào đánh giá F5 chính thức. Không tự tạo metadata thiếu ở KB.

**F6**: 20 **micro-KB tổng hợp biệt lập**, mỗi micro-KB có hai rule áp dụng được, heads đối nghịch và không có `exception_of`/priority. Khi test PHẢI dùng fixture làm KB duy nhất, không merge vào KB pháp luật. Đây là thí nghiệm synthetic encoded-KB conflict; **không** đại diện cho mâu thuẫn của văn bản Việt Nam.

**CONTROL**: 20 ca QA không bị tiêm lỗi, từ nguồn DRAFT. Dùng để kiểm tra false positive.

## Quy trình tích hợp vào repo

1. Copy các file JSONL đến `data/diagnostic_dataset/` (không thay thế file QA schema). Chạy `python validate_diagnostic_dataset.py` trong thư mục được giải nén để kiểm tra tính nhất quán nội bộ.
2. Dùng `diagnostic_model_inputs.jsonl` để chạy từng record trên runner. Cung cấp **oracle goal** như cấu hình paper hiện tại, tuyệt đối không nạp `diagnostic_gold_labels_DRAFT.jsonl` trong inference.
3. Với F5: điền real `general_rule_id`, `exception_rule_id` từ KB export + xác nhận quan hệ thực tế. Những ca chưa map giữ ở **candidate queue**, không tính vào denominator F5.
4. Với F6: khởi tạo **isolated synthetic KB fixture**, không thêm rule giả vào KB luật đang đánh giá.
5. Chạy NLI, reasoning, backward dependencies và MBD; ghi observed labels/recovery, so sánh với `diagnostic_gold_labels_DRAFT.jsonl` sau khi kết thúc.
6. Đánh giá `diagnosis_accuracy`, `macro-F1` theo mode, `abstention_precision`, `recovery_success`, `unnecessary_intervention_rate`, tách thực nghiệm law-grounded và synthetic; không dùng các nhãn dự báo NLI trong gold làm hard observations nếu chưa xác minh.
7. Audit độc lập `source_legal_basis` và tái duyệt gold QA trước khi khóa test set. BHXH đã dùng để phát triển KB; toàn bộ nhóm BHXH phải là dev/exposed.

## Quy ước gold QA

`insufficient` theo luật hiện hành áp dụng, độc lập KB; thiếu điều kiện quy định chung quan trọng => insufficient. Ngoại lệ hoàn toàn không có dấu hiệu trong câu hỏi => không kích hoạt theo giả định benchmark đã công bố; ngoại lệ được kích hoạt một phần mà thiếu điều kiện có thể thay đổi kết luận => insufficient. Không tạo câu loại "tôi chưa đề cập X". Giả định benchmark này không phải bằng chứng ngoài đời rằng ngoại lệ không tồn tại.

## Trạng thái dữ liệu

- **Có**: manifest tái lập, expected observations dựa trên fact span và fixture, split-warning, synthetic KB overlays, controlled fault labels.
- **Chưa có**: 100% thẩm định pháp lý, chạy SWI-Prolog theo KB mới, xác nhận real rule pairs F5, kiểm thử MBD end-to-end, kiểm soát hoàn toàn paraphrase leakage.
- **Không được làm**: đổi gold theo output KB, tính 216 là 216 trường hợp pháp lý độc lập, gộp F6 synthetic với các KB conflict có thật để báo cáo mà không ghi chú.
''',encoding='utf-8')

(DST/'README_VI.md').open('a',encoding='utf-8').write("""

## Chạy local

```bash
python validate_diagnostic_dataset.py
# Runner của bạn tạo predictions.jsonl, ví dụ:
# {"id":"DIAG-0001","predicted_mode":"F1","recovery_success":true}
python score_diagnostic_predictions.py predictions.jsonl
# Chỉ khi muốn chấm riêng F6 synthetic:
python score_diagnostic_predictions.py predictions.jsonl --include-f6-synthetic
# Chỉ khi muốn chấm riêng F5 fixture (chưa được xác nhận ở KB thật):
python score_diagnostic_predictions.py predictions.jsonl --include-f5-fixtures
```

`score_diagnostic_predictions.py` **mặc định chỉ chấm 180 ca F1--F4 và CONTROL**. F5 đang đợi xác minh rule_ids; F6 là micro-KB synthetic. Không gộp kết quả các nhánh thành legal diagnosis accuracy. `predictions_TEMPLATE.jsonl` chỉ mô tả dạng file nộp, chưa chứa dự đoán.

`crosslayer_300_DRAFT_SOURCE.jsonl` là bản sao 300 QA đầu vào để truy được trích dẫn và span gốc. Chỉ đưa `diagnostic_model_inputs.jsonl` vào hệ thống chạy suy luận, **không** đưa file gold hoặc manifest vào parser. `build_diagnostic_fixtures.py` và input gốc đi cùng cho phép tái tạo lại với seed `20261018`.
""")

print(json.dumps(report,indent=2,ensure_ascii=False))
