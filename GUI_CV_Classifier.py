#!/usr/bin/env python3



# /******************************************************************************************************************************************************************************************
# Nom du fichier : GUI_CV_Classifier.py
# Rôle du fichier : Ce fichier gère l'interface graphique complète et assure de lier les fonctionnalités du programme avec des boutons simple pour l'utilisateur. 

# Auteur : Maxime BRONNY
# Version : V1
# Licence : Réalisé dans le cadre des cours "Fouille de données, Ingéniérie des langues, Développement logiciel libre, IA & Apprentisage" L3 INFORMATIQUE IED
# Usage : Un paquetage a été mit en place pour l'utiliser veuillez utiliser dans un système debian la commande suivante :
#           - INSTALLATION DU PAQUET GÉNÉRÉ
#               - sudo apt install ./cv-classifier_1.0-1_all.deb

#           Puis exécute ton programme avec :
#               - cv-classifier
# ******************************************************************************************************************************************************************************************/



# **************************************** # 
# --- LIBRAIRIES UTILISÉES POUR LA GUI --- # 
# **************************************** # 



# Import des modules de base du système
import sys            # Accès aux variables et fonctions du système Python (args, exit, version, etc.)
import os             # Interaction avec le système d'exploitation (chemins, fichiers, variables d'environnement)
import subprocess     # Exécution de processus externes (appels système, commandes shell)

# Import de la fonction de conversion de PDF en images
from pdf2image import convert_from_path  # Conversion de PDF en images PIL via Poppler

# Import des composants Qt pour l'interface utilisateur
from PyQt6.QtWidgets import (
    QApplication,   # Gestionnaire principal de l'application Qt
    QWidget,        # Widget de base pour toutes les fenêtres et éléments
    QLabel,         # Widget pour afficher du texte ou des images
    QPushButton,    # Bouton cliquable
    QFileDialog,    # Boîte de dialogue pour sélectionner fichiers/dossiers
    QVBoxLayout,    # Layout vertical pour organiser les widgets
    QMessageBox,    # Boîte de message pour alertes/informations
    QTextEdit,      # Zone de texte modifiable
    QHBoxLayout,    # Layout horizontal pour organiser les widgets
    QProgressBar,   # Barre de progression
    QGroupBox,      # Conteneur de widgets avec titre
    QSplitter,      # Séparateur redimensionnable entre widgets
    QFrame,         # Cadre générique pour structurer l'UI
    QTabWidget,     # Widget à onglets
    QTreeView,      # Arborescence pour afficher hiérarchies
    QSizePolicy     # Politique de redimensionnement des widgets
)

from PyQt6.QtGui import (
    QFont,           # Gestion des polices de caractères
    QFileSystemModel,# Modèle de données représentant le système de fichiers
    QImage,          # Classe représentant une image en mémoire
    QPixmap,         # Classe optimisée pour afficher des images dans Qt
    QKeyEvent        # Événements de frappe clavier
)

from PyQt6.QtCore import (
    QThread,         # Exécution de tâches en arrière-plan (multithreading)
    pyqtSignal,      # Système de signaux/slots pour communication entre objets Qt
    Qt               # Énumérations et constantes globales (alignements, rôles, etc.)
)

# Import pour la gestion dynamique de modules et flux de données
import importlib.util  # Utilitaires pour charger dynamiquement des modules Python
import contextlib      # Contexte managers utilitaires (suppression d'exceptions, redirections)
import io              # Manipulation de flux en mémoire (StringIO, BytesIO)




# ******************************************* # 
# --- THREAD POUR LANCER L'ANALYSE DES CV --- # 
# ******************************************* # 



