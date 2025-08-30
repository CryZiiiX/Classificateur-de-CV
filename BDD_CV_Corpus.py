# /***************************************************************************************************************************************************************************************************************************
# Nom du fichier : BDD_CV_Corpus.py
# Rôle du fichier : Ce fichier s'occupe de sauvegarder et de gérer la base de donnée SupaBase, où l'on sauvegarde les informations qui servent a l'entrainement du modèle de classification de CV.

# Auteur : Maxime BRONNY
# Version : V1
# Licence : Réalisé dans le cadre des cours "Fouille de données, Ingéniérie des langues, Développement logiciel libre, IA & Apprentisage" L3 INFORMATIQUE IED
# Usage : Un paquetage a été mit en place pour l'utiliser veuillez utiliser dans un système debian la commande suivante :
#           - INSTALLATION DU PAQUET GÉNÉRÉ
#               - sudo apt install ./cv-classifier_1.0-1_all.deb

#           Puis exécute ton programme avec :
#               - cv-classifier
# ***************************************************************************************************************************************************************************************************************************/



# ****************************************************** # 
# --- LIBRAIRIES UTILISÉES POUR STOCKER LA BDD FLAIR --- # 
# ****************************************************** # 



import os                             # interaction avec l'OS et variables d'environnement
from supabase import create_client, Client  # client pour interagir avec Supabase
from datetime import datetime        # manipulation et formatage des dates/heures



# ******************************* # 
# --- PARAMÈTRES DE CONNEXION --- # 
# ******************************* #



SUPABASE_URL: str = os.environ.get(
    "SUPABASE_URL",
    "https://bkisnmipaqzfludqicjz.supabase.co"
)
SUPABASE_KEY: str = os.environ.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJraXNubWlwYXF6Zmx1ZHFpY2p6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU0MjczMjQsImV4cCI6MjA2MTAwMzMyNH0.aWTJ83bJux6TIzUztdeH9MK_HnvuSIiEI3wpHM_FEmw"
)



# ********************************************************************** # 
# --- INITIALISATION DU CLIENT 'SUPABASE' POUR INTÉRAGIR AVEC LA BDD --- # 
# ********************************************************************** #



supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



# ************************************************************ # 
# --- FONCTIONS QUI CHARGE LE CORPUS DEPUIS UN FICHIER TXT --- # 
# ************************************************************ #



def load_corpus_from_file(filename="data/cv_corpus.txt"):
    """
    Charge le corpus depuis un fichier .txt, y compris les sections (#)
    et les paires 'phrase|categorie'. Retourne une liste de tuples.
    """
    corpus = []
    try:
        # Lecture et parsing ligne par ligne
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line.startswith("#"):
                    # Section marquée par '#'
                    corpus.append((line, "Titre"))
                elif "|" in line:
                    # Entrée formatée 'texte|catégorie'
                    parts = line.split("|")
                    corpus.append((parts[0].strip(), parts[1].strip()))
        print("Corpus chargé avec succès depuis le fichier.")
    except FileNotFoundError:
        print(f"Le fichier {filename} est introuvable.")
    return corpus



# *********************************************************************************** # 
# --- FONCTIONS DE NETTOYAGE DE LA BDD SUPABASE UTILISÉE POUR EVITER LES DOUBLONS --- # 
# *********************************************************************************** #



def clear_corpus_table():
    """
    Vide la table 'cv_corpus' dans Supabase pour éviter les doublons.
    """
    # Suppression de toutes les lignes dont l'id est différent de 0
    response = supabase.table("cv_corpus") \
                       .delete().neq("id", 0) \
                       .execute()
    # Feedback sur l'opération
    if response.data:
        print("Table 'cv_corpus' vidée avec succès.")
    elif response.error:
        print(f"Erreur lors de la suppression : {response.error}")
    else:
        print("Une réponse inattendue a été reçue lors de la suppression.")



# ********************************************************* # 
# --- FONCTIONS DE SAUVEGARDE DU FICHIER D'ENTRAINEMENT --- # 
# ********************************************************* #



