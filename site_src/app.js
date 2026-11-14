// Seaborn with Penguins: navigation, quizzes, and progress ticks.
(function () {
  "use strict";
  var page = document.body.dataset.page;

  function store(key, value) {
    try {
      if (value === undefined) return JSON.parse(localStorage.getItem(key) || "null");
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) { return null; }
  }

  // Mobile menu
  var toggle = document.querySelector(".nav-toggle");
  var sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", function () {
      var open = sidebar.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Progress ticks in the sidebar: a page is "done" when its quiz is all correct.
  function markDone() {
    var done = store("sbp-done") || {};
    document.querySelectorAll(".nav-list a").forEach(function (a) {
      if (done[a.dataset.page]) a.classList.add("done");
    });
  }
  markDone();

  // Quizzes
  var questions = Array.prototype.slice.call(document.querySelectorAll(".quiz-q"));
  var results = {};  // first attempt per question
  var solved = {};
  function updateScore() {
    var box = document.querySelector(".quiz-score");
    if (!box || !questions.length) return;
    var answered = Object.keys(results).length;
    var right = Object.keys(results).filter(function (k) { return results[k]; }).length;
    box.textContent = "Score: " + right + " / " + questions.length +
      (answered < questions.length ? "  (" + (questions.length - answered) + " to go)" : "");
    if (Object.keys(solved).length === questions.length) {
      box.textContent += "  - all questions solved, lesson complete!";
      var done = store("sbp-done") || {};
      done[page] = true;
      store("sbp-done", done);
      markDone();
    }
  }
  questions.forEach(function (q) {
    var btn = q.querySelector('[data-action="grade"]');
    var feedback = q.querySelector(".quiz-feedback");
    var explain = q.querySelector(".quiz-explain");
    btn.addEventListener("click", function () {
      var picked = q.querySelector("input:checked");
      q.querySelectorAll("label").forEach(function (l) { l.classList.remove("is-correct", "is-wrong"); });
      if (!picked) {
        feedback.className = "quiz-feedback no";
        feedback.textContent = "Pick an answer first.";
        return;
      }
      var ok = picked.value === q.dataset.answer;
      if (!(q.id in results)) results[q.id] = ok;  // first attempt counts
      picked.closest("label").classList.add(ok ? "is-correct" : "is-wrong");
      if (ok) {
        solved[q.id] = true;
        feedback.className = "quiz-feedback ok";
        feedback.textContent = "Correct.";
        explain.hidden = false;
      } else {
        feedback.className = "quiz-feedback no";
        feedback.textContent = "Not quite - try another option.";
        explain.hidden = true;
      }
      if (ok && results[q.id] === false) {
        feedback.textContent = "Correct (on a retry - the score keeps your first answer).";
      }
      updateScore();
    });
  });
  updateScore();
})();
