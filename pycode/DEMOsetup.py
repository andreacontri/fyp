import os, sys
import random
import time
import json
from transformers import BartTokenizer, BartForConditionalGeneration, BartTokenizer
from typing import List
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.luhn import LuhnSummarizer
import spacy
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize
from textblob import TextBlob
from flair.models import TextClassifier
from flair.data import Sentence
import matplotlib as plt
import textwrap
import torch

import warnings
import traceback
warnings.filterwarnings("ignore", category=FutureWarning) # remove future warnings for debugging

# Import custom modules
from packages.vtt_formatting import format_VTT
from packages.timeline_generator import create_timeline_figure
from packages.stats_generator import create_stats_figure
from packages.chunk_splitter import split_text_into_chunks
from packages.summaries import abstractive_summarize_chunks, extractive_summarize_chunks, format_vtt_as_dialogue
from packages.openai import summarize_text, utility_text
from packages.sentiment import sentiment

ab = None  # Abstractive summarization result placeholder
ex = None  # Extractive summarization result placeholder
ai = None  # Summary generated by openAI api
timeline = None  # Timeline visualization placeholder
stats = None  # Statistical data visualization placeholder
chunks = None  # Text chunks for analysis placeholder
df = None  # DataFrame to hold VTT data, if applicable

print("setup loaded")

vtt_filename = "data/example_transcripts.vtt"
df, formatted_content = format_VTT(vtt_filename)


txt_dir = 'data/'#ami-transcripts'
file_name = 'test.txt'
file_path = os.path.join(txt_dir, file_name)
with open(file_path, 'r', encoding='utf-8') as file:
	text = file.read()

chunks = split_text_into_chunks(text)
sentence_count = 5
summaries = []
summarizer = LuhnSummarizer()
parser = PlaintextParser.from_string(text, Tokenizer("english"))
summary = summarizer(parser.document, sentence_count)
summarized_text = ' '.join([sentence._text for sentence in summary])
summaries.append(summarized_text)
items = summaries[0].split(".")

model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')
tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
inputs = tokenizer.encode(text, return_tensors="pt", max_length=1024, truncation=True)
inputs = inputs.to(device)
# Generate summary
summary_ids = model.generate(inputs, max_length=400, min_length=10, length_penalty=2.0, num_beams=4, early_stopping=True)
# Decode and clean up the summary
summary_text = tokenizer.decode(summary_ids[0], skip_special_tokens=True)