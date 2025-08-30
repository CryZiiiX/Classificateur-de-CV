# /************************************************************************************************************************************************************************************
# Nom du fichier : BDD_Flair.py
# Rôle du fichier : Ce fichier mets en lien nos fichiers pour le modèle Flair avec la base de données stockée sur SupaBase.

# Auteur : Maxime BRONNY
# Version : V1
# Licence : Réalisé dans le cadre des cours "Fouille de données, Ingéniérie des langues, Développement logiciel libre, IA & Apprentisage" L3 INFORMATIQUE IED
# Usage : Un paquetage a été mit en place pour l'utiliser veuillez utiliser dans un système debian la commande suivante :
#           - INSTALLATION DU PAQUET GÉNÉRÉ
#               - sudo apt install ./cv-classifier_1.0-1_all.deb

#           Puis exécute ton programme avec :
#               - cv-classifier
# ************************************************************************************************************************************************************************************/



# ****************************************************** # 
# --- LIBRAIRIES UTILISÉES POUR SROCKER LA BDD FLAIR --- # 
# ****************************************************** # 



import os
from supabase import create_client, Client



# ******************************* # 
# --- PARAMÈTRES DE CONNEXION --- # 
# ******************************* #



SUPABASE_URL: str = os.environ.get(
    "SUPABASE_URL",
    "https://bkisnmipaqzfludqicjz.supabase.co"
)
SUPABASE_KEY: str = os.environ.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
)



# ********************************************************************** # 
# --- INITIALISATION DU CLIENT 'SUPABASE' POUR INTÉRAGIR AVEC LA BDD --- # 
# ********************************************************************** #



supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



# ********************************************************* # 
# --- FONCTIONS DE SAUVEGARDE DU FICHIER D'ENTRAINEMENT --- # 
# ********************************************************* #



def store_file_content(file_path: str):
    """
    Lit le contenu du fichier file_path et stocke ce contenu dans
    la table 'file_storage' de Supabase.
    """
    # Vérification et lecture du fichier source
    if not os.path.exists(file_path):
        print(f"Erreur : le fichier {file_path} n'existe pas.")
        return
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Préparation des données et insertion dans Supabase
    file_name = os.path.basename(file_path)
    data = {"file_name": file_name, "file_content": content}
    response = supabase.table("file_storage").insert(data).execute()

    # Retour d’état de l’opération
    if not response.data:
        print("Erreur lors de l'insertion :", response)
    else:
        print("Contenu du fichier stocké avec succès :", response.data)



# ****************************************************************************** # 
# --- FONCTIONS DE RÉCUPÉRATION DU FICHIER D'ENTRAINEMENT STOCKÉ DANS LA BDD --- # 
# ****************************************************************************** #



def copy_file_content_from_db(file_name: str, target_file_path: str, id: int):
    """
    Récupère depuis la table 'file_storage' le contenu associé à 'file_name'
    et l'écrit dans le fichier target_file_path.
    """
    # Récupération du ou des enregistrements correspondants
    response = supabase.table("file_storage") \
                       .select("*") \
                       .eq("file_name", file_name) \
                       .execute()
    if not response.data:
        print(f"Aucune donnée trouvée pour le fichier {file_name}")
        return

    # Écriture du contenu sélectionné dans le fichier cible
    file_entry = response.data[id-1]
    with open(target_file_path, "w", encoding="utf-8") as f:
        f.write(file_entry["file_content"])
    print(f"Le contenu du fichier {file_name} a été copié vers {target_file_path}")



# *********************************** # 
# --- POINT D'ENTRÉE DU PROGRAMME --- # 
# *********************************** # 



if __name__ == "__main__":
    print("Bienvenue dans le programme de gestion du corpus Flair !", flush=True)

    # Proposition de sauvegarde du fichier local dans Supabase
    print(
        "Souhaitez-vous sauvegarder le fichier local nommé 'train.txt' "
        "dans la base de données Supabase ? (y/n) : ",
        flush=True
    )
    save_choice = input().strip().lower()
    if save_choice == "y":
        local_train_file = "data/train.txt"
        if os.path.exists(local_train_file):
            store_file_content(local_train_file)
        else:
            print(
                f"Le fichier '{local_train_file}' est introuvable. "
                "Sauvegarde ignorée.",
                flush=True
            )
    else:
        print("Sauvegarde ignorée.", flush=True)

    # Proposition de téléchargement du corpus depuis Supabase
    print(
        "Souhaitez-vous télécharger le corpus sauvegardé dans la BDD Supabase "
        "vers le fichier local 'data/train_test.txt' ? (y/n) : ",
        flush=True
    )
    download_choice = input().strip().lower()
    if download_choice == "y":
        print(
            "Entrez l'identifiant du corpus stocké dans Supabase "
            "que vous souhaitez télécharger (exemple : 0) : ",
            flush=True
        )
        id = input().strip()
        if id.isdigit():
            id = int(id)
            copy_file_content_from_db(
                "train.txt",
                "data/Corpus_France_Travail.txt",
                id
            )
        else:
            print("Identifiant invalide. Téléchargement ignoré.", flush=True)
    else:
        print("Téléchargement ignoré.", flush=True)
