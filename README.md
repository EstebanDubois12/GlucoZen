# GlucoZen
GlucoZen est une application de bureau conçue pour simplifier le suivi alimentaire des personnes diabétiques. Elle permet de rechercher des aliments issus de la base Ciqual 2025, de composer des repas et d'obtenir automatiquement leur composition nutritionnelle.

---

## Distinction

Projet sélectionné pour la phase territoriale du Trophée NSI 2026 et récompensé par le Prix de l'Originalité.

Cette sélection récompense un projet informatique développé dans le cadre de l'enseignement de spécialité Numérique et Sciences Informatiques, évalué pour son intérêt, sa conception et sa réalisation technique.

---

## Fonctionnalités principales

- Recherche de plus de 3 400 aliments issus de la base Ciqual
- Création et gestion d'aliments personnalisés
- Composition de repas avec calcul nutritionnel automatique
- Estimation indicative d'insuline selon les paramètres configurés
- Historique des repas
- Personnalisation du thème (clair/sombre/système)
- Sauvegarde persistante des données
  
---

# Pré-requis
Avant de lancer l’application, assurez-vous que l’arborescence suivante est respectée :


```
GlucoZen/
├── main.py
├── model.py
├── utils.py
├── data/
│   ├── image.png
│   └── Table Ciqual 2025_FR_2025_11_03.csv
└── requirements.txt
```

Les trois fichiers Python (`main.py`, `model.py`, `utils.py`) doivent se trouver dans le dossier racine du projet.

Le dossier `data/` doit contenir le logo (`image.png`) et la table Ciqual.

---

## Démarrage

**1) Installer les dépendances**  
Ouvrez un terminal dans le dossier du projet et exécutez :

```bash
pip install -r requirements.txt
```

**2) Lancer l’application**

```bash
python main.py
```

---

## Fabriqué avec

- Langage : Python 3.10+  
- Bibliothèques : customtkinter, tkcalendar, rapidfuzz, Pillow, CTkMessagebox  
- Base de données : Table Ciqual 2025 (ANSES)  
- Éditeur : Visual Studio Code / Pyzo  
- Logo : Adobe Photoshop  

---

## Version actuelle

La version actuelle est la **V1.0**, première version stable regroupant l'ensemble des fonctionnalités principales.

---

## Auteurs

- Emilien Jacolin  
- Esteban Dubois  
- Nils Milleret  

---

### Licence

Ce projet est distribué sous la licence **Apache 2.0**.  
Voir le fichier **LICENSE** pour plus de détails.
