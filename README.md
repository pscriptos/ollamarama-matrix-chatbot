# ollamarama-matrix-chatbot

### Zuerst das Wichtigste:

Dies ist ein Fork von [Dustin Whyte](https://github.com/h1ddenpr0cess20/ollamarama-matrix), welchen ich anschließend in Docker inpelementiert habe.


Ollamarama ist ein KI-Chatbot für das [Matrix](https://matrix.org/) Chatprotokoll mit Ollama. Er kann fast alles spielen, was Du dir vorstellen kannst. Du kannst jede Standardpersönlichkeit einstellen, die du möchtest. Sie kann jederzeit geändert werden, und jeder Benutzer hat seinen eigenen Chatverlauf mit der von ihm gewählten Persönlichkeitseinstellung. Die Benutzer können mit den Chatverläufen der anderen interagieren, um zusammenzuarbeiten, wenn sie das möchten, aber ansonsten sind die Unterhaltungen getrennt, pro Kanal und pro Benutzer.
Dieser Chatbot kommt zusammen mit dem Ollama Docker, zu finden [hier](https://hub.docker.com/r/ollama/ollama).


## Setup

Installiere dir zuerst Docker. Dies kannst du mit [diesem Script](https://github.com/h1ddenpr0cess20/ollamarama-matrix) machen.

Anschließend clonst du mein Projekt:

```bash
git clone https://git.techniverse.net/scriptos/ollamarama-matrix
```

Anschließend ins Verzeichnis wechseln und die Konfigurationsdatei für den Matrix-Chatbot konfigurieren:

```bash
cd ollamarama-matrix && nano data/chatbot/config.json)
```

In der `config.json` werden die Zugangsdaten für den Chatbot gepflegt. Dieser muss im Vorfeld auf dem Matrix Server erstellt werden. Dies kann [hier](https://app.element.io/) gemacht werden.
Weiterhin können in dieser Konfigurationsdatei weitere Modelle gepflegt werden, welche vom Chatbot anschließend verwendet werden könnten.

In der Datei `start.sh` können weitere Modelle gepflegt werden, welche dann nach dem Starten vom Ollama Docker Container runtergeladen werden.

Weitere Modelle können [hier](https://ollama.ai/library) geladen werden.

Wenn die Konfiguration gemacht ist, kann der Docker mit 

```bash
docker-compose up --build
```

gestartet werden.
Dies ist ideal um gleich auch die Logs zu sehen.

Nun tritt der Bot automatisch den konfigurierten Channels bei und sollte dir im Idealfall direkt zu Verfügung stehen.

Den Docker startest du richtig mit

```bash
docker-compose -d
```

Die erste Nachricht versendest du mit `.ai message`

Ein Beispiel:

```bash
.ai Hallo, wie geht es dir?
```


# Verwendung  

**.ai _nachricht_** oder **botname: _nachricht_**

   Grundlegende Verwendung.

**.x _benutzer_ _nachricht_**

   Erlaubt es dir, auf die Chat-Historie eines anderen Benutzers zuzugreifen.

   _benutzer_ ist der Anzeigename des Benutzers, dessen Historie du verwenden möchtest.

**.persona _persönlichkeit_**

   Ändert die Persönlichkeit. Es kann eine Figur, ein Persönlichkeitstyp, ein Objekt, eine Idee, was auch immer sein. Nutze deine Fantasie.

**.custom _eingabeaufforderung_**

   Erlaubt die Verwendung einer benutzerdefinierten Systemaufforderung anstelle der Rollenspielaufforderung.

**.reset**

   Verlauf löschen und auf voreingestellte Persönlichkeit zurücksetzen.

**.stock**

   Verlauf löschen und ohne Systemaufforderung verwenden.

**Nur für Admins**

**.model _modell_**

   Lasse den Modellnamen weg, um das aktuelle Modell und verfügbare Modelle anzuzeigen.

   Gib den Modellnamen ein, um das Modell zu wechseln.

**.clear**

   Setzt den Bot für alle zurück.

