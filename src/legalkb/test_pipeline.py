"""Offline regression tests: actual Prolog/SQLite, mocked measurement and wording boundaries."""
from copy import deepcopy
import json
import pytest
from .verify import decide, diagnose, components


def row(cid='c1', kind='checked', label='entail', layer='case', **extras):
    return {'id': cid, 'kind': kind, 'layer': layer, 'item': f'p({cid})', 'statement': cid,
            'polarity': 'pos', **{f'p_{l}': .98 if l == label else .01 for l in ('entail','neutral','contra')}, **extras}


def test_cross_layer_needed_invention():
    r = row(label='neutral', needed=True)
    result = decide([r], [])
    assert result['diagnoses'] == [['missing(c1)', 'unsupported(c1)']]
    assert result['action'] == 'ask'
    heuristic = decide([deepcopy(r)], [], system='heuristic')
    assert heuristic['action'] == 'confirm'


def test_shared_parser_fault_hits_multiple_rule_conflicts():
    # No accepted label for c1: either polarity is possible. One faulty parser
    # component supports two inconsistent proof pairs across the KB layer.
    r = row(p_entail=.35, p_neutral=.3, p_contra=.35)
    rules = [row('n'+str(n), 'rule', layer='kb') for n in range(1, 4)]
    result = decide([r, *rules], [('n1','n2'),('n1','n3')], supports=[('n1','n2','c1'),('n1','n3','c1')])
    diagnoses = [set(x) for x in result['diagnoses']]
    assert {'misinterp(c1)'} in diagnoses
    assert {'unsupported(c1)'} in diagnoses
    assert {'kbconflict(n1,n2)', 'kbconflict(n1,n3)'} in diagnoses
    assert all(not a < b for a in diagnoses for b in diagnoses)
    assert decide([deepcopy(r), *rules], [('n1','n2')], system='heuristic')['action'] == 'answer'


def test_two_independent_faults_and_diagnosis_bound():
    table = [row(label='contra'), row('c2', label='neutral')]
    result = decide(table, [])
    assert result['diagnoses'] == [['misinterp(c1)', 'unsupported(c2)']]
    obs, atoms = result['observations'], result['candidates']
    assert diagnose(obs, atoms, k=1)[0] == []
    assert decide([row('r1','near_miss','neutral','retrieval',expected=True)], [])['action'] == 'warn'


def test_components_preserve_false_and_unused_parser_outputs():
    proof = {'kind':'fact','goal':'p(a)'}
    part = {'kind':'case','parsed':{},'goal':'p(a)','false_facts':['q(a)'],
            'answers':[{'status':'certain','missing':[],'presumed_absent':[], 'proof':proof}],
            'contrary':[{'status':'conditional','missing':['z(a)'],'presumed_absent':[], 'proof':proof}]}
    got = components([part], ['p(a)','unused(a)'])['atoms']
    assert any(r['atom']=='unused(a)' for r in got.values())
    assert any(r['atom']=='q(a)' and r['polarity']=='neg' for r in got.values())
    assert not any(r['atom']=='z(a)' for r in got.values())


def test_shared_split_validates_overlap_and_missing(tmp_path):
    from .splits import split_of
    d = tmp_path / 'bhxh'; d.mkdir()
    p = d / 'split.json'
    assert split_of('BHXH-001',root=tmp_path)=='dev'
    p.write_text(json.dumps({'dev':['BHXH-002'],'test':['BHXH-001']}))
    assert split_of('BHXH-001/misinterp0',root=tmp_path)=='test'
    with pytest.raises(ValueError, match='missing'):
        split_of('BHXH-003',root=tmp_path)
    p.write_text(json.dumps({'dev':['BHXH-001'],'test':['BHXH-001']}))
    with pytest.raises(ValueError, match='overlapping'):
        split_of('BHXH-001',root=tmp_path)


def test_action_scoring():
    from .batch import score_actions
    rows = [{'gold':'insufficient','action':'ask'}, {'gold':'true','action':'answer','verdict':'yes'},
            {'gold':'false','action':'answer','verdict':'no'}, {'gold':'true','action':'confirm','verdict':'yes'},
            {'gold':'false','action':'warn','verdict':'no'}, {'gold':'true','action':'answer','verdict':'no'},
            {'gold':'insufficient','action':'answer','verdict':'unknown'}, {'gold':'true','error':'failed'}]
    got = score_actions(rows)
    assert (got['n'],got['correct'],got['lack_of_confidence'],got['errors'])==(8,3,2,1)
    assert score_actions(rows * 37 + rows[:4])['n'] == 300


def test_control_false_positives_and_wildcard_matching():
    from .inject import score_predictions
    rec = {'mode':None,'key':None}
    faulty = {'mode':'missing','key':None}
    got = score_predictions([(rec,{('unsupported',('a',))},'confirm'),
                             (faulty,{('missing',('b',)),('missing',('c',))},'ask')])
    assert got['fault_precision'] == .333
    assert got['fault_recall'] == 1
    assert got['false_alarm_rate'] == 1


