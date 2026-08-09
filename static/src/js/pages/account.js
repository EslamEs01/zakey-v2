/**
 * Account page behaviour (T-1606/T-1607).
 *
 * Whether a visitor is signed in, what their orders are, and what is on their
 * wishlist are all decided by the session and rendered by the server. The
 * prototype decided all three in the browser: it read a fabricated account out
 * of the fixture and flipped between "signed-in" and "signed-out" on a query
 * parameter, which meant anyone could render a stranger's account page.
 *
 * The tabs are ordinary links (`?tab=`), so they work without JavaScript. This
 * only upgrades them to in-page switching to avoid a round trip.
 */

const PANEL_SELECTOR = "[data-account-panel-id]";

function showTab(tab) {
  const panels = [...document.querySelectorAll(PANEL_SELECTOR)];
  const target = panels.find((panel) => panel.dataset.accountPanelId === tab);
  if (!target) return false;

  panels.forEach((panel) => {
    panel.hidden = panel !== target;
  });
  document.querySelectorAll("[data-account-tab-id]").forEach((link) => {
    const active = link.dataset.accountTabId === tab;
    link.classList.toggle("is-active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  target.querySelector("h3")?.focus?.();
  return true;
}

export function initialize() {
  const root = document.querySelector("[data-account-mode]");
  if (!root || root.dataset.accountMode !== "signed-in") return;

  document.querySelectorAll("[data-account-tab-id]").forEach((link) => {
    link.addEventListener("click", (event) => {
      const tab = link.dataset.accountTabId;
      if (!showTab(tab)) return; // fall through to a normal navigation
      event.preventDefault();
      const url = new URL(window.location.href);
      url.searchParams.set("tab", tab);
      window.history.pushState({ tab }, "", url);
    });
  });

  window.addEventListener("popstate", () => {
    showTab(new URLSearchParams(window.location.search).get("tab") || "orders");
  });
}
