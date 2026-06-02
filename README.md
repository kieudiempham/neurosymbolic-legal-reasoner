# ⚖️ Verification-Centric Neuro-Symbolic Legal Reasoner

> Building reliable AI systems through requirement-driven reasoning, proof construction, and multi-stage verification.

<p align="center">

![Research](https://img.shields.io/badge/AI-Engineering-blue)
![Validation](https://img.shields.io/badge/AI-Validation-green)
![LLM](https://img.shields.io/badge/LLM-Powered-orange)
![Python](https://img.shields.io/badge/Python-3.11-yellow)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Paper](https://img.shields.io/badge/Paper-Under%20Submission-success)

</p>

---

## Why This Project?

Large Language Models can generate convincing answers.

The real challenge is determining:

* Is the answer actually correct?
* Are all required conditions satisfied?
* Is the reasoning process complete?
* Can the conclusion be verified?

These challenges become critical in enterprise environments where AI-generated outputs directly affect business processes, compliance, and decision making.

This project explores a verification-centric approach for improving AI reliability through structured reasoning and validation mechanisms.

---

## Enterprise AI Perspective

Although developed in the legal domain, the core ideas are applicable to many enterprise AI systems:

| Enterprise AI Problem       | This Project                |
| --------------------------- | --------------------------- |
| AI-generated workflows      | Requirement verification    |
| AI-generated business logic | Rule validation             |
| Agent decision making       | Proof construction          |
| Hallucinated outputs        | Multi-stage verification    |
| Reliability engineering     | Verification & repair loops |
| Explainability              | Traceable reasoning         |

The project treats AI generation as a process that must be validated before execution, rather than trusted by default.

---

## System Overview

The framework combines:

* GraphRAG Retrieval
* Symbolic Reasoning
* Backward Chaining
* Forward Chaining
* Multi-Stage Verification
* Entailment-Based Validation

Instead of directly generating answers, the system follows:

Question
→ Goal
→ Requirement Set
→ Proof
→ Verification
→ Answer

This design improves reliability and reduces unsupported conclusions.

---

## Key Engineering Contributions

### Requirement-Driven Reasoning

Transforms user questions into explicit requirement sets.

Benefits:

* Detect missing information
* Prevent premature conclusions
* Improve controllability of AI outputs

---

### Proof Construction

The system builds reasoning chains before generating conclusions.

Benefits:

* Explainable decisions
* Traceable reasoning paths
* Better debugging and analysis

---

### Multi-Stage Verification

Verification is applied at multiple stages:

* Parse Verification
* Rule Verification
* Requirement Verification
* Proof Verification
* Answer Verification

This acts as a reliability layer for AI-generated outputs.

---

### Repair-Oriented Architecture

Instead of restarting the entire pipeline when errors occur, the system identifies failing components and performs targeted repair.

Benefits:

* Reduced error propagation
* Faster recovery
* More robust AI behavior

---

## Technical Stack

### AI & NLP

* Large Language Models
* GraphRAG
* Natural Language Inference
* Semantic Retrieval

### Backend

* Python
* FastAPI

### Knowledge & Reasoning

* Knowledge Graphs
* Rule-Based Systems
* Symbolic Reasoning
* Backward Chaining
* Forward Chaining

### Engineering

* Docker
* Git
* Evaluation Pipelines

---

## Evaluation

The framework was evaluated on 141 Vietnamese legal questions spanning multiple legal domains.

Results demonstrate:

* Higher answer quality compared to retrieval-based and generation-based baselines
* Improved groundedness
* Better proof construction
* Strong missing-fact detection capability
* Reduced unsupported conclusions

---

## Research Paper

### A Verification-Centric Neuro-Symbolic Framework for Vietnamese Legal Question Answering

Status:

📄 Conference Submission in Preparation

---

## What I Learned

Through this project I gained hands-on experience in:

* Designing reliable AI systems
* Validation engineering for AI outputs
* Building reasoning pipelines
* Failure analysis and error handling
* Evaluation framework design
* LLM system architecture
* Retrieval-Augmented Generation (RAG)
* Explainable AI systems

---

## Future Work

* Agentic AI validation
* Workflow generation validation
* Enterprise AI reliability engineering
* Multi-domain reasoning systems
* AI-assisted software engineering

---

> AI systems should not only generate outputs — they should verify them.
