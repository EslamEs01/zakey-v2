import { announce, emailIsValid, setBusy } from "../utilities/dom.js";

export function initializePrototypeForms() {
  document.querySelectorAll("[data-prototype-form='newsletter']").forEach((form) => {
    form.addEventListener("submit", (event) => validateNewsletter(event, form));
  });
}

async function validateNewsletter(event, form) {
  event.preventDefault();
  const input = form.elements.email;
  const error = form.querySelector("#newsletter-error");
  const status = document.querySelector("[data-form-status='newsletter']");
  const button = form.querySelector("button[type='submit']");
  if (!emailIsValid(input.value)) {
    input.setAttribute("aria-invalid", "true");
    error.textContent = "اكتب بريداً إلكترونياً صحيحاً، مثل name@example.com";
    error.hidden = false;
    input.focus();
    return;
  }
  input.removeAttribute("aria-invalid");
  error.hidden = true;
  setBusy(button, true, "جارٍ العرض...");
  await new Promise((resolve) => window.setTimeout(resolve, 450));
  setBusy(button, false);
  status.className = "status-message status-message--success";
  status.textContent = "تم التحقق من البريد في النموذج فقط — لم يتم إرسال أو حفظ أي بيانات.";
  status.hidden = false;
  announce(status.textContent);
}
