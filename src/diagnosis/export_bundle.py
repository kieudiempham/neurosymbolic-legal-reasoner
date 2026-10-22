"""Package the experiment for external review (data, KBs, per-instance results, selection logs, code).

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.export_bundle   -> release/aciids_experiment_bundle.zip

Nothing is re-run: the bundle is built from the saved results of the reported configuration.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .dataset import check_case, extend_kb_vocab, load_items, to_gold_cases
from .external_diag import DOMAINS
from .inject import build_instances
from .kb import load_kb
from .run_eval import correct_action

ROOT = Path(__file__).resolve().parents[2]
REL = ROOT / "release"
B = REL / "aciids_experiment_bundle"
RUNS = {"bhxh_dev": ("bhxh_v1/bhxh_90.jsonl", "kb_bhxh_v1.yaml"), "dn_dev": ("dn_v1/dn_dev.jsonl", "kb_dn_v2.yaml"),
        "dn_test": ("dn_v1/dn_test.jsonl", "kb_dn_v2.yaml"), "thue_dev": ("thue_v1/thue_dev.jsonl", "kb_thue_v2.yaml"),
        "thue_test": ("thue_v1/thue_test.jsonl", "kb_thue_v2.yaml"), "ld_dev": ("ld_v1/ld_dev.jsonl", "kb_ld_v2.yaml"),
        "ld_test": ("ld_v1/ld_test.jsonl", "kb_ld_v2.yaml"), "ln_dev": ("ln_v1/ln_dev.jsonl", "kb_ln_v2.yaml"),
        "ln_test": ("ln_v1/ln_test.jsonl", "kb_ln_v2.yaml")}
CAT_VI = {"Normal": "Không lỗi", "MissingCaseInformation": "Thiếu thông tin (người dùng)", "ParserOmission": "Parser bỏ sót",
          "ParserMisinterpretation": "Parser hiểu sai", "UnsupportedParserFact": "Parser thêm dữ kiện không có",
          "ResolvableRuleOverlap": "Chồng lấn luật giải quyết được", "UnresolvedKBConflict": "Xung đột KB chưa giải quyết",
          "Ambiguous": "Mơ hồ (hỏi lại)", "-": "-"}
HF, HFILL = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="305496")


def sheet(ws, header, rows, widths):
    ws.append(header)
    for c in ws[1]:
        c.font, c.fill, c.alignment = HF, HFILL, Alignment(wrap_text=True, vertical="top")
    for r in rows:
        ws.append(r)
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions


def asks(r) -> int:
    return sum(x.startswith(("Clarify", "MissingCase")) for x in r["recovery"])


def instance_workbook(path: Path) -> None:
    wb = Workbook()
    g = wb.active
    g.title = "Hướng dẫn"
    for line in [
        "KẾT QUẢ TỪNG CA — cấu hình báo cáo trong paper (đo NLI: mDeBERTa + GPT-4o-mini, τ = 0,50, chọn trên dev)",
        "",
        "Sheet 'Tiêm lỗi (test)' và 'Tiêm lỗi (dev)': mỗi dòng là một ca chẩn đoán sinh từ một câu hỏi gốc bằng cách tiêm",
        "  đúng MỘT lỗi (hoặc không lỗi). 'Câu hỏi đưa vào hệ thống' là câu hỏi sau khi tiêm (với lỗi Thiếu thông tin, đoạn",
        "  nêu dữ kiện đã bị xóa khỏi câu hỏi). 'Dữ kiện parser' là đầu vào hệ thống nhận (sau khi tiêm lỗi parser).",
        "  So sánh Ours (MBD) với Heuristic (IF-THEN) trên cùng bằng chứng. 'Đúng chẩn đoán' = chẩn đoán đầu tiên trùng lỗi",
        "  đã tiêm; 'Đáp án' = kết luận cuối sau khi sửa lỗi; người dùng mô phỏng trả lời câu hỏi lại bằng dữ kiện gold.",
        "Sheet 'F1-F4 ngoài (test/dev)': bộ lỗi do GPT tạo độc lập với KB; 'observable' = lỗi làm đổi kết quả suy luận.",
        "Sheet 'Chọn tham số (dev)': lưới ngưỡng τ và kết quả trên dev dùng để chọn cấu hình — test không được dùng.",
        "Toàn bộ số trong bảng của paper tính lại được từ các sheet này (lọc theo cột Split).",
    ]:
        g.append([line])
    g.column_dimensions["A"].width = 150

    hdr = ["Ca", "Lĩnh vực", "Split", "Câu gốc", "Loại lỗi đã tiêm", "Lỗi cụ thể", "Câu hỏi đưa vào hệ thống",
           "Dữ kiện parser (đầu vào)", "Đáp án đúng", "Ours: chẩn đoán", "Ours: đúng chẩn đoán", "Ours: hành động đúng",
           "Ours: đáp án", "Ours: đúng đáp án", "Ours: số lần hỏi lại", "Heur.: chẩn đoán", "Heur.: đúng chẩn đoán",
           "Heur.: đáp án", "Heur.: đúng đáp án", "Heur.: số lần hỏi lại", "Symbolic QA: đáp án"]
    by_split = {"test": [], "dev": []}
    for name, (ds, kbf) in RUNS.items():
        res = json.loads((ROOT / "experiments" / "diag_dataset" / "ensemble_gpt" / name / "results_all.json").read_text(encoding="utf-8"))
        items = load_items([str(ROOT / "data" / "dataset" / ds)])
        kb = extend_kb_vocab(load_kb(kbf), items)
        cases, _ = to_gold_cases(items, kb)
        cases = [c for c in cases if check_case(kb, c)["verdict"] in ("ok", "ok_partial_missing")]
        insts = {i.iid: i for i in build_instances(kb, cases)}
        P = {cfg: {r["iid"]: r for r in res["per_instance"][cfg]} for cfg in ("nesy_diag", "rule_check", "base_nesy")}
        split = "test" if name.endswith("test") else "dev"
        for iid, o in P["nesy_diag"].items():
            h, s, inst = P["rule_check"][iid], P["base_nesy"][iid], insts[iid]
            by_split[split].append([
                iid, name.split("_")[0], split, o["case"], CAT_VI.get(o["gold_category"], o["gold_category"]), o["gold_fault"],
                inst.question, ", ".join(f"{'' if f.value else '¬'}{p}" for p, f in inst.parsed.items()), o["expected"],
                "; ".join(o["first_diagnosis"]) or "(không lỗi)", "đúng" if o["hit"] else "sai",
                "đúng" if correct_action(o) else "sai", o["answer"], "đúng" if o["answer_ok"] else "sai", asks(o),
                "; ".join(h["first_diagnosis"]) or "(không lỗi)", "đúng" if h["hit"] else "sai", h["answer"],
                "đúng" if h["answer_ok"] else "sai", asks(h), s["answer"]])
    widths = [26, 8, 6, 10, 22, 34, 55, 40, 12, 40, 9, 9, 14, 9, 8, 40, 9, 14, 9, 8, 14]
    sheet(wb.create_sheet("Tiêm lỗi (test)"), hdr, by_split["test"], widths)
    sheet(wb.create_sheet("Tiêm lỗi (dev)"), hdr, by_split["dev"], widths)

    ext = {c: json.loads((ROOT / "experiments" / "diag_external" / "ensemble_gpt" / f"results_{c}.json").read_text(encoding="utf-8"))
           for c in ("nesy_diag", "rule_check")}
    E = {c: {r["iid"]: r for r in d["per_instance"]} for c, d in ext.items()}
    inputs = {json.loads(x)["id"]: json.loads(x) for x in
              (ROOT / "data" / "dataset" / "diag_gpt_v1" / "diagnostic_model_inputs.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()}
    ehdr = ["Ca", "Loại lỗi (F1–F4)", "Câu gốc", "Lĩnh vực", "Split", "Trạng thái", "Câu hỏi", "Dữ kiện parser (đầu vào)",
            "Đáp án đúng", "Ours: chẩn đoán", "Ours: đúng chẩn đoán", "Ours: hành động đúng", "Ours: đáp án",
            "Heur.: chẩn đoán", "Heur.: đúng chẩn đoán", "Heur.: đáp án"]
    for split in ("test", "dev"):
        rows = []
        for iid, o in sorted(E["nesy_diag"].items()):
            if o["split"] != split:
                continue
            h = E["rule_check"][iid]
            rows.append([iid, o["mode"], o["source"], o["domain"], split, o["status"], inputs[iid]["original_question"],
                         ", ".join(f"{'' if f['value'] else '¬'}{f['pred']}" for f in inputs[iid]["parsed_facts"]), o["expected"],
                         "; ".join(o["first_diagnosis"]) or "(không lỗi)", "đúng" if o["hit"] else "sai",
                         "đúng" if o.get("correct_action", o["hit"]) else "sai", o["answer"],
                         "; ".join(h["first_diagnosis"]) or "(không lỗi)", "đúng" if h["hit"] else "sai", h["answer"]])
        sheet(wb.create_sheet(f"F1-F4 ngoài ({split})"), ehdr, rows, [11, 8, 10, 12, 6, 12, 55, 40, 12, 40, 9, 9, 14, 40, 9, 14])

    grid = []
    for f in sorted((ROOT / "experiments" / "diag_external").glob("calibration_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for g_ in d.get("grid", []):
            grid.append([f.stem.replace("calibration_", ""), g_["tau"], g_["rule"], g_["dev_score"], g_["diag_acc_observable"],
                         g_["false_alarm_control"], g_["final_answer_acc"], "được chọn" if g_ == d.get("chosen") else ""])
    sheet(wb.create_sheet("Chọn tham số (dev)"), ["Dụng cụ đo", "τ", "Luật chấp nhận", "Điểm dev", "Chẩn đoán đúng (dev)",
                                                  "Báo lỗi oan (dev)", "Đúng đáp án (dev)", ""], grid, [22, 6, 12, 10, 12, 12, 12, 12])
    add_final_sheets(wb)
    wb.save(path)


VERDICT_VI = {"true": "CÓ", "false": "KHÔNG", "insufficient": "CHƯA ĐỦ DỮ KIỆN", "abstain": "KHÔNG KẾT LUẬN", "other": "khác"}
METHOD_VI = {"gpt4o": "GPT-4o thuần", "symbolic": "Symbolic QA", "heuristic": "Heuristic", "ours": "Ours (MBD)"}


def add_final_sheets(wb) -> None:
    import re

    E = ROOT / "experiments" / "e2e"
    W = {"I": 0.10, "R": 0.35, "A": 0.40, "C": 0.15}
    snap = lambda v: min((0.0, 0.5, 1.0), key=lambda x: abs(x - float(v)))
    items = {}
    for d in ("bhxh_v1", "dn_v1", "thue_v1", "ld_v1", "ln_v1"):
        for f in (ROOT / "data" / "dataset" / d).glob("*.jsonl"):
            if f.stem.endswith(("_dev", "_test")) or f.stem == "bhxh_90":
                for it in load_items([str(f)]):
                    items[it["id"]] = it

    # --- QA end-to-end, 300 questions ---
    qa = json.loads((E / "qa_results.json").read_text(encoding="utf-8"))["rows"]
    rows = []
    for r in qa:
        it = items[r["id"]]
        rows.append([r["id"], r["domain"], r["split"], it["question"], VERDICT_VI[r["expected"]],
                     ", ".join(f"{'' if v else '¬'}{k}" for k, v in r["parsed"].items())]
                    + [x for m in ("gpt4o", "symbolic", "heuristic", "ours")
                       for x in (VERDICT_VI.get(r[m], r[m]), "đúng" if r[m] == r["expected"] else "sai")]
                    + ["; ".join(r["ours_diagnosis"]) or "(không lỗi)", "; ".join(r["heuristic_diagnosis"]) or "(không lỗi)"])
    hdr = ["ID", "Lĩnh vực", "Split", "Câu hỏi", "Đáp án gold", "Dữ kiện parser GPT-4o trích"] + \
          [f"{METHOD_VI[m]}: {x}" for m in ("gpt4o", "symbolic", "heuristic", "ours") for x in ("kết luận", "đúng/sai")] + \
          ["Ours: chẩn đoán", "Heuristic: chẩn đoán"]
    sheet(wb.create_sheet("QA 300 câu (end-to-end)"), hdr, rows, [10, 12, 6, 55, 14, 40] + [14, 8] * 4 + [40, 40])

    # --- IRAC, 1,200 answers ---
    ans = {q["id"]: q for q in json.loads((E / "irac_answers_all.json").read_text(encoding="utf-8"))}
    key = json.loads((E / "irac_key_all.json").read_text(encoding="utf-8"))
    sc = json.loads((E / "irac_scores_v2_all.json").read_text(encoding="utf-8"))["scores"]
    rows = []
    for anon in sorted(key, key=lambda a: (key[a]["question_id"], key[a]["method"])):
        k = key[anon]
        q, s_ = ans[k["question_id"]], sc[anon]
        comp = {c: snap(s_.get(c, 0)) for c in W}
        a = q["answers"][k["method"]]
        rows.append([q["id"], q["domain"], q["split"], METHOD_VI[k["method"]], anon, VERDICT_VI[q["gold_expected"]],
                     comp["I"], comp["R"], comp["A"], comp["C"], round(100 * sum(W[c] * comp[c] for c in W), 1),
                     s_.get("reason", ""), a.get("issue", ""), a.get("rule", ""), a.get("application", ""), a.get("conclusion", ""),
                     "; ".join(f"{b.get('doc', '')} Đ{b.get('article', '')}" for b in q["gold_legal_basis"])])
    sheet(wb.create_sheet("IRAC 300 câu (từng câu trả lời)"),
          ["ID câu", "Lĩnh vực", "Split", "Phương pháp", "Mã ẩn danh", "Đáp án gold", "I", "R", "A", "C", "IRAC (0-100)",
           "Lý do của giám khảo", "[I] Vấn đề", "[R] Quy định", "[A] Áp dụng", "[C] Kết luận", "Căn cứ gold"],
          rows, [10, 12, 6, 14, 9, 14, 5, 5, 5, 5, 8, 40, 30, 40, 55, 35, 35])

    # --- two simultaneous faults ---
    mf = json.loads((ROOT / "experiments" / "multi_fault" / "results.json").read_text(encoding="utf-8"))["rows"]
    rows = []
    for split in ("test", "dev"):
        H = {r["iid"]: r for r in mf[f"{split}|rule_check"]}
        for o in mf[f"{split}|nesy_diag"]:
            h = H[o["iid"]]
            rows.append([o["iid"], o["domain"], split, o["combo"], o["expected"],
                         "; ".join(o["first_diagnosis"]) or "(không lỗi)", "đúng" if o["both_found"] else "sai", o["answer"],
                         "đúng" if o["answer_ok"] else "sai", o["asks"],
                         "; ".join(h["first_diagnosis"]) or "(không lỗi)", "đúng" if h["both_found"] else "sai", h["answer"],
                         "đúng" if h["answer_ok"] else "sai", h["asks"]])
    sheet(wb.create_sheet("Hai lỗi cùng lúc"),
          ["Ca", "Lĩnh vực", "Split", "Kiểu ghép lỗi", "Đáp án đúng", "Ours: chẩn đoán đầu", "Ours: tìm đủ 2 lỗi", "Ours: đáp án",
           "Ours: đúng đáp án", "Ours: số lần hỏi", "Heur.: chẩn đoán đầu", "Heur.: tìm đủ 2 lỗi", "Heur.: đáp án",
           "Heur.: đúng đáp án", "Heur.: số lần hỏi"], rows, [40, 8, 6, 22, 10, 45, 9, 12, 9, 7, 45, 9, 12, 9, 7])

    # --- summary of the headline metrics ---
    g = wb.create_sheet("Bảng tổng hợp", 1)
    for line in (ROOT / "experiments" / "tables_aciids.md").read_text(encoding="utf-8").splitlines():
        g.append([line])
    g.append([])
    for line in (ROOT / "experiments" / "strict_eval.md").read_text(encoding="utf-8").splitlines():
        g.append([line])
    g.column_dimensions["A"].width = 200

def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if B.exists():
        shutil.rmtree(B)
    (B / "ket_qua").mkdir(parents=True)

    def cp(src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        (shutil.copytree if src.is_dir() else shutil.copy2)(src, dst)

    for d in ("bhxh_v1", "dn_v1", "thue_v1", "ld_v1", "ln_v1", "diag_gpt_v1"):
        cp(ROOT / "data" / "dataset" / d, B / "du_lieu" / "dataset" / d)
    for kb in ("kb_bhxh_v1", "kb_dn_v2", "kb_thue_v2", "kb_ld_v2", "kb_ln_v2"):
        for suf in ("", "_vocabulary", "_patches", "_alignment", "_templates"):
            f = ROOT / "data" / "diag" / f"{kb}{suf}.yaml"
            if f.exists():
                cp(f, B / "du_lieu" / "kb" / f.name)
    for f in ("CrossLayer_MBD_Benchmark_300QA.xlsx", "draft_rules_7906.zip"):
        src = ROOT / "docs" / "dataset" / f
        if src.exists():
            cp(src, B / "du_lieu" / f)
    cp(ROOT / "experiments" / "tables_aciids.md", B / "ket_qua" / "bang_ket_qua.md")
    cp(ROOT / "experiments" / "diag_external" / "ensemble_gpt", B / "ket_qua" / "chan_doan_ngoai" / "ensemble_gpt")
    for tool in ("mdeberta", "qwen", "gpt4omini", "ensemble"):
        cp(ROOT / "experiments" / "diag_external" / tool / "results_nesy_diag.json",
           B / "ket_qua" / "chan_doan_ngoai" / tool / "results_nesy_diag.json")
    for f in (ROOT / "experiments" / "diag_external").glob("calibration_*.json"):
        cp(f, B / "ket_qua" / "hieu_chinh_dev" / f.name)
    cp(ROOT / "experiments" / "diag_dataset" / "ensemble_gpt", B / "ket_qua" / "tiem_loi_theo_domain")
    cp(ROOT / "experiments" / "nli_gpu" / "nli_dev_metrics.json", B / "ket_qua" / "nli_dev_metrics.json")
    cp(ROOT / "experiments" / "multi_fault" / "results.json", B / "ket_qua" / "hai_loi" / "results.json")
    cp(ROOT / "experiments" / "budget" / "budget_results.json", B / "ket_qua" / "gioi_han_hoi_lai" / "budget_results.json")
    cp(ROOT / "experiments" / "strict_eval.json", B / "ket_qua" / "danh_gia_chat_tung_loi.json")
    cp(ROOT / "experiments" / "strict_eval.md", B / "ket_qua" / "danh_gia_chat_tung_loi.md")
    cp(ROOT / "experiments" / "strict_eval_ci.json", B / "ket_qua" / "danh_gia_chat_khoang_tin_cay.json")
    for f in ("qa_results.json", "irac_answers_all.json", "irac_scores_v2_all.json", "irac_key_all.json",
              "irac_answers.json", "irac_scores.json", "irac_scores_v2.json", "irac_key.json", "irac_human_sheet.xlsx"):
        cp(ROOT / "experiments" / "e2e" / f, B / "ket_qua" / "end_to_end" / f)
    for f in ("nli_cache.json", "nli_cache_qwen2.5-7b.json", "nli_cache_gpt4omini.json"):
        cp(ROOT / "experiments" / "diag" / f, B / "nli_cache" / f)
    cp(ROOT / "src" / "diagnosis", B / "ma_nguon" / "src" / "diagnosis")
    cp(ROOT / "kaggle", B / "ma_nguon" / "kaggle")
    for f in ("requirements_diag.txt",):
        if (ROOT / f).exists():
            cp(ROOT / f, B / "ma_nguon" / f)
    for f in ("irac_rubric.md", "paper_revision_checklist.md", "paper_section5_draft.md"):
        cp(ROOT / "docs" / f, B / "docs" / f)
    cp(ROOT / "docs" / "paper_section5_draft.md", B / "paper_section5_draft.md")
    for p in B.rglob("__pycache__"):
        shutil.rmtree(p)
    for p in B.rglob("README*"):
        p.unlink()
    print("building per-instance workbook...", flush=True)
    instance_workbook(B / "ket_qua" / "ket_qua_thuc_nghiem.xlsx")

    z = REL / "aciids_experiment_bundle_final.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(B.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(REL))
    print(z, round(z.stat().st_size / 1e6, 1), "MB")


if __name__ == "__main__":
    main()
