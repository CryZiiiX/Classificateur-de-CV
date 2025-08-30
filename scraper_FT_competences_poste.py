# /***************************************************************************************************************************************************************************************
# Nom du fichier : scraper_FT_competences_poste.py
# Rôle du fichier : Ce fichier est un scraper pour récupérer des offres d'emplois dans des domaines de l'informatique afin de s'en servir pour classer les CV recu dans le logiciel.

# Auteur : Maxime BRONNY
# Version : V1
# Licence : Réalisé dans le cadre des cours "Fouille de données, Ingéniérie des langues, Développement logiciel libre, IA & Apprentisage" L3 INFORMATIQUE IED
# Usage : Un paquetage a été mit en place pour l'utiliser veuillez utiliser dans un système debian la commande suivante :
#           - INSTALLATION DU PAQUET GÉNÉRÉ
#               - sudo apt install ./cv-classifier_1.0-1_all.deb

#           Puis exécute ton programme avec :
#               - cv-classifier
# ***************************************************************************************************************************************************************************************/



# ************************************************************************ # 
# --- LIBRAIRIES UTILISÉES POUR SCRAPER DES DONNÉES D'OFFRES D'EMPLOIS --- # 
# ************************************************************************ # 



# Requêtes HTTP et gestion des délais
import requests
import time

# Traitement de texte : expressions régulières et normalisation Unicode
import re
import unicodedata

# Correspondance floue de chaînes
from rapidfuzz import fuzz

# Traitement du langage naturel
import spacy


# ***************************************** # 
# --- Chargement du modèle linguistique --- # 
# ***************************************** # 



nlp = spacy.load('fr_core_news_sm')



# ******************************* # 
# --- PARAMÈTRES DE CONNEXION --- # 
# ******************************* #



client_id = 'PAR_scraperdecompetencesp_3605e73f2b854c7e1102b922201528774463e14add3b1feef45147ea7a9dcde4'
client_secret = 'cdbcf77da3cf22e4e0745007834cf3eceaab5b0fd15fa901b2a7add95b9eac80'


# ************************************************** # 
# --- REGROUPEMENT DES LISTES --- # 
# ************************************************** # 

# Définition des catégories métiers et des mots-clés associés
categories = {
    'Développement Web': 'Développeur web',
    'DevOps': 'DevOps',
    'Cybersécurité': 'Cybersécurité',
    'Data Science': 'Data Scientist',
    'Intelligence Artificielle': 'Intelligence Artificielle',
    'Gestion de Projet': 'Chef de projet',
    'Administration Système': 'Administrateur système',
    'Réseaux': 'Administrateur réseau',
    'Testing et QA': 'Testeur logiciel',
    'Blockchain': 'Blockchain'
}



# *************************************************************************************** # 
# --- Fonction d’authentification : obtention d’un token OAuth2 auprès de Pôle Emploi --- # 
# *************************************************************************************** #



def get_access_token(client_id, client_secret):
    url = 'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=/partenaire'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'api_offresdemploiv2 o2dsoffre'
    }
    response = requests.post(url, headers=headers, data=data)
    if not response.ok:
        print(f"Erreur d'authentification : {response.status_code} - {response.text}")
        return None
    try:
        return response.json()['access_token']
    except Exception as e:
        print("Erreur lors du décodage du token :", e)
        return None



# ******************************************************************************* # 
# --- Fonction de requête des offres d’emploi pour un mot-clé avec pagination --- # 
# ******************************************************************************* #



def get_offres(access_token, mot_cle, offset=0, nombre=10):
    url = 'https://api.pole-emploi.io/partenaire/offresdemploi/v2/offres/search'
    headers = {'Authorization': f'Bearer {access_token}'}
    range_value = f"{offset}-{offset + nombre - 1}"
    params = {'motsCles': mot_cle, 'range': range_value}
    
    # Envoi de la requête et affichage des informations de debug
    response = requests.get(url, headers=headers, params=params)
    print(f"[DEBUG] Statut HTTP pour '{mot_cle}' (range: {range_value}) : {response.status_code}")
    print(f"[DEBUG] Corps de la réponse pour '{mot_cle}' (range: {range_value}) : '{response.text}'")
    
    if not response.ok:
        print(f"Erreur HTTP pour '{mot_cle}' (range: {range_value}) : {response.status_code} - {response.text}")
        return []
    
    if not response.text.strip():
        print(f"La réponse est vide pour '{mot_cle}' (range: {range_value}). Aucun résultat n'a été retourné.")
        return []
    
    # Traitement du JSON renvoyé et extraction des résultats
    try:
        data = response.json()
        if 'resultats' in data:
            return data['resultats']
        else:
            print(f"La clé 'resultats' est absente pour '{mot_cle}' (range: {range_value}): {data}")
            return []
    except Exception as err:
        print("Erreur lors de la conversion de la réponse en JSON pour range", range_value, ":", err)
        return []



