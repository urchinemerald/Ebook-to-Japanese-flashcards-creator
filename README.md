

A project that takes japanese Ebooks of all popular formats, or PDFs, and creates flashcards to be used in [Anki](https://apps.ankiweb.net/). The program makes a flashcard of each unique kanji in the book and creates a flashcard complete with hiragana, english translation generated sound. The program tokenizes the book / document using [Mecab](https://en.wikipedia.org/wiki/MeCab) to recognize japanese words since most japanese texts are written without the use of the spacebar. A minimum occurance filter can also be applied to ensure that the kanji / token is mentioned in the book for x amounts of times to become a flashcard. 

\
The program runs with a simple grafic interface to navigate the program. 

Mecab will have to be installed for segmentation of japanese text. 
pip install mecab-python3
ex:
wakati = MeCab.Tagger("-Owakati") 
>>> wakati.parse("pythonが大好きです").split()
['python', 'が', '大好き', 'です']

Genanki will have to be installed for creation of the anki flashcards. \
pip install genanki

\
[Calibre](https://calibre-ebook.com/download ) will have to be installed for ebook and PDF conversion.

gTTS will have to be installed for sound generation \
pip install gTTS





