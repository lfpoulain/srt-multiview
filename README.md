# SRT Multiview

Application locale Python pour router et lire plusieurs flux SRT sur des écrans Windows, avec une émission **OMT** intégrée pour publier un écran sur le réseau.

## Fonctionnalités

- **Réception SRT** : écoute plusieurs flux SRT en mode `listener` (la régie envoie en `caller`)
- **Réception OMT** : ajoute un flux dont la source est une publication OMT découverte sur le LAN
- **Routage SRT → UDP multicast** : un seul flux SRT peut alimenter plusieurs `ffplay` via une sortie multicast `ffmpeg`
- **Source par flux** : SRT direct, OMT, ou Route
- **Contrôle par flux** : Bouton ▶/⏹, statut (arrêté / démarrage / en cours), purge des logs
- **Rotation par flux** : 0° / 90° / 180° / 270°
- **Modes d'affichage** : fit / fill / stretch
- **Émission OMT** : capture un écran (gdigrab) et le publie comme source OMT (`libomt`, codec VMX)
- **Multi-écrans** : chaque flux occupe un écran Windows en plein écran
- **Exclusion écran principal** : option pour réserver l'écran de travail
- **Auto-mapping** : assigne automatiquement les flux aux écrans disponibles
- **Reset global** : réinitialise toute la configuration et stoppe lectures/émission/routes
- **Découverte OMT** : modal de scan des sources OMT visibles sur le LAN
- **Configuration persistante** : flux, mapping, routes, options et paramètres d'émission sauvegardés (atomique + backup en cas de JSON corrompu)

## Prérequis

1. **Python 3.10+**
2. **`ffplay.exe`** et **`ffmpeg.exe`** dans le dossier `bin/` du projet (uniquement en exécution locale)
3. Le `ffmpeg.exe` **doit être compilé avec `libomt`** pour que l'émission et la réception OMT fonctionnent (les builds standards de FFmpeg n'incluent pas libomt — voir [openmediatransport/ffmpeg](https://github.com/openmediatransport)).

### Installation des binaires FFmpeg

1. Télécharger un build FFmpeg avec `libomt` (ou compiler depuis le fork OMT).
2. Copier `ffmpeg.exe` et `ffplay.exe` dans `bin/`.

## Arborescence

```
srt-multiview/
├── bin/
│   ├── ffmpeg.exe
│   └── ffplay.exe
├── build_exe.ps1
├── img/
│   ├── icon.ico
│   └── icon.png
├── pyproject.toml
├── srt_multiview/
│   ├── __init__.py
│   ├── __main__.py
│   ├── core.py
│   ├── paths.py
│   ├── styles.py
│   └── ui.py
├── srt_multiview.spec
└── requirements.txt
```

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
- Le workflow **utilise directement le contenu de `bin/`** versionné dans le repo (FFmpeg + DLLs `libomt`/`libvmx`). Plus de download externe → la Nightly est OMT-aware out of the box.
- Le job de build vérifie la présence de `ffmpeg.exe`, `ffplay.exe`, `libomt.dll`, `libomtnet.dll`, `libvmx.dll` et échoue si l'un manque.
- ⚠ Si tu remplaces `bin/ffmpeg.exe` par une build standard (sans `libomt`), l'EXE compile toujours mais l'émission/réception OMT renverra `Unknown encoder/muxer 'libomt'`.

Pour télécharger l'exe :

1. Aller sur l'onglet **Releases** du repo
2. Ouvrir **Nightly**
3. Télécharger `SRT-MultiView.exe`

### Workflow — Réception

1. **Ajouter un flux** (« + Ajouter un flux »)
2. **Choisir la source** :
   - **SRT** : l'app écoute `srt://0.0.0.0:PORT` (listener)
   - **OMT** : saisir le nom de la source ou utiliser 🔍 pour la découvrir sur le LAN
   - **Route** : sélectionner une route existante (voir section Routage)
3. **Mapper l'écran** : associer le flux à un écran via le sélecteur
4. **Démarrer** : ▶ sur le flux (ou « ▶ Démarrer tout »)
5. **Envoyer depuis la régie** : OBS/vMix/etc. en `caller` vers `srt://IP:PORT`

> 💡 Si un écran assigné n'est pas détecté au lancement (en veille, replug…), l'application **conserve** le binding et affiche `⚠ Écran absent` dans le sélecteur. Dès que l'écran réapparaît, le flux peut être démarré normalement — plus de mapping perdu au redémarrage.

### Workflow — Émission OMT

1. **Sélectionner l'écran** à capturer dans le panneau « 📡 Émission OMT »
2. **Configurer** :
   - **Nom OMT** : nom publié sur le réseau (visible par les receveurs)
   - **FPS** : 1 à 60
   - **Pixel format** : `UYVY 4:2:2` (recommandé), `BGRA` (4:4:4 avec alpha) ou `YUV422P10LE` (10-bit)
   - **Clock output** : option `libomt -clock_output 1`
3. **Émettre** : « ▶ Émettre »

L'audio n'est pas (encore) géré côté émetteur.

### Exemple OBS — émission SRT vers SRT Multiview

Dans OBS, créer une sortie SRT :

```
srt://192.168.1.100:9001?mode=caller&latency=120000
```

## Configuration

La configuration est stockée dans le fichier utilisateur, dans le dossier dédié de l'application :

- Windows : `%APPDATA%\srt-multiview\config.json`
- macOS / Linux : `~/.config/srt-multiview/config.json` (les binaires y sont aussi cherchés en fallback)

Sauvegarde **atomique** (fichier temporaire + `os.replace` + `fsync`). Si le JSON existant est corrompu au chargement, il est renommé en `config.json.bak` avant la création d'un nouveau fichier vierge.

Champs principaux :

- **Flux** : nom, source (`srt` / `omt` / `route`), port/latence SRT, source OMT, mode d'affichage, rotation
- **Mapping** : flux → écran (préservé même si l'écran disparaît temporairement)
- **Noms d'écrans** personnalisés
- **Routes** : port SRT in, latence, sortie UDP multicast
- **Options** : exclure écran principal, auto-start réception/émission
- **Émission OMT** : écran, nom, fps, pixel format, clock output, reference level

## Routage (SRT → UDP multicast)

Le routage **duplique** un flux SRT en sortie UDP multicast pour qu'il soit lu par plusieurs `ffplay`.

- Une **Route** écoute un port SRT (listener)
- `ffmpeg` repack en MPEG-TS et sort vers `udp://@239.x.x.x:PORT`
- Plusieurs écrans peuvent lire la même route en parallèle

Note : le démarrage UDP peut prendre quelques secondes. L'UI affiche un état **« démarrage »** (loader) pendant ce temps.

## Notes techniques

- `ffplay` est lancé avec `-fs` (fullscreen) positionné via `-left`/`-top` sur l'écran cible
- `ffmpeg gdigrab` capture l'écran ; le pipeline OMT est sans encodeur applicatif (le codec VMX est appliqué par `libomt` lui-même, via `wrapped_avframe`)
- Latence SRT en millisecondes (120 ms par défaut)
- Les flux SRT entrants sont en `listener` ; l'émission OMT publie en TCP sur la plage **6400-6600** (DNS-SD via Bonjour/Avahi pour la découverte)
- Le décodage côté receveur peut être forcé en CPU ou délégué à un accélérateur matériel (`dxva2`, `h264_cuvid`, `h264_qsv`, `h264_amf`, ou détection auto)

## Licence

Srt-MultiView © 2026 by LFPoulain — licence **CC BY-NC-SA 4.0**.
Voir https://creativecommons.org/licenses/by-nc-sa/4.0/.
