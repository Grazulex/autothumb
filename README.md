# AutoThumb

**Générateur automatique de thumbnails YouTube avec IA**

AutoThumb est un outil CLI qui génère automatiquement des thumbnails attractives pour vos vidéos YouTube en utilisant Claude Vision d'Anthropic pour analyser intelligemment votre vidéo et créer des miniatures optimisées.

## Fonctionnalités

- **Extraction intelligente de frames** : Extrait automatiquement les meilleures frames de votre vidéo
- **Analyse par IA** : Utilise Claude Vision pour sélectionner l'image la plus engageante
- **Génération de texte** : Crée automatiquement un texte accrocheur basé sur votre prompt
- **Personnalisation** : Styles prédéfinis pour différents types de contenu
- **Export haute qualité** : Génère des thumbnails en 1280x720 et 1920x1080

## Prérequis

- Docker et Docker Compose
- Une clé API Anthropic (Claude)

## Installation

1. **Cloner le projet** :
```bash
git clone <votre-repo>
cd AutoThumb
```

2. **Configurer l'API key** :
```bash
cp .env.example .env
# Éditer .env et ajouter votre ANTHROPIC_API_KEY
```

3. **Construire l'image Docker** :
```bash
docker-compose build
```

## Utilisation

### Méthode 1 : Via Docker Compose (Recommandé)

```bash
# Placer vos vidéos dans le dossier ./videos
mkdir -p videos
cp /chemin/vers/video.mp4 ./videos/

# Générer un thumbnail
docker-compose run --rm autothumb autothumb \
  --video /app/videos/video.mp4 \
  --prompt "Tutoriel Python pour débutants" \
  --style youtube \
  --output /app/output/thumbnail.jpg
```

### Méthode 2 : Mode interactif

```bash
# Lancer un shell dans le container
docker-compose run --rm autothumb /bin/bash

# À l'intérieur du container
autothumb --video /app/videos/video.mp4 --prompt "Mon super titre"
```

## Options CLI

```bash
autothumb [OPTIONS]

Options:
  --video PATH          Chemin vers la vidéo à traiter [requis]
  --prompt TEXT         Description/thème pour le thumbnail [requis]
  --style TEXT          Style prédéfini (youtube, minimalist, bold, tech)
  --output PATH         Chemin de sortie du thumbnail
  --resolution TEXT     Résolution (1280x720 ou 1920x1080) [défaut: 1280x720]
  --frames INTEGER      Nombre de frames à extraire [défaut: 10]
  --font-size INTEGER   Taille de la police [défaut: 72]
  --help                Afficher l'aide
```

## Exemples

### Thumbnail pour tutoriel
```bash
autothumb --video tuto.mp4 \
  --prompt "Apprendre Python en 10 minutes" \
  --style youtube
```

### Thumbnail minimaliste
```bash
autothumb --video demo.mp4 \
  --prompt "Clean Code Tips" \
  --style minimalist \
  --resolution 1920x1080
```

### Avec options avancées
```bash
autothumb --video video.mp4 \
  --prompt "DevOps avec Docker" \
  --style tech \
  --frames 15 \
  --font-size 96 \
  --output custom_thumb.jpg
```

## Architecture

```
AutoThumb/
├── src/
│   └── autothumb/
│       ├── core/           # Modules principaux
│       │   ├── video.py    # Extraction de frames
│       │   ├── analyzer.py # Analyse IA avec Claude Vision
│       │   └── composer.py # Génération du thumbnail
│       ├── cli/            # Interface CLI
│       │   └── main.py
│       └── utils/          # Utilitaires
├── tests/                  # Tests unitaires
├── examples/               # Exemples de vidéos
├── output/                 # Thumbnails générés
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Développement

### Installation en mode développement

```bash
# Dans le container
pip install -e .
```

### Lancer les tests

```bash
pytest tests/
```

## Workflow

1. **Extraction** : FFmpeg extrait N frames clés de la vidéo
2. **Analyse** : Claude Vision analyse chaque frame et sélectionne la meilleure
3. **Texte** : Claude génère un texte accrocheur basé sur votre prompt
4. **Composition** : Pillow compose l'image finale avec texte stylisé
5. **Export** : Thumbnail sauvegardé en haute qualité

## Limitations

- Nécessite une connexion internet (API Claude)
- Coût API proportionnel au nombre de frames analysées
- Formats vidéo supportés : MP4, AVI, MOV, MKV (tout format supporté par FFmpeg)

## Roadmap

- [ ] Support de styles personnalisés via JSON
- [ ] Mode batch pour traiter plusieurs vidéos
- [ ] Preview interactif avant génération finale
- [ ] Support des templates de texte
- [ ] Cache des analyses pour éviter les coûts répétés

## Licence

MIT

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou un PR.
