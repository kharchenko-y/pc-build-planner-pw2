document.querySelector("[data-print]")?.addEventListener("click", () => window.print());

const filter = document.querySelector("#catalogue-filter");
if (filter) {
  const results = document.querySelector("#catalogue-results");
  const status = document.querySelector("#catalogue-status");
  let pending;

  filter.addEventListener("submit", async event => {
    event.preventDefault();
    pending?.abort();
    pending = new AbortController();
    const request = pending;
    const search = new URLSearchParams(new FormData(filter));
    results.setAttribute("aria-busy", "true");
    status.textContent = "Searching…";

    try {
      const response = await fetch("/components/results?" + search, { signal: request.signal });
      if (!response.ok) throw new Error("Search request failed");
      const markup = await response.text();
      if (request.signal.aborted) return;
      results.innerHTML = markup;
      status.textContent = "Search results updated.";
      history.replaceState(null, "", "/components?" + search);
    } catch (error) {
      if (!request.signal.aborted) {
        status.textContent = "Search could not load. Opening the full results page.";
        location.assign("/components?" + search);
      }
    } finally {
      if (pending === request) results.removeAttribute("aria-busy");
    }
  });
}
