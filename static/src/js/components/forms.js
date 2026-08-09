import { emailIsValid } from "../utilities/dom.js";

/**
 * Form enhancement (T-1607, FR-136).
 *
 * The prototype's newsletter handler called `preventDefault()`, faked a delay,
 * and reported success while explicitly telling the visitor nothing had been
 * saved. The form now POSTs to a real endpoint that persists the subscription.
 *
 * What is left here is a courtesy: catch an obviously malformed address before
 * the round trip. If it looks valid the submit proceeds normally, and the
 * server validates it again — this check is never the one that decides.
 */
export function initializeForms() {
  document.querySelectorAll("[data-newsletter-form]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const input = form.elements.email;
      const error = form.querySelector("#newsletter-error");
      if (emailIsValid(input.value)) {
        input.removeAttribute("aria-invalid");
        if (error) error.hidden = true;
        return; // let the browser submit
      }
      event.preventDefault();
      input.setAttribute("aria-invalid", "true");
      if (error) {
        error.textContent = "اكتب بريداً إلكترونياً صحيحاً، مثل name@example.com";
        error.hidden = false;
      }
      input.focus();
    });
  });
}
