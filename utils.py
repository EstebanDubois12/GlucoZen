#Projet : GlucoZen
#Auteurs : Emmilien Jacolin, Esteban Dubois, Nils Milleret
#utils.py

import os
import logging
import platform
import time
import csv
import json
import unicodedata
import model
from datetime import datetime

os_windows = platform.system() == 'Windows'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(BASE_DIR, "data", "config.json")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "data", "app.log"), mode='a'),
        logging.StreamHandler()
    ]
)
logging.getLogger('PIL').setLevel(logging.WARNING)

#_________________________________________

def charger_aliments_csv() -> list:
    """Charge les aliments depuis le fichier CSV Ciqual.

    Lit le fichier ``data/Table Ciqual 2025_FR_2025_11_03.csv`` encodé en cp1252
    et instancie un objet ``Aliment_obj`` par ligne valide.

    Returns:
        list[model.Aliment_obj]: Liste des aliments chargés.
            Retourne une liste vide si le fichier est absent ou illisible.
    """
    chemin_csv = normaliser_chemin(os.path.join(BASE_DIR, "data", "Table Ciqual 2025_FR_2025_11_03.csv"))

    if not os.path.exists(chemin_csv):
        logging.error(f"Fichier CSV introuvable : {chemin_csv}")
        return []

    aliments = []
    try: #on essaie d'ouvrir le fichier 
        with open(chemin_csv, 'r', encoding='cp1252') as file:
            reader = csv.reader(file, delimiter=';')
            next(reader)  #saute l'en-tête
            for row in reader:
                if len(row) > 7:
                    obj = model.Aliment_obj(row[7])
                    obj.remplir_data_csv(row)
                    aliments.append(obj)
    except Exception as e:
        logging.error(f"Erreur lors de la lecture du CSV : {e}")
        return []

    return aliments


def load_json() -> "model.Config":
    """Charge la configuration de l'application depuis le fichier JSON.

    Reconstruit un objet ``Config`` complet (paramètres, aliments personnalisés,
    historique des repas) à partir de ``data/config.json``.

    En cas de fichier absent, un ``Config`` par défaut est retourné (premier lancement).
    En cas de fichier corrompu, un backup horodaté est créé dans
    ``data/backups_erreurs/`` et un ``Config`` vide est retourné.

    Returns:
        model.Config: Configuration chargée ou configuration par défaut réinitialisée.

    Side effects:
        Peut créer un fichier de backup et supprimer ``config.json`` si corrompu.
    """

    if not config_existe(): #1er lancement
        return model.Config(None, "Clair", "Vert", {}, [],[], False,30) #reset

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, ValueError):
        logging.warning("Fichier config.json corrompu, réinitialisation...")
        backup_and_reset("Erreur de lecture du fichier JSON")
        return model.Config(None, "Clair", "Vert", {}, [],[], False,30) #reset

    try:
        #Chargement des paramètres
        parametres = data.get("parametres", {})
        nom = parametres.get("nom")
        theme  = parametres.get("theme", "Clair")
        theme_bouton  = parametres.get("theme_bouton", "Vert")
        glucides_pour_1U = parametres.get("glucides_pour_1U",{})
        tuto =  parametres.get("tuto",False)
        nombre_resultats = parametres.get("nombre_resultats",30)

        #Chargement des aliments personnalisés
        aliments_perso = []
        for aliment_json in data.get("aliments_perso", []):
            obj = model.Aliment_obj(aliment_json["nom"])
            obj.remplir_data_json(aliment_json)
            aliments_perso.append(obj)

        #Chargement des repas
        liste_repas = []
        for repas_json in data.get("repas",[]):
            repas_obj = model.Repas(repas_json.get("moment","Collation"),repas_json.get("date","jj/mm/aaaa"))  
            repas_obj.insuline_conseille = repas_json.get("insuline", 0) or 0
            for aliment_data in repas_json.get("aliments",[]): #on recupere tous les aliments qui sont dans le repas
                fiche_aliment = aliment_data["fiche_aliment"]
                aliment_obj = model.Aliment_obj(fiche_aliment["nom"]) #on cree un objet aliment avec le "nom"
                aliment_obj.remplir_data_json(fiche_aliment) #on remplit l'objet crée juste avant avec les données qu'on a recupéré 
                repas_obj.ajouter_aliment(aliment_obj,aliment_data["quantite"]) #on ajoute l'objet crée au repas avec sa quantité en plus

            liste_repas.append(repas_obj) #on ajoute le repas crée à la liste des repas

        return model.Config(nom, theme, theme_bouton, glucides_pour_1U, aliments_perso, liste_repas,tuto,nombre_resultats)
    except Exception as e: #ici le reset permet d'annuler toutes les erreurs possibles 
        backup_and_reset(f"Erreur lors du chargement : {e}")
        return model.Config(None, "Clair", "Vert", {}, [],[], False,30) #reset