def save_corpus_to_supabase(corpus):
    """
    Insère chaque tuple (phrase, catégorie) du corpus dans Supabase,
    en ajoutant la date de création.
    """
    # Mise en forme des données pour insertion
    data = [
        {
            "phrase": sample[0],
            "categorie": sample[1],
            "date_created": datetime.now().isoformat()
        }
        for sample in corpus
    ]
    response = supabase.table("cv_corpus").insert(data).execute()

    # Feedback sur l'opération
    if response.data:
        print("Corpus sauvegardé avec succès dans la base de données !")
    elif response.error:
        print(f"Erreur : {response.error}")
    else:
        print("Une réponse inattendue a été reçue de Supabase.")



# ****************************************************************************** # 
# --- FONCTIONS DE RÉCUPÉRATION DU FICHIER D'ENTRAINEMENT STOCKÉ DANS LA BDD --- # 
# ****************************************************************************** #



def download_corpus_to_file(filename="data/cv_corpus_download.txt"):
    """
    Récupère le corpus de la base de données et le sauvegarde dans un fichier .txt.
    Les lignes ayant la catégorie 'Titre' ne contiennent que la colonne 'phrase', avec une ligne vide avant.
    """
    response = supabase.table("cv_corpus").select("phrase, categorie").execute()
    
    # Vérification de la réponse
    if response.data:  # Si des données ont été récupérées
        with open(filename, "w", encoding="utf-8") as file:
            for row in response.data:
                # Si la catégorie est 'Titre', insérer une ligne vide avant et n'insérer que la 'phrase'
                if row['categorie'] == "Titre":
                    file.write("\n")  # Ajouter une ligne vide
                    file.write(f"{row['phrase']}\n")
                else:
                    file.write(f"{row['phrase']}|{row['categorie']}\n")
        print(f"Corpus téléchargé et sauvegardé dans le fichier {filename}.")
    elif response.error:  # Si une erreur est survenue
        print(f"Erreur lors de la récupération : {response.error}")
    else:  # Si aucune donnée ou erreur n'est retournée
        print("Une réponse inattendue a été reçue de Supabase.")



# *********************************** # 
# --- POINT D'ENTRÉE DU PROGRAMME --- # 
# *********************************** # 



if __name__ == "__main__":
    print("Bienvenue dans le programme de gestion du corpus de la classification de CV !", flush=True)
    
    # Étape 1 : Proposer de supprimer les données existantes dans la table
    print("Souhaitez-vous supprimer les données existantes dans la base de donnée Supabase ? (y/n) : ", flush=True)
    clear_choice = input().strip().lower()
    if clear_choice == "y":
        clear_corpus_table()
    else:
        print("Suppression ignorée.", flush=True)

    # Étape 2 : Proposer de sauvegarder un fichier local dans Supabase
    print("Souhaitez-vous sauvegarder le fichier local nommé 'cv_corpus.txt' dans la base de données Supabase ? (y/n) : ", flush=True)
    save_choice = input().strip().lower()
    if save_choice == "y":
        local_corpus_file = "data/cv_corpus.txt"
        if os.path.exists(local_corpus_file):
            corpus = load_corpus_from_file(local_corpus_file)
            if corpus:
                save_corpus_to_supabase(corpus)
            else:
                print("Le fichier 'cv_corpus.txt' est vide ou invalide. Sauvegarde ignorée.", flush=True)
        else:
            print(f"Le fichier '{local_corpus_file}' est introuvable. Sauvegarde ignorée.", flush=True)
    else:
        print("Sauvegarde ignorée.", flush=True)

    # Étape 3 : Proposer de télécharger les données de Supabase vers un fichier local
    print("Souhaitez-vous télécharger le corpus sauvegardé dans la BDD Supabase vers le fichier local 'cv_corpus_download.txt' ? (y/n) : ", flush=True)
    download_choice = input().strip().lower()
    if download_choice == "y":
        local_output_file = "cv_corpus_download.txt"
        download_corpus_to_file(local_output_file)
    else:
        print("Téléchargement ignoré.", flush=True)
