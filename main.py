#Projet : GlucoZen
#Auteurs : Emmilien Jacolin, Esteban Dubois, Nils Milleret

#main.py
from CTkMessagebox import CTkMessagebox
from tkcalendar import Calendar
import customtkinter as ctk
import utils
import model
from PIL import Image
from rapidfuzz import process, fuzz
import sys
import logging
import os 

#Configuration :

FONT = {"titre": ("Georgia", 38, "bold"),
"texte": ("Georgia", 14)}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def changer_theme(theme: str) -> None:
    """Applique le thème d'interface CustomTkinter sélectionné.

    Args:
        theme (str): Thème en français (``"Clair"``, ``"Sombre"``, ``"Systeme"``).

    Side effects:
        Appelle ``ctk.set_appearance_mode`` — effet immédiat sur toute l'interface.
    """
    theme_trad = {"Clair": "Light", "Sombre": "Dark", "Systeme": "System"} #on traduit car tkinter attend des mots anglais
    ctk.set_appearance_mode(theme_trad[theme])

def changer_theme_bouton(theme_bouton: str) -> None:
    """Applique le thème de couleur des boutons CustomTkinter.

    Args:
        theme_bouton (str): Couleur en français (``"Bleu"``, ``"Vert"``, ``"Bleu Foncé"``).

    Side effects:
        Appelle ``ctk.set_default_color_theme`` — le changement est visible
        uniquement au prochain lancement de l'application.
    """
    theme_trad = {"Bleu": "blue", "Vert": "green", "Bleu Foncé": "dark-blue"}
    ctk.set_default_color_theme(theme_trad[theme_bouton])
 
def afficher_message(label_widget, message: str, couleur: str, duree: int | None = None) -> None:
    """Affiche un message temporaire ou permanent dans un label CustomTkinter.

    Args:
        label_widget: Widget ``CTkLabel`` cible.
        message (str): Texte à afficher.
        couleur (str): Couleur du texte (ex: ``"red"``, ``"green"``).
        duree (int | None): Durée d'affichage en millisecondes avant effacement.
            Si ``None``, le message reste affiché indéfiniment.
    """
    label_widget.configure(text=message, text_color=couleur)

    if duree is not None:
        label_widget.after(duree, lambda: label_widget.configure(text=""))

def safe_insertions(entree: ctk.CTkEntry, valeur) -> None:
    """Insère une valeur dans un champ CTkEntry de manière sécurisée.
    Args:
        entree (ctk.CTkEntry): Champ cible.
        valeur: Valeur à insérer. Si ``None``, le champ reste vide.
    """
    entree.delete(0, "end")
    if valeur is not None:
        entree.insert(0, str(valeur))


class GlucoZen(ctk.CTk):
    """Contrôleur principal de l'application GlucoZen.

    Gère le cycle de vie de l'application : chargement de la configuration,
    initialisation de toutes les vues, navigation entre les pages et persistance
    des données.

    Attributes:
        configuration (model.Config): Configuration et données utilisateur chargées
            depuis le JSON au démarrage.
        aliment_liste (list[model.Aliment_obj]): Liste complète des aliments
            (personnalisés + CSV Ciqual).
        aliment_cache_recherche (list[str]): Noms normalisés pré-calculés pour
            les recherches rapidfuzz.
        frames (dict[str, ctk.CTkFrame]): Toutes les vues instanciées, indexées
            par leur nom de classe.
    """
    def __init__(self):
        super().__init__()
        #configuration fenetre principale
        self.geometry("810x775")
        self.title("GlucoZen")

        #la fenetre principale distribue tout son espace au container
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        #configure le conteneur, c'est ce qui va contenir les differentes frames
        self.container = ctk.CTkFrame(self)
        self.container.pack(side="top", fill="both", expand=True)

        #le container distribue son espace aux frames qu'il contient
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {} #dictionnaire qui va stocker les pages quand elles seront crées


        #Chargement de la config
        self.configuration = utils.load_json()
        changer_theme(self.configuration.theme)
        changer_theme_bouton(self.configuration.theme_bouton)
        self.protocol("WM_DELETE_WINDOW", self.on_quit)

        #On charge les aliments CSV
        aliments_csv = utils.charger_aliments_csv()
        self.aliment_liste = self.configuration.aliments + aliments_csv

        logging.info(f"Aliments personnalises charges : {len(self.configuration.aliments)}")
        logging.info(f"Aliments CSV charges : {len(aliments_csv)}")
        logging.info(f"Repas charges : {len(self.configuration.repas)}")
        logging.info(f"Total aliments : {len(self.aliment_liste)}")

        #on charge le cache pour la recherche :
        self.aliment_cache_recherche = []
        self.reconstruire_cache()

        #on initalise toutes les pages qu'on veut créer:
        for pages in (Accueil, Recherche_Aliment, CreationRepas, AlimentInfos,  HistoriqueRepas, CreationAlimentPersonnalise, Parametres): #page devient "lobjet" sur lequel la boucle itere, ici on met le nom de toutes les pages qui existent
            frame  = pages(self.container, self) #ici dans frame on instancie la page, dans chaque init on a en 1er le parent, puis le controlleur qui sert de pont entre chaque frame

            #on stocke les pages dans le dictionnaire:
            pages_nom = pages.__name__
            self.frames[pages_nom] = frame

            frame.grid(row=0, column=0, sticky="nsew") #on place les frames dans la grille

        utils.save_json(self.configuration) #en cas d'erreur lors du chargement (type json corrompu) on a direct un nouveau config.json propre
        self.show_frame("Accueil") #on affiche la 1ere page

    def reconstruire_cache(self) -> None:
        """Reconstruit la liste de noms normalisés utilisée par la recherche rapide.

        Doit être appelée après tout ajout ou suppression d'aliment afin que
        ``rapidfuzz`` travaille sur des données à jour.

        Side effects:
            Met à jour ``self.aliment_cache_recherche``.
        """
        self.aliment_cache_recherche = [utils.normaliser_nom(aliment.nom) for aliment in self.aliment_liste]
        
        
    def on_quit(self):
        utils.save_json(self.configuration)
        self.destroy()

    def show_frame(self, page_nom: str, mode: str | None = None, provenance: str = None) -> None:
        """Affiche la vue demandée en la faisant passer au premier plan.

        Configure la vue avant de l'afficher si nécessaire (ex : rechargement
        de l'historique, passage d'un mode à la page de recherche).

        Args:
            page_nom (str): Nom de classe de la vue à afficher
                (ex: ``"Accueil"``, ``"Recherche_Aliment"``).
            mode (str | None): Mode optionnel transmis à la vue lors de sa
                configuration. Utilisé par ``Recherche_Aliment``
                (``"recherche"`` ou ``"ajout_repas"``).
        """
        frame = self.frames[page_nom]

        if page_nom == "HistoriqueRepas":
            frame.rafraichir()

        elif page_nom == "Accueil":
            tuto = self.configuration.tuto
            self.frames["Accueil"].configurer(tuto)

        elif page_nom=="Recherche_Aliment":
            self.frames["Recherche_Aliment"].configurer(mode, provenance)

 
        frame.tkraise()

    def ouvrir_fiche_aliment(self, aliment: model.Aliment_obj, mode: str) -> None:
        """Affiche la fiche détaillée d'un aliment.

        Récupère la page AlimentInfos, la configure avec le mode donné
        (recherche libre ou ajout au repas), charge les informations
        de l'aliment pour 100 g, puis affiche la page.

        Args:
            aliment (model.Aliment_obj): Aliment à consulter.
            mode (str): Mode d'affichage (``"recherche"`` ou ``"ajout_repas"``).
        """

        page_fiche = self.frames["AlimentInfos"] #on recuperer l'instance de la page
        page_fiche.configurer(mode) #on configure la page avec le mode actuel
        page_fiche.charger_informations(aliment,1) #on charge les infos avant de les affichers dans la page, et 1 = ratio de 1 donc 100g

        self.show_frame("AlimentInfos") #on charge les informations

    def ajouter_aliment_repas(self, aliment: "model.Aliment_obj", quantite: float) -> None:
        """Transfère un aliment validé depuis AlimentInfos vers le repas en cours.

        Délègue l'ajout à ``CreationRepas.ajouter_aliment`` puis navigue
        automatiquement vers la page de création du repas.

        Args:
            aliment (model.Aliment_obj): L'aliment sélectionné par l'utilisateur.
            quantite (float): Quantité en grammes saisie dans AlimentInfos.
        """
        page_repas = self.frames["CreationRepas"]
        page_repas.ajouter_aliment(aliment, quantite)
        self.show_frame("CreationRepas")