class ProcessCVThread(QThread):
    # Signaux pour communication avec l'interface (texte, progression, fin de commande)
    output_line = pyqtSignal(str)
    command_done = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, folder_path):
        super().__init__()
        # Chemin du dossier à analyser
        self.folder_path = folder_path

    def run(self):
        try:
            # 1) Chargement dynamique de /var/lib/cv-classifier/main.py
            spec = importlib.util.spec_from_file_location(
                "cv_classifier_main", "/var/lib/cv-classifier/main.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, "process_cv_folder"):
                self.output_line.emit("Erreur : process_cv_folder() introuvable.")
                return

            # 2) Capture des sorties stdout/stderr
            line_count = 0

            class _Emitter(io.StringIO):
                def write(_, text):
                    nonlocal line_count
                    for line in text.splitlines():
                        if line:
                            self.output_line.emit(line)
                            line_count += 1
                            if line_count % 5 == 0:
                                self.progress.emit(min(100, line_count))

            with contextlib.redirect_stdout(_Emitter()), \
                 contextlib.redirect_stderr(_Emitter()):
                module.process_cv_folder(self.folder_path)

        except Exception as e:
            self.output_line.emit(f"Erreur d’exécution : {e}")
        finally:
            self.progress.emit(100)
            self.command_done.emit()



# ************************************************************************** # 
# --- THREAD POUR EXÉCUTER UNE COMMANDE MAKE POUR UTILISER LE 'MAKEFILE' --- # 
# ************************************************************************** # 



class MakeCommandThread(QThread):
    # Signaux pour renvoyer les lignes de sortie, la progression et la fin du processus
    output_line = pyqtSignal(str)
    command_done = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, target, directory="/var/lib/cv-classifier"):
        super().__init__()
        self.target = target
        self.directory = directory
        self.process = None

    def run(self):
        try:
            self.process = subprocess.Popen(
                ["make", "-C", self.directory, self.target],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            line_count = 0
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output_line.emit(line.rstrip())
                    line_count += 1
                    if line_count % 5 == 0:
                        self.progress.emit(min(100, line_count))
            self.process.stdout.close()
            self.process.wait()
        finally:
            self.progress.emit(100)
            self.command_done.emit()

    def send_input(self, text):
        # Envoi de texte à l'entrée standard du processus
        if self.process and self.process.stdin:
            self.process.stdin.write(text + "\n")
            self.process.stdin.flush()



# ********************************* # 
# --- INTERFACE D'ANALYSE DE CV --- # 
# ********************************* # 



class CVAnalyzerApp(QWidget):
    # Classe principale gérant l'UI et les actions utilisateur
    def __init__(self):
        super().__init__()
        # Configuration de la fenêtre
        self.setWindowTitle("Analyseur de CV Automatisé")
        self.resize(1200, 800)
        font = QFont("Poppins", 11)

        # --- Cadre de sélection de dossier ---
        selection_frame = QFrame()
        selection_frame.setObjectName("selection_frame")       # nom pour le CSS
        selection_layout = QVBoxLayout(selection_frame)
        selection_layout.setContentsMargins(8, 8, 8, 8)       # padding interne

        # Label et boutons de sélection/démarrage
        self.label = QLabel("Aucun dossier sélectionné.")
        self.label.setFont(font)
        self.button_select = QPushButton("Sélection du dossier de CV")
        self.button_select.setFont(font)
        self.button_start  = QPushButton("Lancer l’analyse")
        self.button_start.setFont(font)

        # Style et taille des boutons de dossier
        self.button_select.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.button_select.setFixedWidth(180)
        self.button_select.setStyleSheet("padding: 4px 6px; font-size: 10pt;")
        self.button_select.setMinimumWidth(200)
        self.button_select.setMinimumHeight(28)

        self.button_start.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.button_start.setFixedWidth(140)
        self.button_start.setStyleSheet("padding: 4px 6px; font-size: 10pt;")

        # Layout horizontal pour les deux boutons
        hl = QHBoxLayout()
        hl.addWidget(self.button_select)
        hl.addWidget(self.button_start)

        # Assemblage dans le cadre de sélection
        selection_layout.addWidget(self.label)
        selection_layout.addLayout(hl)

        # --- Séparateur visuel ---
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)

        # --- Groupe Installation & gestion de la BDD ---
        self.button_install = QPushButton("Installer")
        self.button_install.setFont(font)
        self.button_corpus = QPushButton("Gérer le corpus")
        self.button_corpus.setFont(font)
        self.button_clean = QPushButton("Nettoyer le cache")
        self.button_clean.setFont(font)
        group_install = QGroupBox("Installation & Gestion des BDD")
        group_install.setObjectName("group_install")
        install_layout = QVBoxLayout()
        install_layout.addWidget(self.button_install, alignment=Qt.AlignmentFlag.AlignHCenter)
        install_layout.addWidget(self.button_corpus, alignment=Qt.AlignmentFlag.AlignHCenter)
        install_layout.addWidget(self.button_clean, alignment=Qt.AlignmentFlag.AlignHCenter)
        group_install.setLayout(install_layout)

        # --- Groupe de tests des modèles ---
        self.button_check_sklearn = QPushButton("Tester Sklearn")
        self.button_check_sklearn.setFont(font)
        self.button_check_flair = QPushButton("Tester Flair")
        self.button_check_flair.setFont(font)
        group_model = QGroupBox("Modèles")
        group_model.setObjectName("group_model")
        model_layout = QVBoxLayout()
        model_layout.addWidget(self.button_check_sklearn, alignment=Qt.AlignmentFlag.AlignHCenter)
        model_layout.addWidget(self.button_check_flair, alignment=Qt.AlignmentFlag.AlignHCenter)
        group_model.setLayout(model_layout)

        # --- Section gauche de l'interface ---
        left_layout = QVBoxLayout()
        left_layout.addStretch(1)
        left_layout.addWidget(selection_frame)
        left_layout.addSpacing(10)
        left_layout.addWidget(separator)
        left_layout.addSpacing(10)
        left_layout.addWidget(group_install)
        left_layout.addWidget(group_model)
        left_layout.addStretch(1)
        left_widget = QWidget()
        left_widget.setFixedWidth(400)
        left_widget.setLayout(left_layout)

        # --- Zone de log et saisie utilisateur ---
        self.log_output = QTextEdit()
        self.log_output.setFont(QFont("Poppins", 10))
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Résultats ou messages affichés ici...")

        self.input_line = QTextEdit()
        self.input_line.setPlaceholderText("Écrivez ici et appuyez sur Entrée pour envoyer...")
        self.input_line.setFixedHeight(40)
        self.input_line.keyPressEvent = self.handle_input

        # --- Barre de progression ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Section droite de l'interface ---
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.log_output)
        right_layout.addWidget(self.input_line)
        right_layout.addWidget(self.progress_bar)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # --- Assemblage principal avec splitter ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 800])
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # --- Connexions des signaux aux actions correspondantes ---
        self.button_select.clicked.connect(self.select_folder)
        self.button_start.clicked.connect(self.start_analysis)
        self.button_check_sklearn.clicked.connect(lambda: self.run_make_command("check_Sklearn_cv_classifier"))
        self.button_check_flair.clicked.connect(lambda: self.run_make_command("check_Flair_Experiences_Compétences"))
        self.button_corpus.clicked.connect(lambda: self.run_make_command("management_corpus"))
        self.button_install.clicked.connect(lambda: self.run_make_command("install"))
        self.button_clean.clicked.connect(lambda: self.run_make_command("clean"))

        # Style uniforme pour les boutons de gestion et modèles
        for btn in [self.button_install, self.button_corpus, self.button_clean,
                    self.button_check_sklearn, self.button_check_flair]:
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            btn.setFixedSize(140, 30)
            btn.setStyleSheet("padding: 4px 6px; font-size: 10pt;")

        # Variables d'état initiales
        self.selected_folder = None
        self.make_thread = None


    # ************************************************************* # 
    # --- Gestion de l'entrée utilisateur dans la zone de texte --- # 
    # ************************************************************* # 



    def handle_input(self, event):
        if isinstance(event, QKeyEvent) and event.key() == Qt.Key.Key_Return:
            text = self.input_line.toPlainText().strip()
            self.input_line.clear()
            if self.make_thread:
                self.make_thread.send_input(text)
            else:
                self.log_output.append("Aucune commande active pour recevoir une entrée.")
        else:
            QTextEdit.keyPressEvent(self.input_line, event)



    # **************************************** # 
    # --- Dialogue de sélection de dossier --- # 
    # **************************************** # 




    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier")
        if folder:
            self.selected_folder = folder
            folder_name = os.path.basename(os.path.normpath(folder))
            self.label.setText(f"Dossier sélectionné : {folder_name}")
        else:
            self.label.setText("Aucun dossier sélectionné.")
    


    # ******************************************* # 
    # --- Lancement du thread d'analyse de CV --- # 
    # ******************************************* # 



    def start_analysis(self):
        if self.selected_folder:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.log_output.append(f"\U0001F4DD Analyse en cours du dossier : {self.selected_folder}\n")
            self.cv_thread = ProcessCVThread(self.selected_folder)
            self.cv_thread.output_line.connect(self.log_output.append)
            self.cv_thread.progress.connect(self.progress_bar.setValue)
            self.cv_thread.command_done.connect(self.analysis_finished)
            self.cv_thread.start()
        else:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un dossier d'abord.")


    # ***************************************** # 
    # --- Actions après la fin de l'analyse --- # 
    # ***************************************** # 



    def analysis_finished(self):
        self.log_output.append("\u2705 Analyse terminée avec succès !\n")
        self.progress_bar.setValue(100)



    # *********************************************************** # 
    # --- Exécution d'une commande Make dans un thread séparé --- # 
    # *********************************************************** # 



    def run_make_command(self, target):
        self.log_output.append(f"\u2699\ufe0f Exécution de : make {target}\n")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.make_thread = MakeCommandThread(target, directory="/var/lib/cv-classifier")
        self.make_thread.output_line.connect(self.log_output.append)
        self.make_thread.progress.connect(self.progress_bar.setValue)
        self.make_thread.command_done.connect(lambda: self.log_output.append("\u2705 Terminé.\n"))
        self.make_thread.command_done.connect(lambda: self.progress_bar.setValue(100))
        self.make_thread.start()



