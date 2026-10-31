"use client";
import { FormEvent, useState } from "react";
import Link from "next/link";
import { ArrowRight, MessageSquareText, ShieldCheck, Sparkles } from "lucide-react";
import { WorkspaceShell } from "@/components/workspace-shell";
import { api } from "@/lib/api";

export default function AssistantPage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const suggestedQuestions = [
    "What does a candidate finding mean in Privexis?",
    "How should our team interpret precision and recall metrics?",
    "Why are declared business purpose and retention schedules kept separate?",
    "What steps should our team take after a discovery scan finishes?",
    "How does Privexis guarantee read-only inspection on SQLite files?",
  ];

  async function handleAsk(e: FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setBusy(true);
    setError("");
    try {
      const res = await api<{ message: string }>("/assistant", {
        method: "POST",
        body: JSON.stringify({ question: question.trim() }),
      });
      setAnswer(res.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to obtain response.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <WorkspaceShell title="Privexis Privacy Intelligence">
      <div className="content-heading">
        <div>
          <span className="eyebrow">LOCAL EXPERT ADVISOR</span>
          <h2>Privacy Engineering &amp; Governance Assistant</h2>
          <p>
            Local guidance on classification definitions, empirical metrics interpretation, and metadata mapping best practices without transmitting source values to external providers.
          </p>
        </div>
      </div>

      {error && <div className="notice notice-error" role="alert">{error}</div>}

      <section className="assistant-layout">
        <div className="assistant-chat">
          <div className="assistant-greeting">
            <span className="assistant-mark"><Sparkles size={18} /></span>
            <div>
              <b>Privexis Privacy Intelligence</b>
              <span>Offline deterministic assistance &bull; Zero external AI data transfer</span>
            </div>
          </div>

          <div className="assistant-message">
            Welcome to Privexis Intelligence. I can explain statutory data class distinctions, guide precision and recall interpretation, clarify declared retention vs legal basis, or outline next steps in your evidence review trail.
          </div>

          {answer && (
            <div className="assistant-answer">
              <span className="answer-label">LOCAL PRIVACY ADVISOR</span>
              <p>{answer}</p>
            </div>
          )}

          <form onSubmit={handleAsk} className="assistant-input">
            <input
              required
              maxLength={1000}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask about data classes, evidence gaps, or review protocols…"
              disabled={busy}
            />
            <button className="button button-small" disabled={busy}>
              {busy ? "Consulting…" : <>Ask <ArrowRight size={14} /></>}
            </button>
          </form>
        </div>

        <aside className="panel assistant-side">
          <span className="eyebrow">SUGGESTED EXPLORATIONS</span>
          {suggestedQuestions.map((q) => (
            <button
              className="suggestion"
              key={q}
              onClick={() => {
                setQuestion(q);
              }}
            >
              <span>{q}</span>
              <ArrowRight size={13} />
            </button>
          ))}
          <p className="privacy-hint" style={{ marginTop: 20 }}>
            Defense minimization rule: Do not enter raw individual identifiers or sensitive personal records into query prompts.
          </p>
        </aside>
      </section>

      <div className="disclaimer-line">
        <ShieldCheck size={15} />
        Assistant guidance is informational and assists with technical workbench features. It does not provide certified legal counsel.
      </div>
    </WorkspaceShell>
  );
}