class Accueil(ctk.CTkFrame):
    """Page d'accueil de l'application.

    Affiche le logo, un message de bienvenue personnalisé et les boutons
    de navigation vers les principales fonctionnalités. En mode tutoriel
    (premier lancement), seul le bouton de configuration est actif.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controlleur = controller

        #Frame centrale qui se centre verticalement
        self.frame_centre = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_centre.pack(expand=True, pady=(0, 80)) 

        image = ctk.CTkImage(
            light_image=Image.open(os.path.join(BASE_DIR, "data", "image.png")),
            dark_image=Image.open(os.path.join(BASE_DIR, "data", "image.png")),
            size=(220, 220)
        )
        ctk.CTkLabel(self.frame_centre, image=image, text="").pack(pady=(0, 5))

        self.label_perso = ctk.CTkLabel(self.frame_centre, text="Bienvenue !", font=FONT["titre"])
        self.label_perso.pack()

        self.label_description = ctk.CTkLabel(self.frame_centre, text="", font=FONT["texte"])
        self.label_description.pack(pady=(2, 12))

        self.frame_boutons = ctk.CTkFrame(self.frame_centre, fg_color="transparent")
        self.frame_boutons.pack()

        self.bouton_entrer = ctk.CTkButton(self.frame_boutons, text="Rechercher un aliment", font=FONT["texte"], width=280, command=lambda: controller.show_frame("Recherche_Aliment", "recherche","nouvelle"))
        self.bouton_entrer.pack(pady=4)

        self.bouton_creer_repas = ctk.CTkButton(self.frame_boutons, text="Créer un repas", font=FONT["texte"], width=280,command=lambda: controller.show_frame("CreationRepas"))
        self.bouton_creer_repas.pack(pady=4)

        self.bouton_aliment_perso = ctk.CTkButton(self.frame_boutons, text="Aliments personnalisés",font=FONT["texte"], width=280,command=lambda: controller.show_frame("CreationAlimentPersonnalise"))
        self.bouton_aliment_perso.pack(pady=4)

        self.bouton_repas = ctk.CTkButton(self.frame_boutons, text="Historique repas",font=FONT["texte"], width=280,command=lambda: controller.show_frame("HistoriqueRepas"))
        self.bouton_repas.pack(pady=4)

        #Séparateur visuel avant paramètres
        ctk.CTkLabel(self.frame_boutons, text="", height=4).pack()

        self.bouton_parametres = ctk.CTkButton(self.frame_boutons, text="Paramètres",
            font=FONT["texte"], width=280,
            fg_color="transparent", border_width=1,
            command=lambda: controller.show_frame("Parametres"))
        self.bouton_parametres.pack(pady=4)

    def configurer(self, tuto: bool) -> None:
        """Adapte l'affichage de l'accueil selon l'état du tutoriel.

        En mode tutoriel (``tuto=False``), désactive tous les boutons sauf
        Paramètres et affiche un texte d'introduction. En mode normal,
        affiche le prénom de l'utilisateur et active tous les boutons.

        Args:
            tuto (bool): ``True`` si le tutoriel est terminé (utilisation normale),
                ``False`` si c'est le premier lancement.
        """
        if not tuto:
            self.label_perso.configure(text="Bienvenue !")
            self.label_description.configure(
                text="Voici quelques informations avant de commencer : \n\n"
                    "  •  Rechercher un aliment : permet de consulter les données nutritionnelles d’un aliment.\n"
                    "  •  Créer un repas : permet de composer un repas avec les aliments disponibles dans l’application.\n"
                    "  •  Aliments personnalisés : permet de créer et gérer vos propres aliments.\n"
                    "  •  Historique des repas : permet de visualiser tous les repas enregistrés.\n"
                    "Commencez par la Configuration pour paramétrer votre profil. \n",
                justify="center")
            self.bouton_parametres.configure(text="Configuration →")

            for btn in [self.bouton_entrer, self.bouton_repas,self.bouton_creer_repas, self.bouton_aliment_perso]: #on desactive tous les boutons sauf configuration dans le tuto
                btn.configure(state="disabled")

        else:
            self.label_perso.configure(text=f"Bienvenue {self.controlleur.configuration.nom} !")
            self.label_description.configure( text="GlucoZen est une application vous permettant d'avoir accès\n aux données nutritionnelles de plus de 3 400 aliments.", justify="center")
            self.bouton_parametres.configure(text="Paramètres")

            for btn in [self.bouton_entrer, self.bouton_repas,self.bouton_creer_repas, self.bouton_aliment_perso]: #on reactive tous les boutons pour une utilisation normale
                btn.configure(state="normal")


class HistoriqueRepas(ctk.CTkFrame):
    """Page d'affichage de l'historique des repas enregistrés.

    Les repas sont triés par date décroissante (le plus récent en premier).
    Chaque entrée affiche les aliments, les totaux nutritionnels et
    l'insuline conseillée.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controlleur = controller

        self.label_titre = ctk.CTkLabel(self, text="Historique des repas", font=FONT["titre"])
        self.label_titre.pack(pady=10)

        self.liste_repas = ctk.CTkScrollableFrame(self, width=700, height=500, label_text="Repas enregistrés")
        self.liste_repas.pack(fill="both", expand=True, padx=20, pady=10)

        self.btn_retour = ctk.CTkButton(self,text="Retour Accueil", command=lambda: controller.show_frame("Accueil"))
        self.btn_retour.pack(pady = 10)

    def rafraichir(self) -> None:
        """Reconstruit l'affichage complet de la liste des repas.

        Détruit tous les widgets enfants existants puis recrée une entrée
        par repas, triée par date décroissante. Affiche un message vide
        si aucun repas n'est enregistré.

        Side effects:
            Détruit et recrée tous les widgets enfants de ``self.liste_repas``.
        """

        for widget in self.liste_repas.winfo_children():
            widget.destroy()

        repas_liste = self.controlleur.configuration.repas
        if not repas_liste:
            ctk.CTkLabel(self.liste_repas, text="Aucun repas enregistré").pack()
            return
        
        repas_trie = sorted(repas_liste, key=utils.date_cle)

        for repas in repas_trie[::-1]:  # inverse pour afficher les plus récents en premier
            frame = ctk.CTkFrame(self.liste_repas)
            frame.pack(fill="x", pady=5, padx=5)

            titre = f"{repas.date} - {repas.moment}"
            ctk.CTkLabel(frame, text=titre, font=FONT["texte"]).pack(anchor="w", padx=10, pady=5)

            #aliments
            for aliment, quantite in repas.aliments:
                txt = f"• {aliment.nom} ({quantite} g)"
                ctk.CTkLabel(frame, text=txt).pack(anchor="w", padx=20)

            #totaux
            totaux = repas.calculer_totaux()

            resume = (f"Glucides : {totaux['glucides']} g | Insuline proposé : {repas.insuline_conseille: .2f} U |Protéines : {totaux['proteines']} g | Lipides : {totaux['lipides']} g")
            ctk.CTkLabel(frame, text=resume).pack(anchor="w", padx=20, pady=(0,5))


