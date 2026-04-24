import urllib.request, json, sys, io, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def ask(q, sid, port=8002):
    p = json.dumps({'question': q, 'session_id': sid, 'user_facts': []}, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(f'http://127.0.0.1:{port}/ask', data=p, headers={'Content-Type': 'application/json; charset=utf-8'}, method='POST')
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode('utf-8'))

q1 = ask('Thời hạn thông báo thay đổi nội dung đăng ký doanh nghiệp là bao nhiêu ngày?', 'final_q1_v2')
q2 = ask('Công ty tôi thay đổi nội dung đăng ký nhưng chưa rõ thời điểm gửi thông báo, vậy có bị quá hạn không?', 'final_q2_v2')

# Extract minimal eval data
eval_data = []

for idx, (label, d) in enumerate([('Q1', q1), ('Q2', q2)], 1):
    test_id = f"test_{idx}"
    question = d.get('debug_trace', {}).get('query_text', '')
    question_mode = d.get('debug_trace', {}).get('question_mode', '')
    application_status = d.get('debug_trace', {}).get('application_status', '')
    final_decision = d.get('diagnostics', {}).get('final_status', '')
    answer_text = d.get('answer', {}).get('answer_text', '')
    selected_rule_id = d.get('reasoning', {}).get('selected_rule_ids', [None])[0] if d.get('reasoning', {}).get('selected_rule_ids') else ''
    legal_citations = d.get('answer', {}).get('legal_citations', [])
    proof_present = bool(d.get('proof', {}))
    missing_facts = d.get('reasoning', {}).get('missing_facts', [])
    needs_clarification = d.get('needs_clarification', False)
    error_stage_final = d.get('diagnostics', {}).get('error_stage_final', '')
    forward_failure_reason = d.get('debug_trace', {}).get('forward_gate', [{}])[0].get('failure_reason', '') if isinstance(d.get('debug_trace', {}).get('forward_gate'), list) and d.get('debug_trace', {}).get('forward_gate') else ''
    verification_summary = d.get('answer', {}).get('verification_summary', '')
    table1_view = d.get('debug_trace', {}).get('table1_view', '')
    table2_view = d.get('debug_trace', {}).get('table2_view', '')
    fail_reason = d.get('diagnostics', {}).get('fail_reason', '')

    eval_data.append({
        "test_id": test_id,
        "question": question,
        "question_mode": question_mode,
        "application_status": application_status,
        "final_decision": final_decision,
        "answer_text": answer_text,
        "selected_rule_id": selected_rule_id,
        "legal_citations": legal_citations,
        "proof_present": proof_present,
        "missing_facts": missing_facts,
        "needs_clarification": needs_clarification,
        "error_stage_final": error_stage_final,
        "forward_failure_reason": forward_failure_reason,
        "verification_summary": verification_summary,
        "table1_view": table1_view,
        "table2_view": table2_view,
        "fail_reason": fail_reason if fail_reason else None
    })

# Save to file
output_file = pathlib.Path('tests/runtime_checks/patch2_minimal_eval.json')
output_file.parent.mkdir(parents=True, exist_ok=True)
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(eval_data, f, ensure_ascii=False, indent=2)

print(f"Saved minimal eval data to {output_file}")
print("Summary:")
for item in eval_data:
    print(f"  {item['test_id']}: mode={item['question_mode']} status={item['application_status']} decision={item['final_decision']}")