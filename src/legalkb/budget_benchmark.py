"""Offline clarification experiment on two independent sample deadline questions.

Uses real retrieval and Prolog proofs, deterministic (fixture) observations and
explicit positive user replies. These are protocol tests, not measured NLI scores.
"""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from .policy import SYSTEMS, evaluate_dialogue
from .questions import Question, answer
from .reason import Reasoner
from .verify import components, decide
from .db import connect


def run_budgets():
    from . import sample_kb
    original = sample_kb.SAMPLE_DB, sample_kb.SAMPLE_PL
    scores = {}
    with TemporaryDirectory(prefix='legalkb-budget-') as temp:
        sample_kb.SAMPLE_DB, sample_kb.SAMPLE_PL = Path(temp)/'sample.sqlite', Path(temp)/'sample.pl'
        try:
            sample_kb.build()
            con, rr = connect(sample_kb.SAMPLE_DB), Reasoner(sample_kb.SAMPLE_PL)
            questions = [Question('deadline','toi',modality='obligation',pred='nop_ho_so_mau'),
                         Question('deadline','toi',modality='procedure',pred='bo_sung_ho_so_mau')]
            known = ['instance_of(toi, nguoi_lao_dong)', 'nhan_thong_bao_mau(toi)', 'nhan_yeu_cau_mau(toi)']
            try:
                for system in SYSTEMS:
                    scores[system] = {}
                    for budget in (0,1,2,None):
                        cases=[]
                        for missing in (0,1,2):
                            def evaluate(facts):
                                parts=[{**answer(q,facts,rr,con),'parsed':q.__dict__} for q in questions]
                                comps=components(parts,facts)
                                table=[]
                                for cid,c in comps['atoms'].items():
                                    label='entail' if c['kind']=='checked' else 'neutral'
                                    table.append({'id':cid,'item':c['atom'],'statement':c['atom'],'layer':'case',
                                                  'kind':c['kind'],'polarity':c['polarity'],
                                                  **{f'p_{l}':.98 if l==label else .01 for l in ('entail','neutral','contra')}})
                                for cid,c in comps['rules'].items():
                                    table.append({'id':cid,'item':c['norm'],'statement':c['norm'],'layer':'kb','kind':'rule',
                                                  'p_entail':.98,'p_neutral':.01,'p_contra':.01})
                                result=decide(table,comps['competing'],system=system)
                                result.update(facts=facts, verdicts=[p['verdict'] for p in parts])
                                return result
                            initial=evaluate(known[:3-missing])
                            # Reply oracle is fixed by the fixture; it sees the asked atom, not a gold label.
                            outcome=evaluate_dialogue(initial, lambda q: q['statement'] if q['statement'] in known else None,
                                                      lambda current, reply: evaluate([*current['facts'],reply]),budget)
                            final=outcome['final']
                            cases.append({'missing':missing,'action':final['action'],
                                          'clarifications':outcome['clarifications'],
                                          'correct':final['action']=='answer' and all(v=='yes' for v in final['verdicts'])})
                        scores[system]['unlimited' if budget is None else str(budget)] = cases
            finally:
                rr.close();con.close()
        finally:
            sample_kb.SAMPLE_DB, sample_kb.SAMPLE_PL = original
    return {'measurement':'deterministic fixture observations; actual sample Prolog; explicit user replies', 'scores':scores}


if __name__ == '__main__':
    import json
    print(json.dumps(run_budgets(),ensure_ascii=False,indent=2))
