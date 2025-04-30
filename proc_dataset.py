import pandas as pd
import re
import nltk
nltk.data.path.append("C:/Users/tasni/nltk_data")
from nltk.corpus import stopwords
from nltk.tokenize import TreebankWordTokenizer
from nltk.stem import WordNetLemmatizer

#Load the dataset
file_path = './Source/glassdoor_reviews.csv'
df = pd.read_csv(file_path)

#Handle Missing Values
#Drop rows where essential columns are missing
df.dropna(subset=['firm', 'headline', 'pros', 'cons', 'overall_rating'], inplace=True)

#Fill missing categorical values with 'o' (No Opinion)
categorical_cols = ['recommend', 'ceo_approv', 'outlook']
df[categorical_cols] = df[categorical_cols].fillna('o')


#Correct Formatting
#Convert date_review to datetime format
df['date_review'] = pd.to_datetime(df['date_review'])

#Convert ratings to numeric
rating_cols = ['work_life_balance', 'culture_values', 'diversity_inclusion', 'career_opp', 'comp_benefits', 'senior_mgmt']
df[rating_cols] = df[rating_cols].astype(float)

#Map categorical ranking values
category_mapping = {'v': 'Positive', 'r': 'Mild', 'x': 'Negative', 'o': 'No Opinion'}
df['recommend'] = df['recommend'].map(category_mapping)
df['ceo_approv'] = df['ceo_approv'].map(category_mapping)
df['outlook'] = df['outlook'].map(category_mapping)

#Text Preprocessing
#Ensure stopwords and tokenizer are downloaded
stop_words = set(stopwords.words('english'))
tokenizer = TreebankWordTokenizer()
lemmatizer = WordNetLemmatizer()

def clean_text(text):
    text = text.lower()  #Convert to lowercase
    text = re.sub(r'[^a-z\s]', '', text)  #Remove special characters and numbers
    tokens = tokenizer.tokenize(text)  #Tokenize text
    tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]  #Lemmatize and remove stopwords
    return ' '.join(tokens)

# Apply cleaning function
df['headline'] = df['headline'].astype(str).apply(clean_text)
df['pros'] = df['pros'].astype(str).apply(clean_text)
df['cons'] = df['cons'].astype(str).apply(clean_text)
df['current'] =df['current'].astype(str).apply(clean_text)
df['location'] =df['location'].astype(str).apply(clean_text)
df['job_title'] =df['job_title'].astype(str).apply(clean_text)

df.to_csv("./Source/cleaned_glassdoor_reviews.csv", index=False)
