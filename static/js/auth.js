/**
 * Клиентская валидация форм login/register.
 */
function getFieldScope(input) {
  return input.closest(".form-group, .auth-form-row") || input.parentElement;
}

function showError(input, msg) {
  const scope = getFieldScope(input);
  const fb = scope ? scope.querySelector(".field-error") : null;
  input.classList.add("field-invalid");
  if (scope) scope.classList.add("has-error");
  if (fb) {
    fb.textContent = msg;
    fb.classList.add("visible");
  }
}

function clearError(input) {
  input.classList.remove("field-invalid");
  const scope = getFieldScope(input);
  const fb = scope ? scope.querySelector(".field-error") : null;
  if (scope) scope.classList.remove("has-error");
  if (fb) {
    fb.classList.remove("visible");
    fb.textContent = "";
  }
}

function isEmail(v) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
}

function debounce(fn, ms) {
  let t = null;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

function isName(v) {
  return /^[A-Za-zА-Яа-яЁё]{2,15}$/.test(v);
}

function isLastName(v) {
  return /^[A-Za-zА-Яа-яЁё]{2,15}(-[A-Za-zА-Яа-яЁё]{1,15})?$/.test(v);
}

function passwordOk(v) {
  if (v.length < 8) return "Минимум 8 символов";
  if (/\s/.test(v)) return "Пробелы в пароле недопустимы";
  if (!/[a-z]/.test(v)) return "Нужны строчные буквы";
  if (!/[A-Z]/.test(v)) return "Нужны прописные буквы";
  if (!/\d/.test(v)) return "Нужны цифры";
  if (!/[^a-zA-Z0-9]/.test(v)) return "Нужны спецсимволы";
  return "";
}

document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector("form[data-validate='1']");
  if (!form) return;
  const isRegisterForm = Boolean(form.querySelector("[name='password_confirm']"));

  form.querySelectorAll("[data-password-toggle='1']").forEach((btn) => {
    btn.addEventListener("click", function () {
      const group = btn.closest(".password-field");
      const input = group ? group.querySelector("input[data-password='1']") : null;
      if (!input) return;
      input.type = input.type === "password" ? "text" : "password";
      btn.textContent = input.type === "password" ? "Показать" : "Скрыть";
      btn.setAttribute("aria-label", input.type === "password" ? "Показать пароль" : "Скрыть пароль");
    });
  });

  const emailEl = form.querySelector("[name='email']");
  const loginEl = form.querySelector("[name='login']");
  const passEl = form.querySelector("[name='password']");
  const pass2El = form.querySelector("[name='password_confirm']");
  const firstEl = form.querySelector("[name='first_name']");
  const lastEl = form.querySelector("[name='last_name']");

  const checkUnique = debounce(async () => {
    if (!isRegisterForm) return;
    if (!emailEl && !loginEl) return;
    const email = emailEl ? emailEl.value.trim() : "";
    const login = loginEl ? loginEl.value.trim() : "";

    if (emailEl) {
      if (email === "") { /* ignore */ }
      else if (!isEmail(email)) showError(emailEl, "Неверный формат email");
      else clearError(emailEl);
    }
    if (loginEl) {
      if (login === "") { /* ignore */ }
      else if (login.length < 6) showError(loginEl, "Минимум 6 символов");
      else clearError(loginEl);
    }

    const emailOk = !emailEl || email === "" || isEmail(email);
    const loginOk = !loginEl || login === "" || login.length >= 6;
    if (!emailOk && !loginOk) return;

    try {
      const fd = new FormData();
      if (emailOk) fd.append("email", email);
      if (loginOk) fd.append("login", login);
      const res = await fetch("/api/check_unique", { method: "POST", body: fd });
      const json = await res.json();
      if (!json || !json.ok) return;

      if (emailEl && email && json.email_exists) showError(emailEl, "Пользователь с такой почтой уже существует.");
      if (loginEl && login && json.login_exists) showError(loginEl, "Пользователь с таким логином уже существует.");
    } catch (_) {
      // сеть/сервер недоступны — не блокируем ввод
    }
  }, 300);

  if (isRegisterForm && emailEl) {
    emailEl.addEventListener("input", checkUnique);
    emailEl.addEventListener("blur", checkUnique);
  }
  if (isRegisterForm && loginEl) {
    loginEl.addEventListener("input", checkUnique);
    loginEl.addEventListener("blur", checkUnique);
  }

  if (isRegisterForm && passEl) {
    const onPassInput = () => {
      const msg = passwordOk(passEl.value);
      if (msg) showError(passEl, msg);
      else clearError(passEl);

      if (pass2El && pass2El.value !== "") {
        if (passEl.value !== pass2El.value) showError(pass2El, "Пароли не совпадают");
        else clearError(pass2El);
      }
    };
    passEl.addEventListener("input", onPassInput);
    passEl.addEventListener("blur", onPassInput);
  }

  if (isRegisterForm && pass2El && passEl) {
    const onPass2Input = () => {
      if (passEl.value !== pass2El.value) showError(pass2El, "Пароли не совпадают");
      else clearError(pass2El);
    };
    pass2El.addEventListener("input", onPass2Input);
    pass2El.addEventListener("blur", onPass2Input);
  }

  if (isRegisterForm && firstEl) {
    const onFirstInput = () => {
      const v = firstEl.value.trim();
      if (v === "") clearError(firstEl);
      else if (!isName(v)) showError(firstEl, "Только буквы, 2–15 символов");
      else clearError(firstEl);
    };
    firstEl.addEventListener("input", onFirstInput);
    firstEl.addEventListener("blur", onFirstInput);
  }

  if (isRegisterForm && lastEl) {
    const onLastInput = () => {
      const v = lastEl.value.trim();
      if (v === "") clearError(lastEl);
      else if (!isLastName(v)) showError(lastEl, "2–15 букв, можно двойную через дефис (например, User-U)");
      else clearError(lastEl);
    };
    lastEl.addEventListener("input", onLastInput);
    lastEl.addEventListener("blur", onLastInput);
  }

  form.addEventListener("submit", function (e) {
    let ok = true;

    form.querySelectorAll(".field-invalid").forEach((el) => el.classList.remove("field-invalid"));
    form.querySelectorAll(".has-error").forEach((el) => el.classList.remove("has-error"));
    form.querySelectorAll(".field-error.visible").forEach((el) => {
      el.classList.remove("visible");
      el.textContent = "";
    });

    const first = form.querySelector("[name='first_name']");
    const last = form.querySelector("[name='last_name']");
    const email = form.querySelector("[name='email']");
    const login = form.querySelector("[name='login']");
    const pass = form.querySelector("[name='password']");
    const pass2 = form.querySelector("[name='password_confirm']");
    const rules = form.querySelector("[name='rules']");

    [first, last, email, login].forEach((el) => {
      if (el) el.value = el.value.trim();
    });

    if (first && !isName(first.value.trim())) { ok = false; showError(first, "Только буквы, 2–15 символов"); }
    if (last && !isLastName(last.value.trim())) { ok = false; showError(last, "2–15 букв, можно двойную через дефис"); }
    if (email && !isEmail(email.value.trim())) { ok = false; showError(email, "Неверный формат email"); }
    if (isRegisterForm && login && login.value.trim().length < 6) { ok = false; showError(login, "Минимум 6 символов"); }

    if (isRegisterForm && pass) {
      const msg = passwordOk(pass.value);
      if (msg) { ok = false; showError(pass, msg); }
    }
    if (isRegisterForm && pass && pass2 && pass.value !== pass2.value) { ok = false; showError(pass2, "Пароли не совпадают"); }

    if (rules && !rules.checked) { ok = false; showError(rules, "Нужно принять правила"); }
    if (!ok) e.preventDefault();
  });
});
