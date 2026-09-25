// Runs in <head> so a chosen theme applies before first paint; the system theme is the default.
const KEY = "smudge-theme";
const root = document.documentElement;

function stored() {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

function current() {
  return root.dataset.theme ?? (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}

const saved = stored();
if (saved === "light" || saved === "dark") root.dataset.theme = saved;

document.addEventListener("DOMContentLoaded", () => {
  const button = document.querySelector(".theme");
  const label = () => button.setAttribute("aria-label", `Switch to ${current() === "dark" ? "light" : "dark"} theme`);
  label();
  button.addEventListener("click", () => {
    root.dataset.theme = current() === "dark" ? "light" : "dark";
    try {
      localStorage.setItem(KEY, root.dataset.theme);
    } catch {
      // Private windows can refuse storage; the theme still switches for this visit.
    }
    label();
  });
});