# *************************************************************************************************************** # 
# --- Extraction et formatage des compétences d'une offre (séparation, dé-duplication, association catégorie) --- # 
# *************************************************************************************************************** #



def extraire_competences(offre, categorie):
    competences = offre.get('competences', [])
    if not competences:
        return None

    tokens = []
    for comp in competences:
        texte = comp.get('libelle', '').strip()
        if texte:
            parts = [part.strip() for part in texte.split(',') if part.strip()]
            tokens.extend(parts)
            
    if not tokens:
        return None

    unique_tokens = []
    for token in tokens:
        if token not in unique_tokens:
            unique_tokens.append(token)

    output = []
    for token in unique_tokens:
        output.append(f"{token}|{categorie}")
    return output



# ************************************************************************ # 
# --- NETTOYAGE -> NORMALISATION LEMMATISATION ÉLIMINATION DE DOUBLONS --- # 
# ************************************************************************ #


# Normalisation et lemmatisation d’un token (Unicode, minuscules, suppression stopwords/ponctuation
def nettoyer_token(token):
    token = unicodedata.normalize('NFKD', token)
    token = token.lower()
    doc = nlp(token)
    lemmatized_words = [t.lemma_ for t in doc if not t.is_stop and not t.is_punct]
    cleaned_token = ' '.join(lemmatized_words)
    cleaned_token = re.sub(r'\s+', ' ', cleaned_token).strip()
    return cleaned_token



# Nettoyage partiel d’une ligne “compétence|catégorie” en appliquant nettoyer_token
def nettoyer_ligne_partielle(ligne):
    try:
        token_part, categorie = ligne.rsplit('|', 1)
    except ValueError:
        return ligne
    cleaned_token = nettoyer_token(token_part)
    return f"{cleaned_token}|{categorie}"



# Déduplication floue des compétences par catégorie (seuil de similarité)
def deduplicate_by_category(corpus, threshold=90):
    groupes = {}
    for line in corpus:
        if not line.strip():
            continue
        try:
            token_part, categorie = line.rsplit('|', 1)
        except ValueError:
            continue
        groupes.setdefault(categorie, []).append(line)
    
    corpus_dedup = []
    for categorie, lines in groupes.items():
        unique, unique_cleaned = [], []
        for line in lines:
            cleaned_line = nettoyer_ligne_partielle(line)
            if not any(fuzz.ratio(cleaned_line, uc) > threshold for uc in unique_cleaned):
                unique.append(line)
                unique_cleaned.append(cleaned_line)
        corpus_dedup.extend(unique)
    return corpus_dedup



# *********************************** # 
# --- POINT D'ENTRÉE DU PROGRAMME --- # 
# *********************************** # 



def main():
    # Authentification et récupération du token
    access_token = get_access_token(client_id, client_secret)
    if access_token is None:
        print("La récupération du token a échoué.")
        return

    corpus = []
    # Collecte des offres et extraction des compétences pour chaque catégorie
    for categorie, mot_cle in categories.items():
        for offset in range(0, 200, 10):  # Pagination par blocs de 10 jusqu’à 200 offres
            offres = get_offres(access_token, mot_cle, offset, 10)
            print(f"[INFO] {len(offres)} offres récupérées pour '{mot_cle}' (offset: {offset})")
            for offre in offres:
                lignes = extraire_competences(offre, categorie)
                if lignes:
                    corpus.extend(lignes)
            time.sleep(1)
        corpus.append("")  # Marqueur de séparation entre catégories

    # Déduplication floue des compétences par catégorie
    corpus = deduplicate_by_category(corpus, threshold=90)

    # Nettoyage final et sauvegarde du corpus dans un fichier texte
    with open('data/Corpus_France_Travail.txt', 'w', encoding='utf-8') as f:
        for ligne in corpus:
            final_line = nettoyer_ligne_partielle(ligne)
            f.write(final_line + '\n')



if __name__ == '__main__':
    main()

