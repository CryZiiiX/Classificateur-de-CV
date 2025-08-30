# /********************************************************************************************************************************************************************************************
# Nom du fichier : Flair_Experiences_Compétences.py
# Rôle du fichier : Ce fichier est responsable de l'entrainement du modèle qui s'occupe d'apprendre a reconnaitre les compétences et experiences dans les CV afin d'en sortir 

# Auteur : Maxime BRONNY
# Version : V1
# Licence : Réalisé dans le cadre des cours "Fouille de données, Ingéniérie des langues, Développement logiciel libre, IA & Apprentisage" L3 INFORMATIQUE IED
# Usage : Un paquetage a été mit en place pour l'utiliser veuillez utiliser dans un système debian la commande suivante :
#           - INSTALLATION DU PAQUET GÉNÉRÉ
#               - sudo apt install ./cv-classifier_1.0-1_all.deb

#           Puis exécute ton programme avec :
#               - cv-classifier
# *******************************************************************************************************************************************************************************************/



# *********************************************************************** # 
# --- LIBRAIRIES UTILISÉES POUR LE FICHIER DE GESTION DE MODÈLE FLAIR --- # 
# *********************************************************************** # 



# Modules de base pour la représentation de phrases et la gestion de corpus
from flair.datasets import ColumnCorpus

# Embeddings : vecteurs de mots et embeddings contextuels empilés
from flair.embeddings import WordEmbeddings, FlairEmbeddings, StackedEmbeddings

# Modèle de tagging séquentiel et son entraîneur
from flair.models import SequenceTagger
from flair.trainers import ModelTrainer

# Utilitaires standards Python
import random
import os



# *********************************************** # 
# --- FONCTION D'ENTRAINEMENT DU MODÈLE FLAIR --- # 
# *********************************************** # 



def train_flair_ner_model(data_folder, train_file="/var/lib/cv-classifier/data/models/train.txt", test_file="/var/lib/cv-classifier/data/models/test.txt", dev_file="/var/lib/cv-classifier/data/models/dev.txt"):
    """Entraîne un modèle Flair NER sur un corpus annoté."""
    
    # 1. Nettoyage : suppression de tout ancien modèle Flair
    if os.path.exists('/var/lib/cv-classifier/data/models/flair_ner_model'):
        print("Suppression de l'ancien modèle...")
        os.system("rm -rf /var/lib/cv-classifier/data/models/flair_ner_model")
    
    # 2. Inspection rapide des données d'entraînement avant traitement
    with open(train_file, "r", encoding="utf-8") as f:
        print("Exemple de phrase dans train.txt :", f.readlines()[:10])
    
    # 3. Séparation du corpus en ensembles d'entraînement, de test et de validation
    split_train_test_dev(train_file, test_file, dev_file)
    
    # 4. Vérification du contenu après la séparation
    with open(train_file, "r", encoding="utf-8") as f:
        train_sentences = f.readlines()
        print("Exemple de phrase après séparation dans train.txt :", train_sentences[:10])
    
    # 5. Chargement du corpus avec les colonnes 'text' et 'ner'
    columns = {0: 'text', 1: 'ner'}
    corpus = ColumnCorpus(data_folder, columns,
                          train_file=train_file,
                          test_file=test_file,
                          dev_file=dev_file)
    
    # 6. Création et affichage du dictionnaire initial des entités NER
    print("Entités NER trouvées dans train.txt :", 
          corpus.make_label_dictionary('ner').idx2item)
    tag_dictionary = corpus.make_tag_dictionary(tag_type='ner')
    
    # 7. Ajout manuel des étiquettes BIO pour les entités spécifiques
    tag_dictionary.add_item("B-EXPERIENCE")
    tag_dictionary.add_item("B-COMPETENCE")
    tag_dictionary.add_item("B-DIPLOME")
    tag_dictionary.add_item("B-ORG")
    tag_dictionary.add_item("B-DUREE")
    tag_dictionary.add_item("B-DATE")
    tag_dictionary.add_item("B-LOC")

    tag_dictionary.add_item("I-EXPERIENCE")
    tag_dictionary.add_item("I-COMPETENCE")
    tag_dictionary.add_item("I-DIPLOME")
    tag_dictionary.add_item("I-ORG")
    tag_dictionary.add_item("I-DUREE")
    tag_dictionary.add_item("I-DATE")
    tag_dictionary.add_item("I-LOC")

    tag_dictionary.add_item("S-EXPERIENCE")
    tag_dictionary.add_item("S-COMPETENCE")
    tag_dictionary.add_item("S-DIPLOME")
    tag_dictionary.add_item("S-ORG")
    tag_dictionary.add_item("S-DUREE")
    tag_dictionary.add_item("S-DATE")
    tag_dictionary.add_item("S-LOC")

    tag_dictionary.add_item("E-EXPERIENCE")
    tag_dictionary.add_item("E-COMPETENCE")
    tag_dictionary.add_item("E-DIPLOME")
    tag_dictionary.add_item("E-ORG")
    tag_dictionary.add_item("E-DUREE")
    tag_dictionary.add_item("E-DATE")
    tag_dictionary.add_item("E-LOC")
    
    print("Tags détectés dans le corpus :", tag_dictionary.idx2item)
    
    # 8. Construction des embeddings (mots + Flair français)
    embeddings = StackedEmbeddings([
        WordEmbeddings('fr'),
        FlairEmbeddings('fr-forward'),
        FlairEmbeddings('fr-backward')
    ])
    
    # 9. Initialisation du SequenceTagger (modèle de séquence)
    taggerEXPERIENCE = SequenceTagger(
        hidden_size=256,
        embeddings=embeddings,
        tag_dictionary=tag_dictionary,
        tag_type='ner',
        use_crf=False
    )
    
    # 10. Entraînement du modèle sur le corpus
    trainer = ModelTrainer(taggerEXPERIENCE, corpus)
    trainer.train('/var/lib/cv-classifier/data/models/flair_ner_model',
                  max_epochs=20,
                  mini_batch_size=16,
                  train_with_dev=False)
    
    # 11. Affichage des étiquettes finales et confirmation de sauvegarde
    print("Tags finaux dans le modèle après entraînement :", 
          taggerEXPERIENCE.label_dictionary.idx2item)
    print("Entraînement terminé et modèle sauvegardé !")



