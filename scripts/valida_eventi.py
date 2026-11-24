#!/usr/bin/env python3
"""Controlla che eventi.json sia scritto bene. Esce con errore se trova problemi."""
import json
import os
import sys
from datetime import date
from pathlib import Path

FILE = Path(os.environ.get("EVENTI_JSON", Path(__file__).resolve().parent.parent / "eventi.json"))
TESTI = ["name", "city", "region", "address", "desc"]
TRISTATO = ["free", "camp", "food"]


def data(valore):
    return date.fromisoformat(valore)


def main():
    errori = []
    try:
        eventi = json.loads(FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print("eventi.json non è un JSON valido: riga %d, colonna %d: %s" % (e.lineno, e.colno, e.msg))
        return 1
    if not isinstance(eventi, list):
        print("eventi.json deve contenere una lista di eventi")
        return 1

    visti = set()
    for n, e in enumerate(eventi, 1):
        nome = "evento n. %d (%s)" % (n, e.get("name", "senza nome") if isinstance(e, dict) else "?")
        if not isinstance(e, dict):
            errori.append("%s: non è un oggetto" % nome)
            continue
        if not isinstance(e.get("id"), int):
            errori.append("%s: manca 'id' numerico" % nome)
        elif e["id"] in visti:
            errori.append("%s: l'id %d è usato due volte" % (nome, e["id"]))
        else:
            visti.add(e["id"])
        for campo in TESTI:
            if not isinstance(e.get(campo), str) or not e[campo].strip():
                errori.append("%s: manca il testo '%s'" % (nome, campo))
        for campo in TRISTATO:
            if e.get(campo) not in (True, False, None):
                errori.append("%s: '%s' deve essere true, false o null" % (nome, campo))
        try:
            inizio, fine = data(e["start"]), data(e["end"])
            if fine < inizio:
                errori.append("%s: la data di fine è prima di quella di inizio" % nome)
        except (KeyError, ValueError, TypeError):
            errori.append("%s: 'start' e 'end' devono essere date nel formato AAAA-MM-GG" % nome)
        stato = e.get("status", "ok")
        if stato not in ("ok", "rinviato", "annullato"):
            errori.append("%s: 'status' deve essere ok, rinviato o annullato" % nome)
        if stato == "rinviato":
            try:
                data(e["newStart"]), data(e["newEnd"])
            except (KeyError, ValueError, TypeError):
                errori.append("%s: un evento rinviato richiede 'newStart' e 'newEnd' (AAAA-MM-GG)" % nome)
        for link in e.get("links", []):
            if not (isinstance(link, dict) and str(link.get("url", "")).startswith(("http://", "https://"))
                    and link.get("label")):
                errori.append("%s: ogni link ha bisogno di 'label' e di un 'url' che inizia con https://" % nome)
        for giorno in e.get("days", []):
            if not (isinstance(giorno, dict) and giorno.get("title") and isinstance(giorno.get("items"), list)
                    and all(isinstance(r, list) and len(r) == 2 for r in giorno["items"])):
                errori.append("%s: ogni giorno di 'days' vuole 'title' e 'items' di coppie [orario, testo]" % nome)

    if errori:
        print("Trovati %d problemi in eventi.json:" % len(errori))
        for riga in errori:
            print(" -", riga)
        return 1
    print("eventi.json è a posto: %d eventi." % len(eventi))
    return 0


if __name__ == "__main__":
    sys.exit(main())
