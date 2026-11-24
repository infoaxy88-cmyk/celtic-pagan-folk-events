#!/usr/bin/env python3
"""Controlla una lista fissa di siti e segnala le novità aprendo una Issue su GitHub.

Usa solo la libreria standard di Python: nessuna installazione e nessuna chiave a pagamento.
Senza GITHUB_TOKEN gira in modalità prova e stampa le segnalazioni invece di crearle.
"""
import difflib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(os.environ.get("CALENDARIO_ROOT", Path(__file__).resolve().parent.parent))
STATO_DIR = ROOT / "stato"
STATO_FILE = STATO_DIR / "stato.json"
ETICHETTA = "controllo-siti"
SOGLIA_ERRORI = 3
USER_AGENT = "Mozilla/5.0 (compatible; CalendarioEventi/1.0; controllo periodico)"

MESI = "gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre"
RE_DATA = re.compile(r"\b\d{1,2}(?:\s*[-–/]\s*\d{1,2})*\s+(?:%s)\b" % MESI, re.I)
RE_EDIZIONE = re.compile(
    r"\b(?:[IVXL]{1,6}|\d{1,2}\s*[°ªa])\s*edizione|\bedizione\s+(?:20\d\d|[IVXL]{1,6}|\d{1,2})\b", re.I
)
RE_ANNO = re.compile(r"\b(20\d\d)\b")


class Estrattore(HTMLParser):
    """Trasforma l'HTML in righe di testo, ignorando script, stili e menu nascosti."""

    SALTA = {"script", "style", "noscript", "svg", "template"}
    A_CAPO = {"p", "div", "br", "li", "ul", "ol", "tr", "td", "th", "h1", "h2", "h3", "h4", "h5",
              "h6", "section", "article", "header", "footer", "nav", "main", "table", "form"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pezzi = []
        self.salta = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SALTA:
            self.salta += 1
        elif tag in self.A_CAPO:
            self.pezzi.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SALTA and self.salta:
            self.salta -= 1
        elif tag in self.A_CAPO:
            self.pezzi.append("\n")

    def handle_data(self, data):
        if not self.salta:
            self.pezzi.append(data)


def scarica(url):
    richiesta = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "it"})
    with urllib.request.urlopen(richiesta, timeout=30) as risposta:
        dati = risposta.read()
        codifica = risposta.headers.get_content_charset() or "utf-8"
    return dati.decode(codifica, errors="replace")


def normalizza(html, ignora):
    estrattore = Estrattore()
    estrattore.feed(html)
    righe = []
    for riga in "".join(estrattore.pezzi).splitlines():
        riga = re.sub(r"\s+", " ", riga).strip()
        if not riga or any(re.search(p, riga, re.I) for p in ignora):
            continue
        if not righe or righe[-1] != riga:
            righe.append(riga)
    return righe


def e_un_segnale(riga):
    """Vero se la riga contiene una data, un numero di edizione o un anno dal corrente in poi."""
    anno_corrente = datetime.now().year
    if RE_DATA.search(riga) or RE_EDIZIONE.search(riga):
        return True
    return any(int(a) >= anno_corrente for a in RE_ANNO.findall(riga))


def carica_stato():
    if STATO_FILE.exists():
        return json.loads(STATO_FILE.read_text(encoding="utf-8"))
    return {}


def api_github(metodo, percorso, corpo=None):
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    richiesta = urllib.request.Request(
        "https://api.github.com/repos/%s%s" % (repo, percorso),
        data=json.dumps(corpo).encode() if corpo is not None else None,
        method=metodo,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "calendario-eventi",
        },
    )
    with urllib.request.urlopen(richiesta, timeout=30) as risposta:
        return json.loads(risposta.read().decode())


