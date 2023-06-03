from flair.data import Sentence
from flair.models import SequenceTagger
import stanza    
from googletrans import Translator, constants
import spacy
from spacy import displacy
from collections import Counter
import pandas as pd
from joblib import dump, load
import json
import requests



"""
The method receives a string as a parameter and then, 
with the help of the spacy library specialised in Ner, classifies the 
words in three categories Per, Org , LOC , MISC.
"""
def sp_from_str(text):
	sp = {}



	document = nlp(text)
	for ent in document.ents:
		sp[ent.text]= ent.label_
	return sp

"""
The method receives a string as a parameter and then, 
with the help of the flair library and SequenceTagger ner-spanish-large, 
classifies the 
words in three categories Per, Org , LOC , MISC.
"""

def flair_from_str(text):
	fl={}
	tagger = SequenceTagger.load("flair/ner-spanish-large")
	result = {}
	sentence = Sentence(text)
	tagger.predict(sentence)
	for entity in sentence.get_spans('ner'):
		fl[entity.text]=entity.tag
	return fl
"""
The method receives a string as a parameter and then, 
with the help of the Stanza library and SequenceTagger ner-spanish-large, 
classifies the 
words in three categories Per, Org , LOC , MISC.
"""

def stanza_from_str(text):
	sz = {}
	pipe = stanza.Pipeline("es", processors="tokenize,ner")
	doc = pipe(text)
	for entity in doc.ents:
		sz[str(entity.text)]= str(entity.type)
	return sz

def stanza_from_url(sz):
	final={'text':"", 'PER':[],'LOC':[],'ORG':[],'MISC':[],'DATE':[], 'impact':""}
	for kc in sz:
		c= sz[kc]
		final[c].append(kc)
	return final

def consolidate(fl,sp,sz):
	final={'text':"", 'PER':[],'LOC':[],'ORG':[],'MISC':[],'DATE':[], 'impact':""}
	for ka in fl:
		a= fl[ka]
		b=None
		c=None
		defn = None
		if ka  in sp:
			b= sp[ka]
			sp.pop(ka)
		if ka  in sz:
			c= sz[ka]
			sz.pop(ka)
		if a==b or a==c:
			defn=a
		elif b==c and b != None:
			defn=b
		else:
			defn=a
		final[defn].append(ka)            
       
	for kb in sp:

		b=sp[kb]
		c=None
		defn = None
		if kb  in sz:
			sz.pop(kb)
		final[b].append(kb)
	for kc in sz:
		c= sz[kc]
		final[c].append(kc)
	return final

def translateDate(text,final):
	dates=[]
	translator = Translator()

	nlp = stanza.Pipeline(lang='en', processors='tokenize,ner')
	translated_text = translator.translate(text, src='es', dest='en')
	txt=translated_text.text
	doc = nlp(txt)
	for entity in doc.ents:
		if str(entity.type)=='DATE' :
			translated_text_reverse = translator.translate(str(entity.text), src='en', dest='es')
			dates.append(translated_text_reverse.text)
            
	for dateEn in dates :
		if(dateEn not in final['DATE'] and dateEn not in final['LOC'] and dateEn not in final['ORG'] and dateEn not in final['MISC'] ):
			final['DATE'].append(dateEn)
	return final
		
    
def load_query(route, query):
    pipeline = load(route)
    result = pipeline.predict([query])
    i = result[0]
    if i == 1:
        return 'DEFORESTACION'
    elif i == 2:
        return 'MINERIA'
    elif i == 3:
        return 'CONTAMINACION'
    else:
        return 'NINGUNA'


def pipeline_ner(text, path):
    dates = []
    finalJson= translateDate(text, consolidate(flair_from_str(text),sp_from_str(text),stanza_from_str(text)))
    cat = load_query(path, text)
    finalJson['text']=text
    finalJson['impact']=cat
    f = json.dumps(finalJson)
    return f

def pipeline_url(text,path):
	
	finalJson=stanza_from_url(stanza_from_str(text))
	finalJson['text']=text
	cat = load_query(path, text)
	finalJson['impact']=cat
	f = json.dumps(finalJson)
	return f    



def ner_from_str(text, output_path):
    jsono = pipeline_ner(text, "NLP.joblib")
    with open(output_path, 'w') as outfile:
        json.dump(jsono, outfile)
    pass

def ner_from_file(text_path, output_path):
    text_file = open(text_path, "r")
    data = text_file.read()
    text_file.close()
    jsono = pipeline_ner(data, "NLP.joblib")
    with open(output_path, 'w') as outfile:
        json.dump(jsono, outfile)
    pass

def ner_from_url(url, output_path):
    data = str(requests.get(url).text)
    jsono = pipeline_url(data, "NLP.joblib")
    with open(output_path, 'w') as outfile:
        json.dump(jsono, outfile)
    pass

    
    
# Examples:
#pipeline_ner("El Amazonas está cerca del punto de inflexión de convertirse en una sabana, sugiere un estudio. La selva del Amazonas podría estar acercándose a un punto de inflexión crítico que podría hacer que este ecosistema biológicamente rico y diverso se transforme en una sabana de hierba.El destino de la selva tropical es crucial para la salud del planeta, ya que alberga una variedad única de vida animal y vegetal, almacena una enorme cantidad de carbono e influye en gran medida en los patrones climáticos globales.", "NLP.joblib")
    
#ner_from_str("El Amazonas está cerca del punto de inflexión de convertirse en una sabana, sugiere un estudio. La selva del Amazonas podría estar acercándose a un punto de inflexión crítico que podría hacer que este ecosistema biológicamente rico y diverso se transforme en una sabana de hierba.El destino de la selva tropical es crucial para la salud del planeta, ya que alberga una variedad única de vida animal y vegetal, almacena una enorme cantidad de carbono e influye en gran medida en los patrones climáticos globales.", "JASON.json")

#ner_from_file("untitled.txt", "JASON.json")
#ner_from_url("https://www.elespectador.com/ambiente/la-amazonia-colombiana-fue-la-cuarta-con-mas-deforestacion-durante-2021/", "JASON.json")