# /**********************************************************************************************************************************************************************************
# Nom du fichier : main.py
# Rôle du fichier : C'est le fichier principal gérant le bon déroulement des appelations de fonctions des différents fichiers.

# Auteur : Maxime BRONNY
# Version : V1
# Licence : Réalisé dans le cadre des cours "Fouille de données, Ingéniérie des langues, Développement logiciel libre, IA & Apprentisage" L3 INFORMATIQUE IED
# Usage : Un paquetage a été mit en place pour l'utiliser veuillez utiliser dans un système debian la commande suivante :
#           - INSTALLATION DU PAQUET GÉNÉRÉ
#               - sudo dpkg -i cv-classifier_1.0-1_all.deb

#           Puis exécute ton programme avec :
#               - cv-classifier
# *********************************************************************************************************************************************************************************/



# ****************************************************** # 
# --- LIBRAIRIES UTILISÉES POUR LE FICHIER PRINCIPAL --- # 
# ****************************************************** # 



# --- Librairies standard pour gestion de chaînes et fichiers ---
import re
import os

# --- Librairies lié a la normalisation et lemmatisation ---
from unidecode import unidecode
import spacy

# --- Comparaison floue de chaînes pour correction/ajustement de textes ---
from rapidfuzz import fuzz, process

# --- Composants NLP Flair pour création et annotation de phrases ---
from flair.data import Sentence
from flair.models import SequenceTagger
from pathlib import Path

# --- Fonctions de segmentation de PDF et export en JSON/CSV ---
from Segmentation_cv_json_csv import extract_text_from_pdf, save_as_json, save_as_csv, extract_sections

# --- Prédiction du domaine de CV via un classifieur Sklearn ---
from Sklearn_cv_classifier import predict_cv_domain



# ************************************************* # 
# --- CHARGEMENT DES DIFFÉRENTS MODÈLES NLP/NER --- # 
# ************************************************* # 



# --- Variables globales pour les taggers Flair ---
global tagger, taggerEXPERIENCE

# --- Chargement du modèle NER français générique ---
print("\nChargement du modèle Flair/ner-french... \n")
tagger = SequenceTagger.load("flair/ner-french")

# --- Chargement du modèle NER personnalisé pour l'extraction d'expériences ---
print("\nChargement du modèle local : flair_ner_model/best-model.pt\n")
# Construire un chemin absolu vers le fichier best-model.pt
model_path = Path(__file__).resolve().parent / "data/models/flair_ner_model/best-model.pt"

# Charger le modèle local correctement
taggerEXPERIENCE = SequenceTagger.load(str(model_path))

# Chargement du modèle spacy pour lemmatisation
print("\nChargement du modèle local pour la lemmatisation : fr_core_news_sm\n")
nlp = spacy.load("fr_core_news_sm")



# ************************************************** # 
# --- REGROUPEMENT DES LISTES DE POST-TRAITEMENT --- # 
# ************************************************** # 



# Ensemble des compétences techniques et métiers à reconnaître ( A COMPLÉTER )
KNOWN_COMPETENCIES = {
    "AWS", "Azure", "Google Cloud", "Serverless", "Cloud Security", "Python", "Machine Learning", 
    "Deep Learning", "HTML", "CSS", "JavaScript", "React", "Node.js", "PHP",
    "Pandas", "Scikit-Learn", "TensorFlow", "Docker", "Kubernetes", "CI/CD", 
    "Ansible", "Terraform", "Pentesting", "SIEM", "Firewall", "Intrusion Detection", 
    "OSINT", "NLP", "Computer Vision", "Transformers", "CamemBERT", "GPT",
    "Développer des programmes informatiques",
    "Utiliser des langages de programmation",
    "Concevoir des architectures logicielles",
    "Administrer des bases de données",
    "Concevoir des bases de données",
    "Optimiser les performances des bases de données",
    "Mettre en œuvre des politiques de sécurité",
    "Gérer des incidents de sécurité",
    "Effectuer des tests d'intrusion",
    "Configurer des réseaux",
    "Superviser des réseaux",
    "Diagnostiquer des problèmes réseau",
    "Analyser des données",
    "Utiliser des outils de business intelligence",
    "Interpréter des données statistiques",
    "Respecter les principes de protection des données",
    "Protéger des données à caractère personnel et la vie privée",
    "Comprendre les concepts physiques et techniques de l'organisation du stockage numérique de données",
    "Maîtriser les techniques de représentation visuelle telles que les histogrammes, nuages de points, graphiques de surface"
}



