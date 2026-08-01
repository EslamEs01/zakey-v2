import { focusableElements } from "../utilities/dom.js";

export function openDialog(dialog, trigger) {
  if (!dialog) return;
  dialog.dataset.triggerId = trigger?.id || "";
  dialog.showModal();
  const focusable = focusableElements(dialog);
  (focusable[0] || dialog).focus();
}

export function closeDialog(dialog) {
  if (!dialog?.open) return;
  const trigger = dialog.dataset.triggerId ? document.getElementById(dialog.dataset.triggerId) : null;
  dialog.close();
  trigger?.focus();
}

export function initializeDialogs() {
  document.querySelectorAll("dialog").forEach((dialog) => {
    dialog.addEventListener("cancel", (event) => {
      event.preventDefault();
      closeDialog(dialog);
    });
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) closeDialog(dialog);
    });
    dialog.addEventListener("keydown", (event) => {
      if (event.key !== "Tab") return;
      const items = focusableElements(dialog);
      if (!items.length) return;
      const first = items[0];
      const last = items.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    });
    dialog.querySelectorAll("[data-dialog-close]").forEach((button) => button.addEventListener("click", () => closeDialog(dialog)));
  });
}
