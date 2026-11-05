# KattaPack Website

Die fertige Website liegt direkt hier im Hauptverzeichnis. Sie braucht keine Datenbank, kein WordPress und kein PHP.

## Online stellen

1. Oben rechts auf **Code → Download ZIP** klicken und die ZIP entpacken.
2. Beim Hosting-Anbieter den Dateimanager oder ein FTP-Programm öffnen.
3. Diese Dateien und Ordner ins Hauptverzeichnis der Domain hochladen:
   - alle `.html`-Dateien
   - `site.css`, `site.js`
   - `favicon.svg`, `favicon.ico`, `apple-touch-icon.png`
   - den Ordner `fonts`
   - die Datei `.htaccess` (beginnt mit einem Punkt und ist deshalb manchmal ausgeblendet)

Den Ordner `quellcode` und diese README braucht der Server nicht.

Danach beim Hoster HTTPS einschalten (SSL-Zertifikat, meist kostenlos).

## Vor dem Start ausfüllen

Auf den Seiten **Impressum** und **Datenschutz** sind die fehlenden Angaben grau markiert: Firmenname, Anschrift, Telefon, Hosting-Anbieter und so weiter. Mit dem Hosting-Anbieter einen Vertrag zur Auftragsverarbeitung abschließen (geht meist online im Kundenmenü).

## Texte ändern

Alle Texte stehen in `quellcode/build.py`, Design in `quellcode/site.css`, Funktionen in `quellcode/site.js`. Nach einer Änderung neu bauen (Python 3 genügt):

```
python3 quellcode/build.py .
```

Das schreibt alle Seiten neu ins Hauptverzeichnis.
