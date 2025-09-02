# Classificateur de CV
![Présentation du projet](./images/présentation classificateur CV.pdf)

![Python](https://img.shields.io/badge/python-3.8-blue)
![Build](https://img.shields.io/badge/build-passing-brightgreen)

## Description

Ce projet a été développé dans le cadre de la validation des matières "Fouille de données", "Ingénierie des langues", "Développement logiciel libre" et "IA & Apprentissage" du cursus L3 INFORMATIQUE IED.

## Fonctionnalités

- **Classification automatique de CV** par domaine d'expertise
- **Extraction de compétences** à partir de documents PDF
- **Reconnaissance d'entités nommées (NER)** avec Flair
- **Interface graphique** moderne avec PyQt6
- **Support multilingue** (français principalement)
- **Export des données** en formats JSON et CSV
- **Modèles de machine learning** pré-entraînés

## Technologies utilisées

- **Python 3.8+**
- **Flair** - Framework NLP pour la reconnaissance d'entités
- **PyQt6** - Interface graphique moderne
- **scikit-learn** - Classification et machine learning
- **spaCy** - Traitement du langage naturel
- **PDFplumber** - Extraction de texte depuis les PDF
- **Transformers** - Modèles de langage avancés

## Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Installation du modèle spaCy français

```bash
python -m spacy download fr_core_news_sm
```

## Utilisation

### Interface graphique

```bash
python GUI_CV_Classifier.py
```

### Ligne de commande

```bash
python main.py
```

### Installation via paquet Debian

```bash
sudo dpkg -i cv-classifier_1.0-1_all.deb
cv-classifier
```

## Structure du projet

```
cv-classifier/
├── main.py                          # Point d'entrée principal
├── GUI_CV_Classifier.py            # Interface graphique
├── Sklearn_cv_classifier.py        # Classifieur ML
├── Flair_Experiences_Compétences.py # Extraction NER
├── Segmentation_cv_json_csv.py     # Traitement des PDF
├── data/                           # Données et modèles
│   ├── models/                     # Modèles entraînés
│   └── corpus/                     # Corpus d'entraînement
├── requirements.txt                 # Dépendances Python
└── README.md                       # Documentation
```

## Fonctionnalités principales

### 1. Classification de CV
- Détection automatique du domaine d'expertise
- Support pour Data Science, DevOps, Cybersécurité, IA, etc.

### 2. Extraction de compétences
- Reconnaissance de compétences techniques
- Extraction d'expériences professionnelles
- Normalisation et lemmatisation des termes

### 3. Traitement de documents
- Support des formats PDF
- Extraction de texte structuré
- Segmentation automatique des sections

### 4. Interface utilisateur
- Interface moderne et intuitive
- Visualisation des résultats
- Export des données extraites

## Modèles inclus

- **Modèle NER français** : Reconnaissance d'entités nommées
- **Modèle de classification** : Prédiction du domaine de CV
- **Modèle de lemmatisation** : Normalisation des termes

## Contribution

Ce projet est développé dans un cadre académique. Pour toute question ou suggestion, n'hésitez pas à ouvrir une issue.

## Licence

Projet réalisé dans le cadre des cours de L3 INFORMATIQUE IED.

## Auteur

**Maxime BRONNY** - Étudiant en L3 INFORMATIQUE IED

---

*Développé avec ❤️ pour l'analyse et la classification automatique de CV*