# ****************************************************************************** # 
# --- Widget pour afficher, prévisualiser et gérer les fichiers d'un dossier --- # 
# ****************************************************************************** # 



class FilePreviewer(QWidget):
    # --- Widget pour afficher, prévisualiser et gérer les fichiers d'un dossier ---
    def __init__(self, directory_path):
        super().__init__()
        self.directory_path = directory_path
        layout = QVBoxLayout(self)

        # — 1) Cadre des actions sur les fichiers (suppression / création dossier) —
        file_action_frame = QFrame()
        file_action_frame.setObjectName("file_action_frame")
        file_action_frame.setFrameShape(QFrame.Shape.StyledPanel)
        file_action_frame.setFrameShadow(QFrame.Shadow.Raised)

        self.delete_button = QPushButton("Supprimer")
        self.new_folder_button = QPushButton("Nouveau dossier")
        self.delete_button.clicked.connect(self.delete_selected_file)
        self.new_folder_button.clicked.connect(self.create_new_folder)

        fa_layout = QVBoxLayout(file_action_frame)
        fa_layout.setContentsMargins(8, 8, 8, 8)
        fa_layout.setSpacing(6)
        fa_layout.addWidget(self.delete_button)
        fa_layout.addWidget(self.new_folder_button)

        # — 2) Construction du splitter horizontal entre arbre et zone de prévisualisation —
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Arbre de l'arborescence du dossier
        self.tree = QTreeView()
        self.tree.setObjectName("dir_tree")
        self.tree.setMinimumHeight(600)
        self.model = QFileSystemModel()
        self.model.setRootPath(directory_path)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(directory_path))
        self.tree.doubleClicked.connect(self.open_file)

        # Masquage et ajustement des colonnes inutiles
        self.tree.hideColumn(1)
        self.tree.hideColumn(2)
        # self.tree.hideColumn(3)
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(3, 150)

        # Zone de prévisualisation par défaut (texte)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFont(QFont("Poppins", 10))
        self.preview.setPlaceholderText("Aucun fichier sélectionné...")

        # — 3) Assemblage de la colonne de gauche (arbre + actions) —
        left_panel = QVBoxLayout()
        left_panel.addWidget(self.tree)
        left_panel.addSpacing(100)
        left_panel.addWidget(file_action_frame)
        left_panel.addStretch(1)

        left_widget = QWidget()
        left_widget.setLayout(left_panel)

        # Ajout des widgets au splitter et réglage des proportions
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.preview)
        self.splitter.setSizes([450, 600])

        # Intégration du splitter dans le layout principal
        layout.addWidget(self.splitter)
        self.setLayout(layout)



    # ****************************************************************************************** # 
    # --- Fonction ouvrant et affichant le contenu d'un fichier (texte ou première page PDF) --- # 
    # ****************************************************************************************** # 



    def open_file(self, index):
        self.selected_path = self.model.filePath(index)
        if os.path.isfile(self.selected_path):
            ext = os.path.splitext(self.selected_path)[1].lower()
            if ext == ".pdf":
                try:
                    pages = convert_from_path(self.selected_path, fmt='png', dpi=100, first_page=1, last_page=1)
                    if pages:
                        image = pages[0]
                        image = image.resize((600, 800))
                        qimage = QImage(image.tobytes(), image.width, image.height, QImage.Format.Format_RGB888)
                        pixmap = QPixmap.fromImage(qimage)

                        self.splitter.widget(1).deleteLater()
                        self.preview = QLabel()
                        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.preview.setPixmap(pixmap)
                        self.splitter.insertWidget(1, self.preview)
                    else:
                        self.preview.setText("Conversion du PDF échouée.")
                except Exception as e:
                    self.preview.setText(f"Erreur lors de l'ouverture du PDF : {e}")
            else:
                current = self.splitter.widget(1)
                current.deleteLater()
                self.preview = QTextEdit()
                self.preview.setReadOnly(True)
                self.preview.setFont(QFont("Poppins", 10))
                self.preview.setPlaceholderText("Aucun fichier sélectionné...")
                self.splitter.insertWidget(1, self.preview)
                try:
                    with open(self.selected_path, "r", encoding="utf8") as f:
                        content = f.read()
                    self.preview.setPlainText(content)
                except Exception as e:
                    self.preview.setPlainText(f"Erreur lors de l'ouverture du fichier : {e}")



    # ********************************************************************************************* # 
    # --- Fonction permettant de supprimer le fichier ou dossier sélectionné après confirmation --- # 
    # ********************************************************************************************* # 


    # --- Supprime le fichier ou dossier sélectionné après confirmation ---
    def delete_selected_file(self):
        index = self.tree.currentIndex()
        file_path = self.model.filePath(index)
        if os.path.exists(file_path):
            confirm = QMessageBox.question(
                self, "Confirmer la suppression",
                f"Voulez-vous vraiment supprimer :\n{file_path}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                try:
                    if os.path.isdir(file_path):
                        os.rmdir(file_path)
                    else:
                        os.remove(file_path)
                    QMessageBox.information(self, "Suppression réussie", "Fichier supprimé.")
                except Exception as e:
                    QMessageBox.warning(self, "Erreur", f"Impossible de supprimer le fichier :\n{e}")



    # ***************************************************************************************** # 
    # --- Fonction permettant de créer un nouveau dossier à la racine du répertoire courant --- # 
    # ***************************************************************************************** # 



    def create_new_folder(self):
        folder_name, ok = QFileDialog.getSaveFileName(
            self, "Nom du nouveau dossier", self.directory_path
        )
        if ok and folder_name.strip():
            new_folder_path = os.path.join(self.directory_path, folder_name.strip())
            try:
                os.makedirs(new_folder_path, exist_ok=False)
                QMessageBox.information(self, "Création réussie", f"Dossier créé :\n{new_folder_path}")
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Impossible de créer le dossier :\n{e}")



# ************************************************************************************* # 
# --- CONTENEUR PRINCIPAL AVEC ONGLETS POUR LA GESTION DES CV ET APERCU DE FICHIERS --- #
# ************************************************************************************* # 



class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Titre et taille de la fenêtre
        self.setWindowTitle("Application de Classification de CV")
        self.resize(1200, 800)

        # --- Cadre principal pour fond et bordure ---
        main_frame = QFrame(self)
        main_frame.setObjectName("main_frame")
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)  # pas de marge interne
        frame_layout.setSpacing(0)                    # pas d'espacement

        # --- Création du widget d'onglets ---
        self.tabs = QTabWidget()
        frame_layout.addWidget(self.tabs)

        # --- Onglet : Analyse de CV ---
        self.cv_app = CVAnalyzerApp()
        self.tabs.addTab(self.cv_app, "Analyse de CV")

        # --- Onglet : Aperçu de fichier (si le dossier existe) ---
        ats_path = "/var/lib/cv-classifier/ATS_Classement/"
        if not os.path.exists(ats_path):
            print(f"Le dossier {ats_path} n'existe pas.")
        else:
            self.file_previewer = FilePreviewer(ats_path)
            self.tabs.addTab(self.file_previewer, "Aperçu de fichier")

        # --- Layout extérieur avec marge pour border autour du frame ---
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(4, 4, 4, 4)
        outer_layout.addWidget(main_frame)
        self.setLayout(outer_layout)



