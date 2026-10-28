const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

let catalog = [];
const bookCache = new Map();
let currentBook = null;
let currentBookId = null;
let currentChapterIndex = 0;
let currentSentence = null;
let sheetHistoryEntry = false;
let pointerIsDown = false;
let selectionTimer = null;
let speechRate = .9;
let previousLightTheme = localStorage.getItem("parallel-light-theme") || "eink";

function applyTheme(theme, persist = true) {
  if (theme !== "night") {
    previousLightTheme = theme;
    if (persist) localStorage.setItem("parallel-light-theme", theme);
  }
  document.body.dataset.theme = theme;
  document.querySelector('meta[name="theme-color"]').content = theme === "night" ? "#202321" : "#f3efe5";
  $$(".theme-dot").forEach((button) => button.classList.toggle("active", button.dataset.theme === theme));
  $$('[data-theme-toggle]').forEach((button) => {
    const dark = theme === "night";
    button.setAttribute("aria-label", dark ? "Switch to e-paper mode" : "Switch to dark mode");
    button.title = dark ? "E-paper mode" : "Dark mode";
  });
  if (persist) localStorage.setItem("parallel-theme", theme);
}

const savedTheme = localStorage.getItem("parallel-theme");
if (["eink", "white", "night"].includes(savedTheme)) applyTheme(savedTheme, false);

function showScreen(name) {
  $$(".screen").forEach((element) => element.classList.remove("active"));
  $(name).classList.add("active");
  $(".topbar").style.display = name === "#readerScreen" ? "none" : "flex";
  window.scrollTo({ top: 0, behavior: "instant" });
}

function progressKey(id) {
  return `parallel-progress:${id}`;
}

function getBookProgress(book) {
  const index = Math.max(0, Math.min(Number(localStorage.getItem(progressKey(book.id))) || 0, book.chapterCount - 1));
  return { index, percent: Math.round((index / Math.max(1, book.chapterCount - 1)) * 100) };
}

function coverTitle(title) {
  return title.toUpperCase().replace(/\s+/g, " ");
}

function compactWords(wordCount) {
  return `${Math.max(1, Math.round(wordCount / 1000))}k words`;
}

function bookCard(book) {
  const progress = getBookProgress(book);
  const status = progress.index ? `${progress.percent}% read` : "Ready to read";
  return `
    <button class="book-card" data-id="${book.id}" data-language="${book.flag.toLowerCase()}" data-length="${book.length}" data-difficulty="${book.difficulty}" data-word-count="${book.wordCount}" data-title="${book.title} ${book.targetTitle} ${book.author}" data-open-book="${book.id}">
      <span class="book-cover ${book.cover}"><span>${coverTitle(book.title)}</span><small>${book.author.toUpperCase()}</small><i></i></span>
      <span class="book-meta"><strong>${book.title}</strong><span>${book.author}</span><em><b class="flag">${book.flag}</b>${book.difficultyLabel} · ${book.lengthLabel} · ${compactWords(book.wordCount)}<small>${status} · ${book.chapterCount} chapters</small></em></span>
    </button>`;
}

function addBookCard() {
  return `
    <button class="add-book-card" id="addBookCard">
      <span class="plus">+</span>
      <strong>Add a new book</strong>
      <span>EPUB, TXT, or pasted text</span>
    </button>`;
}

function renderLibrary() {
  $("#bookGrid").innerHTML = catalog.map(bookCard).join("") + '<p class="empty-library" id="emptyLibrary" hidden>No books match these filters.</p>' + addBookCard();
  $("#bookCount").textContent = `${catalog.length} complete books`;
  $("#russianCount").textContent = catalog.filter((book) => book.flag === "RU").length;
  $("#germanCount").textContent = catalog.filter((book) => book.flag === "DE").length;
  $$('[data-open-book]').forEach((button) => button.addEventListener("click", () => renderReader(button.dataset.openBook)));
  $("#addBookCard").addEventListener("click", openImport);

  const lastId = localStorage.getItem("parallel-last-book");
  const continueBook = catalog.find((book) => book.id === lastId) || catalog[0];
  if (continueBook) renderContinueCard(continueBook);
  filterBooks();
}

