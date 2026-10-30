// Custom audio player: wires the .hplayer markup to its hidden <audio> (events are caught on document).
(function () {
    const fmt = s => isFinite(s) ? Math.floor(s / 60) + ":" + String(Math.floor(s % 60)).padStart(2, "0") : "0:00";
    const box = a => a.closest(".hplayer");

    function sync(a) {
        const p = box(a);
        if (!p) return;
        p.querySelector(".hp-btn").textContent = a.paused ? "▶" : "⏸";
        p.querySelector(".hp-fill").style.width = (a.duration ? 100 * a.currentTime / a.duration : 0) + "%";
        p.querySelector(".hp-time").textContent = fmt(a.currentTime) + " / " + fmt(a.duration);
    }

    ["play", "pause", "ended", "timeupdate", "loadedmetadata"].forEach(ev =>
        document.addEventListener(ev, e => e.target.tagName === "AUDIO" && sync(e.target), true));

    document.addEventListener("click", e => {
        const p = e.target.closest(".hplayer");
        if (!p) return;
        const a = p.querySelector("audio");
        if (e.target.closest(".hp-btn")) {
            a.paused ? a.play() : a.pause();
        } else if (e.target.closest(".hp-bar") && a.duration) {
            const r = p.querySelector(".hp-bar").getBoundingClientRect();
            a.currentTime = a.duration * Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
        }
    });
})();
