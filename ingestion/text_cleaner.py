# ingestion/text_cleaner.py
import spacy
nlp = spacy.load("en_core_web_sm")

def preprocess(text):
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents]