function renderContinueCard(book) {
  const progress = getBookProgress(book);
  $("#continueCover").className = `mini-cover ${book.cover}`;
  $("#continueCoverTitle").textContent = coverTitle(book.title);
  $("#continueCoverAuthor").textContent = book.author.toUpperCase();
  $("#continueEyebrow").textContent = `${progress.index ? "CONTINUE READING" : "START READING"} · ${book.languageName.toUpperCase()}`;
  $("#continueTitle").textContent = book.title;
  $("#continueAuthor").textContent = book.author;
  $("#continueProgress").style.width = `${progress.percent}%`;
  $("#continuePosition").textContent = `Chapter ${progress.index + 1} of ${book.chapterCount} · ${progress.percent}%`;
  $("#continueButton").dataset.openBook = book.id;
  $("#continueButton").setAttribute("aria-label", `${progress.index ? "Continue" : "Start"} ${book.title}`);
}

async function loadCatalog() {
  try {
    const response = await fetch("./books/catalog.json?v=10");
    if (!response.ok) throw new Error(`Library returned ${response.status}`);
    catalog = (await response.json()).books;
    renderLibrary();
  } catch (error) {
    console.error(error);
    $("#bookCount").textContent = "Library unavailable";
    $("#bookGrid").innerHTML = '<p class="library-error">The bundled library could not be loaded. Please refresh the page.</p>';
  }
}

async function loadBook(id) {
  if (bookCache.has(id)) return bookCache.get(id);
  const metadata = catalog.find((book) => book.id === id);
  if (!metadata) throw new Error(`Unknown book: ${id}`);
  const response = await fetch(`${metadata.path}?v=10`);
  if (!response.ok) throw new Error(`Book returned ${response.status}`);
  const book = await response.json();
  bookCache.set(id, book);
  return book;
}

async function renderReader(id) {
  showToast("Opening complete edition…");
  try {
    currentBook = await loadBook(id);
    currentBookId = id;
    currentChapterIndex = Math.max(0, Math.min(Number(localStorage.getItem(progressKey(id))) || 0, currentBook.chapters.length - 1));
    localStorage.setItem("parallel-last-book", id);
    renderChapter();
    showScreen("#readerScreen");
  } catch (error) {
    console.error(error);
    showToast("This book could not be opened. Please try again.");
  }
}

function renderChapter() {
  const chapter = currentBook.chapters[currentChapterIndex];
  const chapterNumber = currentChapterIndex + 1;
  const chapterCount = currentBook.chapters.length;
  const kicker = currentBook.flag === "RU" ? "ГЛАВА" : "KAPITEL";
  $("#readerTitle").textContent = currentBook.title;
  $("#readerChapter").textContent = chapter.englishTitle;
  $("#languageFlag").textContent = currentBook.flag;
  $("#languageName").textContent = currentBook.languageName;
  $("#chapterKicker").textContent = `${kicker} ${chapterNumber} · ${chapterCount}`;
  $("#chapterTitle").textContent = chapter.title;
  $("#pageNumber").textContent = `${chapterNumber} / ${chapterCount}`;
  $("#readerProgress").style.width = `${Math.round((chapterNumber / chapterCount) * 100)}%`;
  $("#prevPage").disabled = currentChapterIndex === 0;
  $("#nextPage").disabled = currentChapterIndex === chapterCount - 1;
  $("#editionNote").textContent = currentBook.editionNote;
  $("#sourceLinks").innerHTML = currentBook.sources.map((source) => `<a href="${source.url}" target="_blank" rel="noreferrer">${source.label}</a>`).join("");

  const content = $("#readerContent");
  content.innerHTML = "";
  chapter.paragraphs.forEach((paragraph) => {
    const element = document.createElement("p");
    paragraph.forEach(([target, english]) => {
      const sentence = document.createElement("span");
      sentence.className = "sentence";
      sentence.textContent = target;
      sentence.tabIndex = 0;
      sentence.setAttribute("role", "button");
      sentence.dataset.target = target;
      sentence.dataset.english = english;
      sentence.addEventListener("click", () => {
        // A tap opens the sentence; finishing a text selection is handled separately.
        if (hasReaderSelection()) return;
        openTranslation(sentence);
      });
      sentence.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openTranslation(sentence);
        }
      });
      element.append(sentence, " ");
    });
    content.appendChild(element);
  });
  localStorage.setItem(progressKey(currentBookId), String(currentChapterIndex));
  window.scrollTo({ top: 0, behavior: "instant" });
}

