from PySide6.QtCore import QSettings

TRANSLATIONS = {
    'fr': {
        # Menus
        'menu_file': '📁 &Fichier',
        'menu_edit': '✏️ &Édition',
        'menu_comp': '🧩 &Composants',
        'menu_view': '👁️ &Affichage',
        'menu_sim': '⚡ &Simulation',
        'menu_tools': '🛠️ &Tools',
        'act_teacher_mode': '🎓 Teacher Workspace...',
        'act_settings': '⚙️ Settings...',
                        'menu_courses': '🎓 &Cours & TPs',
        'menu_examples': '💡 &Exemples',
        'menu_help': '❓ &Aide',
        'menu_theme': '🎨 &Thème de l\'interface',
        'menu_language': '🌍 &Langue / Language',

        # Actions Fichier
        'act_home': '🏠 Page d\'accueil',
        'act_new': '📄 Nouveau montage',
        'act_open': '📂 Ouvrir un projet...',
        'menu_recent': '🕒 Projets récents',
        'no_recent_files': 'Aucun fichier récent',
        'act_close': '❌ Fermer le projet',
        'act_save': '💾 Enregistrer',
        'act_save_as': '💾 Enregistrer sous...',
        'act_export_report': '📑 Exporter le compte-rendu de TP...',
        'act_export_bom': '📦 Exporter la nomenclature des composants (BOM CSV)...',
        'act_exit': '🚪 Quitter',

        # Actions Édition
        'act_undo': '↩ Annuler',
        'act_redo': '↪ Rétablir',
        'act_rotate': '🔄 Faire pivoter de 90°',
        'act_delete': '🗑 Supprimer l\'élément sélectionné',
        'act_select_all': '📋 Tout sélectionner',
        'act_clear_circuit': '🧹 Tout effacer (Réinitialiser le montage)',

        # Actions Composants
        'menu_boards': '🎛️ Cartes & Platines',
        'comp_esp32': '🎛️ ESP32 DevKit V1 (30 broches)',
        'menu_basics': '⚡ Composants de base',
        'comp_led': '💡 Diode LED standard',
        'comp_resistor': '⚡ Résistance (220Ω)',
        'comp_button': '🔘 Bouton-Poussoir tactile',
        'comp_switch': '🔀 Interrupteur à glissière SPDT',
        'comp_pot': '🎚️ Potentiomètre rotatif',
        'comp_joystick': '🕹️ Joystick analogique 2 axes',
        'comp_buzzer': '🔊 Buzzer Piezoélectrique',
        'comp_relay': '🔀 Module Relais 5V',
        'comp_servo': '🦾 Servomoteur SG90',
        'menu_displays': '📺 Afficheurs & Optique',
        'comp_rgb_led': '🔴🟢🔵 LED RGB 5mm (Cathode commune)',
        'comp_neopixel': '🌈 Ruban LED RGB NeoPixel (WS2812B)',
        'comp_oled': '📱 Écran OLED SSD1306 128x64 (I2C)',
        'comp_lcd': '📟 Écran LCD 1602 (I2C)',
        'menu_sensors': '🌡️ Capteurs',
        'comp_ldr': '☀️ Photorésistance LDR',
        'comp_pir': '🏃 Capteur de mouvement PIR HC-SR501',
        'comp_dht22': '🌡️ Capteur Température & Humidité DHT22',
        'comp_hcsr04': '📡 Capteur de distance Ultrason HC-SR04',

        # Actions Affichage
        'act_v_sim': '🖥️ Vue Maquette Réaliste (Lab)',
        'act_v_schema': '📐 Vue Schéma Électrique CEI',
        'act_zoom_in': '🔍 Zoom avant',
        'act_zoom_out': '🔍 Zoom arrière',
        'act_zoom_fit': '⛶ Ajuster la vue au montage',
        'act_toggle_montage': '🔌 Volet Montage & Platine physique',
        'act_toggle_palette': '📋 Volet Bibliothèque de composants',
        'act_toggle_props': '⚙ Volet Propriétés du composant',
        'act_toggle_console': '📟 Console Série & REPL',
        'act_toggle_scope': '📊 Oscilloscope & Analyseur',
        'act_toggle_erc': '🛡️ Diagnostic Électrique (ERC)',
        'theme_dark': '🌙 Thème Sombre (Dark)',
        'theme_light': '☀️ Thème Clair (Light)',

        # Actions Simulation
        'act_run': '▶ Démarrer la simulation',
        'act_stop': '⏹ Arrêter la simulation',
        'act_reset': '↻ Réinitialiser ESP32',
        'act_erc': '🛡️ Vérifier le circuit (Règles ERC)',
        'act_upload': '☁ Téléverser vers ESP32 physique...',
        'act_bridge': '🌐 Passerelle Réseau Réelle (Hôte PC)',
        'act_bridge_tip': 'Permet à l\'ESP32 simulé d\'utiliser la vraie connexion Internet du PC (sockets réels, requêtes HTTP, IP locale).',

        # Actions Cours & Exemples & Aide
        'act_all_courses': '📚 Catalogue complet des cours & TPs...',
        'act_evaluate': '📝 Auto-évaluation du circuit actuel...',
        'act_all_examples': '💡 Parcourir la bibliothèque d\'exemples...',
        'act_guide': '📖 Guide de câblage sur Breadboard...',
        'act_shortcuts': '⌨ Raccourcis clavier & Gestes...',
        'act_updates': '🔄 Rechercher des mises à jour...',
        'act_about': 'ℹ️ À propos de ESP32 MicroPython Lab...',

        # Barre de navigation supérieure (Header)
        'btn_nav_home': '🏠 Accueil',
        'btn_nav_home_tip': 'Afficher la page d\'accueil (Ctrl+H)',
        'btn_nav_lab': '💻 Laboratoire',
        'btn_nav_lab_tip': 'Basculer vers l\'espace de travail du laboratoire',
        'app_tagline': 'Coder · Simuler · Expérimenter · Apprendre',

        # Volet simulation et outils
        'title_montage': '🔌 Montage & Platine',
        'zoom_label': 'Zoom',
        'btn_fit_tip': 'Ajuster la vue',
        'zoom_in_tip': 'Agrandir la taille du texte (Ctrl + +)',
        'zoom_out_tip': 'Diminuer la taille du texte (Ctrl + -)',
        'zoom_reset_tip': 'Réinitialiser la taille du texte',

        # Boutons d'action rapides
        'btn_simulate': '▶ Simuler',
        'btn_upload': '☁ Téléverser vers ESP32',
        'btn_stop': '⏹ Stop',
        'btn_reset': '↻ Reset',
        'btn_simulate_tip': 'Démarrer la simulation MicroPython (F5)',
        'btn_stop_tip': 'Arrêter la simulation (F6)',
        'btn_upload_tip': 'Téléverser vers ESP32 physique connecté en USB',
        'btn_reset_tip': 'Réinitialiser l\'ESP32 et la simulation',

        # Onglets
        'tab_simulation': '🧪 Laboratoire Virtuel (Montage)',
        'tab_schematic': '📐 Schéma Électronique Normalisé',
        'tab_console_repl': '📟 Console Série & REPL',
        'tab_oscilloscope': '📊 Oscilloscope & Analyseur Logique',
        'tab_erc': '🛡️ Diagnostic Électrique (ERC)',

        # Page d'accueil
        'welcome_tagline': 'Laboratoire Virtuel de Programmation MicroPython & Électronique',
        'welcome_desc': 'Coder · Simuler · Expérimenter · Apprendre',
        'welcome_hint': 'Ouvrez ou créez un montage depuis le menu Fichier (Ctrl+N / Ctrl+O)',
        'welcome_chk_startup': 'Afficher cette page d\'accueil au démarrage',

        # Barre d'état
        'status_ready': 'Prêt. Créez votre montage ou lancez la simulation.',
        'status_running': 'Simulation en cours d\'exécution...',
        'status_stopped': 'Simulation arrêtée.',
        'status_reset': 'Simulation réinitialisée.',
        'status_welcome': 'Page d\'accueil — Choisissez un point de départ.',
        'status_workspace': 'Espace de travail actif.',
        'lang_changed': 'Langue appliquée : Français',

        # Mises à jour
        'update_checking': 'Vérification des mises à jour en cours...',
        'update_up_to_date': 'Vous utilisez la version la plus récente de ESP32 MicroPython Lab.',
        'update_available_title': 'Nouvelle version disponible !',
        'update_btn_download': 'Télécharger la mise à jour',
        'update_btn_later': 'Plus tard',

        # Enregistrement des modifications
        'save_changes_title': 'Enregistrer les modifications ?',
        'save_changes_msg': 'Le projet en cours a été modifié.\nVoulez-vous enregistrer les modifications avant de {action} ?',
        'btn_save': 'Enregistrer',
        'btn_dont_save': 'Ne pas enregistrer',
        'btn_cancel': 'Annuler',
    },
    'en': {
        # Menus
        'menu_file': '📁 &File',
        'menu_edit': '✏️ &Edit',
        'menu_comp': '🧩 &Components',
        'menu_view': '👁️ &View',
        'menu_sim': '⚡ &Simulation',
        'menu_tools': '🛠️ &Outils',
        'act_teacher_mode': '🎓 Espace Enseignant...',
        'act_settings': '⚙️ Paramètres...',
                'menu_courses': '🎓 &Lessons & Labs',
        'menu_examples': '💡 &Examples',
        'menu_help': '❓ &Help',
        'menu_theme': '🎨 &Interface Theme',
        'menu_language': '🌍 &Language / Langue',

        # Actions File
        'act_home': '🏠 Welcome Home',
        'act_new': '📄 New Project',
        'act_open': '📂 Open Project...',
        'menu_recent': '🕒 Recent Projects',
        'no_recent_files': 'No recent files',
        'act_close': '❌ Close Project',
        'act_save': '💾 Save',
        'act_save_as': '💾 Save As...',
        'act_export_report': '📑 Export Lab Report...',
        'act_export_bom': '📦 Export Bill of Materials (BOM CSV)...',
        'act_exit': '🚪 Exit',

        # Actions Edit
        'act_undo': '↩ Undo',
        'act_redo': '↪ Redo',
        'act_rotate': '🔄 Rotate 90°',
        'act_delete': '🗑 Delete Selected Item',
        'act_select_all': '📋 Select All',
        'act_clear_circuit': '🧹 Clear All (Reset Circuit)',

        # Actions Components
        'menu_boards': '🎛️ Boards & Breadboards',
        'comp_esp32': '🎛️ ESP32 DevKit V1 (30 pins)',
        'menu_basics': '⚡ Basic Components',
        'comp_led': '💡 Standard LED',
        'comp_resistor': '⚡ Resistor (220Ω)',
        'comp_button': '🔘 Push Button',
        'comp_switch': '🔀 SPDT Slide Switch',
        'comp_pot': '🎚️ Rotary Potentiometer',
        'comp_joystick': '🕹️ 2-Axis Analog Joystick',
        'comp_buzzer': '🔊 Piezo Buzzer',
        'comp_relay': '🔀 5V Relay Module',
        'comp_servo': '🦾 SG90 Servo Motor',
        'menu_displays': '📺 Displays & Optics',
        'comp_rgb_led': '🔴🟢🔵 RGB LED 5mm (Common Cathode)',
        'comp_neopixel': '🌈 NeoPixel RGB LED Strip (WS2812B)',
        'comp_oled': '📱 OLED Display SSD1306 128x64 (I2C)',
        'comp_lcd': '📟 LCD Display 1602 (I2C)',
        'menu_sensors': '🌡️ Sensors',
        'comp_ldr': '☀️ LDR Light Sensor',
        'comp_pir': '🏃 PIR Motion Sensor HC-SR501',
        'comp_dht22': '🌡️ DHT22 Temp & Humidity Sensor',
        'comp_hcsr04': '📡 Ultrasonic Distance Sensor HC-SR04',

        # Actions View
        'act_v_sim': '🖥️ Realistic Breadboard View (Lab)',
        'act_v_schema': '📐 IEC Schematic Diagram View',
        'act_zoom_in': '🔍 Zoom In',
        'act_zoom_out': '🔍 Zoom Out',
        'act_zoom_fit': '⛶ Fit View to Circuit',
        'act_toggle_montage': '🔌 Breadboard & Circuit Panel',
        'act_toggle_palette': '📋 Component Palette Panel',
        'act_toggle_props': '⚙ Component Properties Panel',
        'act_toggle_console': '📟 Serial Console & REPL',
        'act_toggle_scope': '📊 Oscilloscope & Analyzer',
        'act_toggle_erc': '🛡️ Electrical Diagnostic (ERC)',
        'theme_dark': '🌙 Dark Theme',
        'theme_light': '☀️ Light Theme',

        # Actions Simulation
        'act_run': '▶ Start Simulation',
        'act_stop': '⏹ Stop Simulation',
        'act_reset': '↻ Reset ESP32',
        'act_erc': '🛡️ Check Circuit (ERC Rules)',
        'act_upload': '☁ Upload to Physical ESP32...',
        'act_bridge': '🌐 Real Host Network Gateway (PC)',
        'act_bridge_tip': 'Allows simulated ESP32 to use the PC\'s real internet connection (real sockets, HTTP requests, local IP).',

        # Actions Lessons & Examples & Help
        'act_all_courses': '📚 Complete Lessons & Labs Catalog...',
        'act_evaluate': '📝 Self-evaluate Current Circuit...',
        'act_all_examples': '💡 Browse Examples Library...',
        'act_guide': '📖 Breadboard Wiring Guide...',
        'act_shortcuts': '⌨ Keyboard Shortcuts & Gestures...',
        'act_updates': '🔄 Check for Updates...',
        'act_about': 'ℹ️ About ESP32 MicroPython Lab...',

        # Header Bar
        'btn_nav_home': '🏠 Home',
        'btn_nav_home_tip': 'Show Home Screen (Ctrl+H)',
        'btn_nav_lab': '💻 Laboratory',
        'btn_nav_lab_tip': 'Switch to Laboratory Workspace',
        'app_tagline': 'Code · Simulate · Experiment · Learn',

        # Simulator & Tools
        'title_montage': '🔌 Breadboard & Circuit',
        'zoom_label': 'Zoom',
        'btn_fit_tip': 'Fit view',
        'zoom_in_tip': 'Increase text size (Ctrl + +)',
        'zoom_out_tip': 'Decrease text size (Ctrl + -)',
        'zoom_reset_tip': 'Reset text size',

        # Action Buttons
        'btn_simulate': '▶ Simulate',
        'btn_upload': '☁ Upload to ESP32',
        'btn_stop': '⏹ Stop',
        'btn_reset': '↻ Reset',
        'btn_simulate_tip': 'Start MicroPython simulation (F5)',
        'btn_stop_tip': 'Stop simulation (F6)',
        'btn_upload_tip': 'Upload to physical ESP32 board via USB',
        'btn_reset_tip': 'Reset ESP32 and simulation',

        # Tabs
        'tab_simulation': '🧪 Virtual Laboratory (Breadboard)',
        'tab_schematic': '📐 Standardized Schematic Diagram',
        'tab_console_repl': '📟 Serial Console & REPL',
        'tab_oscilloscope': '📊 Oscilloscope & Logic Analyzer',
        'tab_erc': '🛡️ Electrical Diagnostic (ERC)',

        # Welcome Page
        'welcome_tagline': 'Virtual MicroPython Programming & Electronics Laboratory',
        'welcome_desc': 'Code · Simulate · Experiment · Learn',
        'welcome_hint': 'Open or create a circuit from the File menu (Ctrl+N / Ctrl+O)',
        'welcome_chk_startup': 'Show this welcome screen on startup',

        # Status Bar
        'status_ready': 'Ready. Build your circuit or start simulation.',
        'status_running': 'Simulation running...',
        'status_stopped': 'Simulation stopped.',
        'status_reset': 'Simulation reset.',
        'status_welcome': 'Welcome Home — Choose a starting point.',
        'status_workspace': 'Active workspace.',
        'lang_changed': 'Language applied: English',

        # Updates
        'update_checking': 'Checking for updates on GitHub...',
        'update_up_to_date': 'You are using the latest version of ESP32 MicroPython Lab.',
        'update_available_title': 'New Version Available!',
        'update_btn_download': 'Download Update',
        'update_btn_later': 'Later',

        # Save changes prompt
        'save_changes_title': 'Save Changes?',
        'save_changes_msg': 'The current project has unsaved changes.\nDo you want to save changes before {action}?',
        'btn_save': 'Save',
        'btn_dont_save': 'Don\'t Save',
        'btn_cancel': 'Cancel',
    }
}

_current_lang = None

def get_current_language() -> str:
    global _current_lang
    if _current_lang is None:
        settings = QSettings('ESP32Lab', 'ESP32MicroPythonLab')
        _current_lang = settings.value('language', 'fr')
        if _current_lang not in ('fr', 'en'):
            _current_lang = 'fr'
    return _current_lang

def set_current_language(lang: str) -> None:
    global _current_lang
    if lang in ('fr', 'en'):
        _current_lang = lang
        settings = QSettings('ESP32Lab', 'ESP32MicroPythonLab')
        settings.setValue('language', lang)

def tr(key: str, default: str = '') -> str:
    lang = get_current_language()
    dict_lang = TRANSLATIONS.get(lang, TRANSLATIONS['fr'])
    return dict_lang.get(key, default or key)
