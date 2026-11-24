# Calendario eventi Celtic Pagan Folk: istruzioni

Il sito è una pagina statica su GitHub Pages. Gli eventi stanno in `eventi.json`, la pagina (`index.html`) li legge all'apertura. Un controllo automatico settimanale guarda i siti degli organizzatori e ti avvisa quando c'è una novità. Tutto è gratuito e non servono chiavi o abbonamenti.

## Cosa c'è nell'archivio

| File | A cosa serve |
|---|---|
| `index.html` | La pagina del calendario. Non contiene più gli eventi. |
| `eventi.json` | **Gli eventi.** È l'unico file da modificare per aggiungere o cambiare un evento. |
| `manifest.json`, `sw.js`, `icon-192.png`, `icon-512.png` | Servono al pulsante "Installa come app". |
| `siti.json` | La lista dei siti da controllare. |
| `scripts/controlla_siti.py` | Lo script che controlla i siti. |
| `scripts/valida_eventi.py` | Verifica che `eventi.json` sia scritto bene. |
| `.github/workflows/controlla-siti.yml` | Avvia il controllo dei siti ogni lunedì. |
| `.github/workflows/valida-eventi.yml` | Avvia la verifica di `eventi.json` a ogni modifica. |
| `stato/` | Si crea da sola: le pagine di riferimento dei siti controllati. Non toccarla. |

## Installazione (una volta sola)

1. **Carica i file.** Meglio da computer. Nell'archivio scegli Add file → Upload files e trascina `index.html`, `eventi.json`, `manifest.json`, `sw.js`, le due icone, `siti.json` e le cartelle `scripts` e `.github`. Se il caricamento non accetta la cartella `.github` (inizia con un punto), usa Add file → Create new file, scrivi come nome `.github/workflows/controlla-siti.yml` (le barre creano le cartelle) e incolla il contenuto del file. Ripeti per `valida-eventi.yml`.
2. **Permessi.** In Settings → Actions → General, in fondo, sotto "Workflow permissions" scegli **Read and write permissions** e salva. Senza questo il controllo non può salvare il suo stato né aprire segnalazioni.
3. **Prima prova.** Vai nella scheda Actions, scegli "Controlla i siti degli organizzatori", poi Run workflow. Alla prima esecuzione lo script salva la pagina di riferimento di ogni sito e non segnala nulla. È normale. Da quel momento confronta ogni pagina con quella salvata.

Il sito deve restare su GitHub Pages: aperto con un doppio clic sul computer, `index.html` non riesce a leggere `eventi.json`.

## Aggiungere un evento

Apri `eventi.json` su GitHub, premi la matita (Edit), aggiungi un blocco in fondo alla lista (con la virgola dopo il blocco precedente) e conferma con Commit changes. Il sito si aggiorna in uno o due minuti. Esempio:

```json
{
  "id": 11,
  "name": "Nome dell'evento",
  "start": "2027-05-28",
  "end": "2027-05-30",
  "city": "Masserano",
  "region": "Piemonte",
  "address": "Parco Arcobaleno",
  "desc": "Descrizione breve.",
  "free": false,
  "camp": true,
  "food": true,
  "links": [
    { "label": "Sito ufficiale", "url": "https://beltanefestival.it/it" }
  ]
}
```

- **id:** un numero che non si ripete.
- **start, end:** date nel formato AAAA-MM-GG. Per un evento di un giorno sono uguali.
- **free, camp, food:** `true` (sì), `false` (no) oppure `null` (non indicato). Per `free`, `false` significa "a pagamento".
- **links:** uno o più link, ognuno con testo e indirizzo che inizia con `https://`.
- **Programma a giorni (facoltativo):** `"days": [ { "title": "Sabato 19 dicembre", "items": [ ["Dalle 10", "Apertura del mercatino."] ] } ]`. Vedi l'evento Yule.
- **Evento annullato:** aggiungi `"status": "annullato"` e, se vuoi, `"note": "Motivo."`.
- **Evento rinviato:** aggiungi `"status": "rinviato"`, `"newStart"`, `"newEnd"` e `"note"`.

Quando salvi, parte la verifica automatica di `eventi.json`. Se hai dimenticato una virgola o un campo, GitHub ti manda una email che dice cosa correggere (e la scheda Actions mostra una croce rossa).

## Quando arriva una segnalazione

Se la pagina di un sito cambia e compaiono date, un numero di edizione o un anno nuovo, nella scheda **Issues** appare una segnalazione con le righe nuove, e ricevi una notifica da GitHub (email e app). Hai due strade:

- **Fai da solo:** aggiungi l'evento a `eventi.json` come sopra.
- **Mandami il link o il testo:** ti preparo la scheda già pronta da incollare.

Chiudi la segnalazione a lavoro finito. Finché è aperta non ne arrivano altre per lo stesso sito.

Una modifica che non riguarda date o edizioni (un banner, un contatore) non apre segnalazioni. Se vuoi essere avvisato di tutto, in `siti.json` aggiungi `"segnala_ogni_modifica": true` al sito. Se un sito ha una riga che cambia sempre (per esempio un contatore di visite), aggiungi `"ignora": ["^Visite"]`: è un elenco di espressioni regolari per le righe da non considerare.

Se un sito non risponde per tre controlli di fila, ricevi una segnalazione "il sito non risponde".

## Cambiare la lista dei siti o la frequenza

- **Siti:** modifica `siti.json`, copiando un blocco (`id` senza spazi, `nome`, `url`).
- **Frequenza:** in `.github/workflows/controlla-siti.yml` cambia la riga `cron`. `"0 6 * * 1"` è ogni lunedì; `"0 6 * * *"` è ogni giorno, alle 06:00 UTC.
- **Controllo subito:** scheda Actions → "Controlla i siti degli organizzatori" → Run workflow.

## Limiti da conoscere

- Il controllo **non legge** Facebook, Instagram, Dice e Vivaticket, che bloccano l'accesso automatico. Per gli eventi che compaiono solo lì servono ancora i dati a mano.
- Il controllo **non compila le schede**: ti dice dove guardare. Senza un modello di linguaggio le estrazioni automatiche di date e luoghi sarebbero troppo fragili, e un evento sbagliato rovina la fiducia nel calendario.
- GitHub può sospendere i controlli programmati degli archivi pubblici senza attività per un lungo periodo (di solito 60 giorni). Se succede, la scheda Actions mostra un avviso con il pulsante per riattivarli.
- I controlli salvano ogni volta un file in `stato/`, quindi nell'archivio compare una modifica automatica a ogni esecuzione. È voluto.
