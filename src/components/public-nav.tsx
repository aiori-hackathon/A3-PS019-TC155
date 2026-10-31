"use client";
import Link from "next/link";
import { Menu, Search, X } from "lucide-react";
import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Brand } from "./brand";

const links = [["Platform", "/features"], ["How it works", "/how-it-works"], ["Security", "/security"], ["Documentation", "/documentation"]];
export function PublicNav() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const router = useRouter();
  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const term = query.trim();
    if (term) router.push(`/search?q=${encodeURIComponent(term)}`);
  }
  return <header className="public-nav"><Brand /><button className="mobile-menu" aria-label={open ? "Close navigation" : "Open navigation"} aria-expanded={open} onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button>
    <nav className={open ? "nav-links nav-open" : "nav-links"} aria-label="Main navigation">{links.map(([label, href]) => <Link key={href} href={href} onClick={() => setOpen(false)}>{label}</Link>)}</nav>
    <form className="site-search" role="search" onSubmit={search}><Search size={15} /><input aria-label="Search Privexis" placeholder="Search features or findings" value={query} onChange={(event) => setQuery(event.target.value)} /><button type="submit">Search</button></form>
    <div className="nav-actions"><Link href="/data-sources" className="button button-small">Get started <span aria-hidden="true">↗</span></Link></div>
  </header>;
}
