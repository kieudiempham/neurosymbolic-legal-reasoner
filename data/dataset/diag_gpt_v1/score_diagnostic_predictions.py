#!/usr/bin/env python3
"""Score case-level diagnostic predictions from a JSONL run.
Example: python score_diagnostic_predictions.py predictions.jsonl
Predictions: {"id":"DIAG-0123", "predicted_mode":"F2", "recovery_success":true}
This measures labels only; no proof/legal correctness certification.
"""
import argparse
import collections
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parent
MODES=['F1','F2','F3','F4','F5','F6','CONTROL']

def read(p):
 with open(p,encoding='utf-8') as fp:
  return [json.loads(l) for l in fp if l.strip()]

def score(path,include_f5=False,include_f6=False):
 gold={r['id']:r for r in read(ROOT/'diagnostic_gold_labels_DRAFT.jsonl')}
 pred=read(path)
 pids=[r['id'] for r in pred]
 if len(pids)!=len(set(pids)):
  raise ValueError('Duplicate prediction IDs')
 unknown=set(pids)-set(gold)
 if unknown:raise ValueError('Unknown prediction IDs: '+str(sorted(unknown)[:10]))
 predicted={r['id']:r for r in pred}
 excluded=set()
 if not include_f5:excluded.add('F5')
 if not include_f6:excluded.add('F6')
 selected=[g for g in gold.values() if g['target_mode'] not in excluded]
 matrix=collections.Counter()
 totals=collections.Counter();matched=collections.Counter()
 rr=[]
 for g in selected:
  mode=g['target_mode'];totals[mode]+=1
  pr=predicted.get(g['id'],{})
  guess=pr.get('predicted_mode','MISSING')
  if guess not in MODES:guess='INVALID' if guess!='MISSING' else 'MISSING'
  matrix[(mode,guess)]+=1
  if guess==mode:matched[mode]+=1
  if type(pr.get('recovery_success')) is bool:rr.append(pr['recovery_success'])
 row_metrics={}
 for mode in MODES:
  if mode in excluded:continue
  n=totals[mode];tp=matrix[(mode,mode)]
  pred_count=sum(cnt for (ref,pred),cnt in matrix.items() if pred==mode)
  precision=tp/pred_count if pred_count else None
  recall=tp/n if n else None
  f1=2*precision*recall/(precision+recall) if precision is not None and recall is not None and precision+recall else (0.0 if n else None)
  row_metrics[mode]={'support':n,'precision':precision,'recall':recall,'f1':f1}
 correct=sum(matched.values());n=sum(totals.values())
 return {
  'warning':'Gold labels are diagnostic DRAFT, based on unreviewed QA; not final published test results.',
  'evaluated_modes':[x for x in MODES if x not in excluded],
  'case_count':n,'prediction_count':sum(1 for r in selected if r['id'] in predicted),
  'accuracy_with_missing_as_wrong':correct/n if n else None,
  'macro_f1':sum(row_metrics[m]['f1'] for m in row_metrics if row_metrics[m]['f1'] is not None)/sum(1 for m in row_metrics if row_metrics[m]['f1'] is not None),
  'per_mode':row_metrics,
  'confusion':[{ 'gold':a,'predicted':b,'count':c } for (a,b),c in sorted(matrix.items())],
  'recovery_success_rate_on_explicitly_reported':sum(rr)/len(rr) if rr else None,
  'recovery_reporting_count':len(rr),
  'do_not_mix_real_kb_and_synthetic_f6':True,
  'f5_actual_kb_review':'NOT_VERIFIED',
 }

if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('prediction_jsonl',type=pathlib.Path)
 p.add_argument('--include-f5-fixtures',action='store_true',help='Score provisional F5 fixtures; NEVER describe as verified real KB overlap')
 p.add_argument('--include-f6-synthetic',action='store_true',help='Score F6 SYNTHETIC KB micro-fixtures separately')
 args=p.parse_args()
 if not args.prediction_jsonl.exists():p.error('prediction file does not exist')
 print(json.dumps(score(args.prediction_jsonl,args.include_f5_fixtures,args.include_f6_synthetic),ensure_ascii=False,indent=2))