# ****************************************** # 
# --- DÉMARRAGE DE L'INTERFACE GRAPHIQUE --- #
# ****************************************** # 



if __name__ == "__main__":
    # 1) Initialisation de l'application Qt
    app = QApplication(sys.argv)

    # 2) Application du style Fusion pour l'apparence générale
    app.setStyle("Fusion")

    # 3) Chargement et application du thème global via une feuille de style CSS
    app.setStyleSheet("""
    /* Cadre blanc de 4px autour de tout le frame principal */
    QFrame#main_frame {
        border: 1px solid #FFFFFF;
        border-radius: 0px;   /* ou 4px si vous souhaitez des coins arrondis */
    }
    /* 1. Fond & texte généraux */
    QWidget {
        /* Bleu Copilot ultra-foncé */
        background: qlineargradient(
            x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 #001A2B,   /* bleu foncé intense en haut */
            stop: 1 #00071A    /* presque noir en bas */
        );
        color: #FFFFFF;
        font-family: "Poppins", "Segoe UI", sans-serif;
        font-size: 11pt;
    }
    /* 2. Boutons modernes & sobres */
    QPushButton {
        background-color: #0F172A;       /* fond bleu nuit */
        color: #38BDF8;                  /* texte bleu néon */
        border: 1px solid #1E88E5;       /* liseré bleu clair */
        border-radius: 8px;
        padding: 4px 12px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #1E293B;       /* survol subtil */
    }
    QPushButton:pressed {
        background-color: #1E88E5;       /* clic = accent plein */
        color: #FFFFFF;                  /* texte blanc sur fond bleu vif */
    }

    /* 3. Champs de saisie, textedit, combo, spinbox, tables */
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QTableWidget {
        background-color: #1E1E1E;
        color: #E0E0E0;
        border: 1px solid #333333;
        border-radius: 4px;
        selection-background-color: #2196F3;
        selection-color: #FFFFFF;
    }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
        border: 1px solid #1E88E5;
    }

    /* 4. Onglets (tabbar + pane) */
    QTabWidget::pane {
        border: none;
        background: #121212;
    }
    QTabBar::tab {
        background: #1E1E1E;
        color: #E0E0E0;
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    QTabBar::tab:selected {
        background: #121212;
        color: #1E88E5;
    }

    /* 5. Scrollbars fines & sombres */
    QScrollBar:vertical {
        background: #121212;
        width: 8px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #424242;
        min-height: 20px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #616161;
    }
    QScrollBar::add-line, QScrollBar::sub-line,
    QScrollBar::add-page, QScrollBar::sub-page {
        background: none;
        border: none;
    }

    /* 6. En-têtes de table simplifiées */
    QHeaderView::section {
        background-color: #1E1E1E;
        color: #1E88E5;
        padding: 4px;
        border: 1px solid #333333;
    }

    /* 7. GroupBox épuré */
    QGroupBox {
        border: 1px solid #333333;
        border-radius: 4px;
        margin-top: 10px;
        padding: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 5px;
        color: #1E88E5;
    }
    /* 8. Contour blanc pour les boîtes spécifiques */
    QGroupBox#group_install,
    QGroupBox#group_model {
      border: 2px solid #FFFFFF;
      border-radius: 4px;
    }
    /* --- contour blanc autour du cadre de sélection de dossier --- */
    QFrame#selection_frame {
        border: 2px solid #FFFFFF;
        border-radius: 4px;
        padding: 8px;           /* espace interne */
        margin-bottom: 10px;    /* séparation visuelle avant la suite */
    }
    /* 9) Bordures blanches sur le panel de boutons et l'arborescence */
    QFrame#file_action_frame,
    QTreeView#dir_tree {
        border: 2px solid #FFFFFF;
        border-radius: 4px;
    }
    /* 10. Progress bar avec bordure blanche */
    QProgressBar#progress_bar {
        border: 2px solid #FFFFFF;
        border-radius: 2px;
        background-color: #1E1E1E;         /* fond foncé neutre */
        text-align: center;
        height: 20px;
    }
    QTextEdit {
        background-color: #001322;     /* teinte intermédiaire entre les deux stops */
        color: #E0F7FA;                /* texte très clair, bleuté */
        border: 1px solid #003144;
        border-radius: 4px;
        padding: 6px;
        font-family: "Poppins", "Segoe UI", sans-serif;
        font-size: 11pt;
    }

    """)

    # 4) Création et affichage de la fenêtre principale
    window = MainWidget()
    window.showMaximized()

    # 5) Démarrage de la boucle d'exécution de l'application
    sys.exit(app.exec())