class Recherche_Aliment(ctk.CTkFrame):
    """Page de recherche d'aliments par nom.

    Utilise rapidfuzz pour une recherche approchée sur l'ensemble de la
    base (CSV Ciqual + aliments personnalisés). Fonctionne en deux modes :
    consultation libre (``"recherche"``) ou sélection pour un repas
    (``"ajout_repas"``).
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controlleur = controller
        self.mode = "recherche" #valeur de base
        self.boutons_liste = []

        self.label_titre = ctk.CTkLabel(self, text="Rechercher un aliment", font=FONT["titre"])
        self.label_titre.pack(pady=20)

        self.entry_recherche = ctk.CTkEntry(self, placeholder_text="Tapez un aliment (ex: Pomme)...", font=FONT["texte"], width=400, height=40)
        self.entry_recherche.pack(pady = 10)
        self.entry_recherche.bind("<KeyRelease>", self.filtrer_liste)

        self.liste_aliment = ctk.CTkScrollableFrame(self, width=600, height=350, label_text="Résultats")
        self.liste_aliment.pack()

        self.btn_retour = ctk.CTkButton(self, text="Retour Accueil", command=lambda: controller.show_frame("Accueil"))
        self.btn_retour.pack(pady = 10)

    def mise_a_jour_bouton(self) -> None:
        """Synchronise le pool de boutons de résultats avec le paramètre ``nombre_resultats``.

        Si le nombre de boutons existants correspond déjà à la configuration,
        aucune action n'est effectuée (optimisation). Sinon, tous les anciens
        boutons sont détruits et un nouveau pool est créé.

        Side effects:
            Modifie ``self.boutons_liste`` et les widgets enfants de
            ``self.liste_aliment``.
        """
        max_resultats = self.controlleur.configuration.nombre_resultats
        #on verifie si le nombre de boutons a changer ou pas : 
        if len(self.boutons_liste) == max_resultats:
            return #c'est egaux donc inutile de refaire des boutons
        
        for btn in self.boutons_liste: #on detruit tout les boutons 
            btn.destroy()
        
        
        self.boutons_liste = []

        for _ in range(max_resultats):
            bouton = ctk.CTkButton(self.liste_aliment, text="", height=24, fg_color = "transparent", text_color=("black", "white"), command = lambda: None) 
            bouton.pack(fill="x")
            self.boutons_liste.append(bouton)

    def configurer(self, mode: str | None, provenance: str = None) -> None:
        """Configure la page de recherche selon le contexte d'appel.

        Adapte le titre, le bouton de retour et déclenche un premier filtrage
        à vide pour pré-remplir la liste de résultats.

        Args:
            mode (str | None): ``"ajout_repas"`` si la recherche est initiée
                depuis la création d'un repas, ``"recherche"`` ou ``None``
                pour une consultation libre.
        """
        self.mode = mode

        if mode == "ajout_repas":
            self.label_titre.configure(text="Choisir un aliment pour le repas")
            self.btn_retour.configure(text="Retour Repas", command=lambda: self.controlleur.show_frame("CreationRepas"))
        else:
            self.label_titre.configure(text="Rechercher un aliment")
            self.btn_retour.configure(text="Retour Accueil", command=lambda: self.controlleur.show_frame("Accueil"))

        if provenance == "nouvelle":
        
            self.entry_recherche.delete(0, "end")
            self.entry_recherche.configure(placeholder_text="Tapez un aliment (ex: Pomme)...")
            self.focus_set()  #enleve le curseur des champ entry pour empecher les bugs

        #forcer refresh lorsque la page Recherche est affichée pour éviter les résultats obsolètes
        self.mise_a_jour_bouton() #on met a jour les boutons de la barre de recherche 
        self.filtrer_liste("auto")


    def update_liste(self, donnee: list["model.Aliment_obj"]) -> None:
        """Met à jour l'affichage des boutons de résultats selon la liste fournie.

        Configure les boutons visibles avec le nom et la commande de chaque aliment,
        et masque les boutons en trop via ``pack_forget``.

        Args:
            donnee (list[model.Aliment_obj]): Aliments à afficher, dans l'ordre
                de pertinence. La longueur est bornée par ``self.boutons_liste``.
        """

        nbr_trouves = len(donnee)
        for i in range(nbr_trouves):
                if i < len(self.boutons_liste): #evite de depasser la taille max
                    aliment = donnee[i]
                    bouton = self.boutons_liste[i]
                    
                    #on configure le bouton 
                    bouton.configure(text=aliment.nom, command=lambda a=aliment: self.controlleur.ouvrir_fiche_aliment(a, self.mode))
                    
                    if not bouton.winfo_ismapped():
                        bouton.pack(fill="x", pady=1) #si il n'est pas affiché on l'affiche

        for j in range(nbr_trouves, len(self.boutons_liste)): #tous les boutons en plus on les cache
                bouton = self.boutons_liste[j]
                if bouton.winfo_ismapped():
                    bouton.pack_forget()
                
    def filtrer_liste(self, e) -> None:
        """Filtre et affiche les aliments correspondant à la saisie courante.

        Appelée à chaque frappe clavier via le binding ``<KeyRelease>``,
        ou manuellement avec ``e="auto"``. Si le champ est vide, affiche
        les premiers aliments de la liste. Si Entrée est pressée et qu'un
        résultat existe, ouvre directement la fiche du premier résultat.

        Args:
            e: Événement clavier tkinter ou chaîne ``"auto"`` pour un
                déclenchement programmatique sans événement réel.
        """
        nombre_resultats = self.controlleur.configuration.nombre_resultats #donne le nbr de resultats à afficher
        texte = utils.normaliser_nom(self.entry_recherche.get().strip())
        if texte =="":
            self.update_liste(self.controlleur.aliment_liste[:nombre_resultats])
            return

        donnee = self.controlleur.aliment_cache_recherche


        #Chercher les meilleurs matches
        #limit = nombre max de résultats retournés
        #score_cutoff = score mini (0–100) pour filtrer le bruit
        matches = process.extract(
                    texte,
                    donnee,
                    scorer=fuzz.WRatio,  
                    processor=None,     
                    limit=nombre_resultats,
                    score_cutoff=62,
                )

        donnee = [self.controlleur.aliment_liste[idx] for (_, _, idx) in matches] #ici on recupere uniquement les infos qui nous interessent

        if hasattr(e, "keysym") and e.keysym == "Return" and len(donnee) > 0: #si touche entrée est cliqué + que des aliments sont trouvé alors
            self.controlleur.ouvrir_fiche_aliment(donnee[0],self.mode) #ouvre la premiere fiche
            return

        self.update_liste(donnee)


class CreationRepas(ctk.CTkFrame):
    """Page de composition et d'enregistrement d'un repas.

    Permet d'ajouter des aliments depuis la recherche, de saisir une date
    via un calendrier popup, de choisir le moment de la journée et
    d'afficher les totaux nutritionnels ainsi que l'insuline conseillée.
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controlleur = controller
        self.repas_en_cours = model.Repas("Collation","")  # repas vide par défaut

        self.label_titre = ctk.CTkLabel(self, text="Créer un repas", font=FONT["titre"])
        self.label_titre.pack(pady=10)

        #Zone principale : liste à gauche, totaux à droite
        self.frame_principal = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_principal.pack(fill="both", expand=True, padx=20)

        #Colonne gauche : liste des aliments
        self.frame_gauche = ctk.CTkFrame(self.frame_principal)
        self.frame_gauche.pack(side="left", fill="both", expand=True, padx=10)

        self.liste_aliments = ctk.CTkScrollableFrame(self.frame_gauche, width=400, height=350, label_text="Aliments du repas")
        self.liste_aliments.pack(fill="both", expand=True)

        self.btn_ajouter = ctk.CTkButton(self.frame_gauche, text="+ Ajouter un aliment",command=lambda: controller.show_frame("Recherche_Aliment","ajout_repas","nouvelle"))
        self.btn_ajouter.pack(pady=5)

        #Colonne droite : totaux
        self.frame_droite = ctk.CTkFrame(self.frame_principal)
        self.frame_droite.pack(side="right", fill="y", padx=10)

        ctk.CTkLabel(self.frame_droite, text="Totaux", font=FONT["texte"]).pack(pady=5)

        self.labels_totaux = {}
        for nutriment in ["energie_kcal", "energie_kj", "proteines", "glucides", "sucres", "lipides", "fibre", "sel"]:
            label = ctk.CTkLabel(self.frame_droite, text=f"{nutriment} : 0", font=FONT["texte"], anchor="w")
            label.pack(padx=10, pady=2, anchor="w")
            self.labels_totaux[nutriment] = label

        self.label_UniteesInsuline =  ctk.CTkLabel(self.frame_droite, text=f"Unités d'insuline conseillées : N/A", anchor="w")
        self.label_UniteesInsuline.pack(padx=10, pady=2, anchor="w")

        #Bas de page : moment du repas + date + boutons
        self.frame_bas = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_bas.pack(pady=10)

        self.entry_moment = ctk.CTkOptionMenu(self.frame_bas,
            values=["Petit-dej", "Dejeuner", "Collation", "Diner"],
            command=self.changer_moment, width=150)
        self.entry_moment.set("Collation")
        self.entry_moment.pack(side="left", padx=(0, 15))  # séparateur visuel avant la date

        #séparateur visuel
        ctk.CTkLabel(self.frame_bas, text="|", text_color="gray").pack(side="left", padx=(0, 15))

        #date + bouton calendrier
        self.date_var = ctk.StringVar(value="Choisir une date")
        self.entry = ctk.CTkEntry(self.frame_bas, textvariable=self.date_var, width=140)
        self.entry.configure(state="disabled")
        self.entry.pack(side="left", padx=(0, 5))

        self.button = ctk.CTkButton(self.frame_bas, text="📅", width=30, command=self.open_calendar)
        self.button.pack(side="left")

        self.cal_window = None

        #suite
        self.label_message = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.label_message.pack()

        self.btn_enregistrer = ctk.CTkButton(self, text="Enregistrer le repas",command=self.enregistrer)
        self.btn_enregistrer.pack(pady=5)

        self.btn_retour = ctk.CTkButton(self, text="Retour Accueil", command=lambda: controller.show_frame("Accueil"))
        self.btn_retour.pack(pady=5)

    def changer_moment(self, moment: str) -> None:
        # Met à jour le moment du repas et recalcule les totaux
        self.repas_en_cours.moment = moment
        self.rafraichir()

    def ajouter_aliment(self, aliment, quantite):
        """Appelé par le contrôleur quand un aliment est confirmé depuis AlimentInfos"""
        self.repas_en_cours.ajouter_aliment(aliment, quantite)
        self.rafraichir()

    def rafraichir(self):
        """Met à jour l'affichage de la liste et des totaux"""
        #Vider la liste affichée
        for widget in self.liste_aliments.winfo_children():
            widget.destroy()

        #Reconstruire la liste
        for i, (aliment, quantite) in enumerate(self.repas_en_cours.aliments):
            ligne = ctk.CTkFrame(self.liste_aliments, fg_color="transparent")
            ligne.pack(fill="x", pady=2)

            ctk.CTkLabel(ligne, text=f"{aliment.nom} — {quantite}g", font=FONT["texte"]).pack(side="left", padx=5)

            #bouton supprimer
            idx = i  # capture pour le lambda
            ctk.CTkButton(ligne, text="✕", width=30, fg_color="red",
                command=lambda i=idx: self.supprimer_aliment(i)).pack(side="right", padx=5)

        #Mettre à jour les totaux
        totaux = self.repas_en_cours.calculer_totaux()
        noms_affichage = {
            "energie_kcal": "Énergie (kcal)", "energie_kj": "Énergie (kJ)",
            "proteines": "Protéines (g)", "glucides": "Glucides (g)",
            "sucres": "Dont sucres (g)", "lipides": "Lipides (g)",
            "fibre": "Fibres (g)", "sel": "Sel (g)"
        }
        for nutriment, label in self.labels_totaux.items():
            label.configure(text=f"{noms_affichage[nutriment]} : {totaux[nutriment]}")

        glucides_pour_1U = self.controlleur.configuration.glucides_pour_1U.get(self.entry_moment.get())