# ******************************************************************* # 
# --- FONCTION POUR LE CHARGEMENT DU MODÈLE --- # 
# ******************************************************************* # 



# Chargement et utilisation du modèle Flair NER pré-entraîné
def load_flair_ner_model():
    """
    Charge le modèle NER Flair préalablement entraîné.
    """
    print("Chargement du modèle best-model.pt...")
    return SequenceTagger.load('/var/lib/cv-classifier/data/models/flair_ner_model/best-model.pt')



# ********************************************************************************************************************** # 
# --- FONCTION SERVANT A DIVISER LE FICHIER D'ENTRAINEMENT EN ENSEMBLES TRAIN/TEST/DEV (dev servant a la validation) --- # 
# ********************************************************************************************************************** # 



def split_train_test_dev(train_file, test_file, dev_file, test_ratio=0.2, dev_ratio=0.2):
    """
    Sépare les données en trois fichiers : entraînement, test et validation,
    en fonction des ratios spécifiés.
    """
    
    # Vérification de l'existence et du contenu du fichier source
    if not os.path.exists(train_file):
        print(f"Erreur : {train_file} n'existe pas.")
        return
    with open(train_file, "r", encoding="utf-8") as f:
        data = f.read().strip()  # Lecture et suppression des espaces superflus
    if not data:
        print("Erreur : train.txt est vide !")
        return

    # Extraction des phrases en les séparant par des lignes vides
    sentences = [s.strip() for s in data.split("\n\n") if s.strip()]
    print(f"Total de phrases dans train.txt : {len(sentences)}")

    if len(sentences) < 3:
        print("Erreur : Pas assez de phrases pour diviser en train/dev/test.")
        return

    # Mélange aléatoire des phrases
    random.shuffle(sentences)

    # Détermination des tailles minimales pour chaque ensemble
    total = len(sentences)
    test_size = max(1, int(total * test_ratio))
    dev_size = max(1, int(total * dev_ratio))

    # Attribution des phrases aux ensembles correspondants
    test_data = sentences[:test_size]
    dev_data = sentences[test_size:test_size + dev_size]
    train_data = sentences[test_size + dev_size:]

    # Écriture des données dans les fichiers respectifs
    for file, data in [(train_file, train_data), (test_file, test_data), (dev_file, dev_data)]:
        with open(file, "w", encoding="utf-8") as f:
            f.write("\n\n".join(data) if data else "")

    print(f"Fichiers générés : train ({len(train_data)} phrases), dev ({len(dev_data)} phrases), test ({len(test_data)} phrases)")



if __name__ == "__main__":
    # Exécution de l'entraînement uniquement en mode script
    train_flair_ner_model("/var/lib/cv-classifier/data/")


    