function changeChapter(direction) {
  const nextIndex = currentChapterIndex + direction;
  if (nextIndex < 0 || nextIndex >= currentBook.chapters.length) return;
  closePanels();
  currentChapterIndex = nextIndex;
  renderChapter();
}

function openTranslation(element, selectedText = "") {
  $$(".sentence").forEach((sentence) => sentence.classList.remove("active"));
  if (element) element.classList.add("active");
  currentSentence = { target: selectedText || element.dataset.target, english: element.dataset.english };
  $("#targetQuote").textContent = currentSentence.target;
  $("#englishQuote").textContent = currentSentence.english;
  $("#sheetLabel").textContent = `${currentBook.languageName.toUpperCase()} · ${selectedText ? "SELECTION" : "SENTENCE"}`;
  $("#englishLabel").textContent = selectedText ? "ORIGINAL ENGLISH · FULL SENTENCE" : "ORIGINAL ENGLISH";
  const sheet = $("#translationSheet");
  sheet.scrollTop = 0;
  sheet.style.transform = "";
  sheet.classList.add("open");
  sheet.setAttribute("aria-hidden", "false");
  $("#scrim").classList.add("active");
  // Let the phone's back button/gesture close the sheet instead of leaving the book.
  if (!sheetHistoryEntry) {
    history.pushState({ sheet: true }, "");
    sheetHistoryEntry = true;
  }
}

function hasReaderSelection() {
  const selection = window.getSelection();
  return Boolean(selection && !selection.isCollapsed && selection.toString().trim() && $("#readerContent").contains(selection.anchorNode));
}

function closePanels() {
  clearTimeout(selectionTimer);
  if (sheetHistoryEntry) {
    sheetHistoryEntry = false;
    history.back();
  }
  if (hasReaderSelection()) window.getSelection().removeAllRanges();
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  $("#listenButton").classList.remove("speaking");
  $("#listenButton span").textContent = "Listen";
  $$(".translation-sheet,.settings-panel,.modal").forEach((element) => {
    element.classList.remove("open");
    element.setAttribute("aria-hidden", "true");
  });
  $("#scrim").classList.remove("active");
  $$(".sentence").forEach((sentence) => sentence.classList.remove("active"));
}

function speak() {
  if (!currentSentence || !("speechSynthesis" in window)) return showToast("Speech isn’t available in this browser.");
  if (window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
    return;
  }
  const utterance = new SpeechSynthesisUtterance(currentSentence.target);
  utterance.lang = currentBook.language;
  utterance.rate = speechRate;
  const preferred = window.speechSynthesis.getVoices().find((voice) => voice.lang.toLowerCase().startsWith(currentBook.language.slice(0, 2).toLowerCase()));
  if (preferred) utterance.voice = preferred;
  utterance.onstart = () => {
    $("#listenButton").classList.add("speaking");
    $("#listenButton span").textContent = "Stop";
  };
  utterance.onend = utterance.onerror = () => {
    $("#listenButton").classList.remove("speaking");
    $("#listenButton span").textContent = "Listen";
  };
  window.speechSynthesis.speak(utterance);
}

function openImport() {
  closePanels();
  $("#importModal").classList.add("open");
  $("#importModal").setAttribute("aria-hidden", "false");
  $("#scrim").classList.add("active");
}

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("show"), 2600);
}

