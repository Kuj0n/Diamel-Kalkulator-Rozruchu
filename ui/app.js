/* Kalkulator Rozruchu - logika okna. Obliczenia, raport i pliki: Python (interfejs.py) przez window.pywebview.api */
'use strict';

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (t) => String(t ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const lp = (n, m = 2) => Number(n || 0).toLocaleString('pl-PL', { minimumFractionDigits: m, maximumFractionDigits: m });
const lc = (n) => Number(n || 0).toLocaleString('pl-PL', { maximumFractionDigits: 2 });
const nazwaPliku = (p) => String(p || '').split(/[\\/]/).pop();

const IK = {
  ok: '<path d="M20 6 9 17l-5-5"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  plik: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
  pobierz: '<path d="M12 3v12M7 10l5 5 5-5M5 21h14"/>',
  odswiez: '<path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  kosz: '<path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 8h.01M11 12h1v5h1"/>',
  uwaga: '<path d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/>',
  folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>',
  zapisz: '<path d="M5 3h11l5 5v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/><path d="M7 3v5h8M7 21v-7h10v7"/>',
  nowy: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z"/><path d="M14 3v5h5M12 11v6M9 14h6"/>',
  otworz: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v1M3 7v10a2 2 0 0 0 2 2h12l4-8H7l-4 8"/>',
  word: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z"/><path d="M14 3v5h5M8 12l1.3 5L11 13l1.7 4L14 12"/>',
  piorun: '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z"/>',
  bateria: '<rect x="2" y="7" width="18" height="11" rx="2"/><path d="M22 11v3M6 11v3M10 11v3"/>',
  kabel: '<path d="M4 4v5a4 4 0 0 0 4 4h8a4 4 0 0 1 4 4v3M2 4h4M18 20h4"/>',
  wtyczka: '<path d="M9 2v6M15 2v6M6 8h12v4a6 6 0 0 1-12 0V8ZM12 18v4"/>',
  zegar: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  silnik: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M7 7V4h3v3M14 7V4h3v3M13 10l-3 4h4l-3 4"/>',
  obraz: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m21 16-5-5-9 9"/>',
  dokument: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z"/><path d="M14 3v5h5"/>',
  dalej: '<path d="M9 6l6 6-6 6"/>',
  wyslij: '<path d="M22 2 11 13M22 2l-7 20-4-9-9-4Z"/>',
  baza: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
  szukaj: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
};
const ik = (n, kl = '') => `<svg class="ik ${kl}" viewBox="0 0 24 24">${IK[n]}</svg>`;

// ------------------------------------------------------------------ stan okna
let INFO = {}, BAZA = { starters: {}, batteries: {} }, P = null, W = null, AKT = null, AKT_BAZY = null, KONTO = { zalogowany: false };
let ZAPISANY = '';      // projekt w chwili ostatniego zapisu / wczytania (do wykrywania zmian)
let widok = 'obliczenia';
let przeliczTimer = null;
const baza = { rodzaj: 'starters', wybrany: null, szukaj: '' };
const MINIATURY = {};  // ścieżka -> data URI (albo '' gdy pliku nie ma)

async function api(nazwa, ...arg) {
  try {
    return await window.pywebview.api[nazwa](...arg);
  } catch (e) {
    toast(`Błąd programu (${nazwa}): ${esc(e.message || e)}`, 'blad');
    console.error(e);
    return null;
  }
}

// ------------------------------------------------------------------ motyw i rozmiar
const ciemnySystem = window.matchMedia('(prefers-color-scheme: dark)');
function ustawMotyw(m) {
  document.documentElement.dataset.motyw = m === 'system' ? (ciemnySystem.matches ? 'ciemny' : 'jasny') : m;
  $$('#motyw button').forEach((b) => b.classList.toggle('akt', b.dataset.motyw === m));
}
ciemnySystem.addEventListener('change', () => INFO.program && ustawMotyw(INFO.program.motyw));
async function zmienProgram(klucz, wartosc) {
  INFO.program = await api('ustaw_program', klucz, wartosc);
  if (klucz === 'motyw') ustawMotyw(wartosc);
  if (klucz === 'rozmiar') document.documentElement.dataset.rozmiar = wartosc;
}

// ------------------------------------------------------------------ powiadomienia i okna dialogowe
function toast(tekst, rodzaj = '', akcje = null, czas = 5000) {
  const el = document.createElement('div');
  el.className = `toast ${rodzaj}`;
  el.innerHTML = `${ik(rodzaj === 'blad' ? 'uwaga' : rodzaj === 'ok' ? 'ok' : 'info')}<span>${tekst}</span>`;
  for (const a of [].concat(akcje || [])) {
    const b = document.createElement('button');
    b.className = 'btn btn-maly';
    b.textContent = a.tekst;
    b.onclick = () => { a.fn(); el.remove(); };
    el.append(b);
  }
  $('#powiadomienia').append(el);
  setTimeout(() => el.remove(), rodzaj === 'blad' ? czas * 2 : czas);
}

let modalOtwarty = null;
function modal({ tytul, tresc = '', przyciski = [], szeroki = false, poOtwarciu = null }) {
  return new Promise((gotowe) => {
    const tlo = document.createElement('div');
    tlo.className = 'modal-tlo';
    tlo.innerHTML = `<div class="modal ${szeroki ? 'szeroki' : ''}" role="dialog"><h2>${tytul}</h2><div class="tresc-modala">${tresc}</div>
      ${przyciski.length ? `<div class="przyciski">${przyciski.map((p, i) => `<button class="btn ${p.klasa || ''}" data-i="${i}">${p.tekst}</button>`).join('')}</div>` : ''}</div>`;
    const zamknij = (w) => { tlo.remove(); modalOtwarty = null; gotowe(w); };
    tlo.addEventListener('click', (e) => {
      if (e.target === tlo) zamknij(null);
      const b = e.target.closest('[data-i]');
      if (b) zamknij(przyciski[+b.dataset.i].wartosc);
      const w = e.target.closest('[data-wybor]');
      if (w) zamknij(w.dataset.wybor);
    });
    modalOtwarty = { zamknij, el: tlo };
    $('#modal-miejsce').append(tlo);
    const dom = przyciski.findIndex((p) => p.domyslny);
    (dom >= 0 ? $(`[data-i="${dom}"]`, tlo) : $('input, textarea, .btn', tlo))?.focus();
    poOtwarciu?.(tlo, zamknij);
  });
}

// ------------------------------------------------------------------ start
window.addEventListener('pywebviewready', start);

async function start() {
  INFO = await api('informacje');
  ustawMotyw(INFO.program.motyw);
  document.documentElement.dataset.rozmiar = INFO.program.rozmiar;
  $('#boczne-wersja').textContent = `DIAMEL · v${INFO.wersja}`;
  BAZA = INFO.baza;
  KONTO = INFO.konto;
  ustawProjekt(INFO.projekt);
  pokaz('obliczenia');
  if (INFO.przeniesiono_baze) toast('Twoja baza urządzeń została przeniesiona do folderu ustawień programu (AppData) - własne wpisy zostały zachowane.', 'ok', null, 9000);
  sprawdzAktualizacje(false);
  sprawdzBaze(false);
  odswiezKonto();
}

// ------------------------------------------------------------------ konto Diamel (nieobowiązkowe): szablon raportu firmy, inicjały
async function odswiezKonto() {
  if (!KONTO.zalogowany) return;
  const r = await api('konto_odswiez');
  if (!r) return;
  KONTO = r.stan;
  if (r.wylogowano) toast(`Wylogowano z konta Diamel: ${esc(r.wylogowano)} Raporty mają teraz stopkę programu.`, 'blad');
  odswiezDol();
  if (widok === 'ustawienia') rysujUstawienia();
  if (widok === 'obliczenia') rysujWyniki();
}

/** Po zalogowaniu / wylogowaniu: nowy, nieruszony projekt dostaje inicjały z konta. */
async function poZmianieKonta() {
  if (!P._plik && !czyNiezapisane()) ustawProjekt(await api('nowy_projekt'));
  odswiezDol();
  rysujUstawienia();
}

function opisSzablonu() {
  if (INFO.program.szablon) return `stopka z szablonu ${nazwaPliku(INFO.program.szablon)}`;
  if (KONTO.szablon) return `papier firmowy ${KONTO.firma}`;
  return 'stopka programu';
}

function pokaz(nazwa) {
  widok = nazwa;
  $$('.poz').forEach((b) => b.classList.toggle('akt', b.dataset.widok === nazwa));
  $$('.widok').forEach((s) => s.classList.toggle('ukryty', s.id !== `widok-${nazwa}`));
  if (nazwa === 'obliczenia') rysujObliczenia();
  if (nazwa === 'baza') rysujBaze();
  if (nazwa === 'ustawienia') rysujUstawienia();
  if (nazwa === 'zglos') rysujZglos();
  rysujPasek();
}
$$('.poz').forEach((b) => b.addEventListener('click', () => pokaz(b.dataset.widok)));
$$('#motyw button').forEach((b) => b.addEventListener('click', () => zmienProgram('motyw', b.dataset.motyw)));

function odswiezDol() {
  $('#dol-projekt').innerHTML = (KONTO.zalogowany ? `Konto: <b>${esc(KONTO.nazwa)}</b>${KONTO.firma ? ` · ${esc(KONTO.firma)}` : ''}<br>` : '')
    + (P._plik ? `Projekt: <b title="${esc(P._plik)}">${esc(nazwaPliku(P._plik))}</b>` : 'Projekt niezapisany');
  $('#dol-baza').innerHTML = `Baza urządzeń: <b>v${esc(BAZA.wersja)}</b>${AKT_BAZY?.nowsza ? ` · <span class="akt-nowa" id="dol-baza-akt">nowa v${esc(AKT_BAZY.wersja)}</span>` : ''}`;
  const w = $('#dol-wersja');
  w.innerHTML = `Program: <b>v${esc(INFO.wersja)}</b> ${AKT?.do_instalacji ? `· <span class="akt-nowa">${AKT.wycofana ? 'zalecana' : 'dostępna'} v${esc(AKT.wersja)}</span>` : AKT?.ok ? '<span class="akt-ok">· aktualny</span>' : ''}`;
  w.onclick = AKT?.do_instalacji ? oknoAktualizacji : null;
  $('#dol-baza-akt')?.addEventListener('click', () => aktualizujBaze(false));
  $('#licznik-baza').classList.toggle('ukryty', !AKT_BAZY?.nowsza);
  $('#licznik-baza').textContent = 'nowa';
  $('#licznik-ustawienia').classList.toggle('ukryty', !AKT?.do_instalacji);
  $('#licznik-ustawienia').textContent = '1';
}

// ------------------------------------------------------------------ aktualizacje programu i bazy
async function sprawdzAktualizacje(recznie) {
  AKT = await api('sprawdz_aktualizacje');
  odswiezDol();
  if (widok === 'ustawienia') rysujUstawienia();
  if (recznie) {
    if (!AKT?.ok) toast(`Nie udało się sprawdzić aktualizacji: ${esc(AKT?.blad || '')}`, 'blad');
    else if (AKT.do_instalacji) oknoAktualizacji();
    else toast(`Masz najnowszą wersję programu (${esc(INFO.wersja)}).`, 'ok');
  } else if (AKT?.do_instalacji) {
    toast(AKT.wycofana ? `Zalecana jest wersja <b>${esc(AKT.wersja)}</b> (w tej wersji wykryto błąd).` : `Dostępna nowa wersja programu: <b>${esc(AKT.wersja)}</b>`, '', { tekst: 'Zobacz', fn: oknoAktualizacji }, 12000);
  }
}

async function oknoAktualizacji() {
  const w = await modal({
    tytul: `${ik('pobierz')} ${AKT.wycofana ? 'Powrót do wersji' : 'Aktualizacja do wersji'} ${esc(AKT.wersja)}`, szeroki: true,
    tresc: `<p>Obecna wersja: <b>${esc(INFO.wersja)}</b>. ${AKT.wycofana ? 'W tej wersji wykryto błąd - zalecana jest poprzednia wersja. Twoje projekty, ustawienia i baza urządzeń zostaną. ' : ''}Program zamknie się na czas instalacji.</p>
      <pre class="changelog">${esc(AKT.opis || 'Brak opisu zmian.')}</pre>`,
    przyciski: [{ tekst: 'Później', wartosc: null }, { tekst: `${ik('pobierz')} Pobierz i zainstaluj`, klasa: 'btn-hr', wartosc: 'tak', domyslny: true }],
  });
  if (w !== 'tak') return;
  if (czyNiezapisane() && !(await pytajOZapis('Zainstalować aktualizację?'))) return;
  modal({ tytul: 'Pobieranie aktualizacji…', tresc: '<div class="pasek-wyniku"><i id="akt-postep" style="width:0%"></i></div><p class="podp" id="akt-tekst" style="margin-top:10px">0%</p>' });
  window.postepAktualizacji = (p) => { const el = $('#akt-postep'); if (el) { el.style.width = `${p}%`; $('#akt-tekst').textContent = `${p}%`; } };
  window.aktualizacjaPobrana = (ok, blad) => {
    if (ok) return api('uruchom_instalator');
    modalOtwarty?.zamknij();
    toast(`Nie udało się pobrać aktualizacji: ${esc(blad)}`, 'blad');
  };
  api('pobierz_aktualizacje', AKT.link);
}

async function sprawdzBaze(recznie) {
  AKT_BAZY = await api('sprawdz_baze');
  odswiezDol();
  if (widok === 'baza') rysujBaze();
  if (recznie) {
    if (!AKT_BAZY?.ok) toast(`Nie udało się sprawdzić bazy: ${esc(AKT_BAZY?.blad || '')}`, 'blad');
    else aktualizujBaze(false);
  } else if (AKT_BAZY?.nowsza) {
    aktualizujBaze(true);  // jak lista pracowników w HR: nowa baza globalna pobierana od razu przy starcie
  }
}

/** Pełna aktualizacja bazy globalnej z serwera - pobrana baza zastępuje poprzednią, wpisy własne zostają. */
async function aktualizujBaze(auto) {
  if (!auto) {
    const wlasne = Object.values(BAZA.zrodla || {}).reduce((n, z) => n + Object.values(z).filter((x) => x !== 'globalna').length, 0);
    const w = await modal({
      tytul: `${ik('baza')} Pobierz bazę urządzeń z serwera`,
      tresc: `<p>Twoja wersja: <b>v${esc(BAZA.wersja)}</b>${AKT_BAZY?.ok ? `, na serwerze: <b>v${esc(AKT_BAZY.wersja)}</b>` : ''}. Baza globalna Diamel zostanie pobrana w całości i zastąpi obecną - także urządzenia usunięte z bazy globalnej znikną z listy.</p>
        <p>${wlasne ? `Twoje wpisy własne i zmienione (${wlasne}) zostaną bez zmian.` : 'Nie masz wpisów własnych.'} Przed zmianą program zrobi kopię obecnej bazy.</p>
        ${AKT_BAZY?.opis ? `<pre class="changelog">${esc(AKT_BAZY.opis)}</pre>` : ''}`,
      przyciski: [{ tekst: 'Anuluj', wartosc: null }, { tekst: `${ik('pobierz')} Pobierz bazę`, klasa: 'btn-hr', wartosc: 'tak', domyslny: true }],
    });
    if (w !== 'tak') return;
  }
  const r = await api('aktualizuj_baze');
  if (!r?.ok) return toast(esc(r?.blad || 'Aktualizacja bazy nie powiodła się.'), 'blad');
  BAZA = r.baza;
  AKT_BAZY = { ...(AKT_BAZY || {}), ok: true, nowsza: false, wersja: r.jest };
  const opis = (rodz, n) => {
    const z = r.zmiany[rodz] || { nowe: [], zmienione: [], usuniete: [] };
    const c = [z.nowe.length && `nowe ${z.nowe.length}`, z.zmienione.length && `zmienione ${z.zmienione.length}`, z.usuniete.length && `usunięte ${z.usuniete.length}`].filter(Boolean);
    return `${n}: ${c.join(', ') || 'bez zmian'}`;
  };
  toast(`Baza urządzeń ${r.bylo === r.jest ? `pobrana ponownie (v${esc(r.jest)})` : `zaktualizowana: v${esc(r.bylo)} → <b>v${esc(r.jest)}</b>`}<br>${opis('starters', 'Rozruszniki')} · ${opis('batteries', 'Akumulatory')}`,
    'ok', { tekst: 'Kopia', fn: () => api('otworz_folder', r.kopia) }, 10000);
  odswiezDol();
  if (widok === 'baza') rysujBaze();
  if (widok === 'obliczenia') rysujObliczenia();
}

// ------------------------------------------------------------------ projekt: nowy, wczytaj, zapisz
const doPorownania = (p) => JSON.stringify({ ...p, _plik: undefined });
const czyNiezapisane = () => P && doPorownania(P) !== ZAPISANY;

function ustawProjekt(projekt) {
  P = projekt;
  ZAPISANY = doPorownania(P);
  api('ustaw_niezapisane', false);
  W = null;
}

function zmiana() {
  const nz = czyNiezapisane();
  api('ustaw_niezapisane', nz);
  rysujPasek();
}

/** Pyta o zapis niezapisanych zmian. true = można kontynuować (zapisano albo porzucono). */
async function pytajOZapis(pytanie = 'Kontynuować?') {
  const w = await modal({
    tytul: `${ik('uwaga')} Niezapisane zmiany`,
    tresc: `<p>Projekt <b>${esc(P.project_no || nazwaPliku(P._plik) || 'bez nazwy')}</b> ma niezapisane zmiany. ${esc(pytanie)}</p>`,
    przyciski: [{ tekst: 'Anuluj', wartosc: null }, { tekst: 'Nie zapisuj', klasa: 'btn-czerwony', wartosc: 'porzuc' },
      { tekst: `${ik('zapisz')} Zapisz`, klasa: 'btn-hr', wartosc: 'zapisz', domyslny: true }],
  });
  if (w === 'porzuc') return true;
  if (w === 'zapisz') return zapiszProjekt(false);
  return false;
}

window.pytajPrzedZamknieciem = async () => {
  if (modalOtwarty) modalOtwarty.zamknij(null);
  if (await pytajOZapis('Zamknąć program?')) api('zamknij');
};

async function nowyProjekt() {
  if (czyNiezapisane() && !(await pytajOZapis('Utworzyć nowy projekt?'))) return;
  ustawProjekt(await api('nowy_projekt'));
  pokaz('obliczenia');
  toast('Nowy projekt.', 'ok', null, 2500);
}

async function otworzProjekt() {
  const ostatnie = (await api('ostatnie')) || [];
  const w = await modal({
    tytul: `${ik('otworz')} Otwórz projekt`,
    tresc: ostatnie.length ? `<p class="podp">Ostatnio otwierane</p><div class="lista-ostatnich">${ostatnie.map((o) => `
        <button data-wybor="${esc(o.sciezka)}"><b>${esc(o.nazwa)}</b><span>${esc(o.data)}</span><span style="grid-column:span 2">${esc(o.folder)}</span></button>`).join('')}</div>`
      : '<p class="podp">Brak ostatnio otwieranych projektów.</p>',
    przyciski: [{ tekst: 'Anuluj', wartosc: null }, { tekst: `${ik('folder')} Wybierz plik…`, klasa: 'btn-hr', wartosc: '', domyslny: true }],
  });
  if (w === null) return;
  if (czyNiezapisane() && !(await pytajOZapis('Otworzyć inny projekt?'))) return;
  const r = await api('wczytaj_projekt', w);
  if (r?.anulowano) return;
  if (!r?.ok) return toast(esc(r?.blad || 'Nie udało się wczytać projektu.'), 'blad');
  ustawProjekt(r.projekt);
  pokaz('obliczenia');
  toast(`Wczytano projekt <b>${esc(nazwaPliku(r.projekt._plik))}</b>`, 'ok', null, 3000);
  if (r.brakujace.length) toast(`Nie znaleziono plików załączników: ${r.brakujace.map(esc).join(', ')} - raport powstanie bez nich.`, 'blad');
}

async function zapiszProjekt(jako) {
  const r = await api('zapisz_projekt', P, jako);
  if (r?.anulowano) return false;
  if (!r?.ok) { toast(esc(r?.blad || 'Nie udało się zapisać projektu.'), 'blad'); return false; }
  P._plik = r.plik;
  ZAPISANY = doPorownania(P);
  api('ustaw_niezapisane', false);
  rysujPasek();
  toast(`Zapisano projekt <b>${esc(nazwaPliku(r.plik))}</b>`, 'ok', { tekst: 'Pokaż w folderze', fn: () => api('otworz_folder', r.plik) }, 4000);
  return true;
}

function rysujPasek() {
  const tytul = $('#pasek-tytul'), nad = $('#pasek-nad'), prawe = $('#pasek-prawe');
  odswiezDol();
  if (widok !== 'obliczenia') {
    nad.textContent = 'Kalkulator Rozruchu';
    tytul.textContent = { baza: 'Baza urządzeń', ustawienia: 'Ustawienia', zglos: 'Zgłoszenia' }[widok];
    prawe.innerHTML = '';
    return;
  }
  const nz = czyNiezapisane();
  nad.innerHTML = `${P._plik ? esc(nazwaPliku(P._plik)) : 'Nowy projekt'}${nz ? '<span class="stan-projektu"><span class="kropka-z"></span>niezapisane zmiany</span>' : P._plik ? '<span class="stan-projektu">zapisany</span>' : ''}`;
  tytul.innerHTML = `<span class="nazwa-projektu">${esc([P.project_no, P.client].filter(Boolean).join(' · ') || 'Obliczenia układu rozruchowego')}</span>`;
  prawe.innerHTML = `
    <button class="btn btn-maly" id="p-nowy" title="Nowy projekt (Ctrl+N)">${ik('nowy')} Nowy</button>
    <button class="btn btn-maly" id="p-otworz" title="Otwórz projekt (Ctrl+O)">${ik('otworz')} Otwórz</button>
    <button class="btn btn-maly" id="p-zapisz-jako" title="Zapisz jako…">Zapisz jako…</button>
    <button class="btn btn-maly ${nz ? 'btn-hr' : ''}" id="p-zapisz" title="Zapisz projekt (Ctrl+S)">${ik('zapisz')} Zapisz</button>`;
  $('#p-nowy').onclick = nowyProjekt;
  $('#p-otworz').onclick = otworzProjekt;
  $('#p-zapisz').onclick = () => zapiszProjekt(false);
  $('#p-zapisz-jako').onclick = () => zapiszProjekt(true);
}

// ------------------------------------------------------------------ ekran obliczeń: dane
function pLiczba(pole, etykieta, jedn = '', { szer2 = false, dodatek = '', podpowiedz = '' } = {}) {
  return `<div class="p-pole ${szer2 ? 'szer2' : ''}"><label class="etykieta" for="f-${pole}"><span>${etykieta}</span>${dodatek}</label>
    <div class="z-jednostka"><input class="pole" id="f-${pole}" data-pole="${pole}" value="${esc(P[pole])}" inputmode="decimal" spellcheck="false" ${podpowiedz ? `placeholder="${esc(podpowiedz)}"` : ''}><span class="jedn">${jedn}</span></div>
    <div class="blad-pola ukryty" data-blad="${pole}"></div></div>`;
}
function pTekst(pole, etykieta, { podpowiedz = '' } = {}) {
  return `<div class="p-pole"><label class="etykieta" for="f-${pole}">${etykieta}</label><input class="pole" id="f-${pole}" data-pole="${pole}" value="${esc(P[pole])}" spellcheck="false" placeholder="${esc(podpowiedz)}"></div>`;
}
function pSegment(pole, opcje, kl = '') {
  return `<div class="segment ${kl}" data-seg="${pole}">${opcje.map(([v, t]) => `<button data-v="${esc(v)}" class="${String(P[pole]) === String(v) ? 'akt' : ''}">${t}</button>`).join('')}</div>`;
}
function pModel(rodzaj, pole, etykieta) {
  const lista = Object.keys(BAZA[rodzaj]).sort((a, b) => a.localeCompare(b, 'pl'));
  const wBazie = lista.includes(P[pole]);
  return `<div class="p-pole"><label class="etykieta" for="f-${pole}"><span>${etykieta}</span>${P[pole] && !wBazie ? '<span class="zbazy" style="color:var(--zolty-tekst)">nie ma w bazie</span>' : ''}</label>
    <select class="pole" id="f-${pole}" data-model="${rodzaj}" data-pole-model="${pole}">
      <option value="">— własne parametry (wpisz poniżej) —</option>
      ${P[pole] && !wBazie ? `<option value="${esc(P[pole])}" selected>${esc(P[pole])}</option>` : ''}
      ${lista.map((n) => `<option value="${esc(n)}" ${n === P[pole] ? 'selected' : ''}>${esc(n)}</option>`).join('')}
    </select></div>`;
}

function rysujObliczenia() {
  const el = $('#widok-obliczenia');
  el.innerHTML = `<div class="dane" id="dane">
    <div class="karta">
      <div class="naglowek-karty"><h3><span class="nr">1</span>Projekt</h3>${pSegment('language', [['English', 'Raport EN'], ['Polski', 'Raport PL']])}</div>
      <div class="pola">
        ${pTekst('project_no', 'Numer projektu', { podpowiedz: 'np. PRJ-2026-002' })}${pTekst('client', 'Klient')}${pTekst('author', 'Przygotował (inicjały)')}
        ${pTekst('genset', 'Model agregatu', { podpowiedz: 'np. C3500D5EB' })}<div class="p-pole"><label class="etykieta" for="f-engine"><span>Model silnika</span>${P.engine && BAZA.engines?.[P.engine] ? '<span class="zbazy">z bazy</span>' : ''}</label>
          <input class="pole" id="f-engine" data-pole="engine" list="lista-silnikow" value="${esc(P.engine)}" spellcheck="false" placeholder="${Object.keys(BAZA.engines || {}).length ? 'wybierz z bazy albo wpisz' : 'np. QSK78-G39'}">
          <datalist id="lista-silnikow">${Object.keys(BAZA.engines || {}).sort((a, b) => a.localeCompare(b, 'pl')).map((n) => `<option value="${esc(n)}">${esc(BAZA.engines[n].genset || '')}</option>`).join('')}</datalist></div>
        <div class="p-pole cca-silnika"><label class="zaznacz" style="margin-bottom:6px"><input type="checkbox" id="f-cca-znane" ${P.cca_znane ? 'checked' : ''}> CCA silnika znane z karty katalogowej</label>
          ${P.cca_znane ? `<div class="z-jednostka"><input class="pole" id="f-cca_silnika" data-pole="cca_silnika" value="${esc(P.cca_silnika)}" inputmode="decimal" placeholder="wymagane CCA, np. 2000"><span class="jedn">A</span></div><div class="blad-pola ukryty" data-blad="cca_silnika"></div>
            <div class="norma-cca"><span class="podp">norma:</span>${pSegment('cca_silnika_norma', [['EN', 'EN'], ['SAE', 'SAE']])}</div>`
            : '<span class="podp">bez wymagania - CCA oceniane tylko informacyjnie</span>'}</div>
      </div>
      <details class="sekcja" id="sekcja-rewizje"><summary>${ik('dalej')} Tabela rewizji dokumentu <span class="podp">(${P.revisions.length})</span></summary><div id="rewizje"></div></details>
    </div>

    <div class="karta">
      <div class="naglowek-karty"><h3><span class="nr">2</span>Rozruszniki</h3>${pSegment('system_v', [['12', '12 VDC'], ['24', '24 VDC']], 'duzy-seg')}</div>
      <div class="wybor-modelu">${pModel('starters', 'starter_model', 'Model rozrusznika')}${pLiczba('starter_qty', 'Ilość w agregacie', 'szt.')}</div>
      <div class="pola p4">
        ${pLiczba('starter_normal', 'Prąd znamionowy', 'A', { podpowiedz: 'opcjonalnie' })}${pLiczba('starter_peak', 'Prąd szczytowy', 'A')}
        ${pLiczba('crank_v', 'Napięcie kręcenia', 'V')}${pLiczba('min_v', 'Napięcie minimalne', 'V', { podpowiedz: 'opcjonalnie' })}
        ${pLiczba('r_test_mohm', 'Rezystancja obwodu wg karty', 'mΩ', { podpowiedz: 'np. 8 (akum. + kable)' })}
      </div>
      ${(() => { const u = BAZA.starters[P.starter_model]; return u && +u.voltage_v && +u.voltage_v !== +P.system_v ? `<div class="uwaga-pola">${ik('uwaga')} Rozrusznik z bazy ma napięcie ${lc(u.voltage_v)} V, a układ ${P.system_v} V - wybierz rozrusznik ${P.system_v} V albo wpisz jego parametry.</div>` : ''; })()}
      <p class="podp" style="margin:10px 0 0">Napięcie kręcenia i minimalne - z krzywej rozrusznika (przy prądzie znamionowym i szczytowym). Rezystancja obwodu wg karty - obwód testowy (akumulator + kable), dla którego producent wyznaczył krzywą; z rezystancją akumulatora program porównuje go z Twoim obwodem.</p>
    </div>

    <div class="karta">
      <div class="naglowek-karty"><h3><span class="nr">3</span>Akumulatory</h3>${pSegment('batt_type', [['Lead-Acid', 'Kwasowo-ołowiowe'], ['AGM', 'AGM'], ['Li-Ion', 'Li-Ion']])}</div>
      <div class="wybor-modelu">${pModel('batteries', 'batt_model', 'Model akumulatora')}${pLiczba('batt_v', 'Napięcie', 'V')}</div>
      <div class="pola p4">
        ${pLiczba('batt_ah', 'Pojemność 1 szt.', 'Ah')}${pLiczba('batt_cca', 'Prąd CCA 1 szt.', 'A')}
        ${pLiczba('batt_series', 'Szeregowo', 'szt.')}${pLiczba('batt_parallel', 'Łańcuchy równoległe', 'szt.')}
        ${pLiczba('batt_rint_mohm', 'Rezystancja wewn. 1 szt.', 'mΩ', { podpowiedz: 'z karty, np. 2,5' })}
        <div class="p-pole"><label class="etykieta">Norma CCA</label>${pSegment('batt_cca_norma', [['EN', 'EN'], ['SAE', 'SAE']])}</div>
      </div>
      ${P.cca_znane && P.batt_cca_norma && P.cca_silnika_norma && P.batt_cca_norma !== P.cca_silnika_norma ? `<div class="uwaga-pola">${ik('uwaga')} CCA akumulatora podano wg ${P.batt_cca_norma}, a wymaganie silnika wg ${P.cca_silnika_norma} - wartości wg różnych norm nie są wprost porównywalne (porównanie orientacyjne). Jeśli karta akumulatora podaje CCA wg ${P.cca_silnika_norma}, wpisz tę wartość.</div>` : ''}
      <div id="bank"></div>
      <div class="redundancja">
        <div class="p-pole"><label class="etykieta">Redundancja rozruchu</label>${pSegment('zestawy', [['1', '1 zestaw'], ['2', '2 zestawy (przełączane)']])}</div>
        ${+P.zestawy > 1 ? pLiczba('zmiana_co', 'Zmiana zestawu co', 'rozr.', { podpowiedz: 'np. 5 (puste = przy awarii)' }) : '<div></div>'}
        <p class="podp">${+P.zestawy > 1 ? 'Drugi taki sam zestaw akumulatorów z własną ładowarką, przełączany przekaźnikami / stycznikami - nigdy łączony z pierwszym. Każdy zestaw jest liczony osobno i sam musi zapewnić pełny profil rozruchu.' : 'Opcjonalnie drugi taki sam zestaw akumulatorów i ładowarki, przełączany co kilka rozruchów albo przy awarii.'}</p>
      </div>
    </div>

    <div class="karta">
      <div class="naglowek-karty"><h3><span class="nr">4</span>Kable i profil rozruchu</h3></div>
      <div class="pola">
        ${pLiczba('cable_l', 'Długość kabli (tam i z powrotem)', 'm')}${pLiczba('cable_a', 'Przekrój żyły', 'mm²')}${pLiczba('cable_cores', 'Żył na biegun', 'szt.')}
        ${pLiczba('time_s', 'Czas jednej próby', 's')}${pLiczba('attempts', 'Ilość prób rozruchu', 'szt.')}${pLiczba('charge_h', 'Czas pełnego naładowania', 'h')}
      </div>
    </div>

    <div class="karta">
      <div class="naglowek-karty"><h3><span class="nr">5</span>Załączniki do raportu</h3><span class="podp">obrazy PNG / JPG - krzywa i karta podpowiadane z bazy</span></div>
      <div class="zalaczniki" id="zalaczniki"></div>
    </div>
  </div>
  <aside class="wyniki"><div class="przewijane" id="wyniki"></div>
    <div class="stopka">
      <div class="przyciski-raportu"><button class="btn btn-hr btn-raport-duzy" id="generuj" title="Raport PDF (Ctrl+G)">${ik('dokument')} Raport PDF</button>
        <button class="btn btn-raport-duzy" id="generuj-docx" title="Raport do edycji w Wordzie (Ctrl+Shift+G)">${ik('word')} DOCX</button></div>
      <div class="podp" id="stopka-raportu"></div>
    </div>
  </aside>`;
  rysujRewizje();
  rysujZalaczniki();
  przelicz();
  $('#generuj').onclick = () => generujRaport('pdf');
  $('#generuj-docx').onclick = () => generujRaport('docx');
}

const widokObl = $('#widok-obliczenia');
widokObl.addEventListener('input', (e) => {
  const pole = e.target.dataset.pole;
  if (pole) {
    P[pole] = e.target.value;
    if (['project_no', 'client'].includes(pole)) rysujPasek();
    zmiana();
    przeliczPozniej();
  }
  const rev = e.target.dataset.rev;
  if (rev !== undefined) { P.revisions[+rev][e.target.dataset.k] = e.target.value; zmiana(); }
});
widokObl.addEventListener('change', (e) => {
  if (e.target.id === 'f-cca-znane') {
    P.cca_znane = e.target.checked ? '1' : '';
    zmiana();
    const przew = $('#dane').scrollTop; rysujObliczenia(); $('#dane').scrollTop = przew;
    if (P.cca_znane) $('#f-cca_silnika')?.focus();
    return;
  }
  if (e.target.dataset.model) wybierzModel(e.target.dataset.model, e.target.value);
  if (e.target.id === 'f-engine' && BAZA.engines?.[e.target.value]) wybierzModel('engines', e.target.value);
});
widokObl.addEventListener('click', (e) => {
  const b = e.target.closest('[data-seg] button');
  if (b) {
    const pole = b.closest('[data-seg]').dataset.seg;
    if (pole === 'system_v') zmienNapiecieUkladu(+b.dataset.v);
    else P[pole] = b.dataset.v;
    zmiana();
    if (['system_v', 'zestawy', 'batt_cca_norma', 'cca_silnika_norma'].includes(pole)) { const przew = $('#dane').scrollTop; rysujObliczenia(); $('#dane').scrollTop = przew; return; }
    $$('button', b.parentElement).forEach((x) => x.classList.toggle('akt', x === b));
    przeliczPozniej(0);
  }
});

const domyslneKrecenie = (u) => Math.round(u * 2 / 3 * 100) / 100;
function zmienNapiecieUkladu(u) {
  const stare = +P.system_v;
  if (+P.crank_v === domyslneKrecenie(stare) || P.crank_v === '') { P.crank_v = String(domyslneKrecenie(u)); ustawPole('crank_v'); }
  P.system_v = String(u);
  dopasujSzeregowo();
}
function dopasujSzeregowo() {
  const n = +P.system_v / +String(P.batt_v).replace(',', '.');
  if (Number.isInteger(n) && n > 0 && String(n) !== String(P.batt_series)) {
    P.batt_series = String(n);
    ustawPole('batt_series');
    toast(`Szeregowo: <b>${n}</b> szt. (${lc(P.batt_v)} V × ${n} = ${P.system_v} V)`, '', null, 2500);
  }
}
function ustawPole(pole) { const el = $(`[data-pole="${pole}"]`); if (el) el.value = P[pole]; }

function zastosujModel(rodzaj, nazwa) {
  const u = BAZA[rodzaj][nazwa];
  P[{ starters: 'starter_model', batteries: 'batt_model', engines: 'engine' }[rodzaj]] = nazwa;
  if (!u) return false;
  const t = (v) => (v === undefined || v === null || v === 0 || v === '' ? '' : String(v));
  if (rodzaj === 'starters') {
    if ([12, 24].includes(+u.voltage_v)) P.system_v = String(u.voltage_v);
    Object.assign(P, { starter_normal: t(u.normal_current_a), starter_peak: t(u.peak_current_a),
      crank_v: t(u.crank_voltage_v) || String(domyslneKrecenie(+P.system_v)), min_v: t(u.min_voltage_v),
      r_test_mohm: +u.test_res_ohm > 0 ? String(Math.round(u.test_res_ohm * 1e5) / 100) : '' });
    if (u.curve_path) P.images.curve = u.curve_path;
    if (u.pliki?.obraz) plikDoZalacznika(u.pliki.obraz.id, 'curve');
  } else if (rodzaj === 'batteries') {
    Object.assign(P, { batt_type: u.type || P.batt_type, batt_v: t(u.voltage_v) || '12', batt_ah: t(u.capacity_ah), batt_cca: t(u.cca_a), batt_cca_norma: u.cca_norma || '',
      batt_rint_mohm: +u.internal_res_ohm > 0 ? String(Math.round(u.internal_res_ohm * 1e5) / 100) : '' });
    if (u.batt_path) P.images.batt = u.batt_path;
    if (u.pliki?.obraz) plikDoZalacznika(u.pliki.obraz.id, 'batt');
    const n = +P.system_v / +P.batt_v;
    if (Number.isInteger(n) && n > 0) P.batt_series = String(n);
  } else {  // silnik: agregat, napięcie układu, liczba i model rozrusznika, wymagane CCA z karty silnika
    if (u.genset && !P.genset) P.genset = u.genset;
    if ([12, 24].includes(+u.voltage_v)) P.system_v = String(u.voltage_v);
    if (+u.starter_qty > 0) P.starter_qty = String(u.starter_qty);
    if (+u.cca_a > 0) Object.assign(P, { cca_znane: '1', cca_silnika: String(u.cca_a), cca_silnika_norma: u.cca_norma || '' });
    if (u.starter_model && BAZA.starters[u.starter_model]) zastosujModel('starters', u.starter_model);
  }
  return true;
}

let ostrzezenieOLogowaniu = false;
/** Krzywa rozrusznika / karta akumulatora z bazy jako załącznik raportu (plik producenta - po zalogowaniu). */
async function plikDoZalacznika(id, klucz) {
  const r = await api('plik_bazy', id);
  if (r?.ok) { P.images[klucz] = r.sciezka; zmiana(); rysujZalaczniki(); return; }
  if (r?.zaloguj && !ostrzezenieOLogowaniu) {
    ostrzezenieOLogowaniu = true;
    toast('Krzywa rozrusznika / karta z bazy trafi do raportu po zalogowaniu kontem Diamel (Ustawienia).', '', { tekst: 'Zaloguj', fn: () => pokaz('ustawienia') }, 9000);
  } else if (r && !r.zaloguj) toast(esc(r.blad || 'Nie udało się pobrać pliku z bazy.'), 'blad');
}

function wybierzModel(rodzaj, nazwa) {
  if (zastosujModel(rodzaj, nazwa)) toast(`Wczytano parametry z bazy: <b>${esc(nazwa)}</b>`, 'ok', null, 2500);
  zmiana();
  const przewiniecie = $('#dane')?.scrollTop || 0;
  rysujObliczenia();
  $('#dane').scrollTop = przewiniecie;
}

// Rewizje
function rysujRewizje() {
  const el = $('#rewizje');
  if (!el) return;
  el.innerHTML = `<table class="rewizje"><thead><tr><th>Rew.</th><th>Opis zmiany</th><th>Wykonał</th><th>Sprawdził</th><th>Data</th><th></th></tr></thead><tbody>
    ${P.revisions.map((r, i) => `<tr>
      <td class="w-rev"><input class="pole" data-rev="${i}" data-k="rev" value="${esc(r.rev)}"></td>
      <td><input class="pole" data-rev="${i}" data-k="desc" value="${esc(r.desc)}"></td>
      <td class="w-kr"><input class="pole" data-rev="${i}" data-k="drawn" value="${esc(r.drawn)}"></td>
      <td class="w-kr"><input class="pole" data-rev="${i}" data-k="check" value="${esc(r.check)}"></td>
      <td class="w-data"><input class="pole" data-rev="${i}" data-k="date" value="${esc(r.date)}"></td>
      <td class="w-x"><button class="btn btn-bez btn-ikona" data-usun-rev="${i}" title="Usuń rewizję">${ik('kosz')}</button></td></tr>`).join('')}
    </tbody></table>
    <button class="btn btn-maly" id="dodaj-rev">${ik('plus')} Dodaj rewizję</button>`;
  $('#dodaj-rev').onclick = () => {
    const nr = P.revisions.length ? String((parseInt(P.revisions.at(-1).rev, 10) || 0) + 1) : '0';
    const d = new Date(), mies = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'][d.getMonth()];
    P.revisions.push({ rev: nr, desc: '', drawn: P.author, check: '', date: `${String(d.getDate()).padStart(2, '0')}${mies}${String(d.getFullYear()).slice(2)}` });
    zmiana(); rysujRewizje(); odswiezLicznikRewizji();
    $$('#rewizje [data-k="desc"]').at(-1)?.focus();
  };
  $$('[data-usun-rev]', el).forEach((b) => b.onclick = () => { P.revisions.splice(+b.dataset.usunRev, 1); zmiana(); rysujRewizje(); odswiezLicznikRewizji(); });
}
function odswiezLicznikRewizji() { const s = $('#sekcja-rewizje summary .podp'); if (s) s.textContent = `(${P.revisions.length})`; }

// Załączniki
const ZALACZNIKI = [['curve', 'Krzywa rozrusznika'], ['batt', 'Karta akumulatora'], ['diagram', 'Schemat połączeń'], ['charger', 'Karta ładowarki']];
function rysujZalaczniki() {
  const el = $('#zalaczniki');
  if (!el) return;
  el.innerHTML = ZALACZNIKI.map(([k, t]) => {
    const p = P.images[k];
    const pod = p ? MINIATURY[p] : undefined;  // data URI, '' = nie ma pliku, 'duzy' = bez podglądu, null = wczytywanie
    const obraz = typeof pod === 'string' && pod.startsWith('data:');
    return `<div class="zal ${p ? 'jest' : ''}">
      <div class="miniatura" data-zal-wybierz="${k}" style="${obraz ? `background-image:url('${pod}')` : ''}">${obraz ? '' : ik('obraz')}</div>
      <b>${t}</b><div class="nazwa-pliku ${p && pod === '' ? 'brak' : ''}" title="${esc(p)}">${p ? (pod === '' ? 'nie znaleziono: ' : '') + esc(nazwaPliku(p)) : 'brak - pominięty w raporcie'}</div>
      <div class="akcje"><button class="btn btn-maly" data-zal-wybierz="${k}">${p ? 'Zmień' : 'Wybierz…'}</button>${p ? `<button class="btn btn-maly btn-ikona" data-zal-usun="${k}" title="Usuń">${ik('x')}</button>` : ''}</div></div>`;
  }).join('');
  $$('[data-zal-wybierz]', el).forEach((b) => b.onclick = async () => {
    const s = await api('wybierz_obraz');
    if (s) { P.images[b.dataset.zalWybierz] = s; zmiana(); rysujZalaczniki(); }
  });
  $$('[data-zal-usun]', el).forEach((b) => b.onclick = () => { P.images[b.dataset.zalUsun] = ''; zmiana(); rysujZalaczniki(); });
  for (const [k] of ZALACZNIKI) {
    const p = P.images[k];
    if (p && MINIATURY[p] === undefined) {
      api('obraz', p).then((r) => { MINIATURY[p] = r?.ok ? r.podglad || 'duzy' : ''; rysujZalaczniki(); });
      MINIATURY[p] = null;
    }
  }
}

// Schemat zestawu akumulatorów
function rysujBank() {
  const el = $('#bank');
  if (!el) return;
  const s = parseInt(P.batt_series, 10) || 0, p = parseInt(P.batt_parallel, 10) || 0;
  if (!s || !p) { el.innerHTML = ''; return; }
  const ws = Math.min(s, 6), wp = Math.min(p, 6);
  const lancuch = `<div class="lancuch">${'<div class="ogniwo"></div>'.repeat(ws)}${s > ws ? `<span class="wiecej">+${s - ws}</span>` : ''}</div>`;
  const zgodne = W?.ok ? W.napiecie_zgodne : true;
  el.innerHTML = `<div class="bank"><div class="schemat">${lancuch.repeat(wp)}${p > wp ? `<span class="wiecej">+${p - wp} łańcuchy</span>` : ''}</div>
    <div class="opis-banku"><b>${s * p} szt. · ${s} szeregowo × ${p} równolegle</b><span>szeregowo sumuje się napięcie, równolegle - prąd i pojemność</span>
      ${W?.ok ? `<div class="liczby"><div>Napięcie <b>${lc(W.napiecie_banku)} V</b></div><div>Pojemność <b>${lc(W.total_ah_available)} Ah</b></div><div>CCA <b>${lc(W.total_cca_available)} A</b></div></div>` : ''}</div></div>
    ${!zgodne ? `<div class="uwaga-pola">${ik('uwaga')} Napięcie zestawu (${lc(W.napiecie_banku)} V) nie zgadza się z napięciem układu (${P.system_v} V) - sprawdź ilość szeregowo.</div>` : ''}`;
}

// ------------------------------------------------------------------ obliczenia i wyniki
function przeliczPozniej(ms = 140) {
  clearTimeout(przeliczTimer);
  przeliczTimer = setTimeout(przelicz, ms);
}

async function przelicz() {
  W = await api('oblicz', P);
  if (!W) return;
  $$('#dane .pole.zle').forEach((x) => x.classList.remove('zle'));
  $$('#dane [data-blad]').forEach((x) => x.classList.add('ukryty'));
  if (!W.ok) for (const [pole, tekst] of Object.entries(W.bledy)) {
    if (String(P[pole] ?? '').trim() === '') continue;  // puste pole - tylko na liście braków w wynikach
    $(`[data-pole="${pole}"]`)?.classList.add('zle');
    const b = $(`[data-blad="${pole}"]`);
    if (b) { b.textContent = tekst.split(': ').pop(); b.classList.remove('ukryty'); }
  }
  rysujWyniki();
  rysujBank();
}

function status(ok, tekstOk, tekstZle, info = false) {
  if (ok === null || ok === undefined) return '<span class="status szary">brak danych</span>';
  return ok ? `<span class="status ok">${ik('ok')}${tekstOk}</span>` : `<span class="status ${info ? 'info' : 'zle'}">${ik(info ? 'info' : 'uwaga')}${tekstZle}</span>`;
}

function rysujWyniki() {
  const el = $('#wyniki');
  if (!el) return;
  const stopka = $('#stopka-raportu');
  if (!W?.ok) {
    const bledy = Object.entries(W?.bledy || {});
    el.innerHTML = `<div class="werdykt brak"><div class="ikona-w">${ik('info')}</div><div><b>Uzupełnij dane</b><span>Wyniki pojawią się od razu po wpisaniu brakujących wartości.</span></div></div>
      <div class="bledy-danych">Brakuje albo niepoprawne:<ul>${bledy.map(([, t]) => `<li>${esc(t)}</li>`).join('')}</ul></div>`;
    $('#generuj').disabled = $('#generuj-docx').disabled = true;
    stopka.textContent = 'Raport można wygenerować po uzupełnieniu danych.';
    return;
  }
  $('#generuj').disabled = $('#generuj-docx').disabled = false;
  stopka.textContent = `Raport ${P.language === 'Polski' ? 'po polsku' : 'po angielsku'} · załączniki: ${ZALACZNIKI.filter(([k]) => P.images[k]).length} · ${opisSzablonu()}`;
  const problemy = [W.napiecie_ok === false && 'napięcie na rozruszniku', !W.pojemnosc_ok && 'pojemność akumulatorów', !W.napiecie_zgodne && 'napięcie zestawu akumulatorów',
    W.cca_stan === 'zle' && 'CCA poniżej wymagania silnika'].filter(Boolean);
  el.innerHTML = `
    <div class="werdykt ${problemy.length ? 'zle' : 'ok'}"><div class="ikona-w">${ik(problemy.length ? 'uwaga' : 'ok')}</div>
      <div><b>${problemy.length ? 'Układ wymaga poprawy' : 'Układ rozruchowy spełnia wymagania'}</b><span>${problemy.length ? `Sprawdź: ${problemy.join(', ')}` : `${W.starter_qty} × ${esc(P.starter_model || 'rozrusznik')} · ${W.batt_series * W.batt_parallel} akumulatorów ${lc(W.batt_ah)} Ah`}</span></div></div>

    <div class="wynik">
      <div class="gora-wyniku"><div><div class="tytul-wyniku">${ik('piorun')}Napięcie na rozruszniku</div>
        <div class="wartosc">${lp(W.sustained_voltage)}<small>V</small></div></div>
        ${status(W.napiecie_ok, `min. ${lp(W.min_v, 1)} V`, `poniżej min. ${lp(W.min_v, 1)} V`)}</div>
      <div class="szczegol">${W.metoda === 'karta'
        ? `przy prądzie szczytowym w Twoim obwodzie <b>${lp(W.r_obw * 1000)} mΩ</b> (karta: ${lp(W.r_test * 1000)} mΩ)${W.sustained_normal !== null ? ` · przy znamionowym: <b>${lp(W.sustained_normal)} V</b>` : ''}`
        : `metoda uproszczona: ${lp(W.crank_v)} V − spadek na kablu <b>${lp(W.v_drop)} V</b>${W.sustained_normal !== null ? ` · przy znamionowym: <b>${lp(W.sustained_normal)} V</b>` : ''}<br><span style="color:var(--zolty-tekst)">Wpisz rezystancję obwodu z karty i rezystancję akumulatora, aby porównać obwody (wynik dokładniejszy).</span>`}</div>
      ${wykres()}
    </div>

    <div class="wynik">
      <div class="gora-wyniku"><div><div class="tytul-wyniku">${ik('bateria')}Zużycie pojemności</div>
        <div class="wartosc">${lp(W.consumed_ah)}<small>Ah z ${lc(W.total_ah_available)} Ah</small></div></div>
        ${status(W.pojemnosc_ok, `${lp(W.zuzycie_proc, 0)}%`, 'brak pojemności')}</div>
      <div class="pasek-wyniku ${W.pojemnosc_ok ? '' : 'zle'}"><i style="width:${Math.min(100, W.zuzycie_proc)}%"></i></div>
      <div class="szczegol">${W.attempts} prób × ${lc(W.time_s)} s przy <b>${lc(W.prad_rozruchu)} A</b> (${W.starter_qty} × ${lc(W.starter_peak)} A) · zapas <b>${lp(W.krotnosc, 1)}×</b></div>
    </div>

    <div class="male-wyniki">
      <div class="wynik"><div class="tytul-wyniku">${ik('wtyczka')}Ładowarka</div>
        <div class="wartosc">${W.ladowarka_do ? `${W.ladowarka_od}–${W.ladowarka_do}` : `<small style="margin:0 4px 0 0">około</small>${W.ladowarka_od}`}<small>A</small></div>
        <div class="szczegol">wyliczone <b>${lp(W.charger_amps)} A</b>, w górę do pełnych 5 A · ładowanie ${lc(W.charge_h)} h, współczynnik ${lc(W.inefficiency)}</div></div>
      ${W.cca_znane ? `<div class="wynik"><div class="gora-wyniku"><div class="tytul-wyniku">${ik('piorun')}CCA</div>${W.cca_stan === 'tolerancja' ? `<span class="status info">${ik('info')}w tolerancji (−${lp(W.cca_niedobor_proc, 1)}%)</span>` : status(W.cca_ok, `min. ${lc(W.cca_silnika)} A`, `brakuje ${lc(W.cca_silnika - W.total_cca_available)} A`)}</div>
        <div class="wartosc">${lc(W.total_cca_available)}<small>A</small></div>
        <div class="szczegol">wymagane wg producenta silnika <b>${lc(W.cca_silnika)} A</b>${W.cca_silnika_norma ? ` (${W.cca_silnika_norma})` : ''}${W.cca_normy_rozne ? `, akumulatory wg ${W.batt_cca_norma} - <b>porównanie orientacyjne</b>` : ''}${W.cca_stan === 'tolerancja' ? ` - brakuje ${lc(W.cca_silnika - W.total_cca_available)} A, w tolerancji ${lc(W.cca_tolerancja)}%` : ''} · szczyt rozruszników ${lc(W.cca_wymagane)} A (informacyjnie)</div></div>`
      : `<div class="wynik"><div class="gora-wyniku"><div class="tytul-wyniku">${ik('piorun')}CCA</div>${status(W.cca_ok, 'pokryte', 'informacyjnie', true)}</div>
        <div class="wartosc">${lc(W.total_cca_available)}<small>A</small></div>
        <div class="szczegol">szczyt wszystkich rozruszników <b>${lc(W.cca_wymagane)} A</b> - prąd chwilowy, nie dyskwalifikuje. Znasz CCA z karty silnika? Zaznacz w karcie Projekt.</div></div>`}
    </div>

    ${W.zestawy > 1 ? `<div class="wynik"><div class="tytul-wyniku">${ik('odswiez')}Redundancja · ${W.zestawy} zestawy</div>
      <div class="szczegol" style="margin-top:6px">Wyniki powyżej dotyczą <b>jednego zestawu</b> - zestawy są przełączane${W.zmiana_co ? ` co <b>${W.zmiana_co}</b> rozruchów` : ' przy awarii'}, nigdy łączone.<br>
      Do zamówienia: <b>${W.akumulatory_razem} akumulatorów</b> (${W.zestawy} × ${W.akumulatory_zestaw}) i <b>${W.zestawy} ładowarki</b> po ${W.ladowarka_do ? `${W.ladowarka_od}–${W.ladowarka_do}` : `około ${W.ladowarka_od}`} A</div></div>` : ''}

    <div class="wynik"><div class="tytul-wyniku">${ik('kabel')}Okablowanie</div>
      <div class="szczegol" style="margin-top:6px">Rezystancja kabli <b>${lp(W.res * 1000, 3)} mΩ</b> (${W.cable_cores} × ${lc(W.cable_a)} mm², ${lc(W.cable_l)} m)<br>
      ${W.metoda === 'karta' ? `Zestaw akumulatorów <b>${lp(W.r_zestawu * 1000, 3)} mΩ</b> (${W.batt_series} × ${lc(W.batt_rint_mohm)} / ${W.batt_parallel})${W.starter_qty > 1 ? ` × ${W.starter_qty} rozruszniki` : ''} → obwód <b>${lp(W.r_obw * 1000, 3)} mΩ</b> ${W.r_obw <= W.r_test ? '≤' : '>'} ${lp(W.r_test * 1000, 2)} mΩ z karty<br>` : ''}
      Spadek: <b>${lp(W.v_drop)} V</b> przy ${lc(W.starter_peak)} A${W.starter_normal ? ` · <b>${lp(W.v_drop_normal)} V</b> przy ${lc(W.starter_normal)} A` : ''}
      ${W.prad_graniczny ? `<br>Napięcie minimalne zostanie osiągnięte przy <b>${lc(Math.round(W.prad_graniczny))} A</b>` : W.prad_graniczny === 0 ? '<br><b style="color:var(--czerwony-tekst)">Napięcie kręcenia jest niższe niż minimalne rozrusznika.</b>' : ''}</div></div>`;
}

/** Napięcie na rozruszniku w funkcji prądu: U(I) = U kręcenia − I·R (spadek liczony płynnie, nie tylko w dwóch punktach). */
function wykres() {
  const k = W.krzywa, szer = 330, wys = 150, l = 34, pr = 8, g = 10, d = 24;
  const iMax = k.at(-1).i || 1;
  const kk = W.krzywa_karty;
  const uMin = Math.min(W.min_v || Infinity, k.at(-1).u, kk ? kk.at(-1).u : Infinity), uMaks = W.u0;
  const dol = Math.max(0, Math.floor(uMin - 1)), gora = Math.ceil(Math.max(uMaks, W.min_v || 0) + 0.5);
  const x = (i) => l + (i / iMax) * (szer - l - pr), y = (u) => g + (1 - (u - dol) / (gora - dol || 1)) * (wys - g - d);
  const sciezka = k.map((p, i) => `${i ? 'L' : 'M'}${x(p.i).toFixed(1)},${y(p.u).toFixed(1)}`).join('');
  const krokU = gora - dol > 8 ? 4 : 2;
  const siatkaU = []; for (let u = Math.ceil(dol / krokU) * krokU; u <= gora; u += krokU) siatkaU.push(u);
  const krokI = iMax > 2500 ? 1000 : 500;
  const siatkaI = []; for (let i = 0; i <= iMax; i += krokI) siatkaI.push(i);
  const punkt = (i, kl, r = 4.5) => `<circle class="${kl}" cx="${x(i).toFixed(1)}" cy="${y(W.u0 - i * W.r_obw).toFixed(1)}" r="${r}"/>`;
  const sciezkaKarty = kk ? kk.map((p, i) => `${i ? 'L' : 'M'}${x(p.i).toFixed(1)},${y(p.u).toFixed(1)}`).join('') : '';
  return `<div class="wykres"><svg viewBox="0 0 ${szer} ${wys}" role="img" aria-label="Napięcie na rozruszniku w funkcji prądu">
    <defs><linearGradient id="gradU" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--kolor)" stop-opacity="0.28"/><stop offset="1" stop-color="var(--kolor)" stop-opacity="0"/></linearGradient></defs>
    ${siatkaU.map((u) => `<line class="siatka-w" x1="${l}" x2="${szer - pr}" y1="${y(u)}" y2="${y(u)}"/><text class="opis-w" x="${l - 6}" y="${y(u) + 3}" text-anchor="end">${u} V</text>`).join('')}
    ${siatkaI.map((i) => `<text class="opis-w" x="${x(i)}" y="${wys - 8}" text-anchor="middle">${i ? `${i / 1000} kA` : '0'}</text>`).join('')}
    <line class="os-w" x1="${l}" x2="${szer - pr}" y1="${wys - d}" y2="${wys - d}"/>
    <path class="pod-linia" d="${sciezka}L${x(iMax)},${wys - d}L${x(0)},${wys - d}Z"/>
    ${kk ? `<path class="linia-karty" d="${sciezkaKarty}"/>` : ''}
    <path class="linia-u" d="${sciezka}"/>
    ${W.min_v ? `<line class="linia-min" x1="${l}" x2="${szer - pr}" y1="${y(W.min_v)}" y2="${y(W.min_v)}"/><text class="opis-min" x="${szer - pr}" y="${y(W.min_v) - 4}" text-anchor="end">min. ${lp(W.min_v, 1)} V</text>` : ''}
    ${W.prad_graniczny && W.prad_graniczny <= iMax ? punkt(W.prad_graniczny, 'pkt-gran', 3.5) : ''}
    ${W.starter_normal ? punkt(W.starter_normal, 'pkt-norm') : ''}
    ${punkt(W.starter_peak, 'pkt-peak', 5)}
  </svg>
  <div class="legenda">${W.starter_normal ? `<span><i style="background:var(--niebieski)"></i>znamionowy ${lc(W.starter_normal)} A</span>` : ''}<span><i style="background:var(--kolor)"></i>szczytowy ${lc(W.starter_peak)} A</span>${kk ? '<span><i style="background:var(--muted)"></i>krzywa karty (obwód testowy)</span>' : ''}${W.prad_graniczny && W.prad_graniczny <= iMax ? `<span><i style="background:var(--czerwony)"></i>granica ${lc(Math.round(W.prad_graniczny))} A</span>` : ''}</div></div>`;
}

async function generujRaport(format = 'pdf') {
  if (!W?.ok) return toast('Uzupełnij dane przed wygenerowaniem raportu.', 'blad');
  const b = $(format === 'pdf' ? '#generuj' : '#generuj-docx'), tekst = b.innerHTML;
  b.disabled = true;
  if (format === 'pdf') b.innerHTML = 'Tworzenie PDF…';
  const r = await api('generuj_raport', P, format);
  b.disabled = false;
  b.innerHTML = tekst;
  if (r?.anulowano) return;
  if (!r?.ok) return toast(esc(r?.blad || 'Nie udało się utworzyć raportu.'), 'blad');
  toast(`Zapisano raport <b>${esc(nazwaPliku(r.plik))}</b>${r.pominiete.length ? '<br><span class="podp">Pominięto brakujące załączniki.</span>' : ''}`, 'ok',
    [{ tekst: 'Otwórz', fn: () => api('otworz_plik', r.plik) }, { tekst: 'Folder', fn: () => api('otworz_folder', r.plik) }], 8000);
}

// ------------------------------------------------------------------ baza urządzeń
const RODZAJE = { starters: 'Rozruszniki', batteries: 'Akumulatory', engines: 'Silniki' };
const NAZWA_POJ = { starters: 'rozrusznik', batteries: 'akumulator', engines: 'silnik' };
function opisUrzadzenia(rodzaj, u) {
  const pliki = u.pliki ? ` · ${Object.keys(u.pliki).length === 2 ? 'krzywa + karta' : u.pliki.obraz ? 'obraz' : 'karta'}` : '';
  if (rodzaj === 'engines') return `${esc(u.genset || '')}${u.genset ? ' · ' : ''}${lc(u.voltage_v)} V · ${lc(u.starter_qty)} × rozrusznik${+u.cca_a ? ` · CCA ${lc(u.cca_a)} A` : ''}${pliki}`;
  return (rodzaj === 'starters' ? `${lc(u.voltage_v)} V · ${lc(u.peak_current_a)} A szczyt · kręcenie ${lc(u.crank_voltage_v)} V`
    : `${esc(u.type || '')} · ${lc(u.capacity_ah)} Ah · ${lc(u.cca_a)} CCA`) + pliki;
}

function rysujBaze() {
  const el = $('#widok-baza');
  el.className = 'widok baza-widok';
  const lista = Object.entries(BAZA[baza.rodzaj]).filter(([n]) => n.toLowerCase().includes(baza.szukaj.toLowerCase())).sort(([a], [b]) => a.localeCompare(b, 'pl'));
  el.innerHTML = `<div class="karta lista-urzadzen">
      <div class="gora-listy">
        <div class="segment pelny" id="b-rodzaj">${Object.entries(RODZAJE).map(([k, t]) => `<button data-v="${k}" class="${baza.rodzaj === k ? 'akt' : ''}">${t} <span class="podp">${Object.keys(BAZA[k]).length}</span></button>`).join('')}</div>
        <div class="z-jednostka"><input class="pole" id="b-szukaj" placeholder="Szukaj modelu…" value="${esc(baza.szukaj)}" style="font-family:var(--font-body)"><span class="jedn">${ik('szukaj')}</span></div>
        <button class="btn btn-maly" id="b-nowe">${ik('plus')} Nowe urządzenie</button>
      </div>
      <div class="przewijana-lista">${lista.map(([n, u]) => { const z = BAZA.zrodla?.[baza.rodzaj]?.[n] || 'globalna'; return `<button class="urz ${baza.wybrany === n ? 'akt' : ''} ${z !== 'globalna' ? 'lokalna' : ''}" data-urz="${esc(n)}" title="${z === 'wlasna' ? 'Wpis własny - nie ma go w bazie globalnej' : z === 'zmieniona' ? 'Zmieniona przez Ciebie wersja urządzenia z bazy globalnej' : 'Z bazy globalnej Diamel'}"><b>${esc(n)}</b><span>${z === 'wlasna' ? '<em>własny</em> · ' : z === 'zmieniona' ? '<em>zmieniony</em> · ' : ''}${opisUrzadzenia(baza.rodzaj, u)}</span></button>`; }).join('') || '<p class="podp" style="padding:12px">Brak urządzeń.</p>'}</div>
    </div>
    <div class="edytor" id="edytor"></div>`;
  $$('#b-rodzaj button').forEach((b) => b.onclick = () => { baza.rodzaj = b.dataset.v; baza.wybrany = null; rysujBaze(); });
  $('#b-szukaj').oninput = (e) => { baza.szukaj = e.target.value; const poz = e.target.selectionStart; rysujBaze(); const s = $('#b-szukaj'); s.focus(); s.setSelectionRange(poz, poz); };
  $('#b-nowe').onclick = () => { baza.wybrany = ''; rysujBaze(); $('#e-nazwa')?.focus(); };
  $$('[data-urz]').forEach((b) => b.onclick = () => { baza.wybrany = b.dataset.urz; rysujBaze(); });
  rysujEdytor();
}

function rysujEdytor() {
  const el = $('#edytor');
  const nowy = baza.wybrany === '';
  if (baza.wybrany === null) {
    el.innerHTML = `<div class="karta"><h3>${ik('baza')} Baza urządzeń <span class="podp" style="font-weight:400">v${esc(BAZA.wersja)}</span></h3>
      <p class="opis">Twoja lokalna baza - wpisy z bazy globalnej Diamel i Twoje własne. Wybierz urządzenie z listy albo dodaj nowe.</p>
      <p class="opis">Baza globalna jest pobierana w całości z serwera przy starcie programu (jak lista pracowników w Korektorze HR). Wpisy oznaczone <b style="color:var(--zolty)">●</b> są Twoje - aktualizacja ich nie zmienia.</p>
      <div class="wiersz"><span class="et">Baza globalna Diamel v${esc(BAZA.wersja)}${AKT_BAZY?.ok ? (AKT_BAZY.nowsza ? ` - <b style="color:var(--zolty-tekst)">na serwerze v${esc(AKT_BAZY.wersja)}</b>` : ' - aktualna') : ''}</span>
        <button class="btn btn-maly ${AKT_BAZY?.nowsza ? 'btn-hr' : ''}" id="b-akt">${ik('pobierz')} Pobierz z serwera</button></div>
      <div class="wiersz"><span class="et">Brakuje urządzenia w bazie globalnej?<small>Wyślij prośbę - po dodaniu trafi do wszystkich użytkowników.</small></span><button class="btn btn-maly" id="b-zglos">${ik('wyslij')} Zgłoś sprzęt</button></div>
      <div class="wiersz"><span class="et">Pliki bazy (kopie przed aktualizacją są obok)</span><button class="btn btn-maly" id="b-folder">${ik('folder')} Otwórz folder</button></div></div>`;
    $('#b-akt').onclick = () => sprawdzBaze(true);
    $('#b-zglos').onclick = () => { zglos.rodzaj = 'sprzet'; zglos.kategoria = baza.rodzaj === 'starters' ? 'Rozrusznik' : 'Akumulator'; pokaz('zglos'); };
    $('#b-folder').onclick = () => api('folder_bazy');
    return;
  }
  const u = nowy ? {} : BAZA[baza.rodzaj][baza.wybrany] || {};
  const zrodlo = nowy ? 'wlasna' : BAZA.zrodla?.[baza.rodzaj]?.[baza.wybrany] || 'globalna';
  const pola = INFO.pola_urzadzen[baza.rodzaj];
  const wartosc = (k) => (u[k] === undefined || u[k] === null ? '' : u[k]);
  el.innerHTML = `<div class="karta">
    <div class="naglowek-karty"><h3>${ik(baza.rodzaj === 'batteries' ? 'bateria' : 'silnik')} ${nowy ? `Nowy ${NAZWA_POJ[baza.rodzaj]}` : esc(baza.wybrany)}</h3>
      <span class="wartosci">${Object.entries(u.pliki || {}).map(([rola, p]) => `<button class="btn btn-maly" data-plik-bazy="${esc(p.id)}" title="${esc(p.nazwa)}">${ik(rola === 'obraz' ? 'obraz' : 'dokument')} ${rola === 'obraz' ? 'Krzywa / obraz' : 'Karta katalogowa'}</button>`).join('')}
      ${!nowy ? `<button class="btn btn-maly" id="e-uzyj">${ik('dalej')} Użyj w obliczeniach</button>` : ''}</span></div>
    <div class="pola p2">
      <div class="p-pole szer2"><div class="podp" style="margin-bottom:8px">${zrodlo === 'globalna' ? 'Urządzenie z bazy globalnej Diamel. Zapisanie zmian utworzy Twoją wersję (●) - baza globalna zostaje bez zmian.' : zrodlo === 'zmieniona' ? '● Twoja wersja urządzenia z bazy globalnej - ma pierwszeństwo przed wersją z bazy.' : '● Wpis własny - nie ma go w bazie globalnej. Możesz go zgłosić do dodania (Zgłoszenia).'}</div>
        <label class="etykieta" for="e-nazwa">Nazwa modelu</label><input class="pole" id="e-nazwa" value="${esc(nowy ? '' : baza.wybrany)}"></div>
      ${pola.map(([k, opis, jedn, liczbowe]) => (k === 'type'
        ? `<div class="p-pole"><label class="etykieta">${opis}</label><select class="pole" data-e="${k}">${['Lead-Acid', 'AGM', 'Li-Ion'].map((t) => `<option ${wartosc(k) === t ? 'selected' : ''}>${t}</option>`).join('')}</select></div>`
        : k === 'cca_norma' ? `<div class="p-pole"><label class="etykieta">${opis}</label><select class="pole" data-e="${k}">${[['', '— nie podano'], ['EN', 'EN 50342-1'], ['SAE', 'SAE J537']].map(([v, t]) => `<option value="${v}" ${wartosc(k) === v ? 'selected' : ''}>${t}</option>`).join('')}</select></div>`
        : liczbowe ? `<div class="p-pole"><label class="etykieta">${opis}</label><div class="z-jednostka"><input class="pole" data-e="${k}" value="${esc(wartosc(k) === 0 ? '' : wartosc(k))}" inputmode="decimal"><span class="jedn">${jedn}</span></div></div>`
          : k.endsWith('_path') ? `<div class="p-pole szer2"><label class="etykieta">${opis}</label><div style="display:flex;gap:8px"><input class="pole" data-e="${k}" value="${esc(wartosc(k))}" style="flex:1"><button class="btn btn-maly" data-e-wybierz="${k}">Wybierz…</button></div></div>`
            : `<div class="p-pole"><label class="etykieta">${opis}</label><input class="pole" data-e="${k}" value="${esc(wartosc(k))}"></div>`)).join('')}
    </div>
    <div class="przyciski-edytora">
      <button class="btn btn-hr" id="e-zapisz">${ik('zapisz')} Zapisz w bazie</button>
      ${zrodlo === 'wlasna' && !nowy ? `<button class="btn btn-czerwony" id="e-usun">${ik('kosz')} Usuń</button>` : zrodlo === 'zmieniona' ? `<button class="btn" id="e-usun">${ik('odswiez')} Przywróć z bazy globalnej</button>` : ''}
      <button class="btn btn-bez" id="e-anuluj">Anuluj</button>
    </div></div>`;
  $$('[data-e-wybierz]', el).forEach((b) => b.onclick = async () => { const s = await api('wybierz_obraz'); if (s) $(`[data-e="${b.dataset.eWybierz}"]`).value = s; });
  $('#e-anuluj').onclick = () => { baza.wybrany = null; rysujBaze(); };
  $('#e-zapisz').onclick = async () => {
    const dane = Object.fromEntries($$('[data-e]', el).map((x) => [x.dataset.e, x.value]));
    const nazwa = $('#e-nazwa').value.trim();
    const r = await api('zapisz_urzadzenie', baza.rodzaj, nowy ? '' : baza.wybrany, nazwa, dane);
    if (!r?.ok) return toast(esc(r?.blad || 'Nie udało się zapisać.'), 'blad');
    BAZA = r.baza; baza.wybrany = nazwa; rysujBaze();
    toast(`Zapisano w bazie: <b>${esc(nazwa)}</b>`, 'ok', null, 2500);
  };
  $('#e-usun')?.addEventListener('click', async () => {
    const przywroc = zrodlo === 'zmieniona';
    const w = await modal({ tytul: `${ik(przywroc ? 'odswiez' : 'kosz')} ${przywroc ? 'Przywrócić wersję z bazy globalnej?' : 'Usunąć z bazy?'}`,
      tresc: `<p><b>${esc(baza.wybrany)}</b> - ${przywroc ? 'Twoje zmiany zostaną usunięte, urządzenie wróci do parametrów z bazy globalnej.' : 'wpis własny zostanie usunięty.'} Zapisane projekty zachowują swoje wartości.</p>`,
      przyciski: [{ tekst: 'Anuluj', wartosc: null }, { tekst: przywroc ? 'Przywróć' : 'Usuń', klasa: przywroc ? 'btn-hr' : 'btn-czerwony', wartosc: 'tak' }] });
    if (w !== 'tak') return;
    const r = await api('usun_urzadzenie', baza.rodzaj, baza.wybrany);
    BAZA = r.baza; if (!przywroc) baza.wybrany = null; rysujBaze();
  });
  $('#e-uzyj')?.addEventListener('click', () => { const n = baza.wybrany; pokaz('obliczenia'); wybierzModel(baza.rodzaj, n); });
  $$('[data-plik-bazy]', el).forEach((b) => b.onclick = async () => {
    b.disabled = true;
    const r = await api('otworz_plik_bazy', b.dataset.plikBazy);
    b.disabled = false;
    if (!r?.ok) toast(esc(r?.blad || 'Nie udało się otworzyć pliku.'), r?.zaloguj ? '' : 'blad', r?.zaloguj ? { tekst: 'Zaloguj', fn: () => pokaz('ustawienia') } : null, 7000);
  });
}

// ------------------------------------------------------------------ ustawienia
function przelacznik(id, wl) { return `<button class="przelacznik ${wl ? 'wl' : ''}" id="${id}" role="switch" aria-checked="${wl}"></button>`; }

function rysujUstawienia() {
  const el = $('#widok-ustawienia');
  const pr = INFO.program;
  el.innerHTML = `<div class="siatka k2" style="align-items:start">
    <div class="siatka">
      <div class="karta"><h3>${ik('nowy')} Nowy projekt</h3><p class="opis">Wartości wpisywane w nowym projekcie.</p>
        <div class="wiersz"><span class="et">Przygotował (inicjały)</span><input class="pole waski" id="u-autor" value="${esc(pr.autor)}"></div>
        <div class="wiersz"><span class="et">Język raportu</span><div class="segment" id="u-jezyk">${[['English', 'Angielski'], ['Polski', 'Polski']].map(([v, t]) => `<button data-v="${v}" class="${pr.jezyk === v ? 'akt' : ''}">${t}</button>`).join('')}</div></div>
      </div>
      <div class="karta"><h3>${ik('word')} Raport</h3>
        <div class="wiersz"><span class="et">Otwórz raport po zapisaniu</span>${przelacznik('u-otworz', pr.otworz_raport)}</div>
        <div class="wiersz"><span class="et">Tolerancja CCA względem karty silnika<small>niedobór do tej wartości nie dyskwalifikuje akumulatorów (np. 10% = 200 A przy 2000 A)</small></span>
          <div class="z-jednostka" style="width:110px"><input class="pole" id="u-cca-tol" value="${esc(pr.cca_tolerancja)}" inputmode="decimal"><span class="jedn">%</span></div></div>
        <div class="wiersz"><span class="et">${KONTO.szablon ? 'Własny szablon (zastępuje papier firmowy)' : 'Szablon z nagłówkiem i stopką'}<small>${pr.szablon ? esc(pr.szablon) : KONTO.szablon ? `brak - raporty na papierze firmowym ${esc(KONTO.firma)} (z konta)` : 'brak - stopka programu (numer projektu, numer strony)'}</small></span>
          <span class="wartosci">${pr.szablon ? '<button class="btn btn-maly btn-bez" id="u-szablon-usun">Usuń</button>' : ''}<button class="btn btn-maly" id="u-szablon">${ik('folder')} Wybierz…</button></span></div>
        <p class="podp" style="margin:8px 0 0">Szablon to zwykły dokument Word (.docx) z Twoim nagłówkiem i stopką. Program bierze z niego nagłówek, stopkę, marginesy i rozmiar strony - treść szablonu pomija. PDF zapisuje Microsoft Word, więc stopka jest taka sama w PDF i DOCX. W nagłówku i stopce szablonu możesz wpisać pola, które program uzupełni: <b>{PROJEKT}</b> <b>{KLIENT}</b> <b>{AGREGAT}</b> <b>{SILNIK}</b> <b>{AUTOR}</b> <b>{DATA}</b> <b>{TYTUL}</b>.</p>
      </div>
      <div class="karta"><h3>${ik('obraz')} Wygląd</h3>
        <div class="wiersz"><span class="et">Motyw</span><div class="segment" id="u-motyw">${[['jasny', 'Jasny'], ['ciemny', 'Ciemny'], ['system', 'Jak w Windows']].map(([v, t]) => `<button data-v="${v}" class="${pr.motyw === v ? 'akt' : ''}">${t}</button>`).join('')}</div></div>
        <div class="wiersz"><span class="et">Wielkość tekstu</span><div class="segment" id="u-rozmiar">${[['maly', 'Mała'], ['normalny', 'Normalna'], ['duzy', 'Duża']].map(([v, t]) => `<button data-v="${v}" class="${pr.rozmiar === v ? 'akt' : ''}">${t}</button>`).join('')}</div></div>
      </div>
    </div>
    <div class="siatka">
      <div class="karta" id="karta-konta"><h3>${ik('ok')} Konto Diamel</h3>
        ${KONTO.zalogowany ? `
        <div class="wiersz"><span class="et"><b style="font-weight:600">${esc(KONTO.nazwa)}</b><small>login ${esc(KONTO.login)}${KONTO.inicjaly ? ` · inicjały w raportach: ${esc(KONTO.inicjaly)}` : ''}</small></span><button class="btn btn-maly" id="u-wyloguj">Wyloguj</button></div>
        <div class="wiersz"><span class="et">Papier firmowy w raportach<small>${KONTO.szablon ? `${esc(KONTO.firma)} · ${esc(KONTO.szablon)}` : KONTO.firma ? `${esc(KONTO.firma)} nie ma jeszcze szablonu w panelu` : 'konto bez przypisanej firmy'}</small></span>${KONTO.szablon ? '<span class="status ok">aktywny</span>' : '<span class="status szary">brak</span>'}</div>`
        : `<p class="opis">Logowanie nie jest obowiązkowe. Po zalogowaniu raporty mają papier firmowy Twojej firmy, a pole <i>Przygotował</i> - Twoje inicjały. Konto i dostęp do programu nadaje administrator.</p>
        <div class="pola p2" style="margin-top:4px">
          <div class="p-pole"><label class="etykieta" for="k-login">Login</label><input class="pole" id="k-login" autocomplete="username" spellcheck="false"></div>
          <div class="p-pole"><label class="etykieta" for="k-haslo">Hasło</label><input class="pole" id="k-haslo" type="password" autocomplete="current-password"></div>
        </div>
        <div class="wiersz" style="border:0"><label class="zaznacz"><input type="checkbox" id="k-zapamietaj" checked> Zapamiętaj na tym komputerze</label><button class="btn btn-maly btn-hr" id="k-zaloguj">Zaloguj</button></div>`}
      </div>
      <div class="karta"><h3>${ik('pobierz')} Aktualizacje</h3>
        ${AKT?.do_instalacji ? `<div class="baner zolty" style="margin:8px 0">${ik('pobierz')}<div class="tekst"><b>${AKT.wycofana ? `Zalecana wersja ${esc(AKT.wersja)}` : `Dostępna wersja ${esc(AKT.wersja)}`}</b>${AKT.wycofana ? 'W tej wersji wykryto błąd.' : 'Nowa wersja programu.'}</div><button class="btn btn-maly btn-hr" id="u-instaluj">Zainstaluj</button></div>` : ''}
        <div class="wiersz"><span class="et">Program<small>wersja ${esc(INFO.wersja)} z ${esc(INFO.data)}</small></span><button class="btn btn-maly" id="u-akt">${ik('odswiez')} Sprawdź</button></div>
        <div class="wiersz"><span class="et">Baza urządzeń<small>wersja ${esc(BAZA.wersja)}</small></span><button class="btn btn-maly" id="u-baza">${ik('odswiez')} Sprawdź</button></div>
      </div>
      <div class="karta"><h3>${ik('info')} O programie</h3>
        <p class="opis">Kalkulator Rozruchu · © Diamel · <button class="link" id="u-strona">diamel.pl</button></p>
        <pre class="changelog">${esc(INFO.changelog)}</pre>
      </div>
    </div></div>`;
  $('#u-autor').onchange = (e) => zmienProgram('autor', e.target.value.trim());
  const seg = (id, klucz) => $$(`#${id} button`).forEach((b) => b.onclick = async () => { await zmienProgram(klucz, b.dataset.v); rysujUstawienia(); });
  seg('u-jezyk', 'jezyk'); seg('u-motyw', 'motyw'); seg('u-rozmiar', 'rozmiar');
  $('#u-cca-tol').onchange = async (e) => {
    const v = Number(String(e.target.value).replace(',', '.'));
    if (!(v >= 0 && v <= 50)) { toast('Tolerancja CCA: wpisz liczbę od 0 do 50 %.', 'blad'); e.target.value = INFO.program.cca_tolerancja; return; }
    await zmienProgram('cca_tolerancja', v);
    toast(`Tolerancja CCA: ${lc(v)}%`, 'ok', null, 2500);
  };
  $('#u-otworz').onclick = async () => { await zmienProgram('otworz_raport', !INFO.program.otworz_raport); rysujUstawienia(); };
  $('#u-wyloguj')?.addEventListener('click', async () => {
    const r = await api('konto_wyloguj');
    KONTO = r.stan;
    toast('Wylogowano - raporty mają teraz stopkę programu.', 'ok', null, 4000);
    poZmianieKonta();
  });
  const zaloguj = async () => {
    const login = $('#k-login').value.trim(), haslo = $('#k-haslo').value;
    if (!login || !haslo) return $(login ? '#k-haslo' : '#k-login').focus();
    const b = $('#k-zaloguj'); b.disabled = true; b.textContent = 'Logowanie…';
    const r = await api('konto_zaloguj', login, haslo, $('#k-zapamietaj').checked);
    if (!r?.ok) { b.disabled = false; b.textContent = 'Zaloguj'; return toast(esc(r?.blad || 'Logowanie nie powiodło się.'), 'blad'); }
    KONTO = r.stan;
    toast(`Zalogowano: <b>${esc(KONTO.nazwa)}</b>${KONTO.szablon ? `<br>Raporty na papierze firmowym ${esc(KONTO.firma)}.` : ''}`, 'ok', null, 6000);
    if (r.uwaga) toast(esc(r.uwaga), 'blad');
    poZmianieKonta();
  };
  $('#k-zaloguj')?.addEventListener('click', zaloguj);
  $$('#k-login, #k-haslo').forEach((el) => el.addEventListener('keydown', (e) => e.key === 'Enter' && zaloguj()));
  $('#u-szablon').onclick = async () => { INFO.program = await api('wybierz_szablon'); rysujUstawienia(); };
  $('#u-szablon-usun')?.addEventListener('click', async () => { await zmienProgram('szablon', ''); rysujUstawienia(); });
  $('#u-akt').onclick = () => sprawdzAktualizacje(true);
  $('#u-baza').onclick = () => sprawdzBaze(true);
  $('#u-instaluj')?.addEventListener('click', oknoAktualizacji);
  $('#u-strona').onclick = () => api('otworz_strone', 'https://diamel.pl');
}

// ------------------------------------------------------------------ zgłoszenia
const zglos = { rodzaj: 'sprzet', kategoria: 'Rozrusznik', email: '', nazwa: '', opis: '', projekt: true, zalaczniki: [] };
function rysujZglos() {
  const el = $('#widok-zglos');
  const sprzet = zglos.rodzaj === 'sprzet';
  el.innerHTML = `<div class="karta formularz">
    <div class="segment pelny" id="z-rodzaj"><button data-v="sprzet" class="${sprzet ? 'akt' : ''}">${ik('baza')} Prośba o dodanie sprzętu do bazy</button><button data-v="blad" class="${!sprzet ? 'akt' : ''}">${ik('uwaga')} Błąd programu</button></div>
    <p class="opis" style="margin:0">${sprzet ? 'Brakuje rozrusznika, akumulatora albo ładowarki? Podaj model i link do karty katalogowej - po weryfikacji trafi do bazy globalnej i do wszystkich użytkowników.' : 'Opisz, co się stało. Możesz dołączyć bieżący projekt - ułatwi to odtworzenie błędu.'}</p>
    <div class="pola p2">
      <div class="p-pole"><label class="etykieta" for="z-email">Twój e-mail (do odpowiedzi)</label><input class="pole" id="z-email" type="email" value="${esc(zglos.email)}"></div>
      ${sprzet ? `<div class="p-pole"><label class="etykieta">Kategoria</label><div class="segment pelny" id="z-kat">${['Rozrusznik', 'Akumulator', 'Silnik', 'Ładowarka'].map((k) => `<button data-v="${k}" class="${zglos.kategoria === k ? 'akt' : ''}">${k}</button>`).join('')}</div></div>
        <div class="p-pole szer2"><label class="etykieta" for="z-nazwa">Producent i model</label><input class="pole" id="z-nazwa" value="${esc(zglos.nazwa)}"></div>` : ''}
    </div>
    <div><label class="etykieta" for="z-opis">${sprzet ? 'Parametry, link do karty katalogowej' : 'Opis problemu'}</label><textarea class="pole" id="z-opis" rows="7">${esc(zglos.opis)}</textarea></div>
    <div><span class="etykieta">Załączniki${sprzet ? ' (karta katalogowa, krzywa, zdjęcie tabliczki)' : ''} - razem do 5 MB</span>
      <div class="lista-zalacznikow">${zglos.zalaczniki.map((z, i) => `<span class="znacznik akt">${ik('plik')} ${esc(z.nazwa)} <span class="podp">${z.kb} kB</span><button class="btn btn-bez btn-ikona" data-usun-zal="${i}" title="Usuń">${ik('x')}</button></span>`).join('')}
        <button class="btn btn-maly" id="z-dodaj-zal">${ik('plus')} Dodaj pliki…</button></div></div>
    ${!sprzet ? `<label class="zaznacz"><input type="checkbox" id="z-projekt" ${zglos.projekt ? 'checked' : ''}> Dołącz bieżący projekt (${esc(P.project_no || 'bez nazwy')})</label>` : ''}
    <div><button class="btn btn-hr" id="z-wyslij">${ik('wyslij')} Wyślij</button></div>
  </div>`;
  const zapamietaj = () => { zglos.email = $('#z-email').value; zglos.opis = $('#z-opis').value; if ($('#z-nazwa')) zglos.nazwa = $('#z-nazwa').value; if ($('#z-projekt')) zglos.projekt = $('#z-projekt').checked; };
  $$('#z-rodzaj button').forEach((b) => b.onclick = () => { zapamietaj(); zglos.rodzaj = b.dataset.v; rysujZglos(); });
  $$('#z-kat button').forEach((b) => b.onclick = () => { zapamietaj(); zglos.kategoria = b.dataset.v; rysujZglos(); });
  $('#z-dodaj-zal').onclick = async () => {
    zapamietaj();
    const nowe = (await api('wybierz_zalaczniki')) || [];
    zglos.zalaczniki = [...zglos.zalaczniki, ...nowe.filter((n) => !zglos.zalaczniki.some((z) => z.sciezka === n.sciezka))];
    const kb = zglos.zalaczniki.reduce((s, z) => s + z.kb, 0);
    if (kb > 5 * 1024) toast(`Załączniki mają razem ${lp(kb / 1024, 1)} MB - limit to 5 MB.`, 'blad');
    rysujZglos();
  };
  $$('[data-usun-zal]').forEach((b) => b.onclick = () => { zapamietaj(); zglos.zalaczniki.splice(+b.dataset.usunZal, 1); rysujZglos(); });
  $('#z-wyslij').onclick = async () => {
    zapamietaj();
    if (!/^\S+@\S+\.\S+$/.test(zglos.email.trim())) { toast('Podaj poprawny adres e-mail.', 'blad'); return $('#z-email').focus(); }
    if (sprzet && !zglos.nazwa.trim()) { toast('Podaj producenta i model.', 'blad'); return $('#z-nazwa').focus(); }
    if (!sprzet && !zglos.opis.trim()) { toast('Opisz problem.', 'blad'); return $('#z-opis').focus(); }
    const b = $('#z-wyslij'); b.disabled = true; b.textContent = 'Wysyłanie…';
    const pliki = zglos.zalaczniki.map((z) => z.sciezka);
    const r = sprzet ? await api('zglos', zglos.email.trim(), zglos.kategoria, zglos.nazwa.trim(), zglos.opis.trim(), null, pliki)
      : await api('zglos', zglos.email.trim(), 'Błąd programu', `Zgłoszenie błędu Kalkulatora v${INFO.wersja}`, zglos.opis.trim(), zglos.projekt ? P : null, pliki);
    b.disabled = false; b.innerHTML = `${ik('wyslij')} Wyślij`;
    if (!r?.ok) return toast(`Nie udało się wysłać: ${esc(r?.blad || '')}`, 'blad');
    toast('Zgłoszenie wysłane - odpowiemy na podany adres e-mail. Dziękujemy!', 'ok', null, 7000);
    zglos.nazwa = ''; zglos.opis = ''; zglos.zalaczniki = []; rysujZglos();
  };
}

// ------------------------------------------------------------------ skróty klawiszowe
document.addEventListener('keydown', (e) => {
  if (modalOtwarty) { if (e.key === 'Escape') modalOtwarty.zamknij(null); return; }
  const kl = e.key.toLowerCase();
  if (e.ctrlKey && kl === 's') { e.preventDefault(); return zapiszProjekt(e.shiftKey); }
  if (e.ctrlKey && kl === 'o') { e.preventDefault(); return otworzProjekt(); }
  if (e.ctrlKey && kl === 'n') { e.preventDefault(); return nowyProjekt(); }
  if (e.ctrlKey && kl === 'g') { e.preventDefault(); if (widok === 'obliczenia') generujRaport(e.shiftKey ? 'docx' : 'pdf'); }
});
