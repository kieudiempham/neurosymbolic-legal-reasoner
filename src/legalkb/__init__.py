"""Legal KB construction: Vietnamese legal documents -> first-order normative rules.

Layers produced (all stored as JSON under data/legalkb/, plus a compiled Prolog program):
  documents  metadata, type, hierarchy rank, issue / effective dates, relations between documents
  units      Chương / Điều / Khoản / Điểm with full text (structure.py, rule-based)
  registry   ontology: entity types (is-a), relations / predicates with typed arguments, attributes with units
  norms      normative rules: modality, bearer / beneficiary, typed variables, conditions (atoms, numeric and
             temporal constraints, alternatives), action or conclusion, formulas, deadlines, exceptions,
             sanctions, validity, source unit and quote (extract.py, LLM with a strict JSON schema)
  relations  exception / priority / implementation / reference links between norms (normalize.py)
  program    first-order Prolog compiled from the norms (compile.py)

    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.build --doc 10_bao_hiem_xa_hoi_41_2024_QH15 --articles 2
"""