function filterBooks() {
  const activeFilter = $(".segmented button.active");
  if (!activeFilter) return;
  const language = activeFilter.dataset.filter;
  const query = $("#searchInput").value.toLowerCase();
  const length = $("#lengthFilter").value;
  const difficulty = $("#difficultyFilter").value;
  const sort = $("#sortBooks").value;
  const difficultyRank = { accessible: 1, intermediate: 2, advanced: 3 };
  const metadata = new Map(catalog.map((book) => [book.id, book]));
  const cards = $$(".book-card");
  cards.sort((left, right) => {
    const a = metadata.get(left.dataset.id);
    const b = metadata.get(right.dataset.id);
    if (sort === "shortest") return a.wordCount - b.wordCount || a.title.localeCompare(b.title);
    if (sort === "longest") return b.wordCount - a.wordCount || a.title.localeCompare(b.title);
    if (sort === "easiest") return difficultyRank[a.difficulty] - difficultyRank[b.difficulty] || a.wordCount - b.wordCount;
    if (sort === "hardest") return difficultyRank[b.difficulty] - difficultyRank[a.difficulty] || b.wordCount - a.wordCount;
    return a.title.localeCompare(b.title);
  });
  const grid = $("#bookGrid");
  cards.forEach((card) => grid.insertBefore(card, $("#emptyLibrary")));
  let count = 0;
  cards.forEach((card) => {
    const show = (language === "all" || card.dataset.language === language)
      && (length === "all" || card.dataset.length === length)
      && (difficulty === "all" || card.dataset.difficulty === difficulty)
      && card.dataset.title.toLowerCase().includes(query);
    card.hidden = !show;
    if (show) count += 1;
  });
  $("#emptyLibrary").hidden = count !== 0;
  $("#bookCount").textContent = `${count} complete book${count === 1 ? "" : "s"}`;
}

let deferredInstallPrompt = null;
const installedAsApp = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
if (installedAsApp) $("#installButton").hidden = true;
window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  $("#installButton").hidden = false;
});
window.addEventListener("appinstalled", () => {
  deferredInstallPrompt = null;
  $("#installButton").hidden = true;
  showToast("Parallel is now on your home screen.");
});
$("#installButton").addEventListener("click", async () => {
  if (deferredInstallPrompt) {
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
    return;
  }
  showToast("On iPhone or iPad: tap Share, then Add to Home Screen.");
});

$("#continueButton").addEventListener("click", (event) => renderReader(event.currentTarget.dataset.openBook));
$("#backButton").addEventListener("click", () => { closePanels(); renderLibrary(); showScreen("#libraryScreen"); });
$("#homeButton").addEventListener("click", () => showScreen("#libraryScreen"));
$("#closeSheet").addEventListener("click", closePanels);
$("#scrim").addEventListener("click", closePanels);
$("#listenButton").addEventListener("click", speak);
$("#importButton").addEventListener("click", openImport);
$("#closeImport").addEventListener("click", closePanels);
$("#readerSettingsButton").addEventListener("click", () => {
  closePanels();
  $("#settingsPanel").classList.add("open");
  $("#settingsPanel").setAttribute("aria-hidden", "false");
  $("#scrim").classList.add("active");
});
$("#closeSettings").addEventListener("click", closePanels);
$("#fontSizeInput").addEventListener("input", (event) => {
  document.documentElement.style.setProperty("--reading-size", `${event.target.value}px`);
  $("#fontSizeOutput").textContent = event.target.value;
});
$("#speechRateInput").addEventListener("input", (event) => {
  speechRate = Number(event.target.value);
  $("#speechRateOutput").textContent = `${speechRate.toFixed(1)}×`;
});
$$('.theme-dot').forEach((button) => button.addEventListener('click', () => applyTheme(button.dataset.theme)));
$$('[data-theme-toggle]').forEach((button) => button.addEventListener('click', () => applyTheme(document.body.dataset.theme === "night" ? previousLightTheme : "night")));
$$('.segmented button').forEach((button) => button.addEventListener('click', () => {
  $$('.segmented button').forEach((item) => item.classList.remove('active'));
  button.classList.add('active');
  filterBooks();
}));
$("#searchInput").addEventListener("input", filterBooks);
[$("#lengthFilter"), $("#difficultyFilter"), $("#sortBooks")].forEach((control) => control.addEventListener("change", filterBooks));
$("#searchButton").addEventListener("click", () => {
  $("#searchInput").focus();
  $("#searchField").scrollIntoView({ behavior: "smooth", block: "center" });
});
$("#fileInput").addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (!file) return;
  const validSize = file.size <= 20 * 1024 * 1024;
  $("#chosenFile").hidden = false;
  $("#chosenFile").textContent = validSize ? `Selected: ${file.name}` : `${file.name} is larger than 20 MB.`;
  $("#prepareBook").disabled = !validSize;
});
$("#prepareBook").addEventListener("click", () => { closePanels(); showToast("Book selected — automated translation is the next build step."); });
$("#prevPage").addEventListener("click", () => changeChapter(-1));
$("#nextPage").addEventListener("click", () => changeChapter(1));
$("#languageChip").addEventListener("click", () => {
  const alternative = currentBook.flag === "RU" ? "German" : "Russian";
  showToast(`This edition is ${currentBook.languageName}. Choose ${alternative} from the library.`);
});

