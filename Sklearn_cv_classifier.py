# /************************************************************************************************************************************************************************************************

# Nom du fichier : Sklearn_cv_classifier.py
# Rôle du fichier : Ce fichier gère le modèle d'apprentissage automatique sklearn choisit pour classer automatiquement les type de CV a l'aide des informations récupérés de ce CV.

# Auteur : Maxime BRONNY
# Version : V1
# Licence : Réalisé dans le cadre des cours "Fouille de données, Ingéniérie des langues, Développement logiciel libre, IA & Apprentisage" L3 INFORMATIQUE IED
# Usage : Un paquetage a été mit en place pour l'utiliser veuillez utiliser dans un système debian la commande suivante :
#           - INSTALLATION DU PAQUET GÉNÉRÉ
#               - sudo apt install ./cv-classifier_1.0-1_all.deb

#           Puis exécute ton programme avec :
#               - cv-classifier
# ***********************************************************************************************************************************************************************************************/



# ****************************************************************************************************************************** # 
# --- LIBRAIRIES UTILISÉES POUR LE MODÈLE SKLEARN POUR CLASSER LES CV PAR RAPPORT A LEURS DOMAINES AU SEIN DE L'INFORMATIQUE --- # 
# ****************************************************************************************************************************** # 



# --- Imports système et utilitaires pour gestion de fichiers et sérialisation ---
import os
import joblib
import re
import spacy
from unidecode import unidecode

# --- Bibliothèque numérique pour calculs vectoriels et manipulation de données ---
import numpy as np

# --- Transformation TF-IDF pour représenter le texte sous forme de vecteurs ---
from sklearn.feature_extraction.text import TfidfVectorizer

# --- Division des données, recherche de paramètres et validation croisée ---
from sklearn.model_selection import train_test_split, GridSearchCV

# --- Classifieur SVM et stratégie One-vs-Rest pour prise en charge multi-étiquette ---
from sklearn.svm import SVC
from sklearn.multiclass import OneVsRestClassifier

# --- Encodage multi-étiquette des cibles et évaluation des performances ---
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import classification_report



# ***************************************** # 
# --- Chargement du modèle linguistique --- # 
# ***************************************** # 



nlp = spacy.load("fr_core_news_md")
STOPWORDS = spacy.lang.fr.stop_words.STOP_WORDS



# ********************************************************************************** # 
# --- PRÉ-TRAITEMENT DES DONNÉES -> NORMALISATION & LEMMATISATION & VECTORISATION--- # 
# ********************************************************************************** # 