def test_budget_executes_real_transitions():
    from .policy import evaluate_dialogue
    def state(n):
        return {'action':'ask' if n else 'answer', 'about':[str(n)] if n else [], 'facts':n}
    def rerun(current, reply):
        return state(current['facts']-1)
    for b, count, action in [(0,0,'unresolved'),(1,1,'unresolved'),(2,2,'answer'),(None,2,'answer')]:
        got = evaluate_dialogue(state(2), lambda q: 'yes', rerun, b)
        assert (got['clarifications'],got['final']['action'])==(count,action)


def test_calibration_never_reads_test(monkeypatch):
    from . import inject
    visited = []
    def evaluate(*args, **kwargs):
        visited.extend(r['split'] for r in kwargs['records'])
        return {'mbd':{'action_accuracy':1,'fault_f1':1,'false_alarm_rate':0}}
    monkeypatch.setattr(inject,'evaluate',evaluate)
    inject.calibrate([{'split':'dev'}, {'split':'test','components':'poison'}])
    assert visited and set(visited)=={'dev'}


@pytest.fixture
def sample_pipeline(tmp_path, monkeypatch):
    from . import sample_kb, ask, verify, answer_gen
    from .trace import connect_runs
    from .questions import Question
    from .test_mbd import BASE, INDEFINITE, PENSION
    monkeypatch.setattr(sample_kb,'SAMPLE_DB',tmp_path/'sample.sqlite')
    monkeypatch.setattr(sample_kb,'SAMPLE_PL',tmp_path/'sample.pl')
    events = []
    class Parser:
        model = 'fixture'
        ex = type('Ex', (), {'client':object()})()
        def __init__(self, con): pass
        def parse(self, text):
            events.append('parse')
            return BASE+[INDEFINITE], [PENSION], [Question('status','toi',pred='thuoc_dien_bhxh_bat_buoc')], {}
    monkeypatch.setattr(ask,'Parser',Parser)
    monkeypatch.setattr(ask,'connect_runs',lambda: connect_runs(tmp_path/'runs.sqlite'))
    def nli(client,pairs):
        events.append('verify')
        out=[]
        for premise,hypothesis,prompt in pairs:
            label = 'entail'
            if prompt=='v4':
                negative = ' không ' in hypothesis.lower() and 'không xác định' not in hypothesis.lower()
                pension = 'hưởng lương hưu' in hypothesis
                label = 'entail' if negative == pension else 'contra'
            scores={k:.98 if k==label else .01 for k in ('entail','neutral','contra')}
            out.append({**scores,'llm':scores,'mdeberta':None})
        return out
    monkeypatch.setattr(verify,'nli',nli)
    def write(prompt,model):
        events.append('generate')
        return 'Kết luận mẫu đã được kiểm chứng.'
    def check(text,premise):
        events.append('faithfulness')
        return [{'sentence':text,'label':'entail','entail':.98,'neutral':.01,'contra':.01}]
    monkeypatch.setattr(answer_gen,'write',write)
    monkeypatch.setattr(answer_gen,'check',check)
    a=ask.Asker(sample=True)
    yield a,events
    a.reasoner.close();a.con.close();a.runs.close()


def test_chat_and_http_route_run_all_five_steps(sample_pipeline, monkeypatch):
    from .chat import Dialogue
    from . import server
    import io
    asker,events=sample_pipeline
    dialogue=Dialogue(asker)
    monkeypatch.setattr(server,'DIALOGUE',dialogue)
    handler=object.__new__(server.Handler)
    body=json.dumps({'message':'Tôi ký hợp đồng không xác định thời hạn, không hưởng lương hưu.'}).encode()
    handler.path='/api/chat';handler.headers={'Content-Length':str(len(body))};handler.rfile=io.BytesIO(body)
    replies=[]
    handler._json=lambda obj,code=200: replies.append((code,obj))
    handler.do_POST()
    code,result=replies[0]
    assert code==200 and result['error'] is None
    assert result['action']=='answer'
    assert result['answer']=='Kết luận mẫu đã được kiểm chứng.'
    assert events.index('parse') < events.index('verify') < events.index('generate') < events.index('faithfulness')
    kinds=[r[0] for r in asker.runs.execute('SELECT stage FROM run_steps WHERE run_id=? ORDER BY step_no',(result['run_id'],))]
    assert 'reason' in kinds and 'verify' in kinds and kinds.index('reason') < kinds.index('verify')
    handler.path='/api/reset'
    body=json.dumps({'session_id':result['session_id']}).encode()
    handler.headers={'Content-Length':str(len(body))};handler.rfile=io.BytesIO(body)
    handler.do_POST()
    assert dialogue.sessions[result['session_id']]['question'] is None


def test_step_five_gate_and_faithfulness_failure(sample_pipeline,monkeypatch):
    from . import answer_gen
    asker,_=sample_pipeline
    run,_=asker.ask('Fixture')
    asker.runs.execute('UPDATE runs SET action=NULL WHERE run_id=?',(run,))
    with pytest.raises(RuntimeError,match='Step 4'):
        answer_gen.generate(asker.runs,run)
    asker.runs.execute("UPDATE runs SET action='answer' WHERE run_id=?",(run,))
    monkeypatch.setattr(answer_gen,'check',lambda text,premise:[{'sentence':text,'label':'uncertain',
                        'entail':.34,'neutral':.33,'contra':.33}])
    text=answer_gen.generate(asker.runs,run)
    assert 'chưa thể' in text
    assert asker.runs.execute('SELECT answer_faithful FROM runs WHERE run_id=?',(run,)).fetchone()[0]==0
    assert asker.runs.execute('SELECT COUNT(DISTINCT attempt) FROM run_answer_checks WHERE run_id=?',(run,)).fetchone()[0]==2