document.addEventListener("keyup", (event) => {
  if (event.key === "Escape") closePanels();
  if (event.key === "ArrowLeft" && $("#readerScreen").classList.contains("active")) changeChapter(-1);
  if (event.key === "ArrowRight" && $("#readerScreen").classList.contains("active")) changeChapter(1);
});

// Selecting words: wait until the finger/mouse is lifted and the selection stops
// changing, so the sheet never pops up while the selection handles are being dragged.
function scheduleSelectionTranslation() {
  clearTimeout(selectionTimer);
  selectionTimer = setTimeout(() => {
    if (pointerIsDown || !hasReaderSelection()) return;
    const selection = window.getSelection();
    const text = selection.toString().replace(/\s+/g, " ").trim();
    const sentence = selection.anchorNode?.parentElement?.closest?.(".sentence");
    if (!sentence || text.length < 2 || text.length > 300) return;
    openTranslation(sentence, text);
  }, 700);
}

document.addEventListener("pointerdown", () => { pointerIsDown = true; clearTimeout(selectionTimer); });
document.addEventListener("pointerup", () => { pointerIsDown = false; if (hasReaderSelection()) scheduleSelectionTranslation(); });
document.addEventListener("pointercancel", () => { pointerIsDown = false; if (hasReaderSelection()) scheduleSelectionTranslation(); });
document.addEventListener("selectionchange", () => {
  if (!$("#translationSheet").classList.contains("open") && hasReaderSelection()) scheduleSelectionTranslation();
});

window.addEventListener("popstate", () => {
  if (!sheetHistoryEntry) return;
  sheetHistoryEntry = false;
  closePanels();
});

// Swipe the sheet down to dismiss it.
(() => {
  const sheet = $("#translationSheet");
  let startY = null;
  let dragY = 0;
  sheet.addEventListener("touchstart", (event) => {
    startY = sheet.scrollTop <= 0 ? event.touches[0].clientY : null;
    dragY = 0;
  }, { passive: true });
  sheet.addEventListener("touchmove", (event) => {
    if (startY === null) return;
    dragY = Math.max(0, event.touches[0].clientY - startY);
    if (dragY > 0) {
      sheet.style.transition = "none";
      sheet.style.transform = `translate(-50%, ${dragY}px)`;
    }
  }, { passive: true });
  sheet.addEventListener("touchend", () => {
    if (startY === null) return;
    sheet.style.transition = "";
    sheet.style.transform = "";
    if (dragY > 90) closePanels();
    startY = null;
  });
})();

loadCatalog();

if ("serviceWorker" in navigator) window.addEventListener("load", () => navigator.serviceWorker.register("./sw.js").catch(() => {}));
