import Image from "next/image";
import Link from "next/link";

export function Brand({ large = false }: { large?: boolean }) {
  return <Link href="/" className={`brand ${large ? "brand-large" : ""}`} aria-label="Privexis home">
    <Image src="/brand/privexis-mark.png" alt="" width={44} height={44} priority />
    <span><strong>PRIVEXIS</strong><small>DETECT. DECRYPT. DEFEND.</small></span>
  </Link>;
}
