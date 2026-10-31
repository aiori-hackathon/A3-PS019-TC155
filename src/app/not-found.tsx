import Link from "next/link";
import { Brand } from "@/components/brand";
export default function NotFound() { return <main className="error-page"><Brand /><span className="eyebrow">404 / NOT FOUND</span><h1>This page isn’t in the inventory.</h1><p>The link may have changed or the page may not exist.</p><Link className="button" href="/">Return to Privexis</Link></main>; }
