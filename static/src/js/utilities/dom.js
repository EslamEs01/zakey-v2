export function announce(message) {
  const region = document.querySelector("#zakey-status");
  if (!region) return;
  region.textContent = "";
  window.requestAnimationFrame(() => { region.textContent = message; });
}

export function focusableElements(root) {
  return [...root.querySelectorAll("a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])")]
    .filter((element) => !element.hidden && element.getClientRects().length);
}

export function setBusy(button, busy, busyLabel = "جارٍ التنفيذ...") {
  if (!button) return;
  if (busy) {
    button.dataset.label = button.textContent;
    button.textContent = busyLabel;
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
  } else {
    button.textContent = button.dataset.label || button.textContent;
    button.disabled = false;
    button.removeAttribute("aria-busy");
  }
}

export function emailIsValid(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

export function normalizeEgyptianMobile(value) {
  let digits = value.replace(/[^\d+]/g, "");
  if (digits.startsWith("+20")) digits = `0${digits.slice(3)}`;
  else if (digits.startsWith("20") && digits.length === 12) digits = `0${digits.slice(2)}`;
  return digits;
}

export function egyptianMobileIsValid(value) {
  return /^01[0125]\d{8}$/.test(normalizeEgyptianMobile(value));
}
