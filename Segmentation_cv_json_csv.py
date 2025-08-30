# /********************************************************************************************************************************************************************************************************************************************
# Nom du fichier : Segmentation_cv_json_csv.py
# Rôle du fichier : Ce fichier s'occupe de la création des fichiers JSON & CSV en extrayant les informations importantes des CV et en les stockants en ayant pour but l'exploitation potentielle des informations des CV utilisateurs.

# Auteur : Maxime BRONNY
# Version : V1
# Licence : Réalisé dans le cadre des cours "Fouille de données, Ingéniérie des langues, Développement logiciel libre, IA & Apprentisage" L3 INFORMATIQUE IED
# Usage : Un paquetage a été mit en place pour l'utiliser veuillez utiliser dans un système debian la commande suivante :
#           - INSTALLATION DU PAQUET GÉNÉRÉ
#               - sudo apt install ./cv-classifier_1.0-1_all.deb

#           Puis exécute ton programme avec :
#               - cv-classifier
# *********************************************************************************************************************************************************************************************************************************************/



# ********************************************************************************************************* # 
# --- LIBRAIRIES UTILISÉES POUR RÉPARTIR LES DONNÉES EXTRAITES DANS DES FORMATS JSON & CSV EXPLOITABLES --- # 
# ********************************************************************************************************* # 



import json  # Gestion des données au format JSON
import csv  # Lecture et écriture de fichiers CSV
import pdfplumber  # Extraction de texte depuis des fichiers PDF
import os  # Interaction avec le système de fichiers et les variables d'environnement
import spacy  # Traitement du langage naturel (NLP)



# ********************************************************** # 
# --- FONCTION D'INITIALISATION DES SECTIONS D'UN PROFIL --- # 
# ********************************************************** # 


# Initialise les sections d’un profil (identité, formations, compétences, etc.)
def extract_sections(text):
    sections = {
        "Identité"    : [],
        "Formations"  : [],
        "Compétences" : [],
        "Expériences" : [],
        "Langues"     : [],
        "Localisation": []
    }
    return sections



# ************************************** # 
# --- NORMALISATION ET LEMMATISATION --- # 
# ************************************** # 



def normalize_text(text):
    """
    Normalise un texte en appliquant la lemmatisation, la mise en minuscules 
    et en supprimant les mots vides (stopwords).

    :param text: Chaîne de caractères à normaliser
    :return: Texte normalisé
    """
    # Charge le modèle linguistique français de spaCy
    nlp = spacy.load("fr_core_news_sm")
    doc = nlp(text)  # Analyse le texte avec spaCy
    # Retourne le texte normalisé (lemmatisé, en minuscules, sans stopwords)
    return " ".join(token.lemma_.lower() for token in doc if not token.is_stop)



# *********************************************** # 
# --- FONCTION D'EXTRACTION DE TEXTE D'UN PDF --- # 
# *********************************************** # 



def extract_text_from_pdf(pdf_path, output_folder="/var/lib/cv-classifier/output_text"):
    """
    Extrait le texte d'un fichier PDF et le sauvegarde dans un fichier .txt.
    :param pdf_path: Chemin du fichier PDF à analyser
    :param output_folder: Dossier où enregistrer le fichier texte extrait
    :return: Texte brut extrait du PDF
    """
    text = ""  # Chaîne accumulant le texte de toutes les pages

    # Parcours chaque page du PDF pour récupérer le texte
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"  # Ajoute un saut de ligne entre les pages

    # Assure l’existence du dossier de sortie
    os.makedirs(output_folder, exist_ok=True)

    # Normalise le texte (suppression stopwords, passage en minuscules, etc.)
    normalize_text(text)

    # Génère le nom du fichier texte à partir du PDF d’origine
    txt_filename = os.path.splitext(os.path.basename(pdf_path))[0] + ".txt"
    txt_path = os.path.join(output_folder, txt_filename)

    # Sauvegarde le texte extrait dans le fichier .txt
    with open(txt_path, "w", encoding="utf-8") as txt_file:
        txt_file.write(text)

    print(f"Texte extrait sauvegardé dans : {txt_path}")
    return text



# *************************************************************************** # 
# --- SAUVEGARDE DES DONNÉES ( FORMAT -> JSON ) SI PROBABILITÉ SUFFISANTE --- # 
# *************************************************************************** # 



def save_as_json(data, output_filename, domains, threshold=0.4):
    """
    Sauvegarde les données au format JSON dans des sous-dossiers correspondant 
    aux domaines détectés avec une probabilité suffisante.

    :param data: Dictionnaire contenant les données structurées
    :param output_filename: Nom du fichier JSON de sortie
    :param domains: Liste de tuples (domaine, probabilité)
    :param threshold: Seuil minimum de probabilité pour sauvegarder les résultats
    """
    base_dir = "/var/lib/cv-classifier/ATS_Classement"  # Répertoire principal pour les fichiers triés
    os.makedirs(base_dir, exist_ok=True)  # Crée le répertoire principal si nécessaire
    
    for domain, probability in domains:
        if probability < threshold:  # Ignore les domaines sous le seuil
            continue
        
        # Prépare le dossier et le chemin du fichier JSON
        dir_name = os.path.join(base_dir, domain.replace(" ", "_"))
        os.makedirs(dir_name, exist_ok=True)
        json_path = os.path.join(dir_name, output_filename)
        
        data["Probabilité"] = probability  # Ajoute la probabilité aux données
        
        # Écrit les données au format JSON
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

        print(f"Données enregistrées dans : {json_path}")



# ************************************************************************** # 
# --- SAUVEGARDE DES DONNÉES ( FORMAT -> CSV ) SI PROBABILITÉ SUFFISANTE --- # 
# ************************************************************************** # 



def save_as_csv(data, output_filename, domains, threshold=0.4):
    """
    Sauvegarde les données au format CSV dans des sous-dossiers correspondant 
    aux domaines détectés avec une probabilité suffisante.

    :param data: Dictionnaire contenant les données structurées
    :param output_filename: Nom du fichier CSV de sortie
    :param domains: Liste de tuples (domaine, probabilité)
    :param threshold: Seuil minimum de probabilité pour sauvegarder les résultats
    """
    base_dir = "/var/lib/cv-classifier/ATS_Classement"  # Répertoire principal pour les fichiers triés
    os.makedirs(base_dir, exist_ok=True)  # Crée le répertoire principal si nécessaire
    
    for domain, probability in domains:
        if probability < threshold:  # Ignore les domaines sous le seuil
            continue
        
        # Prépare le dossier et le chemin du fichier CSV
        dir_name = os.path.join(base_dir, domain.replace(" ", "_"))
        os.makedirs(dir_name, exist_ok=True)
        csv_path = os.path.join(dir_name, output_filename)
        
        data["Probabilité"] = probability  # Ajoute la probabilité aux données
        
        # Écrit les données au format CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Section", "Type", "Contenu"])  # En-tête CSV
            
            for key, value in data.items():
                writer.writerow([])  # Séparation visuelle des sections
                if isinstance(value, dict):  # Clés imbriquées
                    for sub_key, sub_value in value.items():
                        writer.writerow([key, sub_key, sub_value])
                elif isinstance(value, list):  # Listes de valeurs
                    for item in value:
                        writer.writerow([key, "   -   ", item])
                else:  # Valeurs simples
                    writer.writerow([key, "   -   ", value])

        print(f"Données enregistrées dans : {csv_path}")
