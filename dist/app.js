const books = {
  "alice-ru": {
    title: "Alice’s Adventures in Wonderland",
    chapter: "Chapter 2 · The Pool of Tears",
    language: "ru-RU", languageName: "Russian", flag: "RU",
    kicker: "ГЛАВА ВТОРАЯ", chapterTitle: "Море слёз", page: 24, total: 236, progress: 38,
    paragraphs: [
      [
        ["Всё чудесатее и чудесатее!", "Curiouser and curiouser!"],
        ["— воскликнула Алиса (от изумления она вдруг забыла, как правильно говорить).", "cried Alice (she was so much surprised, that for the moment she quite forgot how to speak good English)."],
        ["Теперь я раздвигаюсь, словно самая большая подзорная труба на свете.", "Now I’m opening out like the largest telescope that ever was!"],
        ["Прощайте, ноги!", "Good-bye, feet!"],
      ],
      [
        ["Потому что, когда она взглянула на свои ноги, они были уже почти скрыты из виду — так далеко они оказались.", "For when she looked down at her feet, they seemed to be almost out of sight, they were getting so far off."],
        ["Ах вы, мои бедные ножки, кто же теперь будет надевать на вас чулки и башмаки, милые мои?", "Oh, my poor little feet, I wonder who will put on your shoes and stockings for you now, dears?"],
        ["Уж я-то, конечно, не смогу!", "I’m sure I shan’t be able!"],
      ],
      [
        ["Я буду слишком далеко, чтобы беспокоиться о вас; устраивайтесь как-нибудь сами.", "I shall be a great deal too far off to trouble myself about you: you must manage the best way you can."],
        ["Но мне придётся быть с ними поласковее, — подумала Алиса, — а не то они не захотят идти туда, куда мне нужно.", "But I must be kind to them, thought Alice, or perhaps they won’t walk the way I want to go!"],
      ],
    ],
  },
  "time-de": {
    title: "The Time Machine", chapter: "Chapter 1 · The Inventor", language: "de-DE", languageName: "German", flag: "DE",
    kicker: "ERSTES KAPITEL", chapterTitle: "Der Zeitreisende", page: 8, total: 194, progress: 12,
    paragraphs: [
      [["Der Zeitreisende erklärte uns gerade eine äußerst schwierige Angelegenheit.", "The Time Traveller was expounding a recondite matter to us."], ["Seine grauen Augen leuchteten und funkelten, und sein sonst blasses Gesicht war lebhaft und angeregt.", "His grey eyes shone and twinkled, and his usually pale face was flushed and animated."]],
      [["Das Feuer brannte hell, und das sanfte Licht der Glühlampen fiel auf die Perlen in den Gläsern.", "The fire burned brightly, and the soft radiance of the incandescent lights caught the bubbles that flashed and passed in our glasses."], ["Unsere Stühle, seine eigenen Entwürfe, umarmten und liebkosten uns.", "Our chairs, being his patents, embraced and caressed us."], ["Es herrschte jene luxuriöse Atmosphäre nach dem Abendessen, in der die Gedanken frei und ungezwungen schweifen.", "There was that luxurious after-dinner atmosphere when thought roams gracefully free of the trammels of precision."]],
      [["Sie müssen mir genau folgen.", "You must follow me carefully."], ["Ich werde eine oder zwei Ideen bestreiten müssen, die fast allgemein anerkannt sind.", "I shall have to controvert one or two ideas that are almost universally accepted."], ["Die Geometrie, die man Ihnen in der Schule beigebracht hat, beruht auf einem Irrtum.", "The geometry, for instance, they taught you at school is founded on a misconception."]],
    ],
  },
};

const fallback = {
  "garden-ru": ["The Secret Garden", "Тайный сад", "Мэри стояла на пороге и смотрела на длинную дорожку.", "Mary stood in the doorway and looked down the long path."],
  "frankenstein-de": ["Frankenstein", "Frankenstein", "Es war in einer trüben Novembernacht, als ich die Vollendung meiner Mühen erblickte.", "It was on a dreary night of November that I beheld the accomplishment of my toils."],
  "room-ru": ["A Room with a View", "Комната с видом", "Люси устроилась в своей комнате и открыла окно.", "Lucy settled herself in her room and opened the window."],
};

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
let currentBook = books["alice-ru"];
let currentSentence = null;
let speechRate = .9;

