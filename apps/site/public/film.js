// The loop plays only when the visitor hasn't asked for less motion, and can always be paused.
const PLAY = '<path d="M8 5v14l11-7z"/>';
const PAUSE = '<path d="M8 5h3v14H8zM13 5h3v14h-3z"/>';

document.addEventListener("DOMContentLoaded", () => {
  const video = document.querySelector(".film video");
  const button = document.querySelector(".film .pause");
  const show = () => {
    const playing = !video.paused;
    button.querySelector("svg").innerHTML = playing ? PAUSE : PLAY;
    button.setAttribute("aria-label", `${playing ? "Pause" : "Play"} the film loop`);
  };
  video.addEventListener("play", show);
  video.addEventListener("pause", show);
  button.addEventListener("click", () => (video.paused ? video.play() : video.pause()));
  if (!matchMedia("(prefers-reduced-motion: reduce)").matches) video.play().catch(show);
  show();
});
