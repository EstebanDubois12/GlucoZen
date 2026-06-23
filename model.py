#Projet : GlucoZen
#Auteurs : Emmilien Jacolin, Esteban Dubois, Nils Milleret
#model.py
import utils

class Config:
    """Représente la configuration complète de l'application.

    Regroupe les préférences utilisateur (thème, profil, paramètres insuline),
    la liste des aliments personnalisés et l'historique des repas.

    Attributes:
        nom (str | None): Prénom de l'utilisateur.
        theme (str): Thème d'interface (``"Clair"``, ``"Sombre"``, ``"Systeme"``).
        theme_bouton (str): Couleur des boutons (``"Bleu"``, ``"Vert"``, ``"Bleu Foncé"``).
        glucides_pour_1U (dict[str, float]): Glucides (g) par unité d'insuline,
            par moment de la journée (clés : ``"Petit-dej"``, ``"Dejeuner"``,
            ``"Collation"``, ``"Diner"``).
        nombre_resultats (int): Nombre maximum de résultats affichés en recherche.
        aliments (list[Aliment_obj]): Aliments personnalisés de l'utilisateur.
        repas (list[Repas]): Historique des repas enregistrés.
        tuto (bool): ``True`` si le tutoriel de premier lancement est terminé.
    """
    def __init__(self, nom, theme,theme_bouton, glucides_pour_1U, aliments,repas, tuto,nombre_resultats):
        self.tuto = tuto #False si l'user n'a pas de "compte" si c'est false on peut dire qu'on le force à en crer un
        self.nom = nom
        self.theme = theme
        self.theme_bouton = theme_bouton
        self.glucides_pour_1U = glucides_pour_1U #dico qui pour chaque moment continent  le nbr de glucides
        self.nombre_resultats = nombre_resultats
        self.aliments = aliments
        self.repas = repas if repas is not None else [] 

    def add_aliment(self, aliment: "Aliment_obj") -> bool:
        """Ajoute un aliment personnalisé à la configuration.

        Vérifie l'absence de doublon par nom avant l'ajout.

        Args:
            aliment (Aliment_obj): Aliment à ajouter.

        Returns:
            bool: ``True`` si l'ajout a réussi, ``False`` si un aliment
                du même nom existe déjà.
        """
        if any(a.nom == aliment.nom for a in self.aliments):
            return False
        
        self.aliments.append(aliment)
        return True

    def supprimer_aliment(self, aliment: "Aliment_obj") -> bool:
        """Supprime un aliment personnalisé par correspondance de nom.

        Args:
            aliment (Aliment_obj): Aliment à supprimer.

        Returns:
            bool: ``True`` si l'aliment a été trouvé et supprimé, ``False`` sinon.
        """
        for i, al in enumerate(self.aliments):
            if al.nom == aliment.nom:
                self.aliments.pop(i)
                return True
        return False

    def ajouter_repas(self, repas: "Repas") -> None:
        """Ajoute un repas à l'historique.

        Args:
            repas (Repas): Repas à enregistrer.
        """
        self.repas.append(repas)

    def to_dict(self) -> dict:
        """Sérialise l'objet en dictionnaire pour la persistance JSON."""
        data = {}

        data["parametres"] = {
            "nom": self.nom,
            "theme": self.theme,
            "theme_bouton": self.theme_bouton,
            "glucides_pour_1U" : self.glucides_pour_1U,
            "tuto": self.tuto,
            "nombre_resultats": self.nombre_resultats
        }
        data["aliments_perso"] = [al.to_dict() for al in self.aliments]
        data["repas"] = [r.to_dict() for r in self.repas]

        return data


#_______________________________________________________

