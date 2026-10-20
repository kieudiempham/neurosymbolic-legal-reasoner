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
    wb.save(path)


README = """# Gói thực nghiệm — Cross-Layer Model-Based Diagnosis for Neuro-Symbolic Legal QA (ACIIDS)

Mã nguồn đầy đủ và lịch sử thay đổi: GitHub `kieudiempham/neurosymbolic-legal-reasoner`, branch
`feat/cross-layer-mbd-diagnosis`, commit `{commit}`. Gói này chứa đúng dữ liệu và kết quả của commit đó.

## Mở gì trước
1. `ket_qua/bang_ket_qua.md` — các bảng trong paper (Mục 5).
2. `ket_qua/ket_qua_tung_ca.xlsx` — **kết quả từng ca** của Ours và Heuristic (mỗi dòng một ca), đủ để tự tính lại
   mọi con số trong bảng; sheet "Chọn tham số (dev)" cho thấy tham số được chọn trên dev.
3. `du_lieu/CrossLayer_MBD_Benchmark_300QA.xlsx` — 300 câu hỏi, dữ kiện, đáp án, căn cứ (để thẩm định nhãn).
4. `paper_section5_draft.md` — bản nháp Mục 5.

## Cấu trúc
- `du_lieu/dataset/` — 300 câu hỏi theo domain (jsonl, kèm split dev/test, nhãn đã sửa `label_revisions.json`),
  bộ lỗi F1–F4 ngoài (`diag_gpt_v1/`).
- `du_lieu/kb/` — 5 KB dùng khi suy luận (`kb_*.yaml` = rule + quan hệ ngoại lệ; `*_vocabulary.yaml` = nghĩa
  vị từ; `*_patches.yaml` = các bản vá, CHỈ từ lỗi trên dev, có ghi lý do). `draft_rules_7906.zip` = rule nháp.
- `ket_qua/` — kết quả gốc dạng JSON (`chan_doan_ngoai/` = bộ F1–F4, `tiem_loi_theo_domain/` = benchmark tiêm
  lỗi, mỗi file có `per_instance` từng ca và mọi cấu hình), lưới hiệu chỉnh, chỉ số NLI trên dev.
- `nli_cache/` — điểm NLI đã tính (mDeBERTa, Qwen2.5-7B, GPT-4o-mini) để chạy lại KHÔNG cần GPU hay API.
- `ma_nguon/` — `src/diagnosis` (pipeline, MBD Prolog `mbd.pl`, thực nghiệm), `kaggle/` (script GPU).
- `docs/` — rubric IRAC, quy ước nhãn, checklist sửa paper.

## Quy trình (tóm tắt)
- KB: 18 văn bản → 7.906 rule nháp (GPT-4o-mini) → chọn theo điều luật được trích dẫn, viết lại theo bộ vị từ
  chung, rà soát → 636 rule, 422 quan hệ ngoại lệ.
- Split theo tình huống pháp lý (câu diễn đạt lại đi cùng nhau): dev 194 / test 106; BHXH toàn bộ là dev.
- Mọi lựa chọn (bản vá KB, mô hình đo NLI, prompt, ngưỡng τ) chỉ dựa trên dev; tiêu chí chọn đặt trước
  (trung bình của độ chính xác chẩn đoán và 1 − tỉ lệ báo lỗi oan). Test chỉ chạy một lần với cấu hình đã chọn.
- Chẩn đoán: tập chẩn đoán tối thiểu (Reiter) liệt kê trong SWI-Prolog 10.0.2; NLI là phép đo, chỉ thành quan sát
  khi xác suất ≥ τ.

## Chạy lại (Windows, Python 3.14, SWI-Prolog 10)
```
python -m venv .venv && .venv\\Scripts\\pip install -r ma_nguon/requirements_diag.txt
set PYTHONPATH=ma_nguon/src
set NLI_BACKEND=ensemble_gpt& set NLI_TAU=0.5& set NLI_RULE=pos_only
python -m diagnosis.external_diag --configs base_nesy,nesy_diag,no_mbd,rule_check,raw_nli
python -m diagnosis.run_eval --dataset <file jsonl của domain> --kb <kb_*.yaml> --configs base_nesy,nesy_diag,no_mbd,rule_check,raw_nli
python -m diagnosis.make_aciids_tables
```
(cần đặt `nli_cache/*.json` vào `experiments/diag/` như trong repo; đường dẫn chi tiết xem README của repo.)

## Hạn chế đã biết (ghi trong paper)
Nhãn gold do GPT sinh, đang chờ thẩm định pháp lý; mỗi ca chỉ một lỗi; người dùng mô phỏng biết đủ dữ kiện;
câu hỏi pháp lý (goal) được cho sẵn; tập test nhỏ (106 câu).
"""


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if B.exists():
        shutil.rmtree(B)
    (B / "ket_qua").mkdir(parents=True)
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    (B / "README_VI.md").write_text(README.format(commit=commit), encoding="utf-8")

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
    print("building per-instance workbook...", flush=True)
    instance_workbook(B / "ket_qua" / "ket_qua_tung_ca.xlsx")

    z = REL / "aciids_experiment_bundle.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(B.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(REL))
    print(z, round(z.stat().st_size / 1e6, 1), "MB")


if __name__ == "__main__":
    main()