# Le reste du code gère déjà le cas None, aucun autre changement nécessaire
        if glucides_pour_1U is not None and glucides_pour_1U > 0  : #ici on calcul l'insuline coseille on fonction des parametres remplis par l'utilisateur
            insuline_conseille_calcul =  totaux["glucides"]/glucides_pour_1U
            self.label_UniteesInsuline.configure(text=f"Unitées D'insuline Conseillé : {insuline_conseille_calcul: .2f}") #arrondit a 2nbr apres la virgules
            self.repas_en_cours.insuline_conseille = insuline_conseille_calcul  #on met a jour l'objet
        else : #evite la division par 0 etc
            self.label_UniteesInsuline.configure(text=f"Unités d'insuline conseillées : N/A (voir paramètres)")
            self.repas_en_cours.insuline_conseille = 0 #on met a jour l'objet

    def supprimer_aliment(self, index: int) -> None:
        """Supprime un aliment du repas en cours et rafraîchit l'affichage.

        Args:
            index (int): Index de l'aliment dans la liste du repas.
        """

        self.repas_en_cours.retirer_aliment(index)
        self.rafraichir()

    def enregistrer(self) -> None:
        """Valide et enregistre le repas en cours dans la configuration.

        Vérifie que le repas contient au moins un aliment et qu'une date
        a été saisie. En cas de succès, sauvegarde dans le JSON, affiche
        un message de confirmation et réinitialise le repas.

        Side effects:
            Appelle ``utils.save_json``.
            Réinitialise ``self.repas_en_cours``.
        """
        if not self.repas_en_cours.aliments: #permet de ne pas enregistrer de repas vide
            afficher_message(self.label_message, "Le repas est vide !", "red")
            return

        if not self.repas_en_cours.date: #permet de forcer l'utilisateur a rentrer une date
            afficher_message(self.label_message, "Tu as oublié la date!", "red")
            return

        self.controlleur.configuration.ajouter_repas(self.repas_en_cours)

        utils.save_json(self.controlleur.configuration) #on lance la save dans le json
        afficher_message(self.label_message, "Repas enregistré !", "green", 1500)

        #Réinitialiser pour le prochain repas
        self.repas_en_cours = model.Repas(self.entry_moment.get(),"")
        self.date_var.set("Choisir une date")
        self.rafraichir()

    def open_calendar(self) -> None:
        """Ouvre une fenêtre modale de sélection de date.

        Crée un ``CTkToplevel`` centré sur la fenêtre principale contenant
        un widget ``Calendar``. Si la fenêtre est déjà ouverte, ne crée pas
        de doublon.

        Side effects:
            Crée ``self.cal_window`` et ``self.cal``.
        """
        #si la fenêtre existe déjà ne pas en ouvrir une deuxième
        if self.cal_window is not None and ctk.CTkToplevel.winfo_exists(self.cal_window):
            return

        self.cal_window = ctk.CTkToplevel(self)
        self.cal_window.title("Choisir une date")
        self.cal_window.grab_set()  #Modal: bloque le reste tant que la fenêtre est ouverte

        #création du calendrier
        self.cal = Calendar(self.cal_window, selectmode="day",date_pattern="dd/mm/yyyy")
        self.cal.pack(padx=10, pady=10)

        #bouton de validation
        ok_button = ctk.CTkButton(self.cal_window, text="OK", command=self.set_date)
        ok_button.pack(pady=(0, 10))

        #centrer la popup sur la fenêtre principale
        self.cal_window.update_idletasks()
        popup_width = self.cal_window.winfo_width()
        popup_height = self.cal_window.winfo_height()
        
        main_window = self.winfo_toplevel()
        main_x = main_window.winfo_rootx()
        main_y = main_window.winfo_rooty()
        main_width = main_window.winfo_width()
        main_height = main_window.winfo_height()
        
        x = main_x + (main_width - popup_width) // 2
        y = main_y + (main_height - popup_height) // 2
        
        self.cal_window.geometry(f"+{x}+{y}")

    def set_date(self) -> None:
        """Récupère la date choisie dans le calendrier et ferme la popup.

        Met à jour ``self.date_var`` (affichage) et ``self.repas_en_cours.date``
        (objet métier), puis détruit ``self.cal_window``.
        """
        #on recupere la date + mise a jour
        selected_date = self.cal.get_date()
        self.date_var.set(selected_date)
        #on met a jour l'objet repas :
        self.repas_en_cours.date = str(selected_date)
        #fermer la popup
        if self.cal_window is not None:
            self.cal_window.destroy()
            self.cal_window = None