class Aliment_obj:
    """Représente un aliment avec ses valeurs nutritionnelles pour 100 g.

    Peut être instancié depuis le CSV Ciqual (``remplir_data_csv``)
    ou depuis un dictionnaire JSON (``remplir_data_json``).

    Attributes:
        nom (str): Nom de l'aliment.
        categorie (str): Catégorie alimentaire.
        energie_kcal (float | None): Énergie en kilocalories.
        energie_kj (float | None): Énergie en kilojoules.
        proteines (float | None): Protéines en grammes.
        glucides (float | None): Glucides totaux en grammes.
        sucres (float | None): Dont sucres en grammes.
        lipides (float | None): Lipides en grammes.
        fibre (float | None): Fibres alimentaires en grammes.
        sel (float | None): Sel en grammes.
    """
    def __init__ (self, nom):
        self.categorie = ""
        self.nom = nom
        #On initialise à None pour savoir si la donnée existe ou non
        self.energie_kj = None
        self.energie_kcal = None
        self.proteines = None
        self.glucides = None
        self.lipides = None
        self.sucres = None
        self.fibre = None
        self.sel = None

    def remplir_data_csv(self, ligne: list[str]) -> None:
        """Remplit les attributs nutritionnels depuis une ligne du CSV Ciqual.

        Extrait les colonnes pertinentes (groupe, nom, énergie, macronutriments)
        et convertit les valeurs via ``utils.convertir_valeur``.

        Args:
            ligne (list[str]): Ligne brute du CSV (liste de chaînes).
                Les indices utilisés sont : 4, 7, 9, 10, 15, 16, 17, 18, 26, 49.
        """
        colonne_csv = [4,7,9,10,15,16,17,18,26,49] # Colonnes Ciqual  : groupe, nom, énergie_kJ, énergie_kcal, protéines, glucides, lipides, sucres, fibres, sel
        #On récupère toutes les valeurs brutes
        valeurs_brutes = [ligne[i] for i in colonne_csv]

        #Assignation avec conversion immédiate
        self.categorie = valeurs_brutes[0]
        self.nom = valeurs_brutes[1]

        #Conversion des données numériques
        self.energie_kj = utils.convertir_valeur(valeurs_brutes[2])
        self.energie_kcal = utils.convertir_valeur(valeurs_brutes[3])
        self.proteines = utils.convertir_valeur(valeurs_brutes[4])
        self.glucides = utils.convertir_valeur(valeurs_brutes[5])
        self.lipides = utils.convertir_valeur(valeurs_brutes[6])
        self.sucres = utils.convertir_valeur(valeurs_brutes[7])
        self.fibre = utils.convertir_valeur(valeurs_brutes[8])
        self.sel = utils.convertir_valeur(valeurs_brutes[9])

    def remplir_data_json(self, donnee: dict) -> None:
        """Remplit les attributs nutritionnels depuis un dictionnaire JSON.

        Utilisé au chargement de la configuration pour reconstruire les
        aliments personnalisés et les aliments sauvegardés dans les repas.

        Args:
            donnee (dict): Dictionnaire avec les clés ``"nom"``, ``"categorie"``,
                ``"energie_kcal"``, ``"energie_kj"``, ``"proteines"``,
                ``"glucides"``, ``"sucres"``, ``"lipides"``, ``"fibre"``, ``"sel"``.
        """
        self.categorie = donnee["categorie"]
        self.nom = donnee["nom"]
        self.energie_kj = donnee["energie_kj"]
        self.energie_kcal = donnee["energie_kcal"]
        self.proteines = donnee["proteines"]
        self.glucides = donnee["glucides"]
        self.lipides = donnee["lipides"]
        self.sucres = donnee["sucres"]
        self.fibre = donnee["fibre"]
        self.sel = donnee["sel"]

    def to_dict(self) -> dict:
        """Sérialise l'objet en dictionnaire pour la persistance JSON."""
        dico = {
            "nom": self.nom,
            "categorie": self.categorie,
            "energie_kcal": self.energie_kcal,
            "energie_kj": self.energie_kj,
            "proteines": self.proteines,
            "glucides": self.glucides,
            "sucres": self.sucres,
            "lipides": self.lipides,
            "fibre": self.fibre,
            "sel": self.sel
        }
        return dico

#_______________________________________________________