function showScreen(name) {
  $$(".screen").forEach((el) => el.classList.remove("active"));
  $(name).classList.add("active");
  $(".topbar").style.display = name === "#readerScreen" ? "none" : "flex";
  window.scrollTo({ top: 0, behavior: "instant" });
}

function renderReader(id) {
  currentBook = books[id];
  if (!currentBook && fallback[id]) {
    const [title, translatedTitle, target, english] = fallback[id];
    const german = id.endsWith("-de");
    currentBook = { title, chapter: "Sample chapter", language: german ? "de-DE" : "ru-RU", languageName: german ? "German" : "Russian", flag: german ? "DE" : "RU", kicker: german ? "LESEPROBE" : "ОТРЫВОК", chapterTitle: translatedTitle, page: 1, total: 180, progress: 2, paragraphs: [[[target, english], [german ? "Berühren Sie diesen Satz, um das englische Original zu sehen." : "Коснитесь этого предложения, чтобы увидеть английский оригинал.", "Tap this sentence to see its English original."]]] };
  }
  $("#readerTitle").textContent = currentBook.title;
  $("#readerChapter").textContent = currentBook.chapter;
  $("#languageFlag").textContent = currentBook.flag;
  $("#languageName").textContent = currentBook.languageName;
  $("#chapterKicker").textContent = currentBook.kicker;
  $("#chapterTitle").textContent = currentBook.chapterTitle;
  $("#pageNumber").textContent = `${currentBook.page} / ${currentBook.total}`;
  $("#readerProgress").style.width = `${currentBook.progress}%`;
  const content = $("#readerContent"); content.innerHTML = "";
  currentBook.paragraphs.forEach((paragraph) => {
    const p = document.createElement("p");
    paragraph.forEach(([target, english]) => {
      const b = document.createElement("button");
      b.className = "sentence"; b.textContent = `${target} `;
      b.dataset.target = target; b.dataset.english = english;
      b.addEventListener("click", () => openTranslation(b)); p.appendChild(b);
    });
    content.appendChild(p);
  });
  showScreen("#readerScreen");
}

function openTranslation(el, selectedText = "") {
  $$(".sentence").forEach((s) => s.classList.remove("active"));
  if (el) el.classList.add("active");
  currentSentence = { target: selectedText || el.dataset.target, english: el.dataset.english };
  $("#targetQuote").textContent = currentSentence.target;
  $("#englishQuote").textContent = currentSentence.english;
  $("#sheetLabel").textContent = `${currentBook.languageName.toUpperCase()} · ${selectedText ? "SELECTION" : "SENTENCE"}`;
  $("#translationSheet").classList.add("open"); $("#translationSheet").setAttribute("aria-hidden", "false");
  $("#scrim").classList.add("active");
}

function closePanels() {
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  $("#listenButton").classList.remove("speaking"); $("#listenButton span").textContent = "Listen";
  $$(".translation-sheet,.settings-panel,.modal").forEach((el) => { el.classList.remove("open"); el.setAttribute("aria-hidden", "true"); });
  $("#scrim").classList.remove("active");
  $$(".sentence").forEach((s) => s.classList.remove("active"));
}

function speak() {
  if (!currentSentence || !("speechSynthesis" in window)) return showToast("Speech isn’t available in this browser.");
  if (window.speechSynthesis.speaking) { window.speechSynthesis.cancel(); return; }
  const utterance = new SpeechSynthesisUtterance(currentSentence.target);
  utterance.lang = currentBook.language; utterance.rate = speechRate;
  const preferred = window.speechSynthesis.getVoices().find((v) => v.lang.toLowerCase().startsWith(currentBook.language.slice(0,2).toLowerCase()));
  if (preferred) utterance.voice = preferred;
  utterance.onstart = () => { $("#listenButton").classList.add("speaking"); $("#listenButton span").textContent = "Stop"; };
  utterance.onend = utterance.onerror = () => { $("#listenButton").classList.remove("speaking"); $("#listenButton span").textContent = "Listen"; };
  window.speechSynthesis.speak(utterance);
}

