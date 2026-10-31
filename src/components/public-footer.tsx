import Link from "next/link";
import { Brand } from "./brand";
export function PublicFooter() {
  return <footer className="public-footer"><div className="footer-top"><div><Brand /><p>Structured privacy evidence for data teams.</p></div><div className="footer-links"><Link href="/about">About</Link><Link href="/faq">FAQ</Link><Link href="/contact">Contact</Link><Link href="/privacy">Privacy</Link><Link href="/terms">Terms</Link></div></div><div className="footer-bottom"><span>© {new Date().getFullYear()} Privexis</span><span>Technical evidence for human review. Not a legal determination.</span></div></footer>;
}
