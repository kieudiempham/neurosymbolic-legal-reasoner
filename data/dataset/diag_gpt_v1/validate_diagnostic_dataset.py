#!/usr/bin/env python3
"""Validate integrity of controlled diagnostic fixtures; NOT a legal proof/KB reasoner."""
import collections
import hashlib
import json
import pathlib
import sys

HERE=pathlib.Path(__file__).resolve().parent
SOURCE=HERE/'crosslayer_300_DRAFT_SOURCE.jsonl'

def load(name):
 with open(HERE/name,encoding='utf-8') as fp:
  return [json.loads(line) for line in fp if line.strip()]

def fp(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def clean_sha(q):
 return hashlib.sha256((q['question']+fp(q['goal'])+fp([{'pred':v['pred'],'value':v['value']} for v in q['facts']])).encode()).hexdigest()

def validate():
 cases=load('diagnostic_cases_DRAFT.jsonl')
 inputs=load('diagnostic_model_inputs.jsonl')
 labels=load('diagnostic_gold_labels_DRAFT.jsonl')
 manifests=load('fault_injection_manifest.jsonl')
 f5=load('f5_real_kb_mapping_QUEUE.jsonl')
 f6=load('f6_isolated_synthetic_kb_fixtures.jsonl')
 grouping=load('source_grouping_and_split_warnings.jsonl')
 source={z['id']:z for z in load('crosslayer_300_DRAFT_SOURCE.jsonl')}
 errors=[];checks=collections.Counter()
 def ok(cond,message):
  checks['assertions']+=1
  if not cond:errors.append(message)
 def unique(items,name):
  ids=[x['id'] for x in items]
  ok(len(ids)==len(set(ids)),name+': duplicate ids')
  return {z['id']:z for z in items}
 cidx=unique(cases,'cases');iidx=unique(inputs,'inputs');lidx=unique(labels,'labels');midx=unique(manifests,'manifest')
 ok(len(cases)==216,'must have 216 cases')
 ok(set(cidx)==set(iidx)==set(lidx)==set(midx),'misaligned case ids')
 modes=collections.Counter(c['target_mode'] for c in cases)
 ok(modes=={'F1':40,'F2':40,'F3':40,'F4':40,'F5':16,'F6':20,'CONTROL':20},'mode counts mismatch')
 required_input_keys={'id','source_question_id','domain','original_question','goal','parsed_facts','oracle_goal_supplied','kb_fixture'}
 for c in cases:
  uid=c['id'];i=iidx.get(uid);l=lidx.get(uid);m=midx.get(uid)
  if i is None or l is None or m is None:continue
  q=source.get(c['source_question_id'])
  ok(q is not None,uid+': unknown source id')
  if q is None:continue
  ok(set(i)==required_input_keys,uid+': unapproved input fields/label leakage')
  ok(uid.startswith('DIAG-'),uid+': non-opaque id')
  ok(l['target_mode']==m['target_mode']==c['target_mode'],uid+': mode disagreement')
  ok(i['source_question_id']==l['source_question_id']==m['source_question_id']==q['id'],uid+': source question mismatch')
  ok(i['original_question']==q['question']==c['question'],uid+': question was edited')
  ok(i['goal']==q['goal'],uid+': goal changed')
  ok(i['oracle_goal_supplied'] is True,uid+': oracle goal status invalid')
  ok(i['parsed_facts']==c['observed_parsed_facts'],uid+': injected parsed fact mismatch')
  ok(m['source_question_sha256']==clean_sha(q),uid+': source checksum mismatch')
  ok(m['source_gold_question_unchanged'] is True,uid+': source-question mutation not recorded')
  ok(q['domain']==i['domain']==c['domain'],uid+': domain mismatch')
  clean=[{'pred':f['pred'],'value':f['value']} for f in q['facts']]
  parsed=i['parsed_facts'];op=m['change']['operation'];mode=c['target_mode']
  ok(all(set(z)=={'pred','value'} and isinstance(z['pred'],str) and type(z['value']) is bool for z in parsed),uid+': malformed parser fact')
  if mode=='F1':
   ok(op=='no_injection_naturally_missing',uid+': F1 wrong injection')
   ok(q['expected']=='insufficient',uid+': F1 question not labeled insufficient')
   ok(parsed==clean,uid+': F1 parser corruption')
   missing=m['change']['missing_predicates']
   ok(len(missing)>=1,uid+': F1 no missing predicate')
   ok(all(z not in [f['pred'] for f in clean] for z in missing),uid+': F1 missing predicate present in facts')
   ok(i['kb_fixture'] is None,uid+': F1 unexpected KB fixture')
  elif mode=='F2':
   fact=m['change']['removed_fact']
   ok(op=='remove_parsed_fact',uid+': F2 wrong injection')
   ok(fact in clean,uid+': removed fact not in gold')
   ok([z for z in clean if z['pred']!=fact['pred']]==parsed,uid+': F2 should remove exactly one fact')
   ok(any(f['pred']==fact['pred'] and f['span'] in q['question'] for f in q['facts']),uid+': F2 missing text span')
  elif mode=='F3':
   fact=m['change']['before'];new=m['change']['after']
   ok(op=='replace_polarity',uid+': F3 wrong injection')
   ok(fact in clean,uid+': F3 original fact absent')
   ok(new['pred']==fact['pred'] and new['value'] is not fact['value'],uid+': F3 did not flip fact')
   expected=[]
   for f in clean:
    expected.append(new if f==fact else f)
   ok(parsed==expected,uid+': F3 not one replacement')
  elif mode=='F4':
   added=m['change']['added_fact']
   ok(op=='append_unsupported_neutral_fact',uid+': F4 wrong operation')
   ok(parsed==clean+[added],uid+': F4 must keep source facts and append neutral fact')
   ok(added['pred'] not in [z['pred'] for z in clean],uid+': F4 fact was already supplied')
   ok(added['pred'] in q.get('missing_facts',[]),uid+': F4 fact not a source decision-critical missing premise')
   ok(q['expected']=='insufficient',uid+': F4 must have unresolved source QA')
   ok(l['label_status']=='controlled_unsupported_neutral_fact_from_missing_QA_DRAFT',uid+': F4 annotation grade mismatch')
  elif mode in ('F5','F6'):
   fixture=c['kb_fixture']
   ok(fixture is not None and len(fixture['rules'])==2,uid+': pair fixture missing')
   ok(parsed==clean,uid+': KB mode should preserve parser facts')
   if fixture is None:continue
   actual={f['pred']:f['value'] for f in clean}
   for rule in fixture['rules']:
    ok(all(z['pred'] in actual and actual[z['pred']]==z['value'] for z in rule['if']),uid+': fixture contains unsatisfied premise')
   a,b=fixture['rules']
   ok(a['then']['pred']==b['then']['pred'] and a['then']['value'] is not b['then']['value'],uid+': rule conclusions compatible')
   min_fixture=i['kb_fixture']
   ok(min_fixture is not None and min_fixture['kb_scope']=='isolated_fixture',uid+': runner fixture not isolated')
   ok(min_fixture['rules']==[{'id':r['id'],'if':r['if'],'then':r['then']} for r in fixture['rules']],uid+': fixture drift')
   if mode=='F5':
    ok(len(fixture['exception_of'])==1,uid+': F5 fixture has no exception relation')
    ok(len(fixture['priority_over'])==0,uid+': F5 fixture unexpected priority')
    ok(fixture['real_kb_rule_ids'] is None,uid+': F5 fixture claims actual IDs')
    ok(op=='attach_provisional_rule_pair_fixture',uid+': F5 injection mismatch')
   else:
    ok(not fixture['exception_of'] and not fixture['priority_over'],uid+': F6 synthetic fixture has resolution')
    ok(fixture['scope']=='isolated_synthetic_micro_KB',uid+': F6 fixture type')
    ok(fixture['asserts_real_Vietnamese_law_conflict'] is False,uid+': F6 claims legal conflict')
    ok(op=='replace_with_synthetic_conflicting_micro_kb',uid+': F6 injection mismatch')
  else:
   ok(mode=='CONTROL' and op=='identity_no_fault',uid+': unknown label/CONTROL op')
   ok(clean==parsed,uid+': CONTROL changes facts')
   ok(i['kb_fixture'] is None,uid+': CONTROL extra fixture')
  checks['cases_checked']+=1
 ok(len(f5)==16 and all(r['actual_kb_general_rule_id'] is None and not r['actual_kb_exception_of_verified'] for r in f5), 'F5 real KB mapping incorrectly marked')
 ok(len(f6)==20 and all(r['kb_fixture']['asserts_real_Vietnamese_law_conflict'] is False for r in f6),'F6 genuine conflict claim detected')
 groups=collections.defaultdict(set)
 for r in grouping:groups[r['semantic_signature_group']].add(r['use'])
 ok(all(not ({'dev_exposed','candidate_pool_NOT_held_out'}<=s) for s in groups.values()),'semantic signature crosses dev/candidate groups')
 report={'status':'PASS_STRUCTURAL_ONLY' if not errors else 'FAIL','files':len(cases),
         'checked_assertions':checks['assertions'],'cases_checked':checks['cases_checked'],
         'mode_counts':dict(modes),'error_count':len(errors),'errors':errors[:100],
         'legal_gold_independently_verified':False,'SWI_Prolog_MBD_run':False,
         'F5_mapped_to_actual_KB':0,'F6_syn_conflict_fixture_count':len(f6)}
 (HERE/'diagnostic_validation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))
 return 0 if not errors else 1

if __name__=='__main__':sys.exit(validate())
