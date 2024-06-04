from asyncio import exceptions
from unittest import result
import requests
import re
from bs4 import BeautifulSoup
import spacy
from settings.logging_config import logger
from helpers.classification_helper import get_completion
import fitz
import easyocr
import speech_recognition as sr
from pydub import AudioSegment
import os

# ==================== APPLY NLP USING SPACY FOR CLASSIFICATION ====================
def nlp_for_TextClassification(text: str):
    res = {}
    try:
        nlp = spacy.load('en_core_web_md')
    except Exception as e:
        from spacy.cli import download
        download('en_core_web_md')
        nlp = spacy.load('en_core_web_md')
    doc = nlp(text)

    named_entities = [(entity.text, entity.label_) for entity in doc.ents]

    entities_by_label = {}

    for entity, label in named_entities:
        if label not in entities_by_label:
            entities_by_label[label] = []
        entities_by_label[label].append(re.sub('\s{2,}', " ", entity))

    for label, entities in entities_by_label.items():
        res[label] = list(set(entities))

    return res


# ==================== TEXT CLASSIFICATION FOR WEB URL DATA BY NLP USING SPACY ====================
def getClassifiedDataFromURL(url: str):
    logger.info(f"URL is: {url}")
    try:
        response = requests.get(url, verify=False)
        html_content = response.text
        
        # Parse HTML content with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        extracted_data = soup.get_text()
        cleaned_data = extracted_data.replace('\n', ' ').strip()
        return nlp_for_TextClassification(cleaned_data)
    except Exception as e:
        print('error occured', e)
        pass   
        


# ==================== TEXT CLASSIFICATION FOR Similarty Input DATA  ====================

def getClassifiedDataFromInput(input: str):
    res = {}
    try:
        nlp = spacy.load('en_core_web_md')
    except Exception as e:
        from spacy.cli import download
        download('en_core_web_md')
        nlp = spacy.load('en_core_web_md')
    
    doc = nlp(input)
    res['entities'] = [ent.text for ent in doc.ents if ent.label_ == "ORG"]

    dir_path = os.path.abspath('./')
    if "src" not in dir_path:
        dir_path = os.path.abspath('./src')

    nlp1 = spacy.load(dir_path + '/model/model-last')
    doc = nlp1(input)
    res['attribute'] = [ent.text for ent in doc.ents if ent.label_ == "ATTR"]
    
    return res



# ==================== TEXT CLASSIFICATION FOR docs  ====================

def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        doc = fitz.open(pdf_file)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text += page.get_text()
        doc.close()
    except Exception as e:
        print(e)
        logger.exception(e)
    return text

def extract_text_from_image(image_path):
    extracted_text = ""
    try:
        reader = easyocr.Reader(['en']) 
        result = reader.readtext(image_path)
        extracted_text = ' '.join([res[1] for res in result])

    except Exception as e:
        logger.exception(e)
    return extracted_text

def extract_text_from_audio(audio_file_path):
    text=""
    
    # Load your audio file (e.g., MP3)
    audio = AudioSegment.from_file(audio_file_path)
    # Convert it to WAV format
    audio.export("static/output_audio.wav", format="wav")

    recognizer = sr.Recognizer()
    audio_file = "static/output_audio.wav"

    # Open the audio file
    with sr.AudioFile(audio_file) as source:
        # Listen to the audio and recognize speech
        audio_data = recognizer.record(source)
        try:
            # Use Google Web Speech API to transcribe the audio
            text = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            logger.exception("Google Web Speech API could not understand the audio")
        except sr.RequestError as e:
            logger.exception("Could not request results from Google Web Speech API ")
    # Remove the audio file after processing
    os.remove(audio_file)

    return text

def getClassifiedDataFromDocs(file,file_extension):
    result={'error':None, 'extracted_text':None}
    extracted_text=""
    try:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        parent_directory = os.path.dirname(current_directory)
        # Saving the file to the temporary location
        temp_file_path = f"{parent_directory}/static/{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file.file.read())

        if file_extension in ".pdf" :
            extracted_text = extract_text_from_pdf(temp_file_path)
        elif file_extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".tiff", ".webp", ".ico"]:
            extracted_text = extract_text_from_image(temp_file_path)
        else:
            extracted_text = extract_text_from_audio(temp_file_path)
        resp=nlp_for_TextClassification(extracted_text)
        result['extracted_text']=resp
        
    except exceptions as e:
        result['error']=e
        logger.exception(e)
    finally :
        # remove the temporary file
        if temp_file_path:
            os.remove(temp_file_path)
    return result