function openImport() { closePanels(); $("#importModal").classList.add("open"); $("#importModal").setAttribute("aria-hidden", "false"); $("#scrim").classList.add("active"); }
function showToast(message) { const t=$("#toast"); t.textContent=message; t.classList.add("show"); clearTimeout(showToast.timer); showToast.timer=setTimeout(()=>t.classList.remove("show"),2600); }

$$('[data-open-book]').forEach((button) => button.addEventListener("click", () => renderReader(button.dataset.openBook)));
$("#backButton").addEventListener("click", () => { closePanels(); showScreen("#libraryScreen"); });
$("#homeButton").addEventListener("click", () => showScreen("#libraryScreen"));
$("#closeSheet").addEventListener("click", closePanels); $("#scrim").addEventListener("click", closePanels); $("#listenButton").addEventListener("click", speak);
$("#importButton").addEventListener("click", openImport); $("#addBookCard").addEventListener("click", openImport); $("#closeImport").addEventListener("click", closePanels);
$("#readerSettingsButton").addEventListener("click", () => { closePanels(); $("#settingsPanel").classList.add("open"); $("#settingsPanel").setAttribute("aria-hidden","false"); $("#scrim").classList.add("active"); });
$("#closeSettings").addEventListener("click", closePanels);
$("#fontSizeInput").addEventListener("input", (e) => { document.documentElement.style.setProperty("--reading-size", `${e.target.value}px`); $("#fontSizeOutput").textContent=e.target.value; });
$("#speechRateInput").addEventListener("input", (e) => { speechRate=Number(e.target.value); $("#speechRateOutput").textContent=`${speechRate.toFixed(1)}×`; });
$$('.theme-dot').forEach((b)=>b.addEventListener('click',()=>{$$('.theme-dot').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.body.dataset.theme=b.dataset.theme;}));
$$('.segmented button').forEach((button)=>button.addEventListener('click',()=>{$$('.segmented button').forEach(x=>x.classList.remove('active'));button.classList.add('active');filterBooks();}));
$("#searchInput").addEventListener("input", filterBooks);
$("#searchButton").addEventListener("click",()=>{$("#searchInput").focus();$("#searchField").scrollIntoView({behavior:"smooth",block:"center"});});
function filterBooks(){const lang=$('.segmented button.active').dataset.filter;const q=$('#searchInput').value.toLowerCase();let count=0;$$('.book-card').forEach(c=>{const show=(lang==='all'||c.dataset.language===lang)&&c.dataset.title.toLowerCase().includes(q);c.hidden=!show;if(show)count++;});$('#bookCount').textContent=`${count} book${count===1?'':'s'}`;}

$("#fileInput").addEventListener("change", (e) => { const f=e.target.files[0]; if(!f)return; const ok=f.size<=20*1024*1024; $("#chosenFile").hidden=false; $("#chosenFile").textContent=ok?`Selected: ${f.name}`:`${f.name} is larger than 20 MB.`; $("#prepareBook").disabled=!ok; });
$("#prepareBook").addEventListener("click",()=>{closePanels();showToast("Book selected — translation service is the next build step.");});
$("#prevPage").addEventListener("click",()=>showToast("You’re at the start of this sample."));
$("#nextPage").addEventListener("click",()=>showToast("Next-page navigation is ready for imported chapters."));
$("#languageChip").addEventListener("click",()=>{const alt=currentBook.flag==='RU'?'German':'Russian';showToast(`This edition is ${currentBook.languageName}. Choose ${alt} from the library.`);});

document.addEventListener("keyup",(e)=>{if(e.key==="Escape")closePanels();});
document.addEventListener("selectionchange",()=>{
  const selection=window.getSelection(); const text=selection?.toString().trim();
  if(!text || text.length<2 || !$("#readerContent").contains(selection.anchorNode)) return;
  const sentence=selection.anchorNode?.parentElement?.closest?.('.sentence');
  if(sentence && text.length<180){ clearTimeout(document.selectionTimer); document.selectionTimer=setTimeout(()=>openTranslation(sentence,text),350); }
});

if ("serviceWorker" in navigator) window.addEventListener("load",()=>navigator.serviceWorker.register("./sw.js").catch(()=>{}));
