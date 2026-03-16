# SRT Multiview

Application locale Python pour router des flux SRT vers plusieurs écrans Windows, avec émission SRT intégrée.

## Fonctionnalités

- **Réception SRT** : Écoute plusieurs flux SRT en mode `listener` (vous envoyez en `caller`)
- **Routage SRT → UDP multicast** : Duplication d'un flux SRT via `ffmpeg` pour alimenter plusieurs écrans (`ffplay` lit le multicast)
- **Source par flux** : Chaque flux peut lire en **SRT direct** ou depuis une **Route**
- **Contrôle par flux** : Bouton ▶/⏹ par flux + statut (arrêté / démarrage / en cours)
- **Rotation par flux** : 0° / 90° / 180° / 270°
- **Modes d'affichage** : fit / fill / stretch
- **Émission SRT** : Capture un écran et l'envoie en SRT via ffmpeg (mode `caller`)
- **Multi-écrans** : Affiche chaque flux en plein écran sur un écran Windows différent
- **Exclusion écran principal** : Option pour ne pas utiliser l'écran de travail
- **Auto-mapping** : Peut créer automatiquement des flux si nécessaire
- **Reset global** : Réinitialise toute la configuration et stoppe lectures/émission/routes
- **Configuration persistante** : Flux, mapping, routes, options et paramètres d'émission sauvegardés

## Prérequis

1. **Python 3.10+**
2. **ffplay** et **ffmpeg** (inclus avec FFmpeg) dans le dossier `bin/` (uniquement si tu exécutes/build en local)

### Installation de ffplay / ffmpeg

1. Télécharger FFmpeg : https://github.com/BtbN/FFmpeg-Builds/releases
2. Extraire `ffplay.exe` et `ffmpeg.exe` dans le dossier `bin/` du projet

```
srt-multiview/
├── bin/
│   ├── ffmpeg.exe
│   └── ffplay.exe
├── build_exe.ps1
├── config.json
├── img/
│   ├── icon.ico
│   └── icon.png
├── pyproject.toml
├── run_app.py
├── srt_multiview/
│   ├── __init__.py
│   ├── __main__.py
│   ├── core.py
│   ├── paths.py
│   └── ui.py
├── srt_multiview.spec
└── requirements.txt
```

## Licence

Srt-MultiView © 2026 by LFPoulain is licensed under CC BY-NC-SA 4.0.
To view a copy of this license, visit https://creativecommons.org/licenses/by-nc-sa/4.0/.

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
python -m srt_multiview
```

## Exécutable Windows (.exe)

L'exécutable est généré automatiquement via **GitHub Actions**.

- À chaque `git push` sur `main`, le workflow publie (ou met à jour) une **pré-release** GitHub nommée **Nightly** (tag `nightly`) avec le dernier `SRT-MultiView.exe`.
- Le workflow télécharge FFmpeg (pour obtenir `ffmpeg.exe` et `ffplay.exe`) avant le build.
- Les binaires `bin/*.exe` ne doivent pas être versionnés (GitHub bloque les fichiers > 100MB).

Pour télécharger l'exe :

1. Aller sur l'onglet **Releases** du repo
2. Ouvrir **Nightly**
3. Télécharger `SRT-MultiView.exe`

### Workflow — Réception

1. **Configurer les flux** : Ajouter des flux (« + Ajouter un flux »)
2. **Choisir la source** :
   - **SRT** : l'app écoute `srt://0.0.0.0:PORT` (listener)
   - **Route** : sélectionner une route existante (voir section Routage)
3. **Mapper les écrans** : Associer chaque flux à un écran via le sélecteur
4. **Démarrer** : Cliquer sur « ▶ Démarrer tout » (ou ▶ sur un flux)
5. **Envoyer depuis la régie** : Utiliser OBS/vMix/etc. en mode `caller` vers `srt://IP:PORT`

### Workflow — Émission

1. **Sélectionner l'écran** à capturer dans le panneau « Émission SRT »
2. **Configurer** : hôte destination, port, latence, FPS, bitrate
3. **Émettre** : Cliquer sur « ▶ Émettre »

### Exemple OBS

Dans OBS, créer une sortie SRT :
```
srt://192.168.1.100:9001?mode=caller&latency=120000
```

## Configuration

La configuration est stockée dans le fichier utilisateur :

- Windows : `%USERPROFILE%\srt-multiview-config.json`

Il stocke notamment :

- Les flux (nom, source SRT/Route, port/latence, mode d'affichage, rotation)
- Le mapping flux → écran
- Les noms d'écrans personnalisés
- Les routes de routage (SRT in port/latence, UDP multicast out)
- Les options (exclure écran principal, auto-start)
- Les paramètres d'émission SRT (écran, hôte, port, latence, FPS, bitrate)

`config.json` à la racine du repo est un exemple, il n'est pas utilisé par l'app.

## Routage (SRT → UDP multicast)

Le routage sert à **dupliquer** un flux SRT en une sortie UDP multicast lisible par plusieurs `ffplay`.

- Une **Route** écoute un port SRT (listener)
- `ffmpeg` repack en MPEG-TS et sort vers `udp://@239.x.x.x:PORT`
- Plusieurs écrans peuvent lire la même route en parallèle

Note : le démarrage via UDP peut prendre quelques secondes. L'UI affiche un état **"démarrage"** (loader) pendant ce temps.

## Notes techniques

- ffplay est lancé avec `-fs` (fullscreen) positionné sur l'écran cible
- ffmpeg est utilisé pour la capture d'écran et l'émission SRT en mode `caller`
- La latence SRT est en millisecondes (120 = 120ms par défaut)
- Les flux entrants sont en mode `listener` (l'app attend les connexions)
