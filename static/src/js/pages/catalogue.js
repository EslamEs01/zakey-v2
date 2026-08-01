import { announce } from "../utilities/dom.js";
import { openDialog } from "../components/dialog.js";

export function initialize() {
  const dialog = document.querySelector("#filter-dialog");
  const filterTrigger = document.querySelector("[data-filter-open]");
  if (filterTrigger) {
    filterTrigger.id ||= "filter-dialog-trigger";
    filterTrigger.addEventListener("click", () => openDialog(dialog, filterTrigger));
  }
  document.querySelector("[data-sort-form] select")?.addEventListener("change", (event) => event.currentTarget.form.requestSubmit());
  document.querySelectorAll("[data-filter-remove]").forEach((button) => button.addEventListener("click", () => {
    const url = new URL(window.location.href);
    const key = button.dataset.filterRemove;
    const value = button.dataset.filterValue;
    if (key === "feature") {
      const keep = url.searchParams.getAll(key).filter((item) => item !== value);
      url.searchParams.delete(key);
      keep.forEach((item) => url.searchParams.append(key, item));
    } else {
      url.searchParams.delete(key);
    }
    url.searchParams.delete("page");
    window.location.assign(url);
  }));
  document.querySelector("[data-retry-catalogue]")?.addEventListener("click", () => {
    const url = new URL(window.location.href);
    url.searchParams.delete("qa");
    announce("جار إعادة تحميل النتائج");
    window.location.assign(url);
  });
}