class Repas:
    """Représente un repas composé d'aliments et de leurs quantités.

    Stocke les aliments ajoutés par l'utilisateur avec leurs quantités,
    calcule les totaux nutritionnels et sérialise l'ensemble pour la
    persistance JSON.

    Attributes:
        moment (str): Moment de la journée (``"Petit-dej"``, ``"Dejeuner"``,
            ``"Collation"``, ``"Diner"``).
        date (str): Date du repas au format ``"jj/mm/aaaa"``.
        aliments (list[tuple[Aliment_obj, float]]): Liste des paires
            (aliment, quantité en grammes).
        insuline_conseille (float): Nombre d'unités d'insuline calculées
            pour ce repas. Vaut ``0`` si les paramètres insuline ne sont
            pas configurés.
    """
    def __init__(self, moment,date): 
        self.moment = moment  # "Petit-dej", "Dejeuner" etc.
        self.aliments = []    #données nutrionelles completes, comme ca en cas de suppression d'aliment perso ils sont tjr enregistré de ce coté et pas de soucis
        self.date = date #date du repas 
        self.insuline_conseille = 0 #ici on  enregistrera le nbr d'unitées conseillées  

    def ajouter_aliment(self, aliment: "Aliment_obj", quantite: float) -> None:
        """Ajoute un aliment au repas avec sa quantité.

        Args:
            aliment (Aliment_obj): Aliment à ajouter.
            quantite (float): Quantité consommée en grammes.
        """
        self.aliments.append((aliment, quantite))

    def retirer_aliment(self, index: int) -> None:
        """Retire un aliment de la liste par son index.

        Args:
            index (int): Index de l'aliment dans ``self.aliments``.

        Raises:
            IndexError: Si ``index`` est hors des limites de la liste.
        """
        self.aliments.pop(index)

    def calculer_totaux(self) -> dict[str, float]:
        """Calcule les totaux nutritionnels du repas en tenant compte des quantités.

        Chaque nutriment est pondéré par le ratio ``quantite / 100``
        par rapport aux valeurs de référence pour 100 g.

        Returns:
            dict[str, float]: Dictionnaire des totaux arrondis à 2 décimales.
                Clés : ``"energie_kcal"``, ``"energie_kj"``, ``"proteines"``,
                ``"glucides"``, ``"sucres"``, ``"lipides"``, ``"fibre"``, ``"sel"``.
        """

        totaux = {"energie_kcal": 0, "energie_kj": 0, "proteines": 0,"glucides": 0, "sucres": 0, "lipides": 0, "fibre": 0, "sel": 0}
        for aliment, quantite in self.aliments:
            ratio = quantite / 100
            totaux["energie_kcal"] += (aliment.energie_kcal or 0) * ratio
            totaux["energie_kj"] += (aliment.energie_kj or 0) * ratio
            totaux["proteines"] += (aliment.proteines or 0) * ratio
            totaux["glucides"] += (aliment.glucides or 0) * ratio
            totaux["sucres"] += (aliment.sucres or 0) * ratio
            totaux["lipides"] += (aliment.lipides or 0) * ratio
            totaux["fibre"] += (aliment.fibre or 0) * ratio
            totaux["sel"] += (aliment.sel or 0) * ratio

        return {k: round(v, 2) for k, v in totaux.items()}
    
    def to_dict(self) -> dict:
        """Sérialise le repas en dictionnaire pour la persistance JSON.

        Chaque aliment est sauvegardé avec sa fiche nutritionnelle complète
        (indépendante de la base de données), ce qui garantit l'intégrité
        de l'historique même si l'aliment est supprimé ultérieurement.

        Returns:
            dict: Dictionnaire avec les clés ``"moment"``, ``"date"``,
                ``"nom"``, ``"insuline"`` et ``"aliments"``.
        """
        repas_nom = f"{self.date} - {self.moment}" #le nom que le repas va avoir
        return {
            "moment": self.moment,
            "date" : self.date,
            "nom":repas_nom,
            "insuline": self.insuline_conseille,
            "aliments": [
                {"fiche_aliment":al.to_dict(), "quantite": qte}
                for al, qte in self.aliments
            ]
        }