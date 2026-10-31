"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { Bot, MessageCircle, Send, Sparkles, X } from "lucide-react";
import { api } from "@/lib/api";

type Message = { role: "assistant" | "user"; text: string };

const starters = ["How do I start a scan?", "What are the five classes?", "How do precision and recall work?"];

export function FloatingAssistant() {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [open, messages, busy]);

  async function askText(textInput: string) {
    const text = textInput.trim();
    if (!text || busy) return;
    setQuestion("");
    setError("");
    setMessages((current) => [...current, { role: "user", text }]);
    setBusy(true);
    try {
      const result = await api<{ message: string }>("/assistant", {
        method: "POST",
        body: JSON.stringify({ question: text }),
      });
      setMessages((current) => [...current, { role: "assistant", text: result.message }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The assistant could not answer. Try again.");
    } finally {
      setBusy(false);
    }
  }

  async function ask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await askText(question);
  }

  return (
    <div className="floating-assistant-root">
      {open && (
        <section className="assistant-popover" role="dialog" aria-label="Privexis AI assistance">
          <header className="assistant-popover-head">
            <span className="assistant-popover-icon"><Bot size={18} /></span>
            <div><b>Privexis AI assistance</b><small>Local guidance · no source data sent</small></div>
            <button className="assistant-close" onClick={() => setOpen(false)} aria-label="Close assistant"><X size={17} /></button>
          </header>
          <div className="assistant-popover-body" aria-live="polite">
            <div className="assistant-bubble assistant-bubble-bot">Ask me about scans, the five data classes, review, metadata, or evaluation. I can guide your next step.</div>
            {messages.map((message, index) => <div key={`${index}-${message.role}`} className={`assistant-bubble ${message.role === "user" ? "assistant-bubble-user" : "assistant-bubble-bot"}`}>{message.text}</div>)}
            {messages.length === 0 && <div className="assistant-starters">{starters.map((starter) => <button key={starter} disabled={busy} onClick={() => { void askText(starter); }}>{starter}</button>)}</div>}
            {busy && <div className="assistant-thinking"><Sparkles size={14} /> Preparing an answer…</div>}
            {error && <p className="assistant-error" role="alert">{error}</p>}
            <div ref={endRef} />
          </div>
          <form className="assistant-popover-form" onSubmit={ask}>
            <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask a question…" aria-label="Ask the Privexis assistant" maxLength={1000} disabled={busy} />
            <button type="submit" aria-label="Send question" disabled={busy || !question.trim()}><Send size={16} /></button>
          </form>
        </section>
      )}
      <button className="assistant-fab" onClick={() => setOpen((value) => !value)} aria-label={open ? "Close AI assistance" : "Open AI assistance"} aria-expanded={open}>
        {open ? <X size={21} /> : <><MessageCircle size={21} /><span>AI help</span></>}
      </button>
    </div>
  );
}