# --- Normalise le texte ---
def normalize(text):
    text = unidecode(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text



# --- Prétraitement de chaque texte avant vectorisation (applique le tokenizer) ---
def preprocess_texts(texts):
    processed = []
    for text in texts:
        text = normalize(text)
        doc = nlp(text)
        #lemmatized = [token.lemma_ for token in doc if token.lemma_ not in STOPWORDS and not token.is_punct and not token.is_space]
        tokens = [token.text for token in doc if token.text.lower() not in STOPWORDS and not token.is_punct and not token.is_space]
        #processed.append(" ".join(lemmatized))
        processed.append(" ".join(tokens))

    return processed



# --- Conversion des textes prétraités en vecteurs TF-IDF avec n-grams et filtrage de fréquence ---
def vectorize_texts(texts):
    """
    Convertit une liste de textes prétraités en vecteurs TF-IDF.
    Ici, on utilise des n-grams (1 à 3) et on filtre
    les termes trop rares (min_df=3) et trop fréquents (max_df=0.85).
    """
    vectorizer = TfidfVectorizer(ngram_range=(1, 3), min_df=3, max_df=0.85)
    X = vectorizer.fit_transform(texts)
    return X, vectorizer



# ****************************************************************************************************** # 
# --- FONCTION DE CHARGEMENT DU CORPUS EXTRAIT A L'AIDE DU SCRAPER D'OFFRES D'EMPLOIS FRANCE_TRAVAIL --- # 
# ****************************************************************************************************** # 



# --- Chargement d’un corpus depuis un fichier .txt (ligne = 'texte|catégorie') ---
def load_corpus_from_file(filename="/var/lib/cv-classifier/data/cv_corpus.txt"):
    """
    Charge le corpus à partir d’un fichier .txt.
    Chaque ligne du fichier doit être au format :
    'texte|catégorie'
    """
    corpus = []
    try:
        # Ouverture du fichier en lecture UTF-8
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                # Ne traiter que les lignes contenant le séparateur '|'
                if "|" in line:
                    parts = line.strip().split("|")
                    corpus.append((parts[0], parts[1]))
        print("Corpus chargé avec succès depuis le fichier.")
    except FileNotFoundError:
        # Message en cas d’absence du fichier
        print(f"Le fichier {filename} est introuvable.")
    # Retourne une liste de tuples (texte, catégorie)
    return corpus



# **************************************************************************************************************************************************************** # 
# --- FONCTION D'ENTRAINEMENT DU MODÈLE PERMETTANT DE CLASSER LES CV SUIVANT LEURS DOMAINES VIS A VIS DES COMPÉTENCES ET EXPÉRIENCES SE TROUVANT AU SEIN DU CV --- # 
# **************************************************************************************************************************************************************** # 



# --- Entraînement d’un classifieur SVM multi-label sur un corpus de CV ---
def train_model(corpus_file="/var/lib/cv-classifier/data/cv_corpus.txt", model_path="/var/lib/cv-classifier/data/models/cv_classifier_model.pkl"):
    """
    Entraîne un modèle SVM pour classifier les CV en plusieurs domaines.

    Modifications proposées :
      - 85% des données pour l’entraînement (test_size=0.15)
      - SVC avec class_weight="balanced" pour les classes déséquilibrées
      - Recherche du meilleur C via GridSearchCV sur [0.1, 1, 10, 100]
    """
    # Chargement du corpus texte|catégorie
    cv_samples = load_corpus_from_file(corpus_file)
    if not cv_samples:
        print("Le corpus est vide. Assurez-vous que le fichier contient des données.")
        return

    # Préparation des entrées : textes et ensembles de labels
    texts = [sample[0] for sample in cv_samples]
    labels = [set(sample[1].split(", ")) for sample in cv_samples]

    # Binarisation multi-étiquette des labels
    mlb = MultiLabelBinarizer()
    Y = mlb.fit_transform(labels)

    # normalisation puis lemmatisation ici désactivé car pas utile mais je le laisse si besoin par la suite, puis vectorisation TF-IDF (1-3 gram, filtrage fréquence)
    processed_texts = preprocess_texts(texts)
    X, vectorizer = vectorize_texts(processed_texts)

    # Séparation train/test (85% train, 15% test)
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.15, random_state=42)

    # Construction et optimisation du SVM (One-vs-Rest)
    svc = SVC(kernel="linear", probability=True, class_weight="balanced")
    classifier = OneVsRestClassifier(svc)
    param_grid = {"estimator__C": [0.1, 1, 10, 100]}
    grid = GridSearchCV(classifier, param_grid, cv=3, scoring="f1_micro")
    grid.fit(X_train, Y_train)
    model = grid.best_estimator_

    # Évaluation sur le jeu de test
    predictions = model.predict(X_test)
    print(classification_report(Y_test, predictions, target_names=mlb.classes_))

    # Sauvegarde du modèle, du vectorizer et du binarizer
    joblib.dump((model, vectorizer, mlb), model_path)
    print(f"Modèle sauvegardé sous {model_path}")

    return model, vectorizer, mlb



# *************************************************************************************************************************************** # 
# --- FONCTION PERMETTANT DE CLASSER LES CV SUIVANT LEURS DOMAINES VIS A VIS DES COMPÉTENCES ET EXPÉRIENCES SE TROUVANT AU SEIN DU CV --- # 
# *************************************************************************************************************************************** # 



def predict_cv_domain(cv_text, model_path="/var/lib/cv-classifier/data/models/cv_classifier_model.pkl", top_n=3):
    """
    Prédit les domaines les plus probables d'un candidat selon son CV.
    """
    # Vérification et chargement du modèle existant
    if not os.path.exists(model_path):
        raise FileNotFoundError("Modèle non trouvé. Entraînez d'abord le modèle avec train_model().")
    model, vectorizer, mlb = joblib.load(model_path)

    # Prétraitement et vectorisation du texte unique
    processed_text = preprocess_texts([cv_text])
    X = vectorizer.transform(processed_text)

    # Calcul des probabilités, tri et sélection des top_n labels
    proba = model.predict_proba(X)[0]
    top_indices = np.argsort(proba)[-top_n:][::-1]
    top_labels = mlb.classes_[top_indices]
    top_probabilities = proba[top_indices]

    return list(zip(top_labels, top_probabilities))



# ******************************************************************** # 
# --- POINT D'ENTRÉE DU PROGRAMME SI EXÉCUTÉ COMME SCRIPT PRINCIPAL--- # 
# ******************************************************************** # 



if __name__ == "__main__":
    train_model()




