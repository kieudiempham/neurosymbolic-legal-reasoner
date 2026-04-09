"use client";

import { useMemo, useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001";
const CLARIFY_PLACEHOLDER = "Co, theo thong tin toi cung cap.";

function pretty(obj) {
  if (!obj) {
    return "null";
  }
  return JSON.stringify(obj, null, 2);
}

function qualityBadgeClass(quality) {
  if (quality === "final") {
    return "badge badge-final";
  }
  if (quality === "partial") {
    return "badge badge-partial";
  }
  if (quality === "degraded") {
    return "badge badge-degraded";
  }
  return "badge";
}

async function postJson(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const text = await response.text();
  let body = null;
  if (text.trim()) {
    try {
      body = JSON.parse(text);
    } catch {
      body = { raw_text: text };
    }
  }

  if (!response.ok) {
    const detail = body?.detail || body?.error || text || "unknown_http_error";
    throw new Error(`${path} failed (${response.status}): ${detail}`);
  }

  return body || {};
}

export default function HomePage() {
  const [question, setQuestion] = useState("");
  const [askResponse, setAskResponse] = useState(null);
  const [clarifyResponse, setClarifyResponse] = useState(null);
  const [finalState, setFinalState] = useState(null);
  const [clarifyAnswers, setClarifyAnswers] = useState({});
  const [isLoadingAsk, setIsLoadingAsk] = useState(false);
  const [isLoadingClarify, setIsLoadingClarify] = useState(false);
  const [error, setError] = useState("");

  const activeResponse = finalState || clarifyResponse || askResponse;
  const needsClarification = Boolean(askResponse?.needs_clarification) && !clarifyResponse;

  const warnings = activeResponse?.warnings || [];
  const diagnostics = activeResponse?.diagnostics || {};
  const selectedRule = activeResponse?.selected_rule || null;
  const proof = activeResponse?.proof || null;
  const answer = activeResponse?.answer || null;
  const evalLog = activeResponse?.evaluation_log || {};

  const answerText = useMemo(() => {
    if (!answer) {
      return "";
    }
    return answer.answer_text || answer.text || answer.conclusion || "";
  }, [answer]);

  const ask = async () => {
    setError("");
    setIsLoadingAsk(true);
    setAskResponse(null);
    setClarifyResponse(null);
    setFinalState(null);
    setClarifyAnswers({});

    try {
      const payload = {
        question,
      };
      const response = await postJson("/ask", payload);
      setAskResponse(response);

      if (response?.needs_clarification) {
        const initialAnswers = {};
        for (const q of response?.clarification_questions || []) {
          if (q?.fact_key) {
            initialAnswers[q.fact_key] = "";
          }
        }
        setClarifyAnswers(initialAnswers);
      } else {
        setFinalState(response);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsLoadingAsk(false);
    }
  };

  const submitClarification = async () => {
    if (!askResponse?.session_id) {
      setError("Missing session_id from ask response");
      return;
    }

    setError("");
    setIsLoadingClarify(true);
    try {
      const answersPayload = (askResponse?.clarification_questions || [])
        .filter((q) => q?.fact_key)
        .map((q) => {
          const raw = clarifyAnswers[q.fact_key];
          const value = typeof raw === "string" && raw.trim() ? raw.trim() : CLARIFY_PLACEHOLDER;
          return {
            fact_key: q.fact_key,
            value,
          };
        });

      const payload = {
        session_id: askResponse.session_id,
        answers: answersPayload,
      };

      const response = await postJson("/clarify", payload);
      setClarifyResponse(response);
      setFinalState(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsLoadingClarify(false);
    }
  };

  return (
    <main>
      <section>
        <h1>Legal QA Manual FE</h1>
        <small>API base URL: {API_BASE_URL}</small>
      </section>

      <section>
        <h2>Question Input</h2>
        <textarea
          rows={4}
          placeholder="Nhap cau hoi tieng Viet"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <div className="row" style={{ marginTop: 10 }}>
          <button onClick={ask} disabled={isLoadingAsk || !question.trim()}>
            {isLoadingAsk ? "Asking..." : "Ask"}
          </button>
        </div>
      </section>

      {needsClarification && (
        <section>
          <h2>Clarification Area</h2>
          {(askResponse?.clarification_questions || []).map((q) => (
            <div className="item" key={q.fact_key || q.question_text}>
              <div><strong>fact_key:</strong> {q.fact_key}</div>
              <div><strong>question:</strong> {q.question_text}</div>
              <input
                placeholder="Nhap cau tra loi clarify"
                value={clarifyAnswers[q.fact_key] || ""}
                onChange={(e) =>
                  setClarifyAnswers((prev) => ({
                    ...prev,
                    [q.fact_key]: e.target.value,
                  }))
                }
              />
            </div>
          ))}
          <button onClick={submitClarification} disabled={isLoadingClarify}>
            {isLoadingClarify ? "Submitting..." : "Submit Clarification"}
          </button>
        </section>
      )}

      <section>
        <h2>Final Answer Area</h2>
        <div className="row">
          <span className={qualityBadgeClass(activeResponse?.answer_quality)}>
            quality: {activeResponse?.answer_quality || "n/a"}
          </span>
          {warnings.some((w) => w?.code === "FORWARD_VERIFICATION_FAILED") && (
            <span className="badge badge-warning">warning: FORWARD_VERIFICATION_FAILED</span>
          )}
        </div>
        <p><strong>final_status:</strong> {evalLog?.final_status || "n/a"}</p>
        <p><strong>answer_quality_reason:</strong> {activeResponse?.answer_quality_reason || "n/a"}</p>
        <pre>{answerText || "No answer yet"}</pre>
      </section>

      <section>
        <h2>Debug</h2>
        {error ? <pre className="error">{error}</pre> : null}

        <p><strong>warnings:</strong> {warnings.length ? warnings.map((w) => w.code).join(", ") : "none"}</p>
        <p><strong>diagnostics:</strong></p>
        <pre>{pretty(diagnostics)}</pre>

        <p><strong>selected_rule:</strong></p>
        <pre>{pretty(selectedRule)}</pre>

        <p><strong>proof (compact):</strong></p>
        <pre>{pretty(proof ? {
          proof_id: proof.proof_id,
          conclusion: proof.conclusion,
          proof_step_count: Array.isArray(proof.proof_steps) ? proof.proof_steps.length : 0,
        } : null)}</pre>

        <details>
          <summary>Ask Response JSON</summary>
          <pre>{pretty(askResponse)}</pre>
        </details>

        <details>
          <summary>Clarify Response JSON</summary>
          <pre>{pretty(clarifyResponse)}</pre>
        </details>

        <details>
          <summary>Final Merged State JSON</summary>
          <pre>{pretty(activeResponse)}</pre>
        </details>
      </section>
    </main>
  );
}