# Ensemble de statuts standardisés utilisés pour la correction par fuzzy matching ( A COMPLÉTER )
KNOWN_EXPERIENCES = {
    "Développeur",
    "Ingénieur",
    "Chef de projet",
    "Consultant",
    "Analyste",
    "Manager",
    "Technicien",
    "Administrateur système",
    "Data Scientist",
    "Architecte logiciel",
    "UX Designer"
}



# Liste des langues supportées ( A COMPLÉTER )
LANGUAGES = {
    "français", "anglais", "espagnol", "allemand", "italien", "portugais", "néerlandais",
    "russe", "chinois", "japonais", "arabe", "coréen", "hindi", "suédois", "norvégien"
}

# Liste des niveaux de maîtrise linguistique applicables ( A COMPLÉTER )
LANGUAGE_LEVELS = {
    "A1", "A2", "B1", "B2", "C1", "C2",
    "débutant", "intermédiaire", "courant", "bilingue", "natif", "Langue maternelle"
}

# Ensemble des diplômes et formations usuels ( A COMPLÉTER )
DEGREES = {
    "Licence", "Master", "Doctorat", "BTS", "DUT", "CAP", "Ingénieur", "MBA", "PhD"
}

# Regex pour extraire les sections "Formation" ou "Diplôme" ( A COMPLÉTER )
DEGREE_PATTERN = r"(?:^|\n)(?:Formation|Diplôme)\s*:\s*(.*?)(?:\n|$)"

# Regex pour détecter adresses email et numéros de téléphone 
EMAIL_PATTERN = r"[\w.-]+@[\w.-]+\.[a-z]{2,}"
PHONE_PATTERN = r"(?:\+33|0)\s?[1-9](?:[\s.-]?\d{2}){4}"



# ***************************************************** # 
# --- EXTRACTION DES EMAILS ET NUMEROS DE TELEPHONE --- # 
# ***************************************************** # 


# Extraction des emails et numéros de téléphone via regex 
def extract_emails_phones_ReGex(text):
    emails = re.findall(EMAIL_PATTERN, text)
    phones = re.findall(PHONE_PATTERN, text)
    return {"Emails": emails, "Téléphone": list(set(phones))}


# ************************************** # 
# --- NORMALISATION ET LEMMATISATION --- # 
# ************************************** # 


# Fonction de lemmatisation
def lemmatize(text):
    return " ".join([token.lemma_ for token in nlp(text)])