def backup_and_reset(raison: str) -> None:
    """Crée une sauvegarde horodatée de config.json puis le supprime.

    Utilisée en cas de fichier corrompu ou d'erreur de chargement.
    Le backup est placé dans ``data/backups_erreurs/``.

    Args:
        raison (str): Description de l'erreur ayant déclenché la réinitialisation.
            Utilisée uniquement pour le log.

    Side effects:
        Déplace ``data/config.json`` vers ``data/backups_erreurs/config_backup_<timestamp>.json``.
        Journalise le résultat via ``logging``.
    """
    if os.path.exists(path):
        backup_dir = os.path.join(os.path.dirname(path), "backups_erreurs")  
        os.makedirs(backup_dir, exist_ok=True) #si le dossier n'existe pas il est crée, il permettra de stocker les json 

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_nom = f"config_backup_{timestamp}.json" #on crée le nom du fichier
        backup_path = os.path.join(backup_dir, backup_nom)
        try:
            os.rename(path, backup_path)  #renomme directement le json et il est mis au bon endroit
            logging.info(f"Réinitialisé ({raison}). Backup : {backup_path}")
        except Exception as e:
            logging.error(f"Erreur lors du backup : {e}")


def save_json(config: "model.Config") -> None:
    """
    Convertit l'objet de configuration en dictionnaire puis l'enregistre
    au format JSON dans le fichier ``data/config.json``.

    Args:
        config (model.Config): Configuration à sauvegarder.


    Side effects:
        Écrase le contenu de ``data/config.json`` s'il existe déjà.
        En cas d'erreur d'écriture, un message d'erreur est journalisé.
    """
    data = config.to_dict()

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Sauvegarde reussie dans {path}")
    except Exception as e:
        logging.error(f"Erreur lors de l'écriture du JSON : {e}")

def config_existe() -> bool:
    """Vérifie si le fichier de configuration existe sur le disque.

    Returns:
        bool: ``True`` si ``data/config.json`` est présent, ``False`` sinon.
    """
    return os.path.exists(path)
#_________________________________________

def normaliser_chemin(chemin: str) -> str:
    """Normalise un chemin de fichier selon le système d'exploitation.

    Sur Windows, applique ``os.path.normcase`` pour rendre le chemin
    insensible à la casse. Sur les autres OS, applique uniquement
    ``os.path.normpath``.

    Args:
        chemin (str): Chemin brut à normaliser.

    Returns:
        str: Chemin normalisé adapté à l'OS courant.
    """
    nv_chemin = os.path.normpath(chemin)
    if os_windows:
        nv_chemin = os.path.normcase(nv_chemin)
    return nv_chemin

def normaliser_nom(nom: str) -> str:
    """Normalise une chaîne pour la recherche (supprime accents, met en minuscule).

    Args:
        nom (str): Chaîne à normaliser.

    Returns:
        str: Chaîne normalisée sans accents, en minuscules, sans espaces multiples.
    """
    nom = unicodedata.normalize('NFKD', nom).encode('ASCII', 'ignore').decode('ASCII')
    return ' '.join(nom.lower().split())

def convertir_valeur(valeur: str) -> float | None:
    """Convertit une valeur brute du CSV Ciqual en float Python.

    Gère les cas spéciaux du format Ciqual : séparateur décimal virgule,
    préfixe ``<``, valeurs ``traces``, tiret ou chaîne vide.

    Args:
        valeur (str): Chaîne brute à convertir (ex: ``"12,5"``, ``"< 0.5"``,
            ``"traces"``, ``"-"``).

    Returns:
        float | None: La valeur numérique, ou ``None`` si non convertible.
    """
    if not valeur:
        return None

    #Nettoyage de la chaine
    valeur = valeur.strip()

    #Gestion des cas spéciaux du Ciqual
    if valeur == "-" or valeur == "" or "trace" in valeur.lower():
        return None

    #Remplacement de la virgule par un point (format US pour Python)
    valeur = valeur.replace(',', '.')

    #Gestion du symbole < (ex: "< 0.5" devient 0.5)
    valeur = valeur.replace('<', '').strip()

    try:
        return float(valeur)
    except ValueError:
        return None
    
            
def date_cle(repas_obj: "model.Repas") -> datetime:
    """Retourne une clé de tri temporelle à partir de la date d'un repas.

    Utilisée comme ``key=`` dans ``sorted()`` pour trier les repas par date.
    En cas de date invalide ou manquante, retourne ``datetime.min`` pour
    placer le repas en fin de liste.

    Args:
        repas_obj (model.Repas): Repas dont on veut extraire la date.

    Returns:
        datetime: Date parsée au format ``%d/%m/%Y``, ou ``datetime.min``
            si le format est invalide.
    """
    try:
        return datetime.strptime(repas_obj.date, "%d/%m/%Y")
    except Exception:
        return datetime.min