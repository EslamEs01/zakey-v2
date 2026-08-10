/* ZAKEY admin attention bar.
 *
 * The server renders an empty container; this fills it from `zakey-alerts/`.
 * That split is deliberate: building the counts during page render cost eight
 * COUNT queries and pushed the catalogue and stock changelists past their
 * documented query budget. Fetching them afterwards keeps admin page rendering
 * at zero extra queries, and the endpoint answers from a 60-second cache.
 *
 * Every value from the endpoint is written with textContent or setAttribute,
 * never innerHTML — the labels are staff-facing but the counts are data, and an
 * admin page is the last place to open an injection path.
 */
(function () {
  "use strict";

  var container = document.getElementById("zk-alertbar");
  if (!container) return;

  var endpoint = container.getAttribute("data-endpoint");
  if (!endpoint) return;

  /* Levels the server is allowed to ask for. Anything else falls back to
     `info`, so a new level cannot inject an arbitrary class name. */
  var LEVELS = { critical: 1, warning: 1, info: 1 };

  function chip(alert) {
    var level = LEVELS[alert.level] ? alert.level : "info";

    var link = document.createElement("a");
    link.className = "zk-chip zk-chip--" + level;
    link.href = alert.url;

    var icon = document.createElement("i");
    /* Font Awesome class strings only; reject anything with whitespace oddities
       or characters that have no business in a class list. */
    icon.className = /^[a-z0-9 -]+$/i.test(alert.icon || "") ? alert.icon : "fas fa-bell";
    icon.setAttribute("aria-hidden", "true");

    var label = document.createElement("span");
    label.className = "zk-chip__label";
    label.textContent = alert.label;

    var count = document.createElement("span");
    count.className = "zk-chip__count";
    count.textContent = alert.count;

    link.appendChild(icon);
    link.appendChild(label);
    link.appendChild(count);
    return link;
  }

  function render(alerts) {
    if (!alerts || !alerts.length) {
      container.hidden = true;
      return;
    }

    var head = document.createElement("div");
    head.className = "zk-alertbar__head";
    var bell = document.createElement("i");
    bell.className = "fas fa-bell";
    bell.setAttribute("aria-hidden", "true");
    var heading = document.createElement("span");
    heading.textContent = "يحتاج إجراء";
    head.appendChild(bell);
    head.appendChild(heading);

    var list = document.createElement("ul");
    list.className = "zk-alertbar__list";
    alerts.forEach(function (alert) {
      var item = document.createElement("li");
      item.appendChild(chip(alert));
      list.appendChild(item);
    });

    container.textContent = "";
    container.appendChild(head);
    container.appendChild(list);
    container.hidden = false;
  }

  fetch(endpoint, {
    credentials: "same-origin",
    headers: { "X-Requested-With": "XMLHttpRequest" }
  })
    .then(function (response) {
      /* A redirect to the login page means the session expired. Staying quiet
         is right: the page itself will bounce on the next navigation. */
      if (!response.ok) throw new Error("alerts unavailable");
      return response.json();
    })
    .then(function (data) {
      render(data && data.alerts);
    })
    .catch(function () {
      container.hidden = true;
    });
})();
