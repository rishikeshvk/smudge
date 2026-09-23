import type { Route, TurnTrace } from "./api/types.gen";

export type Tone = "plain" | "ok" | "leak" | "unsure";

export type BadgePart = { text: string; tone: Tone };

const ROUTE_LABEL: Record<Route, string> = {
  answer: "answer",
  deflect: "deflect",
  deflect_out_of_plan: "out of plan",
  general: "general",
  crisis: "crisis",
};

export function routeLabel(route: Route): string {
  return ROUTE_LABEL[route];
}

function retries(count: number): string {
  return `${count} ${count === 1 ? "retry" : "retries"}`;
}

// The badge under a buddy reply: how it was routed, whether the audit passed, and how many
// redrafts that took. Every state carries its word, never colour alone.
export function badgeParts(trace: TurnTrace): BadgePart[] {
  const route: BadgePart = { text: routeLabel(trace.directive.route), tone: "plain" };
  const unsure: BadgePart[] =
    trace.classification.category === "unsure" ? [{ text: "unsure", tone: "unsure" }] : [];

  // A crisis reply is a vetted help template, not a draft, so there's no audit to report.
  if (trace.directive.route === "crisis") return [route, { text: "help template", tone: "plain" }];

  const verdict: BadgePart = trace.fell_back
    ? { text: "fallback", tone: "leak" }
    : { text: "pass", tone: "ok" };
  return [
    route,
    ...unsure,
    verdict,
    { text: retries(Math.max(trace.attempts.length - 1, 0)), tone: "plain" },
  ];
}

export type Segment = { text: string; marked: boolean };

// Splits a draft so the auditor's quoted evidence can be highlighted where it appears.
export function markEvidence(reply: string, evidence: string[]): Segment[] {
  const quotes = evidence.filter((quote) => quote.length > 0 && reply.includes(quote));
  if (quotes.length === 0) return [{ text: reply, marked: false }];

  const segments: Segment[] = [];
  let rest = reply;
  while (rest.length > 0) {
    const hits = quotes
      .map((quote) => ({ quote, at: rest.indexOf(quote) }))
      .filter((hit) => hit.at >= 0)
      .sort((a, b) => a.at - b.at);
    const first = hits[0];
    if (!first) {
      segments.push({ text: rest, marked: false });
      break;
    }
    if (first.at > 0) segments.push({ text: rest.slice(0, first.at), marked: false });
    segments.push({ text: first.quote, marked: true });
    rest = rest.slice(first.at + first.quote.length);
  }
  return segments;
}