class CreationAlimentPersonnalise(ctk.CTkFrame):
    """Page de création et gestion des aliments personnalisés.

    Permet de créer un nouvel aliment, de modifier un aliment existant
    (pré-chargement des champs) ou de le supprimer. Les valeurs saisies
    doivent être exprimées pour 100 g d'aliment.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controlleur = controller
        self.aliment_a_modifier = None

        self.label_info = ctk.CTkLabel(self, text="Si vous ne savez pas la valeur d'un des champs a remplir laissez la partie vide, toutes les valeurs doivent etre pour 100g d'aliment", font=FONT["texte"]) #peut etre ajouter une fonctionnalité ou la personne dit pour combien de g c'est les infos qu'elle a remplis et ca recalcul tout seul pour 100g, mais je ne sais pas si c'est vraiment utile ou pas trop
        self.label_info.pack()

        self.entry_nom = ctk.CTkEntry(self, placeholder_text="Nom de l'aliment")
        self.entry_nom.pack(pady = 3)

        self.entry_categorie = ctk.CTkEntry(self, placeholder_text="Catégorie (salade...)")
        self.entry_categorie.pack(pady = 3)

        self.entry_energiekcal = ctk.CTkEntry(self, placeholder_text="Energie (kcal)")
        self.entry_energiekcal.pack(pady = 3)

        self.entry_energiekj = ctk.CTkEntry(self, placeholder_text="Energie (kJ)")
        self.entry_energiekj.pack(pady = 3)

        self.entry_proteines = ctk.CTkEntry(self, placeholder_text="Proteines (g)")
        self.entry_proteines.pack(pady = 3)

        self.entry_glucides = ctk.CTkEntry(self, placeholder_text="Glucides (pour 100g)")
        self.entry_glucides.pack(pady = 3)

        self.entry_dont_sucres = ctk.CTkEntry(self, placeholder_text="Dont sucres (g)")
        self.entry_dont_sucres.pack(pady = 3)

        self.entry_lipides = ctk.CTkEntry(self, placeholder_text="Lipides (g)")
        self.entry_lipides.pack(pady = 3)

        self.entry_fibre = ctk.CTkEntry(self, placeholder_text="Fibre (g)")
        self.entry_fibre.pack(pady = 3)

        self.entry_sel = ctk.CTkEntry(self, placeholder_text="Sel (g)")
        self.entry_sel.pack(pady = 3)

        self.frame_liste_perso = ctk.CTkScrollableFrame(self, width=400, height=200, label_text="Aliments personnalisés")
        self.frame_liste_perso.pack(pady=10, padx=10, fill="x")
        self.update_liste_perso()

        self.label_message = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.label_message.pack(pady=10)

        self.btn_enregistrer = ctk.CTkButton(self, text="Enregistrer", command=lambda: self.enregistrer())
        self.btn_enregistrer.pack(pady = 5)

        self.btn_retour = ctk.CTkButton(self, text="Retour Accueil", command=lambda: controller.show_frame("Accueil"))
        self.btn_retour.pack()



    def valider_champ(self, entry: ctk.CTkEntry, nom_champ: str,min_val: float | None = None, max_val: float | None = None) -> tuple[bool, float | None]:
        """Valide la valeur d'un champ numérique optionnel.

        Si le champ est vide, retourne ``(True, None)`` (valeur absente tolérée).
        Sinon vérifie que la valeur est un nombre dans l'intervalle autorisé.

        Args:
            entry (ctk.CTkEntry): Champ à valider.
            nom_champ (str): Nom affiché dans le message d'erreur.
            min_val (float | None): Valeur minimale acceptée, ou ``None`` sans borne.
            max_val (float | None): Valeur maximale acceptée, ou ``None`` sans borne.

        Returns:
            tuple[bool, float | None]: ``(True, valeur)`` si valide,
                ``(False, None)`` si invalide.

        Side effects:
            Affiche un message d'erreur dans ``self.label_message`` si invalide.
        """
        val_str = entry.get().strip()

        if not val_str:
            return True, None

        val = utils.convertir_valeur(val_str)
        if val is None:
            afficher_message(self.label_message, f"{nom_champ} doit être un nombre valide", "red")
            return False, None

        if min_val is not None and val < min_val:
            afficher_message(self.label_message, f"{nom_champ} doit être au moins {min_val}", "red")
            return False, None

        if max_val is not None and val > max_val:
            afficher_message(self.label_message, f"{nom_champ} doit être au plus {max_val}", "red")
            return False, None

        return True, val

    def update_liste_perso(self) -> None:
        """Reconstruit la liste affichée des aliments personnalisés.

        Détruit les widgets existants et recrée une ligne par aliment avec
        les boutons d'édition (✎) et de suppression (✕).

        Side effects:
            Détruit et recrée tous les widgets enfants de ``self.frame_liste_perso``.
        """
        for widget in self.frame_liste_perso.winfo_children():
            widget.destroy()

        for aliment in self.controlleur.configuration.aliments:
            ligne = ctk.CTkFrame(self.frame_liste_perso, fg_color="transparent")
            ligne.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(ligne, text=aliment.nom, font=FONT["texte"]).pack(side="left", padx=5)
            ctk.CTkButton(ligne, text="✎", width=30,command=lambda a=aliment: self.charger_aliment(a)).pack(side="right", padx=2) #bouton edit
            ctk.CTkButton(ligne, text="✕", width=30, fg_color="red",command=lambda a=aliment: self.supprimer_aliment(a)).pack(side="right", padx=2) #bouton supprimer

    def charger_aliment(self, aliment: "model.Aliment_obj") -> None:
        """Charge un aliment existant dans les champs du formulaire pour édition.

        Pré-remplit chaque champ avec les données de l'aliment. Les valeurs
        absentes (``None``) affichent uniquement le placeholder.

        Args:
            aliment (model.Aliment_obj): Aliment à modifier.

        Side effects:
            Définit ``self.aliment_a_modifier``.
        """
        champs = [
            (self.entry_nom, aliment.nom, "Nom de l'aliment"),
            (self.entry_categorie, aliment.categorie, "Catégorie (salade...)"),
            (self.entry_energiekcal, aliment.energie_kcal, "Energie (kcal)"),
            (self.entry_energiekj, aliment.energie_kj, "Energie (kJ)"),
            (self.entry_proteines, aliment.proteines, "Proteines (g)"),
            (self.entry_glucides, aliment.glucides, "Glucides (pour 100g)"),
            (self.entry_dont_sucres, aliment.sucres, "Dont sucres (g)"),
            (self.entry_lipides, aliment.lipides, "Lipides (g)"),
            (self.entry_fibre, aliment.fibre, "Fibre (g)"),
            (self.entry_sel, aliment.sel, "Sel (g)")
        ]

        for entry, valeur, placeholder in champs:
            entry.delete(0, 'end') #on supprime le contenu du widget
            if valeur is not None and valeur != "":
                entry.insert(0, str(valeur))  #si y a quelque chose a mettre comme donnée on le remplit
            entry.configure(placeholder_text=placeholder) #sinon on met le placeholder

        #On stocke l'aliment chargé pour savoir si c'est une modification
        self.aliment_a_modifier = aliment


    def enregistrer(self) -> None:
        """Valide le formulaire et enregistre l'aliment (création ou modification).

        Vérifie l'unicité du nom (insensible à la casse), valide chaque champ
        numérique, puis crée ou met à jour l'aliment dans la configuration.

        Side effects:
            Appelle ``utils.save_json`` et ``GlucoZen.reconstruire_cache``.
            Vide le formulaire via ``self.vider_champs``.
        """
        nom = self.entry_nom.get().strip()
        if not nom:
            afficher_message(self.label_message, "Le nom de l'aliment est obligatoire!", "red")
            return
        
        ismodification = self.aliment_a_modifier is not None #permet de savoir si c'est un aliment qu'on est en train de modifier ou non

        if ismodification :
            aliment = self.aliment_a_modifier
        else : 
            aliment = model.Aliment_obj(nom)
 
        #vérifier doublon (CSV + perso), en excluant l'aliment en cours d'édition
        for aliment_exist in self.controlleur.aliment_liste:
            if aliment_exist.nom.lower() == nom.lower():
                if ismodification and aliment_exist == aliment:
                    continue
                afficher_message(self.label_message, f"L'aliment {nom} existe déjà!", "red")
                return

        #valider chaque champ
        success, energie_kcal = self.valider_champ(self.entry_energiekcal, "Énergie (kcal)", 0)
        if not success:
            return
        success, energie_kj = self.valider_champ(self.entry_energiekj, "Énergie (kJ)", 0)
        if not success:
            return
        success, proteines = self.valider_champ(self.entry_proteines, "Protéines", 0, 100)
        if not success:
            return
        success, glucides = self.valider_champ(self.entry_glucides, "Glucides", 0, 100)
        if not success:
            return
        success, sucres = self.valider_champ(self.entry_dont_sucres, "Sucres", 0, 100)
        if not success:
            return
        success, lipides = self.valider_champ(self.entry_lipides, "Lipides", 0, 100)
        if not success:
            return
        success, fibre = self.valider_champ(self.entry_fibre, "Fibre", 0, 100)
        if not success:
            return
        success, sel = self.valider_champ(self.entry_sel, "Sel", 0, 100)
        if not success:
            return

        if not ismodification:
            self.controlleur.configuration.add_aliment(aliment)
            self.controlleur.aliment_liste.append(aliment) #on ajoute l'element a la liste
        else : 
            self.aliment_a_modifier = None #si c'est  une modif on 'sort' de l'edition de l'elemnt 

        #remplir les données
        donnees = {
            "nom": nom,
            "categorie": self.entry_categorie.get().strip() or "Non spécifié",
            "energie_kcal": energie_kcal,
            "energie_kj": energie_kj,
            "proteines": proteines,
            "glucides": glucides,
            "sucres": sucres,
            "lipides": lipides,
            "fibre": fibre,
            "sel": sel
        }

        aliment.remplir_data_json(donnees) #on remplit avec les données au dessus

        utils.save_json(self.controlleur.configuration) #on lance la save dans le json
        afficher_message(self.label_message, "Aliment enregistré avec succès!", "green")

        self.vider_champs()
        self.controlleur.reconstruire_cache() #met a jour le cache pour la recherche
        self.update_liste_perso()


    def supprimer_aliment(self, aliment: "model.Aliment_obj") -> None:
        """Supprime un aliment personnalisé de la configuration et des listes.

        Si l'aliment supprimé était en cours d'édition, quitte le mode édition
        et vide le formulaire. Met à jour la liste globale et le cache de
        recherche.

        Args:
            aliment (model.Aliment_obj): Aliment à supprimer.

        Side effects:
            Appelle ``utils.save_json`` et ``GlucoZen.reconstruire_cache``.
        """
        supprimé = self.controlleur.configuration.supprimer_aliment(aliment)

        #si on supprime l'aliment qu'on est en train d'edit on sort du mode d'edition 
        if self.aliment_a_modifier is not None and self.aliment_a_modifier is aliment:
            self.aliment_a_modifier = None
            self.vider_champs()

        #mise à jour de la liste globale utilisées par la recherche
        self.controlleur.aliment_liste = [a for a in self.controlleur.aliment_liste if a.nom != aliment.nom]

        if supprimé:
            utils.save_json(self.controlleur.configuration)
            self.update_liste_perso()
            self.controlleur.reconstruire_cache() #met a jour le cache pour la recherche
            afficher_message(self.label_message, f"Aliment '{aliment.nom}' supprimé!", "green")
        else:
            afficher_message(self.label_message, f"Impossible de supprimer '{aliment.nom}'", "red")

    def vider_champs(self):
        """Vide tous les champs après enregistrement, réaffiche les placeholders."""
        champs = [
            (self.entry_nom, "Nom de l'aliment"),
            (self.entry_categorie, "Catégorie (salade...)"),
            (self.entry_energiekcal, "Energie (kcal)"),
            (self.entry_energiekj, "Energie (kJ)"),
            (self.entry_proteines, "Proteines (g)"),
            (self.entry_glucides, "Glucides (pour 100g)"),
            (self.entry_dont_sucres, "Dont sucres (g)"),
            (self.entry_lipides, "Lipides (g)"),
            (self.entry_fibre, "Fibre (g)"),
            (self.entry_sel, "Sel (g)")
        ]

        for entry, placeholder in champs:
            entry.delete(0, 'end')
            entry.configure(placeholder_text=placeholder)

        self.label_message.configure(text="")
        self.focus_set()  #enleve le curseur des champ entry pour empecher les bugs


class Parametres(ctk.CTkFrame):
    """Page de configuration du profil utilisateur et des préférences.

    Organisée en cartes thématiques : Profil (nom), Apparence (thème,
    nombre de résultats) et Insuline (glucides par unité selon le moment).
    Inclut un bouton de réinitialisation complète avec confirmation.
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controlleur = controller

        #titre
        ctk.CTkLabel(self, text="Paramètres", font=FONT["titre"]).pack(pady=(15, 10))

        #zone scrollable pour tout le contenu
        self.frame_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frame_scroll.pack(fill="both", expand=True, padx=20, pady=5)

        #ligne 1: profil + apparence cote à cote
        ligne1 = ctk.CTkFrame(self.frame_scroll, fg_color="transparent")
        ligne1.pack(fill="x", pady=(0, 12))
        ligne1.grid_columnconfigure(0, weight=1)
        ligne1.grid_columnconfigure(1, weight=1)

        #carte profil
        carte_profil = ctk.CTkFrame(ligne1)
        carte_profil.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ctk.CTkLabel(carte_profil, text="PROFIL", font=("Baskerville Old Face", 11), text_color="gray").pack(anchor="w", padx=15, pady=(12, 6))

        ctk.CTkLabel(carte_profil, text="Votre nom", font=FONT["texte"]).pack(anchor="w", padx=15)
        vnom = self.controlleur.configuration.nom
        self.entry_nom = ctk.CTkEntry(carte_profil, placeholder_text="Votre nom")
        self.entry_nom.pack(fill="x", padx=15, pady=(3, 15))
        if vnom:
            safe_insertions(self.entry_nom, vnom)

        #carte apparence
        carte_apparence = ctk.CTkFrame(ligne1)
        carte_apparence.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        ctk.CTkLabel(carte_apparence, text="APPARENCE", font=("Baskerville Old Face", 11),text_color="gray").pack(anchor="w", padx=15, pady=(12, 6))

        ctk.CTkLabel(carte_apparence, text="Thème de l'interface :", font=FONT["texte"]).pack(anchor="w", padx=15)
        self.entry_theme = ctk.CTkOptionMenu(carte_apparence, values=["Clair", "Sombre", "Systeme"], command=changer_theme, width=200)
        self.entry_theme.set(controller.configuration.theme)
        self.entry_theme.pack(anchor="w", padx=15, pady=(3, 8))

        ctk.CTkLabel(carte_apparence, text="Thème des boutons :", font=FONT["texte"]).pack(anchor="w", padx=15)
        self.entry_theme_boutons = ctk.CTkOptionMenu(carte_apparence, values=["Bleu", "Vert", "Bleu Foncé"], command=changer_theme_bouton, width=200)
        self.entry_theme_boutons.set(controller.configuration.theme_bouton)
        self.entry_theme_boutons.pack(anchor="w", padx=15, pady=(3, 8))

        valeur_actuelle = self.controlleur.configuration.nombre_resultats
        self.label_slider = ctk.CTkLabel(carte_apparence, text=f"Nombre de résultats : {valeur_actuelle}", font=FONT["texte"])
        self.label_slider.pack(anchor="w", padx=15)
        self.slider = ctk.CTkSlider(carte_apparence, from_=10, to=70, command=self.slider_event)
        self.slider.set(valeur_actuelle)
        self.slider.pack(fill="x", padx=15, pady=(3, 15))

        #carte insuline
        carte_insuline = ctk.CTkFrame(self.frame_scroll)
        carte_insuline.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(carte_insuline, text="INSULINE", font=("Baskerville Old Face", 11), text_color="gray").pack(anchor="w", padx=15, pady=(12, 2))
        ctk.CTkLabel(carte_insuline, text="Glucides pour 1 unité d'insuline rapide, selon le moment de la journée", font=("Baskerville Old Face", 13), text_color="gray").pack(anchor="w", padx=15, pady=(0, 8))

        #4 champs cote a cote
        frame_4champs = ctk.CTkFrame(carte_insuline, fg_color="transparent")
        frame_4champs.pack(fill="x", padx=15, pady=(0, 15))
        for i in range(4):
            frame_4champs.grid_columnconfigure(i, weight=1)

        vglucides_pour_1U = self.controlleur.configuration.glucides_pour_1U

        ctk.CTkLabel(frame_4champs, text="Petit-dej", font=FONT["texte"]).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.entry_G_pour_1U_petitdej = ctk.CTkEntry(frame_4champs, placeholder_text="g")
        self.entry_G_pour_1U_petitdej.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(frame_4champs, text="Déjeuner", font=FONT["texte"]).grid(row=0, column=1, sticky="w", padx=(0, 8))
        self.entry_G_pour_1U_dej = ctk.CTkEntry(frame_4champs, placeholder_text="g")
        self.entry_G_pour_1U_dej.grid(row=1, column=1, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(frame_4champs, text="Collation", font=FONT["texte"]).grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.entry_G_pour_1U_collation = ctk.CTkEntry(frame_4champs, placeholder_text="g")
        self.entry_G_pour_1U_collation.grid(row=1, column=2, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(frame_4champs, text="Dîner", font=FONT["texte"]).grid(row=0, column=3, sticky="w")
        self.entry_G_pour_1U_diner = ctk.CTkEntry(frame_4champs, placeholder_text="g")
        self.entry_G_pour_1U_diner.grid(row=1, column=3, sticky="ew")

        if vglucides_pour_1U:
            safe_insertions(self.entry_G_pour_1U_petitdej, vglucides_pour_1U.get("Petit-dej"))
            safe_insertions(self.entry_G_pour_1U_dej, vglucides_pour_1U.get("Dejeuner"))
            safe_insertions(self.entry_G_pour_1U_collation, vglucides_pour_1U.get("Collation"))
            safe_insertions(self.entry_G_pour_1U_diner, vglucides_pour_1U.get("Diner"))

        self.label_message = ctk.CTkLabel(self.frame_scroll, text="", font=("Arial", 12))
        self.label_message.pack(pady=5)

        #boutons en bas
        frame_boutons = ctk.CTkFrame(self.frame_scroll, fg_color="transparent")
        frame_boutons.pack(fill="x", pady=(5, 15))
        frame_boutons.grid_columnconfigure(0, weight=1)
        frame_boutons.grid_columnconfigure(1, weight=1)
        frame_boutons.grid_columnconfigure(2, weight=0)

        ctk.CTkButton(frame_boutons, text="Enregistrer",command=self.enregistrer).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(frame_boutons, text="Retour Accueil",command=lambda: controller.show_frame("Accueil")).grid(row=0, column=1, sticky="ew", padx=(0, 6))

        ctk.CTkButton(frame_boutons, text="Reset", fg_color="transparent", border_width=1, border_color="red", text_color="red", hover_color="#ffe5e5", command=self.fenetre_confirmation).grid(row=0, column=2, padx=(0, 0))
    
    def slider_event(self, value: float) -> None:
        # Met à jour l'affichage du label pendant le glissement
        self.label_slider.configure(text=f"Nombre de résultats : {int(value)}")

    def reset(self) -> None:
        """Réinitialise complètement la configuration et ferme l'application.

        Remplace la configuration par des valeurs par défaut, sauvegarde
        le JSON vierge puis termine le processus.

        Side effects:
            Écrase ``data/config.json``.
            Appelle ``sys.exit()``.
        """
        self.controlleur.configuration = model.Config(None, "Clair", "Vert", {}, [], [], False, 30)
        utils.save_json(self.controlleur.configuration)
        sys.exit()

    def fenetre_confirmation(self) -> None:
        """Affiche une boîte de dialogue de confirmation avant le reset.

        Ouvre un ``CTkMessagebox`` bloquant. Déclenche ``self.reset()``
        uniquement si l'utilisateur confirme.
        """
        msg = CTkMessagebox(
            title="Êtes-vous sûr ?",
            message="Voulez-vous vraiment remettre l'application à zéro ? (l'application sera fermée)",
            icon="warning",
            option_1="Oui",
            option_2="Non"
        )
        if msg.get() == "Oui":
            self.reset()

    def enregistrer(self) -> None:
        """Valide et sauvegarde les paramètres saisis dans la configuration.

        Vérifie que le nom est renseigné et que les quatre champs insuline
        contiennent des valeurs numériques valides. Gère les messages de
        retour selon le contexte (premier lancement, changement de thème bouton,
        sauvegarde normale).

        Side effects:
            Met à jour ``self.controlleur.configuration``.
            Appelle ``utils.save_json``.
        """
        nom = self.entry_nom.get().strip()
        theme = self.entry_theme.get()
        theme_bouton = self.entry_theme_boutons.get()

        glucides_pour_1U_petit_dej = self.entry_G_pour_1U_petitdej.get()
        glucides_pour_1U_dej = self.entry_G_pour_1U_dej.get()
        glucides_pour_1U_collation = self.entry_G_pour_1U_collation.get()
        glucides_pour_1U_diner = self.entry_G_pour_1U_diner.get()

        nombre_resultats = int(self.slider.get())

        if not nom:
            afficher_message(self.label_message, "Vous n'avez pas entré de nom !", "red")
            return

        glucides = [
            ("Petit-dej", glucides_pour_1U_petit_dej),
            ("Dejeuner",  glucides_pour_1U_dej),
            ("Collation", glucides_pour_1U_collation),
            ("Diner",     glucides_pour_1U_diner),
        ]
        valeurs_float = {}
        for moment, valeur in glucides:
            if not valeur:
                afficher_message(self.label_message, f"Le champ '{moment}' est obligatoire !", "red")
                return
            try:
                valeurs_float[moment] = float(valeur.strip())
            except (ValueError, TypeError):
                afficher_message(self.label_message, f"Valeur invalide pour '{moment}' !", "red")
                return

        boutton_change = theme_bouton != self.controlleur.configuration.theme_bouton
        phase_tuto = not self.controlleur.configuration.tuto

        self.controlleur.configuration.nom = nom
        self.controlleur.configuration.theme = theme
        self.controlleur.configuration.theme_bouton = theme_bouton
        self.controlleur.configuration.glucides_pour_1U = valeurs_float
        self.controlleur.configuration.nombre_resultats = nombre_resultats

        if phase_tuto:
            self.controlleur.configuration.tuto = True

        utils.save_json(self.controlleur.configuration) #on enregistre

        if phase_tuto:
            afficher_message(self.label_message,
                "Configuration terminée ! Retournez à l'accueil :)", "green", 8000)
        elif boutton_change:
            afficher_message(self.label_message,
                "Sauvegardé ! Le thème des boutons s'appliquera au prochain lancement.", "green", 3000)
        else:
            afficher_message(self.label_message, "Sauvegardé avec succès !", "green", 3000)


class AlimentInfos(ctk.CTkFrame):
    """Page de consultation des données nutritionnelles d'un aliment.

    Affiche les valeurs pour 100 g par défaut, avec un champ de calcul
    permettant de recalculer pour une quantité arbitraire. En mode
    ``"ajout_repas"``, propose un bouton pour ajouter l'aliment au repas
    en cours avec la quantité saisie.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controlleur = controller
        self.aliment_obj = None

        #nom de l'aliment en titre
        self.nom_aliment = ctk.CTkLabel(self, text="Nom Aliment", font=FONT["titre"], anchor="w")
        self.nom_aliment.pack(pady=10, padx=20)

        #frame ou on place les données
        self.donnees_aliment_frame = ctk.CTkFrame(self)
        self.donnees_aliment_frame.pack(pady=10, padx=20, fill="both", expand=True)

        #la on met les labels pour chaque infos qu'on veut afficher
        self.categorie = ctk.CTkLabel(self.donnees_aliment_frame, text="Inconnu", font=FONT["texte"], anchor="w")
        self.categorie.pack(padx=10, pady=2, anchor="w")

        self.energie_kcal = ctk.CTkLabel(self.donnees_aliment_frame, text="Inconnu", font=FONT["texte"], anchor="w")
        self.energie_kcal.pack(padx=10, pady=2, anchor="w")

        self.energie_kJ = ctk.CTkLabel(self.donnees_aliment_frame, text="Inconnu", font=FONT["texte"], anchor="w")
        self.energie_kJ.pack(padx=10, pady=2, anchor="w")

        self.proteines = ctk.CTkLabel(self.donnees_aliment_frame, text="Inconnu", font=FONT["texte"], anchor="w")
        self.proteines.pack(padx=10, pady=2, anchor="w")

        self.glucides = ctk.CTkLabel(self.donnees_aliment_frame, text="Inconnu", font=FONT["texte"], anchor="w")
        self.glucides.pack(padx=10, pady=2, anchor="w")

        self.dont_sucre = ctk.CTkLabel(self.donnees_aliment_frame, text="Inconnu", font=FONT["texte"], anchor="w")
        self.dont_sucre.pack(padx=10, pady=2, anchor="w")

        self.lipides = ctk.CTkLabel(self.donnees_aliment_frame, text="Inconnu", font=FONT["texte"], anchor="w")
        self.lipides.pack(padx=10, pady=2, anchor="w")

        self.fibres = ctk.CTkLabel(self.donnees_aliment_frame, text="Inconnu", font=FONT["texte"], anchor="w")
        self.fibres.pack(padx=10, pady=2, anchor="w")

        self.sel = ctk.CTkLabel(self.donnees_aliment_frame, text="Inconnu", font=FONT["texte"], anchor="w")
        self.sel.pack(padx=10, pady=2, anchor="w")


        
        #label d'instruction
        self.label_instruction_calcul = ctk.CTkLabel(self, text="Tapez une quantité en gramme (ex: 120)...", font=FONT["texte"])
        self.label_instruction_calcul.pack()

        #entry + bouton sur la même ligne
        self.frame_calcul = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_calcul.pack(pady=5)

        self.entry_calcul = ctk.CTkEntry(self.frame_calcul, font=FONT["texte"], width=120, height=36)
        self.entry_calcul.pack(side="left", padx=(0, 5))
        self.entry_calcul.bind("<Return>", lambda e: self.calcul_ratio(self.entry_calcul.get()))

        self.calcul_poid = ctk.CTkButton(self.frame_calcul, text="Calculer", width=90, height=36,
            command=lambda: self.calcul_ratio(self.entry_calcul.get()))
        self.calcul_poid.pack(side="left")

        #bouton_ajouter_au_repas
        self.btn_ajout_repas = ctk.CTkButton(self, text="Ajouter l'aliment au repas", command=lambda: self.valider_ajout_repas())
        self.btn_ajout_repas.pack()
        
        #retour
        self.btn_retour = ctk.CTkButton(self, text="Retour Accueil", command=lambda: controller.show_frame("Accueil"))
        self.btn_retour.pack(pady=20)

    def charger_informations(self, aliment_obj: "model.Aliment_obj", ratio: float) -> None:
        """Affiche les données nutritionnelles de l'aliment pondérées par le ratio.

        Met à jour tous les labels de la page. Les valeurs absentes (``None``)
        sont affichées sous la forme ``"—"``.

        Args:
            aliment_obj (model.Aliment_obj): Aliment à afficher.
            ratio (float): Facteur multiplicatif appliqué à toutes les valeurs
                (ex: ``1`` pour 100 g, ``1.5`` pour 150 g).
        """
 
        self.aliment_obj = aliment_obj
        self.nom_aliment.configure(text=str(aliment_obj.nom))

        self.categorie.configure(text=f"Catégorie : {aliment_obj.categorie}")

        parametres = [(aliment_obj.energie_kcal,"Énergie (kcal)",self.energie_kcal),
                      (aliment_obj.energie_kj,"Énergie (kJ)",self.energie_kJ),
                      (aliment_obj.proteines,"Protéines (g)",self.proteines),
                      (aliment_obj.glucides,"Glucides (g)", self.glucides),
                      (aliment_obj.sucres,"Dont sucres (g)",self.dont_sucre),
                      (aliment_obj.lipides,"Lipides (g)",self.lipides),
                      (aliment_obj.fibre,"Fibres (g)",self.fibres),
                      (aliment_obj.sel,"Sel (g)",self.sel)]

        for data,cat_text, cat in parametres:
            if data is not None and data != "":
                donnees = round(data*ratio,2)
            else :
                donnees = "—"
            cat.configure(text=f"{cat_text} : {donnees}")


    def configurer(self, mode: str) -> None:
        """Prépare la page fiche aliment selon le contexte de navigation.

        Réinitialise le champ de saisie, adapte le libellé d'instruction et
        affiche ou masque le bouton d'ajout au repas.

        Args:
            mode (str): ``"ajout_repas"`` pour permettre l'ajout au repas en cours,
                ``"recherche"`` pour une consultation sans ajout.
        """
        self.entry_calcul.delete(0, "end")
        self.entry_calcul.configure(border_color="gray")

        if mode == "ajout_repas":
            self.btn_retour.configure(text="Retour a la page de recherche", command=lambda: self.controlleur.show_frame("Recherche_Aliment","ajout_repas"))
            self.label_instruction_calcul.configure(text="Entrez la quantité pour le repas (g)")
            if not self.btn_ajout_repas.winfo_ismapped():
                self.btn_ajout_repas.pack(before=self.btn_retour)
        else:
            self.btn_retour.configure(text="Retour a la page de recherche", command=lambda: self.controlleur.show_frame("Recherche_Aliment","recherche"))
            self.label_instruction_calcul.configure(text="Tapez une quantité en gramme (ex: 120)...")
            self.btn_ajout_repas.pack_forget()

    def valider_ajout_repas(self) -> None:
        """Valide la quantité saisie et envoie l'aliment au repas en cours.

        Vérifie que la saisie est un nombre strictement positif. En cas d'erreur,
        la bordure du champ passe en rouge. En cas de succès, délègue au
        contrôleur et vide le champ.

        Side effects:
            Appelle ``GlucoZen.ajouter_aliment_repas``.
            Modifie la bordure de ``self.entry_calcul``.
        """
        poid_brut = self.entry_calcul.get().strip()
        if not poid_brut:
            self.entry_calcul.configure(border_color="red")
            return
        try:
            quantite = float(utils.convertir_valeur(poid_brut))
            if quantite <= 0:
                raise ValueError
            self.entry_calcul.configure(border_color="gray")
        except (ValueError, TypeError):
            self.entry_calcul.configure(border_color="red")
            return

        self.controlleur.ajouter_aliment_repas(self.aliment_obj, quantite)
        self.entry_calcul.delete(0, "end")

    def calcul_ratio(self, poid: str) -> None:
        """Recalcule et affiche les valeurs nutritionnelles pour la quantité saisie.

        Convertit la chaîne saisie en float, vérifie qu'elle est strictement
        positive, puis recharge les informations avec le ratio correspondant.
        En cas de saisie invalide, colore la bordure du champ en rouge.

        Args:
            poid (str): Quantité brute saisie par l'utilisateur (en grammes).

        Side effects:
            Appelle ``self.charger_informations``.
            Modifie la bordure de ``self.entry_calcul``.
        """
        try:
            poid = float(utils.convertir_valeur(poid))  #accepte virgule et point, rejette les lettres
            if poid <= 0:
                raise ValueError
            self.entry_calcul.configure(border_color="gray")
        except (ValueError, TypeError):
            self.entry_calcul.configure(border_color="red")
            return
 
        self.charger_informations(self.aliment_obj, poid / 100)

#Lancement
app = GlucoZen()
app.mainloop()


"""
Ressources :
Documentation customtkinter : https://customtkinter.tomschimansky.com/documentation/
Tuto tkinter orienté objet : https://www.geeksforgeeks.org/python/tkinter-application-to-switch-between-different-page-frames/
Pour afficher fenetre de confirmation : https://coderslegacy.com/python/customtkinter-messagebox-using-ctkmessagebox/
"""