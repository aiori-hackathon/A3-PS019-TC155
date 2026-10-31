"use client";
import "./globals.css";
export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <html lang="en"><body><main className="error-page"><span className="eyebrow">SERVICE ERROR</span><h1>Privexis needs another moment.</h1><p>The application could not render this view.</p><button className="button" onClick={() => reset()}>Try again</button></main></body></html>;
}
