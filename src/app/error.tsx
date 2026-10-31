"use client";
import { useEffect } from "react";
export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => { console.error("Privexis route error", error.digest); }, [error]);
  return <main className="error-page"><span className="eyebrow">SERVICE ERROR</span><h1>This view could not load.</h1><p>Try again. If the issue continues, check that the Privexis API is available.</p><button className="button" onClick={() => reset()}>Try again</button></main>;
}
