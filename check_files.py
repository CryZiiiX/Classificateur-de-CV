# /**************************************************************************************************************************************************************************************
# Nom du fichier : check_files.py
# Rôle du fichier : Ce fichier sert a vérifier si les repertoires ont bien été créés pour que le logiciel soit fonctionnel.

# Auteur : Maxime BRONNY
# Version : V1
# Licence : Réalisé dans le cadre des cours "Fouille de données, Ingéniérie des langues, Développement logiciel libre, IA & Apprentisage" L3 INFORMATIQUE IED
# Usage : Un paquetage a été mit en place pour l'utiliser veuillez utiliser dans un système debian la commande suivante :
#           - INSTALLATION DU PAQUET GÉNÉRÉ
#               - sudo apt install ./cv-classifier_1.0-1_all.deb

#           Puis exécute ton programme avec :
#               - cv-classifier
# ***************************************************************************************************************************************************************************************/



# **************************************************************************** # 
# --- LIBRAIRIES UTILISÉES POUR LA VÉRIFICATION DES REPERTOIRES TÉLÉCHAGÉS --- # 
# **************************************************************************** # 



import os



# ****************************************************************************** # 
# --- FONCTION VÉÉRIFIANT LES REPERTOIRES EXISTANTS ET LES RECRÉER SI BESOIN --- # 
# ****************************************************************************** # 



def verifier_et_creer_repertoires():
    """
    Vérifie et crée les répertoires nécessaires au projet.
    Ce script est destiné à être lancé depuis le répertoire contenant main.py.
    """
    # Répertoire(s) à vérifier ou créer
    repertoires = [
        "ATS_Classement",
        "CV_A_TRAITER",
        "data",
        os.path.join("data", "models"),
        "output_text"
    ]

    # Parcours et création si inexistant
    for rep in repertoires:
        if not os.path.exists(rep):
            os.makedirs(rep)
            print(f"[Créé] Répertoire : {rep}")
        else:
            print(f"[OK] Répertoire déjà existant : {rep}")



# *********************************** # 
# --- POINT D'ENTRÉE DU PROGRAMME --- # 
# *********************************** # 



if __name__ == "__main__":
    # Exécution du contrôle de structure de dossiers
    verifier_et_creer_repertoires()