# Fonction de normalisation
def normalize(text):
    text = unidecode(text).lower()
    text = re.sub(r"[-_]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text



# *************************************************************************************************************** # 
# --- FONCTION POUR EXTRAIRE LES EXPERIENCES & DIPLÔMES AINSI QUE LES COMPÉTENCES A L'AIDE DU MODÈLE ENTRAINÉ --- # 
# *************************************************************************************************************** # 



# Extraction des expériences et diplômes via NER Flair
def extract_experiences_flair(text, taggerEXPERIENCE):
    """
    Extrait toutes les entités de type 'EXPERIENCE' et 'DIPLOME' d'un texte.
    """
    sentence = Sentence(text)
    taggerEXPERIENCE.predict(sentence)
    return [
        entity.text
        for entity in sentence.get_spans('ner')
        if entity.tag in ['EXPERIENCE', 'DIPLOME']
    ]



# Extraction des compétences via NER Flair
def extract_competences_flair(text, taggerEXPERIENCE):
    """
    Extrait toutes les entités de type 'COMPETENCE' d'un texte.
    """
    sentence = Sentence(text)
    taggerEXPERIENCE.predict(sentence)
    return [
        entity.text
        for entity in sentence.get_spans('ner')
        if entity.tag == 'COMPETENCE'
    ]



# ********************************** # 
# --- TRAITEMENT DES COMPÉTENCES --- # 
# ********************************** # 



# --- Nettoyage et normalisation des compétences ---
def merge_and_clean_competencies(competences):
    """
    Normalise, filtre et lemmatise les compétences extraites.
    """
    # Listes de mots à filtrer
    remove_if_alone = {"informatique", "data", "skills", "email", "mail", "e mail",}
    remove_if_part_of_phrase = {"base", "de", "niveau", "expert"}
    remove_completely = {"misc", "loc", "per", "org"}

    cleaned_competencies = set()

    for comp in competences:
        norm = normalize(comp)
        words = norm.split()

        # Cas 1 : un seul mot
        if len(words) == 1:
            word = words[0]
            if word in remove_if_alone or word in remove_completely:
                continue
            cleaned_competencies.add(lemmatize(word))
            continue

        # Cas 2 : expression
        filtered_words = [word for word in words if word not in remove_if_part_of_phrase and word not in remove_completely]
        cleaned = " ".join(filtered_words).strip()
        if cleaned and len(cleaned) > 1 and not re.match(r"^[^a-zA-Z0-9]+$", cleaned):
            cleaned_competencies.add(lemmatize(cleaned))

    return list(cleaned_competencies)




# --- Correction des compétences mal orthographiées par fuzzy matching ---
def correct_misspelled_competences(detected_competencies):
    
    corrected = []

    for comp in detected_competencies:
        comp = normalize(comp)
        match, score, _ = process.extractOne(comp, KNOWN_COMPETENCIES)
        if score > 80:
            corrected.append(match)
        else:
            corrected.append(comp)
    return list(set(corrected))



# ************************************ # 
# --- TRAITEMENT DES LOCALISATIONS --- # 
# ************************************ # 



# --- Fusion et nettoyage des localisations détectées ---
def merge_and_clean_locations(detected_locations):
    detected_locations = {loc.strip().lower() for loc in detected_locations}
    blacklist = {"adresse", "rue", "avenue", "route", "université"}
    cleaned_locations = {
        loc for loc in detected_locations
        if loc not in blacklist and len(loc) > 2 and not re.match(r"^[^a-zA-Z0-9]+$", loc)
    }
    return list(set(cleaned_locations))



# ****************************** # 
# --- EXTRACTION DES LANGUES --- # 
# ****************************** # 



# --- Extraction des langues et niveaux depuis le texte ---
def extract_languages(text):
    lang_pattern = rf"(\b(?:{'|'.join(LANGUAGES)})\b)\s*:\s*(\b(?:{'|'.join(LANGUAGE_LEVELS)})\b)"
    matches = re.findall(lang_pattern, text, re.IGNORECASE)
    extracted_languages = [{"Langue": match[0].capitalize(), "Niveau": match[1].capitalize()} for match in matches]
    return extracted_languages



# ********************************************************************************************** # 
# --- DETECTION DES FORMATIONS AU SEIN DES EXPERIENCES ET DIPLÔMES EXTRAIT A L'AIDE DE FLAIR --- # 
# ********************************************************************************************** # 



# --- Filtrage des formations : ne conserve que les entrées contenant un diplôme connu ---
def detect_formations_finetuning(entries):
    """
    Filtre les diplômes à partir d'une liste d'entrées.
    
    Seuls les éléments contenant un diplôme défini dans DEGREES sont conservés.
    """
    
    return [entry for entry in entries if any(degree in entry for degree in DEGREES)]



# ********************************** # 
# --- TRAITEMENT DES EXPERIENCES --- # 
# ********************************** # 



def detect_name_filter_experience(entries, names):
    """
    Supprime les expériences contenant des noms à exclure (après normalisation).
    Gère aussi le cas où 'names' contient des chaînes longues avec plusieurs mots.
    """
    norm_names = []

    for n in names:
        if not n.strip():
            continue
        split_names = n.split()
        norm_names.extend(normalize(x) for x in split_names)

    result = []
    for entry in entries:
        norm_entry = normalize(entry)
        if not any(name in norm_entry for name in norm_names):
            result.append(entry)

    return result



# --- Fusion et nettoyage des compétences détectées ---
def merge_and_clean_experiences(flair_experiences):
    """
    Nettoie et filtre les expériences détectées tout en conservant la forme originale (majuscules, accents...).
    """

    # Dictionnaire : { normalisé : original }
    normalized_to_original = { normalize(comp): comp for comp in flair_experiences }

    # Listes de mots à filtrer
    remove_if_alone = {"informatique", "data", "experience"}
    remove_if_part_of_phrase = {"professionnelle", "experience"}
    remove_completely = {"misc", "loc", "per", "org", "skills"}

    cleaned_experiences = set()

    for norm, original in normalized_to_original.items():
        words = norm.split()
        original_words = original.split()

        # Cas 1 : un seul mot
        if len(words) == 1:
            word = words[0]
            if word in remove_completely or word in remove_if_alone:
                continue
            cleaned_experiences.add(original)
            continue

        # Cas 2 : expression
        filtered_words = [
            original_words[i] for i, word in enumerate(words)
            if word not in remove_completely and word not in remove_if_part_of_phrase
        ]

        cleaned = " ".join(filtered_words).strip()
        if cleaned and len(cleaned) > 1 and not re.match(r"^[^a-zA-Z0-9]+$", cleaned):
            cleaned_experiences.add(cleaned)

    return list(cleaned_experiences)



# Correction des expériences détectées par similarité fuzzy
def correct_experiences_with_rapidfuzz(detected_experiences):
    """
    Ajuste les libellés d'expériences détectées en les comparant
    à une liste de références connues (seuil de ressemblance : 80).
    """
    corrected_experiences = []
    for exp in detected_experiences:
        match, score, _ = process.extractOne(exp, KNOWN_EXPERIENCES, scorer=fuzz.ratio)
        if score > 80:
            corrected_experiences.append(match)
        else:
            corrected_experiences.append(exp)
    return list(set(corrected_experiences))



# ****************************************** # 
# --- TRAITEMENT DES NOMS EXTRAITS DU CV --- # 
# ****************************************** # 



def clean_names_with_blacklist(names):
    """
    Supprime les mots parasites dans les noms extraits, en conservant la forme originale.
    La comparaison se fait en version normalisée temporaire.

    Returns:
        list: Liste de noms nettoyés avec mots parasites retirés.
    """
    blacklist = {"email", "contact", "adresse", "tel", "tél", "téléphone"}
    normalized_blacklist = {normalize(n) for n in blacklist}
    cleaned_names = []

    for original_name in names:
        norm_words = normalize(original_name).split()
        original_words = original_name.split()

        # On garde uniquement les mots qui ne sont pas blacklistés
        filtered_words = [
            original_words[i] for i, word in enumerate(norm_words)
            if word not in normalized_blacklist
        ]

        cleaned = " ".join(filtered_words).strip()
        if cleaned and len(cleaned) > 1:
            cleaned_names.append(cleaned)

    return cleaned_names



# ****************************************************************************************************************************************************************** # 
# --- FONCTION DE GESTIONS D'APPELS DES FONCTIONS PERMETTANT L'EXTRACTION CORRECT DES ENTITÉS PRÉSENTES DANS LES CV QUI SERVENT A CLASSIFIER LES CV PAR LA SUITE --- # 
# ****************************************************************************************************************************************************************** # 



def extract_all_entities(text):
    """
    Extrait différentes entités nommées (compétences, localisation, expériences, etc.)
    d'un texte en utilisant Flair NER.
    
    :param text: Texte à analyser
    :return: Dictionnaire des entités classées par catégories
    """

    # ******************************************* # 
    # ----------------( ÉTAPE 1 )---------------- #
    # --- Initialisation des listes d'entités --- #
    # ******************************************* # 

    Compétences, extracted_localisation, Expériences, Noms  = [], [], [], []

    # ******************************************* # 
    # ----------------( ÉTAPE 2 )---------------- #
    # --- Extraction des emails et téléphones --- #
    # ******************************************* # 

    extracted_info = extract_emails_phones_ReGex(text) 
    Emails = extracted_info["Emails"]
    Téléphone = extracted_info["Téléphone"]
    
    # ********************************* # 
    # -----------( ÉTAPE 3 )----------- #
    # --- Annotation NER avec Flair --- #
    # ********************************* # 

    sentence = Sentence(text)
    tagger.predict(sentence)

    # *************************************************************************** # 
    # --------------------------------( ÉTAPE 4 )-------------------------------- #
    # --- Classification des entités par type a l'aide de Flair non fine-tuné --- #
    # *************************************************************************** # 

    for entity in sentence.get_spans("ner"):
        word  = entity.text.strip()
        label = entity.get_label("ner").value
        
        if "MISC" in label:
            if not re.match(EMAIL_PATTERN, word):
                Compétences.append(word)

        elif "LOC" in label:
            extracted_localisation.append(word)

        elif "PER" in label:
            Noms.append(word)

        elif "ORG" in label:
            Expériences.append(word)

    # ******************************************* # 
    # ----------------( ÉTAPE 5 )---------------- #
    # --- Nettoyage et test des localisations --- #
    # ******************************************* # 

    corrected_localisation = merge_and_clean_locations(extracted_localisation)
    print(" \n ")
    print("Localisations TEST : \n ")
    print("Localisations extraites : ", extracted_localisation)
    print("Localisations corrigées : ", corrected_localisation)
    print(" \n ")

    # ************************************************************ # 
    # -------------------------( ÉTAPE 6 )------------------------ #
    # --- Détection des langues et niveaux a l'aide de 'ReGex' --- #
    # ************************************************************ # 

    extracted_languages = extract_languages(text)
    print(" \n ")
    print("Langues TEST : \n ")
    print("Langues extraites : ", extracted_languages)
    print(" \n ")

    # ********************************************************** # 
    # ------------------------( ÉTAPE 7 )----------------------- #
    # --- Traitement des expériences détectées dans le texte --- #
    # ********************************************************** # 

    # Extraction brute via Flair fine-tuné sur les expériences # 
    extracted_experiences = extract_experiences_flair(text, taggerEXPERIENCE)

    # Correction orthographique et regroupement par similarité via RapidFuzz ( correction des fautes ou variantes proches (ex: développeur / developpeur))
    corrected_experiences = correct_experiences_with_rapidfuzz(extracted_experiences)

    # Suppression des expériences contenant des noms de personnes détectés (ex: "Jean Dupont ingénieur" devient "ingénieur" ou est supprimé selon le cas)
    experiences_without_names = detect_name_filter_experience(corrected_experiences, Noms)

    # Nettoyage final avec suppression des termes parasites (ex: "Professionnelle ingénieur cybersécurité" → "ingénieur cybersécurité")
    # Applique aussi la NORMALISATION (minuscule, accents supprimés) temporairement pour comparer avec des blacklist de mots comme "informatique", "experience", "data", etc.
    blacklist_experiences = merge_and_clean_experiences(experiences_without_names)

    # *********************************************** # 
    # ------------------( ÉTAPE 8 )------------------ #
    # --- Affichage du traitement des EXPERIENCES --- #
    # *********************************************** # 

    print("\n")
    print("Expériences TEST :\n")

    print("Via Flair non fine-tuné              : ", Expériences, "\n")
    print("Via Flair fine-tune (brut)           : ", extracted_experiences, "\n")
    print("Après correction fuzzy (orthographe) : ", corrected_experiences, "\n")
    print("Noms détectés à filtrer              : ", Noms, "\n")
    print("Expériences sans noms de personnes   : ", experiences_without_names, "\n")
    print("Nettoyage final (blacklist + mots parasites supprimés, normalisation incluse) : ", blacklist_experiences, "\n")
    print("\n")


    # ***************************************** # 
    # ---------------( ÉTAPE 9 )--------------- #
    # --- Filtrage des formations détectées --- #
    # ***************************************** # 

    extracted_diplomes = detect_formations_finetuning(blacklist_experiences)

    # ***************************************************** # 
    # ---------------------( ÉTAPE 11 )-------------------- #
    # --- Affichage du traitement des DIPLÔMES extraits --- #
    # ***************************************************** # 

    print(" \n ")
    print("Diplômes TEST : \n ")
    print("Diplômes extraits : ", extracted_diplomes)
    print(" \n ")

    # ********************************************************** # 
    # -----------------------( ÉTAPE 12 )----------------------- #
    # --- Traitement des compétences détectées dans le texte --- #
    # ********************************************************** # 

    # Extraction brute des compétences via Flair
    extracted_competences = extract_competences_flair(text, taggerEXPERIENCE)

    # Nettoyage, normalisation (minuscule, accents, etc.) et lemmatisation
    # - Retire les mots seuls parasites comme "informatique"
    # - Filtre les mots inutiles dans des expressions ("de", "base", etc.)
    # - Lemmatisation avec spaCy pour uniformiser les formes (ex: "analysant" → "analyser")
    cleaned_competencies_with_ReGex = merge_and_clean_competencies(extracted_competences)

    # 3. Correction orthographique avec RapidFuzz
    # - Compare les formes nettoyées aux compétences connues
    # - Corrige les fautes proches (ex: "devolopper" → "développer")
    corrected_competences = correct_misspelled_competences(cleaned_competencies_with_ReGex)

    # *********************************************** # 
    # ------------------( ÉTAPE 13 )----------------- #
    # --- Affichage du traitement des COMPÉTENCES --- #
    # *********************************************** # 

    print("\n")
    print("Compétences TEST :\n")
    print("Compétences extraites (brutes - Flair MISC)         : ", extracted_competences, "\n")
    print("Après nettoyage, normalisation et lemmatisation     : ", cleaned_competencies_with_ReGex, "\n")
    print("Après correction orthographique (fuzzy RapidFuzz)   : ", corrected_competences, "\n")
    print("\n")

    # *************************************************************************************************** # 
    # --------------------------------------------( ÉTAPE 13 )------------------------------------------- #
    # --- Déduplication des noms extraits & Nettoyage des mots faisant partie de la blacklist définie --- #
    # *************************************************************************************************** # 

    Noms_sans_doublons = list({nom.lower(): nom for nom in Noms}.values())
    Noms_blacklist = clean_names_with_blacklist(Noms_sans_doublons)

    # ****************************************************** # 
    # ----------------------( ÉTAPE 14 )-------------------- #
    # --- Affichage des informations liés a l'indentités --- #
    # ****************************************************** # 

    print(" \n ")
    print("Identité TEST : \n ")
    print("Noms      : ", Noms_blacklist, "\n")
    print("Emails    : ", list(set(Emails)), "\n")
    print("Téléphones: ", list(set(Téléphone)), "\n")
    print(" \n ")

    # ********************************************** # 
    # ------------------( ÉTAPE 15 )---------------- #
    # --- Assemblage et retour du résultat final --- #
    # ********************************************** # 

    return {
        "Formations":      extracted_diplomes,
        "Compétences":     list(set(corrected_competences)),
        "Expériences":     blacklist_experiences,
        "Localisation":    corrected_localisation,
        "Identité": {
            "Noms":      Noms_blacklist,
            "Emails":    list(set(Emails)),
            "Téléphone": list(set(Téléphone))
        },
        "Langues": extracted_languages
    }



# ****************************************************************************************** # 
# --- PARCOURS ET TRAITEMENT DE TOUT LES CV AU FORMAT PDF SE TROUVANT DANS UN REPERTOIRE --- # 
# ****************************************************************************************** # 



def process_cv_folder(cv_folder):
    for filename in os.listdir(cv_folder):
        # Ne garder que les fichiers .pdf
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(cv_folder, filename)
            print(f"\nTraitement du fichier : {filename}")
            
            # --- Extraction et structuration des données du CV ---
            text = extract_text_from_pdf(pdf_path)
            extracted_entities = extract_all_entities(text)
            structured_data = extract_sections(text)
            structured_data.update(extracted_entities)
            
            # Affichage du contenu structuré pour vérification
            print("\n\n")
            print(structured_data)
            print("\n\n")

            # --- Prédiction du domaine professionnel du candidat ---
            formatted_text_exp  = " ".join(structured_data["Expériences"])
            formatted_text_comp = " ".join(structured_data["Compétences"])
            formatted_text      = formatted_text_exp + formatted_text_comp
            predicted_domain    = predict_cv_domain(formatted_text)
            print(f"Les domaines prédits sont : {predicted_domain}")

            # --- Génération des noms de fichiers et sauvegarde des résultats ---
            json_name = filename.replace(".pdf", ".json")
            csv_name  = filename.replace(".pdf", ".csv")
            save_as_json(structured_data, json_name, predicted_domain)
            save_as_csv(structured_data, csv_name, predicted_domain)



# ************************************************************** # 
# --- POINT D'ENTRÉE DU SCRIPT SI IL EST EXÉCUTÉ DIRECTEMENT --- # 
# ************************************************************** # 

if __name__ == "__main__":
    process_cv_folder("CV_A_TRAITER")
    print("\n\nAnalyse terminé !\n\n")