def segnalazioni_aperte():
    if not (os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPOSITORY")):
        return []
    try:
        return [i["title"] for i in api_github("GET", "/issues?state=open&labels=%s&per_page=100" % ETICHETTA)]
    except Exception as errore:  # un errore qui non deve fermare il controllo
        print("Impossibile leggere le segnalazioni aperte:", errore)
        return []


def apri_segnalazione(titolo, corpo, aperte):
    prefisso = titolo.split(":")[0] + ":"
    if any(t.startswith(prefisso) for t in aperte):
        print("Segnalazione già aperta, non ne creo un'altra:", prefisso)
        return
    if not (os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPOSITORY")):
        print("\n[PROVA] Segnalazione non creata (manca GITHUB_TOKEN)\nTitolo:", titolo, "\n", corpo, "\n")
        return
    api_github("POST", "/issues", {"title": titolo, "body": corpo, "labels": [ETICHETTA]})
    aperte.append(titolo)
    print("Segnalazione creata:", titolo)


def main():
    configurazione = json.loads((ROOT / "siti.json").read_text(encoding="utf-8"))
    STATO_DIR.mkdir(exist_ok=True)
    stato = carica_stato()
    aperte = segnalazioni_aperte()
    adesso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for sito in configurazione["siti"]:
        id_sito, nome, url = sito["id"], sito["nome"], sito["url"]
        voce = stato.setdefault(id_sito, {"errori": 0})
        voce["ultimo_controllo"] = adesso
        try:
            righe = normalizza(scarica(url), sito.get("ignora", []))
            if not righe:
                raise ValueError("pagina senza testo leggibile")
        except Exception as errore:
            voce["errori"] = voce.get("errori", 0) + 1
            print("%s: errore (%d di fila): %s" % (nome, voce["errori"], errore))
            if voce["errori"] == SOGLIA_ERRORI:
                apri_segnalazione(
                    "%s: il sito non risponde" % nome,
                    "Per %d controlli di fila non sono riuscito a leggere %s.\n\nUltimo errore: `%s`\n\n"
                    "Controlla se l'indirizzo è cambiato e aggiorna `siti.json`. Chiudi questa segnalazione a "
                    "lavoro finito." % (SOGLIA_ERRORI, url, errore),
                    aperte,
                )
            continue
        voce["errori"] = 0

        file_testo = STATO_DIR / (id_sito + ".txt")
        if not file_testo.exists():
            file_testo.write_text("\n".join(righe) + "\n", encoding="utf-8")
            print("%s: primo controllo, salvo la pagina di riferimento." % nome)
            continue

        precedenti = file_testo.read_text(encoding="utf-8").splitlines()
        if righe == precedenti:
            print("%s: nessun cambiamento." % nome)
            continue

        diff = list(difflib.unified_diff(precedenti, righe, lineterm="", n=0))
        aggiunte = [r[1:] for r in diff if r.startswith("+") and not r.startswith("+++")]
        rimosse = [r[1:] for r in diff if r.startswith("-") and not r.startswith("---")]
        segnali = [r for r in aggiunte if e_un_segnale(r)]
        file_testo.write_text("\n".join(righe) + "\n", encoding="utf-8")
        voce["ultima_modifica"] = adesso

        if not segnali and not sito.get("segnala_ogni_modifica"):
            print("%s: pagina cambiata, ma senza date o edizioni nuove. Nessuna segnalazione." % nome)
            continue

        def elenco(voci, massimo=25):
            testo = "\n".join("- " + v[:220] for v in voci[:massimo])
            return testo + ("\n- … e altre %d righe" % (len(voci) - massimo) if len(voci) > massimo else "")

        corpo = (
            "La pagina di **%s** è cambiata.\n\nIndirizzo: %s\n\n" % (nome, url)
            + ("### Righe nuove con date o edizioni\n%s\n\n" % elenco(segnali) if segnali else "")
            + "### Tutte le righe aggiunte\n%s\n\n" % (elenco(aggiunte) if aggiunte else "_nessuna_")
            + "### Righe rimosse\n%s\n\n" % (elenco(rimosse, 10) if rimosse else "_nessuna_")
            + "---\nSe c'è una nuova edizione, aggiungila a `eventi.json` (vedi LEGGIMI.md) oppure mandami il "
            "link. Chiudi questa segnalazione a lavoro finito: finché è aperta non ne arrivano altre per "
            "questo sito."
        )
        apri_segnalazione(
            "%s: possibile novità sul sito (%s)" % (nome, datetime.now().strftime("%d/%m/%Y")), corpo, aperte
        )

    STATO_FILE.write_text(json.dumps(stato, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
