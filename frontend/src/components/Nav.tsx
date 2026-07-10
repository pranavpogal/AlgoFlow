import Link from "next/link";
import type { Route } from "next";

const links: Array<[string, Route]> = [
  ["Dashboard", "/dashboard"],
  ["Analyze", "/problem-analysis"],
  ["Hints", "/hints"],
  ["Review", "/code-review"],
  ["Interview", "/mock-interview"],
  ["Planner", "/study-planner"],
  ["Analytics", "/analytics"],
  ["Trace", "/trajectory"],
  ["Profile", "/profile"]
];

export function Nav() {
  return (
    <nav className="nav">
      <Link className="brand" href="/">
        <span className="brand-mark" />
        <span>AlgoFlow</span>
      </Link>
      <div className="nav-links">
        {links.map(([label, href]) => (
          <Link key={href} href={href}>{label}</Link>
        ))}
      </div>
    </nav>
  );
}
