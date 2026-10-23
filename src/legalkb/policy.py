"""Shared experimental switches; scoped per run, never process-global overrides."""
from contextlib import contextmanager
from contextvars import ContextVar

SYSTEMS = ('mbd', 'symbolic', 'heuristic', 'direct', 'no_acceptance', 'no_mbd', 'no_diagnosis_repair')
OPTIONS = ContextVar('legalkb_policy', default={})


@contextmanager
def policy(system='mbd', budget=None):
    if system not in SYSTEMS or (budget is not None and budget < 0):
        raise ValueError('Invalid system or clarification budget')
    token = OPTIONS.set({'system': system, 'budget': budget})
    try:
        yield
    finally:
        OPTIONS.reset(token)


def budget_arg(text):
    if text in ('unlimited', 'none'):
        return None
    value = int(text)
    if value < 0:
        raise ValueError('Budget must be nonnegative')
    return value


def local_faults(table, direct=False):
    """Heuristic uses accepted labels; direct maps each symptom to a fixed layer cause."""
    faults = []
    for c in table:
        lab, cid = c.get('label'), c['id']
        if lab is None:
            continue
        mode = None
        if c['layer'] == 'case':
            if c['kind'] == 'checked':
                if lab == 'neutral':
                    mode = 'unsupported'
                elif (lab == 'contra') == (c.get('polarity', 'pos') == 'pos'):
                    mode = 'misinterp'
                if mode and direct:
                    mode = 'misinterp'
            elif c['kind'] == 'required':
                mode = 'missing' if direct or lab == 'neutral' else 'omission'
            elif lab == 'entail':
                mode = 'omission'
        elif c['layer'] == 'kb' and lab != 'entail':
            mode = 'misencoded'
        elif c['layer'] == 'retrieval' and lab != 'neutral':
            mode = 'omitted'
        if mode:
            faults.append(f'{mode}({cid})')
    return faults


def limit_questions(result, budget):
    """One clarification round asks one component; exhausted budgets abstain.

    No simulated reply is invented here. evaluate_dialogue executes actual supplied
    reply transitions, including rerunning reasoning and diagnosis after each reply.
    """
    result['budget'] = budget
    result['budget_exhausted'] = False
    if result['action'] in ('ask', 'confirm'):
        if budget == 0:
            result['requested_action'] = result['action']
            result['action'] = 'unresolved'
            result['budget_exhausted'] = True
            result['about'] = []
        else:
            ordered = [q['id'] for q in result.get('questions', []) if q['id'] in result['about']]
            result['about'] = (ordered or result['about'])[:1]
    return result


def evaluate_dialogue(initial, respond, rerun, budget=None):
    """Execute at most B clarification rounds. respond receives only the public query.

    respond returns None when no answer is available. rerun must reparse/reason/verify
    the updated case and return a fresh result. No gold label is passed to either.
    Unlimited runs stop when a state/question repeats or the oracle cannot respond.
    """
    if budget is not None and budget < 0:
        raise ValueError('Budget must be nonnegative')
    current, history, seen = initial, [], set()
    while current['action'] in ('ask', 'confirm'):
        if budget is not None and len(history) >= budget:
            current = limit_questions(dict(current), 0)
            break
        about = current.get('about', [])
        # Information-gain ranking spans all diagnoses; the chosen action can
        # target only a subset (e.g. parser confirmation, not a missing fact).
        query = [q for q in current.get('questions', []) if q['id'] in about][:1] or about[:1]
        signature = repr((query, current.get('diagnoses'), current.get('facts')))
        if not query or signature in seen:
            break
        seen.add(signature)
        reply = respond(query[0])
        if reply is None:
            break
        history.append({'query': query[0], 'reply': reply})
        current = rerun(current, reply)
    return {'initial': initial, 'final': current, 'clarifications': len(history), 'history': history}
