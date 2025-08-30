# *************************************************************** # 
# --- Makefile pour gérer les différentes étapes du programme --- # 
# *************************************************************** #



.PHONY: clean install management_corpus trainmodel run check_Sklearn_cv_classifier check_Flair_Experiences_Compétences



# ********************************************* # 
# --- Installer les dépendances nécessaires --- # 
# ********************************************* #



install:
	@python3 check_files.py

	@echo "Installation des dépendances Python (si requirements.txt présent)..."
	@if [ -f /var/lib/cv-classifier/requirements.txt ]; then \
		echo ">> requirements.txt trouvé, installation..."; \
		pip install -r /var/lib/cv-classifier/requirements.txt || true; \
	else \
		echo ">> requirements.txt non trouvé, on continue sans erreur."; \
	fi

	@echo "requirements.txt toutes les dépendances sont vérifiées ! "

	@echo "Post-installation : installation de la police Poppins..."

	@FONT_DIR="$HOME/.fonts/Poppins"
	@mkdir -p "$FONT_DIR"

	@wget -q https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf -O "$FONT_DIR/Poppins-Regular.ttf"
	@wget -q https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf -O "$FONT_DIR/Poppins-Bold.ttf"
	@wget -q https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Italic.ttf -O "$FONT_DIR/Poppins-Italic.ttf"
	@wget -q https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-BoldItalic.ttf -O "$FONT_DIR/Poppins-BoldItalic.ttf"

	@fc-cache -fv "$FONT_DIR" || echo "Impossible de mettre à jour le cache de police."

	@echo "Police Poppins installée."



# *********************** # 
# --- Gérer le corpus --- # 
# *********************** #



management_corpus:
	@python3 check_files.py
	@echo "Démarrage de la gestion du corpus..."
	@if [ -f "BDD_CV_Corpus.py" ]; then \
		python3 BDD_CV_Corpus.py; \
	else \
		echo "Le fichier 'BDD_CV_Corpus.py' est introuvable."; \
	fi
	@if [ -f "BDD_Flair.py" ]; then \
		python3 BDD_Flair.py; \
	else \
		echo "Le fichier 'BDD_Flair.py' est introuvable."; \
	fi
	@echo "Gestion du corpus terminée !"



# ***************************** # 
# --- Entraîner les modèles --- # 
# ***************************** #



trainmodel:
	@python3 check_files.py
	@$(MAKE) check_Sklearn_cv_classifier
	@$(MAKE) check_Flair_Experiences_Compétences
	@echo "Entraînement des modèles terminé."

check_Sklearn_cv_classifier:
	@if [ -f "data/models/cv_classifier_model.pkl" ]; then \
		read -p "Le fichier cv_classifier_model.pkl existe déjà. Voulez-vous lancer l'entrainement d'un autre modèle de classification des candidats ? (y/n) " choice; \
		if [ "$$choice" = "y" ]; then \
			python3 Sklearn_cv_classifier.py; \
		else \
			echo "Sklearn_cv_classifier.py ignoré."; \
		fi; \
	else \
		read -p "Le fichier cv_classifier_model.pkl n'existe pas. Voulez-vous entraîner un nouveau modèle ? (y/n) " new_train; \
		if [ "$$new_train" = "y" ]; then \
			python3 Sklearn_cv_classifier.py; \
		else \
			echo "Entraînement du modèle annulé."; \
		fi; \
	fi

check_Flair_Experiences_Compétences:
	@if [ -f "data/models/flair_ner_model/best-model.pt" ]; then \
		read -p "Le fichier best-model.pt existe déjà. Voulez-vous lancer l'entrainement d'un autre modèle d'extraction de compétences et d'expériences ? (y/n) " choice; \
		if [ "$$choice" = "y" ]; then \
			python3 Flair_Experiences_Compétences.py; \
		else \
			echo "Flair_Experiences_Compétences.py ignoré."; \
		fi; \
	else \
		read -p "Le fichier best-model.pt n'existe pas. Voulez-vous entraîner un nouveau modèle ? (y/n) " new_train; \
		if [ "$$new_train" = "y" ]; then \
			python3 Flair_Experiences_Compétences.py; \
		else \
			echo "Entraînement du modèle annulé."; \
		fi; \
	fi



# ************************************* # 
# --- Lancer le programme principal --- # 
# ************************************* #



run:
	@python3 check_files.py
	@echo "Démarrage du programme principal..."
	@if [ -f "main.py" ]; then \
		read -p "Le fichier main.py existe. Voulez-vous l'exécuter ? (y/n) " choice; \
		if [ "$$choice" = "y" ]; then \
			python3 main.py; \
		else \
			echo "main.py ignoré."; \
		fi; \
	else \
		echo "main.py n'existe pas."; \
	fi
	@echo "Exécution terminée."



# ***************************************** # 
# --- Nettoyage des fichiers temporaires--- # 
# ***************************************** #



clean:
	@rm -rf __pycache__
	@echo "Clean de __pycache__ terminée !"
