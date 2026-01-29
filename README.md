# SRT Multiview

Application locale Python pour router des flux SRT vers plusieurs écrans Windows.

## Fonctionnalités

- **Réception SRT** : Écoute plusieurs flux SRT en mode `listener` (vous envoyez en `caller`)
- **Multi-écrans** : Affiche chaque flux en plein écran sur un écran Windows différent
- **UI Desktop** : Application Windows pour mapper flux → écran
- **Exclusion écran principal** : Option pour ne pas utiliser l'écran de travail
- **Configuration persistante** : Ports, latence et mapping sauvegardés

## Prérequis

1. **Python 3.10+**
2. **ffplay** (inclus avec FFmpeg) dans le dossier `bin/`

### Installation de ffplay

1. Télécharger FFmpeg : https://github.com/BtbN/FFmpeg-Builds/releases
2. Extraire `ffplay.exe` dans le dossier `bin/` du projet

```
srt-multiview/
├── bin/
│   └── ffplay.exe
├── desktop_app.py
├── core.py
├── config.json
├── img/
│   ├── icon.ico
│   └── icon.png
├── srt_multiview/
│   ├── __init__.py
│   ├── __main__.py
│   ├── core.py
│   ├── paths.py
│   └── ui.py
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

### Workflow

1. **Configurer les flux** : Définir les ports SRT (ex: 9001, 9002, 9003)
2. **Mapper les écrans** : Associer chaque flux à un écran
3. **Démarrer** : Cliquer sur "Démarrer"
4. **Envoyer depuis la régie** : Utiliser OBS/vMix/etc. en mode `caller` vers `srt://IP:PORT`

### Exemple OBS

Dans OBS, créer une sortie SRT :
```
srt://192.168.1.100:9001?mode=caller&latency=120000
```

## Configuration

Le fichier `config.json` stocke :
- Les flux (nom, port, latence)
- Le mapping flux → écran
- L'option d'exclusion de l'écran principal

## Notes techniques

- ffplay est lancé avec `-fs` (fullscreen) positionné sur l'écran cible
- La latence SRT est en millisecondes (120 = 120ms par défaut)
- Les flux sont en mode `listener` (l'app attend les connexions)
