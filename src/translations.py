import os
import sys
import json

def get_translations_dir():
    # Retrieve path to the translations folder (handles both source run and compiled binary)
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'src', 'translations')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'translations')

def load_all_translations():
    trans_dir = get_translations_dir()
    translations = {}
    languages = {}
    
    if os.path.exists(trans_dir):
        for filename in sorted(os.listdir(trans_dir)):
            if filename.endswith('.json'):
                lang_code = os.path.splitext(filename)[0]
                try:
                    with open(os.path.join(trans_dir, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        lang_name = data.get("_lang_name", lang_code)
                        translations[lang_code] = data
                        languages[lang_code] = lang_name
                except Exception as e:
                    print(f"Error loading translation file {filename}: {e}", file=sys.stderr)
    return translations, languages

TRANSLATIONS, LANGUAGES = load_all_translations()
