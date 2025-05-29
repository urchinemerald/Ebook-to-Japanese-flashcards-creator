from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog, QLabel, QSpinBox
import sys
import MeCab
import re
import genanki
import pickle
import subprocess
import os
import tempfile
import shutil
from collections import Counter
from gtts import gTTS
import sys
import os
import shutil

def get_resource_path(filename):
    """Get the correct path to a bundled resource."""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in normal Python
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, filename)


class EbookConverter:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="ebook_to_txt_")

    def convert_to_text(self, ebook_path):
        base_name = os.path.splitext(os.path.basename(ebook_path))[0]
        output_txt_path = os.path.join(self.temp_dir, base_name + ".txt")

        try:
            subprocess.run([
                "ebook-convert",
                ebook_path,
                output_txt_path
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Conversion failed: {e}")
            return None

        if os.path.exists(output_txt_path):
            with open(output_txt_path, encoding="utf-8") as f:
                return f.read()
        else:
            print("[ERROR] Output file not found.")
            return None

    def cleanup(self):
        shutil.rmtree(self.temp_dir)


def regex(tokens):
    result = []

    for token in tokens:
        token = re.sub("\s",'', token)
        token = re.sub(r'^[\u3040-\u309F]+$','',token) # hiragana
        token = re.sub(r'^[\u30A0-\u30FF]+$','',token) # katakana
        token = re.sub(r'^[a-zA-Z]+$','',token) # Romaji
        token = re.sub(r'^[\uFF21-\uFF3A\uFF41-\uFF5A]+$', '', token) # Full length romaji

        token = re.sub(r'^[0-9]+$','',token) # siffror
        token = re.sub(r'^[\uFF10-\uFF19]+$', '', token)  # Full-width digits
        token = re.sub(r'[^\w]', '', token)

        # Detta fungerar för att se om en sträng är tom. 
        if token:
            result.append(token)    
    return result

class cardHandler:
    def __init__(self, kanji, gloss, reb):
        self.kanji = kanji
        self.gloss = self.removeSynonyms(gloss)
        self.reb = reb
       
    def removeSynonyms(self, gloss):
        if len(gloss) > 3:  
            return gloss[:3]
        return gloss  
    
    def formatGloss(self, gloss):
        return "<br>".join(gloss)
    
    def formatReb(self, Reb):
        return "<br>"+"<br>".join(Reb)
    
class DeckBuilder:
    def __init__(self, filename, on_done_callback=None):
        self.filename = filename
        self.on_done_callback = on_done_callback
        self.listOfCards = []

    def tokenize_text(self,book):
        mecab = MeCab.Tagger("-Owakati")
        tokens = mecab.parse(book).strip().split()
        tokens = regex(tokens)
        return tokens
    
    def minOccurenceFilter(self, tokens,min_occurence: int = 1):
        token_counter = Counter(tokens)
        filtered_tokens = []
        for token, count in token_counter.items():
            if count >= min_occurence:
                filtered_tokens.append(token)
        self.listOfCards = []

        return self.create_card_handlers(filtered_tokens)
        
    
    def create_card_handlers(self, tokens):
        source_path = get_resource_path("dictionary.pkl")
        
        writable_path = os.path.join(os.getcwd(), "dictionary.pkl")
        if not os.path.exists(writable_path):
            shutil.copyfile(source_path, writable_path)
        
        with open(writable_path, "rb") as f:
            dictionary = pickle.load(f)

        for token in tokens:
            entry = dictionary.get(token)
            if entry:
                gloss = entry["gloss"]
                reb = entry["reb"]
                newcard = cardHandler(token, gloss, reb)
                self.listOfCards.append(newcard)

        if self.on_done_callback:
            self.on_done_callback()

            return self.listOfCards

    
    def export_to_anki(self):
        my_model = genanki.Model(
            1607392319,
            'Simple Model',
            fields=[
                {'name': 'Question'},
                {'name': 'Answer'},
                {'name': 'Sound'}
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '{{Question}}<br>{{Sound}}',
                    'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
                },
            ]
        )

        my_deck = genanki.Deck(2059400110, self.filename)
        media_files = []

        counter = 0
        for item in self.listOfCards:
            tts_text = item.reb[0]
            
            item.gloss = item.formatGloss(item.gloss)
            item.reb = item.formatReb(item.reb)
            print(item.gloss + " - " + item.reb)

            # Generate TTS and save to file
            tts = gTTS(text=tts_text, lang='ja')
            media_dir = 'media bulk'
            os.makedirs(media_dir, exist_ok=True)  # Creates the folder if it doesn't exist

            filename = os.path.join(media_dir, f'{item.kanji}.mp3')
            ##tts.save(filename)
            media_files.append(filename)

            # Create note
            note = genanki.Note(
                model=my_model,
                fields=[
                    item.kanji,
                    str(item.gloss) + str(item.reb),
                    f"[sound:{filename}]"
                ]
            )

            counter += 1
            print(str(counter) + " / " + str(len(self.listOfCards)))
            my_deck.add_note(note)

        # Export package with media
        my_package = genanki.Package(my_deck)
        my_package.media_files = media_files
        ##e.write_to_file('output.apkg')

  


class MyApp(QWidget):
    def __init__(self):
        self.deck_builder: DeckBuilder = None 
        self.tokens = [] 

        super().__init__()
        self.setWindowTitle("Ebook to Anki - Kanji teacher")
        self.setGeometry(100,100,400,300)

        self.layout = QVBoxLayout()
        self.label = QLabel("Choose a Ebook / txt file")
        
        self.button = QPushButton("Choose File")
        self.button.clicked.connect(self.choose_file)

        self.label_flashcards_detected = QLabel("Number of unique entries found: 0")

        self.spinBox = QSpinBox()
        self.spinBox.setFixedWidth(100)        
        self.spinBox.setFixedHeight(20)        
        self.spinBox.setEnabled(False)
        self.spinBox.valueChanged.connect(self.update_min_occurance)
        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(100)
        self.spinBox.setValue(1)  

        self.spinBox_label = QLabel("Select a minimum occurrence threshold")
        self.spinBox_label.setEnabled(False)

        self.process_button = QPushButton("Create Flashcards")
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self.CreateFlashcards)

        self.layout = QVBoxLayout()
        self.layout.setSpacing(25)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.spinBox_label)
        self.layout.addWidget(self.spinBox)
        self.layout.addWidget(self.process_button)
        self.layout.addWidget(self.label_flashcards_detected)

        self.setLayout(self.layout)


    from ebook_converter import EbookConverter

    def update_min_occurance(self, value):
        if self.deck_builder is not None:
            self.deck_builder.listOfCards = self.deck_builder.minOccurenceFilter(self.tokens, value)
            self.label_flashcards_detected.setText("Number of unique entries found: " + str(len(self.deck_builder.listOfCards)))

    def enableFlashcardsDetected(self): 
        self.label_flashcards_detected.setText(
        "Number of unique entries found: " + str(len(self.deck_builder.listOfCards)))

    def enableProcessButton(self):
        self.process_button.setEnabled(True)
        self.spinBox.setEnabled(True)
        self.spinBox_label.setEnabled(True)
        
    def CreateFlashcards(self):
        self.spinBox.setEnabled(False)
        self.process_button.setEnabled(False)
        return self.deck_builder.export_to_anki()
    

    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Ebooks (*.txt *.epub *.mobi *.azw *.pdf);;All Files (*)")

        if file_path:
            file_name = os.path.basename(file_path)
            print(f"Selected file: {file_name}")

            if not file_path.lower().endswith(".txt"):
                converter = EbookConverter()
                text = converter.convert_to_text(file_path)
                converter.cleanup()
            else:
                with open(file_path, encoding="utf-8") as f:
                    text = f.read()

            if not text:
                print("[ERROR] Could not extract text from file.")
                return

            self.deck_builder = DeckBuilder(file_name, on_done_callback=self.enableProcessButton)
            self.tokens = self.deck_builder.tokenize_text(text)  # <--- extract just tokens
            self.deck_builder.listOfCards = self.deck_builder.minOccurenceFilter(self.tokens, self.spinBox.value())
            self.enableFlashcardsDetected()

            print("Processing file; Done")

        
app = QApplication(sys.argv)
window = MyApp()
window.show()
sys.exit(app.exec()) 

 





