# GlucoZen
GlucoZen est une application de bureau qui permet de consulter les données nutritionnelles de plus de 3 400 aliments (base Ciqual) et de composer des repas en calculant automatiquement les totaux glucidiques, protéiques, lipidiques et la dose d’insuline conseillée.

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
- Base de données : Table Ciqual 2025 (ANSS)  
- Éditeur : Visual Studio Code / Pyzo  
- Logo : Adobe Photoshop  

---

## Versions

La version actuelle est la **V1.0** – première version stable regroupant toutes les fonctionnalités principales :

- Recherche d’aliments (avec cache)  
- Création et gestion d’aliments personnalisés  
- Composition de repas avec calcul nutritionnel et suggestion d’insuline  
- Historique des repas  
- Personnalisation du thème (clair/sombre/systeme)  
- Persistance des données (JSON)  

---

## Auteurs

- Emilien Jacolin  
- Esteban Dubois  
- Nils Milleret  

---

### Licence

Ce projet est distribué sous la licence **Apache 2.0**.  
Voir le fichier **LICENSE** pour plus de détails.
