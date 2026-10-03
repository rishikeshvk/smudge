// The live demo: one question at a time to the demo buddy, through the same gate as the app.
const API = ["localhost", "127.0.0.1"].includes(location.hostname)
  ? "http://localhost:8000"
  : "https://kindred.tail028abe.ts.net";
const INVITE = "mailto:rishikeshvk2001@gmail.com?subject=Smudge%20invite";

const CATEGORY = {
  curriculum: "about the course",
  out_of_plan: "outside the plan",
  off_topic: "off topic",
  meta: "about Juno itself",
  crisis: "a crisis",
  unsure: "unsure, so it plays safe",
};
const ROUTE = {
  answer: "answered from its notes",
  deflect: "held back: not studied yet",
  deflect_out_of_plan: "held back: not on the plan",
  general: "general chat",
  crisis: "pointed to real help",
};

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

const dayLabel = (topic) => `day ${topic.day} · ${topic.title}`;

function audit(attempts, fellBack) {
  if (attempts.length === 0) return fellBack ? "no draft came through; it sent a safe deflection" : "not needed";
  const lines = attempts.map((attempt, i) =>
    attempt.verdict === "pass"
      ? `draft ${i + 1} passed`
      : `draft ${i + 1} blocked${attempt.leaked_topics.length ? `, it touched ${attempt.leaked_topics.join(", ")}` : ""}`,
  );
  if (fellBack) lines.push("so it sent a safe deflection instead");
  return lines.join("; ");
}

function xray(turn) {
  const rows = [
    ["classified", CATEGORY[turn.category] ?? turn.category],
    ["route", ROUTE[turn.route] ?? turn.route],
  ];
  if (turn.deflect_topics.length) rows.push(["kept back", turn.deflect_topics.map(dayLabel).join(", ")]);
  rows.push(["notes read", turn.notes.length ? turn.notes.map(dayLabel).join(", ") : "none"]);
  rows.push(["audit", audit(turn.attempts, turn.fell_back)]);
  rows.push(["took", `${(turn.latency_ms / 1000).toFixed(1)} s · ${turn.turns_left} questions left today`]);

  const list = element("dl", "xray");
  list.append(element("p", "band", "x-ray"));
  for (const [term, detail] of rows) {
    const row = element("div");
    row.append(element("dt", "", term), element("dd", "", detail));
    list.append(row);
  }
  return list;
}

document.addEventListener("DOMContentLoaded", async () => {
  const root = document.querySelector("[data-api]");
  const range = root.querySelector("#try-day");
  const thread = root.querySelector(".thread");
  const suggest = root.querySelector(".suggest");
  const form = root.querySelector(".ask");
  const input = form.querySelector("input");
  const send = form.querySelector("button");
  const status = root.querySelector(".status");
  let days = [];

  const say = (text, invite = false) => {
    status.textContent = text;
    if (invite) {
      const link = element("a", "", "ask for an invite");
      link.href = INVITE;
      status.append(" Want the real thing? ", link, ".");
    }
  };

  const showDay = () => {
    const day = Number(range.value);
    const tomorrow = days[day];
    root.querySelector("#try-day-out").textContent = day;
    root.querySelector("#try-today").textContent = days[day - 1].title;
    root.querySelector("#try-tomorrow").textContent = tomorrow ? tomorrow.title : "nothing, the plan ends here";
    suggest.replaceChildren(
      ...[
        `what did you make of ${days[day - 1].title}?`,
        tomorrow && `what's ${tomorrow.title} about?`,
        "are you an AI?",
      ]
        .filter(Boolean)
        .map((text) => {
          const chip = element("button", "chip", text);
          chip.type = "button";
          chip.addEventListener("click", () => {
            input.value = text;
            input.focus();
          });
          return chip;
        }),
    );
  };

  try {
    const response = await fetch(`${API}/demo`);
    if (!response.ok) throw new Error(String(response.status));
    const demo = await response.json();
    days = demo.days;
    range.max = days.length;
    say(demo.turns_left ? "" : "That's all the questions for today; try again tomorrow.", !demo.turns_left);
  } catch {
    say("Juno is offline right now. The film above shows a real week instead.");
    return;
  }
  for (const part of [root.querySelector(".day"), suggest, form]) part.hidden = false;
  range.addEventListener("input", showDay);
  showDay();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    const day = Number(range.value);
    thread.replaceChildren(element("p", "bubble you", message));
    const waiting = element("p", "checking");
    waiting.append(element("span"), element("span"), element("span"), "writing, then checking it's not a spoiler. this can take a minute");
    thread.append(waiting);
    send.disabled = true;
    say("");
    try {
      const response = await fetch(`${API}/demo/turns`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, day }),
      });
      const body = await response.json();
      waiting.remove();
      if (!response.ok) {
        say(typeof body.detail === "string" ? body.detail : "That didn't go through.", response.status === 429);
        return;
      }
      thread.append(element("p", "bubble", body.reply), xray(body));
      input.value = "";
    } catch {
      waiting.remove();
      say("Couldn't reach Juno. Try again in a minute.");
    } finally {
      send.disabled = false;
    }
  });
});