def test_every_baseline_and_budget_are_selectable():
    from .policy import SYSTEMS
    for system in SYSTEMS:
        for budget in (0,1,2,None):
            result=decide([row(label='contra')],[],system=system,budget=budget)
            assert result['system']==system
            assert result['budget']==budget
            if system in ('symbolic','no_mbd'):
                assert result['action']=='answer'
            elif budget==0 and system!='no_diagnosis_repair':
                assert result['action']=='unresolved'


def test_double_injections_change_two_distinct_components():
    from .inject import instances, akey
    base={'id':'BHXH-901','question':'fixture','q':{},'gold':'true','verdict':'true',
          'facts':['p(a)','q(a)'],'false_facts':[], 'proof_facts':['p(a)','q(a)'],'proof_norms':[]}
    doubles=[i for i in instances([base]) if i['mode']=='double']
    assert doubles and all(len(i['faults'])==2 for i in doubles)
    for i in doubles:
        assert i['faults'][0]['key']!=i['faults'][1]['key']
        assert not set(i['facts']) & set(i['false_facts'])
        assert i['split']=='dev'


def test_offline_cache_misses_never_execute_client(tmp_path,monkeypatch):
    from . import verify, answer_gen
    from .offline import CacheMiss, extractor
    monkeypatch.setenv('LEGALKB_OFFLINE','1')
    monkeypatch.setattr(verify,'CACHE',tmp_path)
    monkeypatch.setattr(answer_gen,'CACHE',tmp_path)
    with pytest.raises(CacheMiss):
        verify._cached_call('test','missing',lambda: pytest.fail('network attempted'))
    with pytest.raises(CacheMiss):
        extractor('unused').client.chat
    with pytest.raises(CacheMiss):
        answer_gen.write('not cached','unused')


def test_shared_benchmark_loads_all_300_once():
    from .batch import load_benchmark
    items=load_benchmark()
    assert len(items)==300 and len({r['id'] for r in items})==300
    assert {r['domain'] for r in items}=={'bhxh','doanh_nghiep','thue','lao_dong','lien_nganh'}
    assert len(load_benchmark(split='dev'))+len(load_benchmark(split='test'))==300


def test_injections_support_all_five_domains():
    from .batch import load_benchmark
    from .inject import instances
    base=[]
    for domain in ('bhxh','doanh_nghiep','thue','lao_dong','lien_nganh'):
        item=load_benchmark(domain)[0]
        base.append({'id':item['id'],'domain':domain,'split':item['split'],'question':'fixture','q':{},
                     'gold':'true','verdict':'true','facts':['p(a)','q(a)'],'false_facts':[],
                     'proof_facts':['p(a)','q(a)'],'proof_norms':[]})
    results=instances(base,addable={b['id']:['r(a)'] for b in base})
    for domain in {b['domain'] for b in base}:
        assert any(i['domain']==domain and i['mode']=='unsupported' for i in results)
        assert any(i['domain']==domain and i['mode']=='double' for i in results)


def test_sample_budget_protocol_reasons_after_each_reply():
    from .budget_benchmark import run_budgets
    got=run_budgets()['scores']['mbd']
    assert not got['0'][2]['correct']
    assert not got['1'][2]['correct'] and got['1'][2]['clarifications']==1
    assert got['2'][2]['correct'] and got['2'][2]['clarifications']==2
    assert got['unlimited'][2]['correct']


@pytest.mark.parametrize('action', ['ask', 'confirm'])
def test_dialogue_queries_only_the_selected_action_target(action):
    from .policy import evaluate_dialogue
    asked = []
    initial = {'action': action, 'about': ['c1'], 'questions': [
        {'id': 'c2', 'statement': 'Unselected candidate', 'gain': 1},
        {'id': 'c1', 'statement': 'Selected candidate', 'gain': .1}],
        'diagnoses': [['misinterp(c1)'], ['missing(c2)']]}

    def respond(question):
        asked.append(question['id'])
        return 'yes'

    outcome = evaluate_dialogue(initial, respond, lambda current, reply: {'action': 'answer'}, budget=1)
    assert asked == ['c1']
    assert outcome['clarifications'] == 1 and outcome['final']['action'] == 'answer'
    assert outcome['history'][0]['query']['id'] == 'c1'


def test_negative_dialogue_budget_is_rejected_before_requesting_input():
    from .policy import evaluate_dialogue
    with pytest.raises(ValueError, match='nonnegative'):
        evaluate_dialogue({'action': 'ask', 'about': ['c1']},
                          lambda q: pytest.fail('Invalid budget must not ask a question'),
                          lambda current, reply: current, budget=-1)
