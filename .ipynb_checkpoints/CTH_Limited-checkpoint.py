# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
#streamlit run /Users/Ben/Library/CloudStorage/Dropbox/Python/OpenAI/Streamlit/CTH/Cth_Limited.py

# %% [markdown]
# # Preliminaries

# %%
#Preliminary modules
import base64 
import json
import pandas as pd
import shutil
import requests
import numpy as np
import re
import datetime
from datetime import date
from datetime import datetime
from dateutil import parser
from dateutil.relativedelta import *
from datetime import datetime, timedelta
import sys
import pause
import requests
from bs4 import BeautifulSoup, SoupStrainer
import httplib2
from urllib.request import urlretrieve
import os


#Streamlit
import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit.components.v1 import html
import streamlit_ext as ste

#NSWCaseLaw
from nswcaselaw.search import Search

#OpenAI
import openai
import tiktoken

#Google
from google.oauth2 import service_account

#Word
import textract



# %%
#Get current directory
current_dir = os.getcwd()


# %%
#today
day = datetime.now().strftime("%-d")
month = datetime.now().strftime("%B")
year = datetime.now().strftime("%Y")
today = day + ' ' + month + ' ' + year
today_in_nums = str(datetime.now())[0:10]
today_month = day + ' ' + month
today_words = datetime.now().strftime('%A')

# %%
# Generate placeholder list of errors
errors_list = set()


# %%
#Create function for saving responses and results
def convert_df_to_json(df):
    return df.to_json(orient = 'split', compression = 'infer')

def convert_df_to_csv(df):
   return df.to_csv(index=False).encode('utf-8')

# %%
#Title of webpage
st.set_page_config(
   page_title="The Empirical Legal Research Kickstarter (CTH)",
   page_icon="🧊",
   layout="centered",
   initial_sidebar_state="collapsed",
)


# %%
#function to create dataframe
def create_df():

    #submission time
    timestamp = datetime.now()

    #Personal info entries
    
    name = name_entry
    email = email_entry
    gpt_api_key = gpt_api_key_entry



    #dates
    
    on_this_date = ''

    if on_this_date_entry != 'None':

        try:

            on_this_date = on_this_date_entry.strftime('%d/%m/%Y') + on_this_date_entry.strftime('%d') + before_date_entry.strftime('%B').lower()[:3] + on_this_date_entry.strftime('Y')

        except:
            pass
        
    
    before_date = ''

    if before_date_entry != 'None':

        try:

            before_date = str(before_date_entry.strftime('%d')) + str(before_date_entry.strftime('%B')).lower()[:3] + str(before_date_entry.strftime('%Y'))

        except:
            pass

    
    after_date = ''

    if after_date_entry != 'None':
        
        try:
            after_date = str(after_date_entry.strftime('%d')) + str(after_date_entry.strftime('%B')).lower()[:3] + str(after_date_entry.strftime('%Y'))
            
        except:
            pass
    

    #Other entries
    case_name_mnc = case_name_mnc_entry
    judge =  judge_entry
    reported_citation = reported_citation_entry
    file_number = file_number_entry
    npa = npa_entry
    with_all_the_words = with_all_the_words_entry
    with_at_least_one_of_the_words = with_at_least_one_of_the_words_entry
    without_the_words = without_the_words_entry
    phrase = phrase_entry
    proximity = proximity_entry
    legislation = legislation_entry
    cases_cited = cases_cited_entry
    catchwords = catchwords_entry 
    
    #Judgment counter bound
    
    judgments_counter_bound_ticked = judgments_counter_bound_entry
    if int(judgments_counter_bound_ticked) > 0:
        judgments_counter_bound = 10
    else:
        judgments_counter_bound = 10000

    #GPT choice and entry
    gpt_activation_status = gpt_activation_entry
    gpt_questions = gpt_questions_entry[0: 1000]

    #metadata choice

    meta_data_choice = meta_data_entry
    
    new_row = {'Processed': '',
           'Timestamp': timestamp,
           'Your name': name, 
           'Your email address': email, 
           'Your GPT API key': gpt_api_key, 
           'Case name or medium neutral citation': case_name_mnc, 
           'Judge' : judge, 
            'Reported citation' : reported_citation, 
            'File number': file_number,
            'National practice area': npa,
            'With all the words': with_all_the_words,
            'With at least one of the words': with_at_least_one_of_the_words,
            'Without the words': without_the_words,
            'Phrase': phrase,
            'Proximity': proximity,
            'On this date': on_this_date,
            'After date': after_date,
            'Before date': before_date,
            'Legislation': legislation,
            'Cases cited': cases_cited,
            'Catchwords' : catchwords, 
            'Metadata inclusion' : meta_data_choice,
           'Maximum number of judgments': judgments_counter_bound, 
           'Enter your question(s) for GPT': gpt_questions, 
            'Tick to use GPT': gpt_activation_status 
          }

    df_master_new = pd.DataFrame(new_row, index = [0])
    
#    df_master_new.to_json(current_dir + '/df_master.json', orient = 'split', compression = 'infer')
#    df_master_new.to_excel(current_dir + '/df_master.xlsx', index=False)

#    if len(df_master_new) > 0:
        
    return df_master_new

#    else:
#        return 'Error: spreadsheet of reponses NOT generated.' 

# %%
#Define format functions for headnotes choice, courts choice, and GPT questions

#Create function to split a string into a list by line
def split_by_line(x):
    y = x.split('\n')
    for i in y:
        if len(i) == 0:
            y.remove(i)
    return y

#Create function to split a list into a dictionary for list items longer than 10 characters
#Apply split_by_line() before the following function
def GPT_label_dict(x_list):
    GPT_dict = {}
    for i in x_list:
        if len(i) > 10:
            GPT_index = x_list.index(i) + 1
            i_label = 'GPT question ' + f'{GPT_index}'
            GPT_dict.update({i_label: i})
    return GPT_dict

#Functions for tidying up

#Tidy up hyperlink
def link(x):
    value = '=HYPERLINK("' + str(x) + '")'
    return value



# %% [markdown]
# # Federal Courts search engine

# %%
#Function turning search terms to search results url
def fca_search(case_name_mnc= '', 
               judge ='', 
               reported_citation ='', 
               file_number ='', 
               npa = '', 
               with_all_the_words = '', 
               with_at_least_one_of_the_words = '', 
               without_the_words = '', 
               phrase = '', 
               proximity = '', 
               on_this_date = '', 
               after_date = '', 
               before_date = '', 
               legislation = '', 
               cases_cited = '', 
               catchwords = ''):
    base_url = "https://search2.fedcourt.gov.au/s/search.html?collection=judgments&sort=date&meta_v_phrase_orsand=judgments%2FJudgments%2Ffca"
    params = {'meta_2' : case_name_mnc, 
              'meta_A' : judge, 
              'meta_z' : reported_citation, 
              'meta_3' : file_number, 
              'meta_n_phrase_orsand' : npa, 
              'query_sand' : with_all_the_words, 
              'query_or' : with_at_least_one_of_the_words, 
              'query_not' : without_the_words, 
              'query_phrase' : phrase, 
              'query_prox' : proximity, 
              'meta_d' : on_this_date, 
              'meta_d1' : after_date, 
              'meta_d2' : before_date, 
              'meta_7' : legislation, 
              'meta_4' : cases_cited, 
              'meta_B' : catchwords}

    response = requests.get(base_url, params=params)
    response.raise_for_status()
    # Process the response (e.g., extract relevant information)
    # Your code here...
    return response.url


# %%
#Auxiliary list for getting more pages of search results
further_page_ending_list = []
for i in range(100):
    further_page_ending = 20 + i
    if ((str(further_page_ending)[-1] =='1') & (str(further_page_ending)[0] not in ['3', '5', '7', '9', '11'])):
        further_page_ending_list.append(str(further_page_ending))


# %%
#Define function turning search results url to links to judgments
def search_results_to_judgment_links(url_search_results, judgment_counter_bound):
    #Scrape webpage of search results
    page = requests.get(url_search_results)
    soup = BeautifulSoup(page.content, "lxml")

    #Start counter

    counter = 1
    
    # Get links of first 20 results
    links_raw = soup.find_all("a", href=re.compile("fca"))
    links = []
    
    for i in links_raw:
        if (('title=' in str(i)) and (counter <=judgment_counter_bound)):
            remove_title = str(i).split('" title=')[0]
            remove_leading_words = remove_title.replace('<a href="', '')
            if 'a class=' not in remove_leading_words:
                links.append(remove_leading_words)
                counter = counter + 1

    #Go beyond first 20 results

    for ending in further_page_ending_list:
        if counter <=judgment_counter_bound:
            url_next_page = url_search_results + '&start_rank=' + f"{ending}"
            page_judgment_next_page = requests.get(url_next_page)
            soup_judgment_next_page = BeautifulSoup(page_judgment_next_page.content, "lxml")
            links_next_page_raw = soup_judgment_next_page.find_all("a", href=re.compile("fca"))
            links_next_page = []
            for i in links_next_page_raw:
                if 'title=' in str(i):
                    remove_title = str(i).split('" title=')[0]
                    remove_leading_words = remove_title.replace('<a href="', '')
                    if 'a class=' not in remove_leading_words:
                        links.append(remove_leading_words)
                        counter = counter + 1

    return links


# %%
#judgment url to word document
#NOT in use
def link_to_doc(url_judgment):
    page_judgment = requests.get(url_judgment)
    soup_judgment = BeautifulSoup(page_judgment.content, "lxml")
    link_word_raw = soup_judgment.find_all('a', string=re.compile('Word'))
    if len(link_word_raw)> 0:
        link_to_word = str(link_word_raw).split('>')[0].replace('[<a href="', '')
        return link_to_word
    else:
        return url_judgment


# %%
#Function for turning a link to judgment to a judgment dictonary
#NOT IN USE Too many problems
def link_to_judgment_dict(url_judgment):
    page_judgment = requests.get(url_judgment)
    soup_judgment = BeautifulSoup(page_judgment.content, "lxml")
    
    #Get meta data
    meta_data_all = str(soup_judgment).split('REASONS FOR JUDGMENT')[0].replace('\\n', '\n\n')
    
    #Get Judgment

    judgment_paras_text_only = []
    
    judgment_raw = str(soup_judgment).split('REASONS FOR JUDGMENT')[1]
    
    judgment_raw_paras = judgment_raw.split('order=')
    
    for para_text_raw in judgment_raw_paras:
        para_text = ''.join(para_text_raw.split('">')[1:])
        if len(para_text) > 0:
            if para_text[0].isdigit():
                para_text_clean = para_text.replace('</span>', '').replace('<span>', '').replace("\xa0", " ").replace('<span style="font:7.0pt &amp;quot;Times New Roman', "").replace('</p><p class="00806350', '')
                judgment_paras_text_only.append(para_text_clean)
    
    judgment_paras_final = ' \n\n PARAGRAPH NUMBER '.join(judgment_paras_text_only)
    
    judgment_paras_finally_final = 'PARAGRAPH NUMBER '+ judgment_paras_final.replace('\\n', '\n\n')
    
    #Orders
    
    #orders_very_raw = str(soup_judgment).split("DATE OF ORDER")[1].split("REASONS FOR JUDGMENT")[0]
    #orders_list = []
    #orders_raw_list = orders_raw.split('">')
    #for i in orders_raw_list:
    #    each_order = i.split('</p>')[0]
    #    if len(each_order) > 3:
    #        orders_list.append(each_order)
    
    #Convert to dict
    
    #orders_text_raw = 'Order number ' + ' Order number '.join(orders_list)
    #orders_text=orders_text_raw.replace('   ',' ').replace('  ',' ')
    #judgment_dict = {"metadata" : '', "orders" : '', "judgment" : ''}
    judgment_dict = {"metadata" : '', "judgment" : ''}
    
    judgment_dict["metadata"] = meta_data_all
    #judgment_dict["orders"] = orders_text
    judgment_dict["judgment"] = judgment_paras_finally_final
    
    #judgment_json= json.dumps(judgment_dict)
    return judgment_dict


# %%
#Convert html link to dictionary 
#NOT IN USE Too many problems

def link_to_dict(url_judgment):
    page_judgment = requests.get(url_judgment)
    soup_judgment = BeautifulSoup(page_judgment.content, "lxml")
    text = soup_judgment.get_text()
    judgment_dic = {'Hyperlink (click)': url_judgment, 'Judgment' : text}
    
    return judgment_dic



# %%
#Convert link to document to dictionary 
#NOT IN USE

def doc_link_to_dict(link_to_doc):

    court_counter = 0
    
    if '.docx' in link_to_doc:

        file_name_raw = link_to_doc.split('.docx')[0]

        for j in ['fcafc', 'FCAFC', 'fca', 'FCA']:

            if ((j in file_name_raw) and (court_counter <1)):
    
                file_name = file_name_raw.split(j)[0][-4:] + j + file_name_raw.split(j)[1] + '.docx'
    
                urlretrieve(link_to_doc, file_name)

                file_loc = current_dir + '/' + file_name

                text = textract.process(file_loc)

                text_list = str(text).split("\\x")
                
                text_clean_list = []
                
                for x in text_list:
                    if len(x)>2:
                        x_clean = x[2:]
                        text_clean_list.append(x_clean)
                    
                text_clean = ' '.join(text_clean_list).replace('\\n', '\n')

                court_counter = court_counter +1
    
    elif '.pdf' in link_to_doc:

        for k in ['fcafc', 'FCAFC', 'fca', 'FCA']:

            if ((k in file_name_raw) and (court_counter <1)):

                file_name = file_name_raw.split(k)[0][-4:] + k + file_name_raw.split(k)[1] + '.pdf'

                urlretrieve(link_to_doc, file_name)

                file_loc = current_dir + '/' + file_name

                text = textract.process(file_loc)

                text_list = str(text).split("\\x")
                
                text_clean_list = []
                
                for x in text_list:
                    if len(x)>2:
                        x_clean = x[2:]
                        text_clean_list.append(x_clean)
                    
                text_clean = ' '.join(text_clean_list).replace('\\n', '\n')

                court_counter = court_counter +1

    else:
        file_name = 'Not working'
        text_clean = 'Not working'
        
    judgment_dic = {'File name' : file_name, 'Hyperlink (click)': link_to_doc, 'Judgment' : text_clean}
    
    return judgment_dic



# %%
#Meta labels
#NOT IN USE, but works

meta_labels = ['MNC', 'Year', 'Appeal', 'File_Number', 'Judge', 'Judgment_Dated', 'Distribution', 'Subject', 'Words_Phrases', 'Legislation', 'Cases_Cited', 'Division', 'NPA', 'Pages', 'All_Parties', 'Jurisdiction', 'Reported', 'Summary', 'Corrigenda', 'Parties', 'FileName', 'Asset_ID', 'Date.published']

def meta_dict(judgment_url):
    meta_dict = {'MNC' : '',  
                 'Year' : '',  
                 'Appeal' : '',  
                 'File_Number' : '',  
                 'Judge' : '',  
                 'Judgment_Dated' : '',  
                 'Distribution' : '',  
                 'Subject' : '',  
                 'Words_Phrases' : '',  
                 'Legislation' : '',  
                 'Cases_Cited' : '',  
                 'Division' : '',  
                 'NPA' : '',  
                 'Pages' : '',  
                 'All_Parties' : '',  
                 'Jurisdiction' : '',  
                 'Reported' : '',  
                 'Summary' : '',  
                 'Corrigenda' : '',  
                 'Parties' : '',  'FileName' : '',  
                 'Asset_ID' : '',  
                 'Date.published' : ''
                }
    page = requests.get(judgment_url)
    soup = BeautifulSoup(page.content, "lxml")
    meta_tags = soup.find_all("meta")

    if len(meta_tags)>0:
        for tag_index in range(len(meta_tags)):
            for tag_name in meta_labels:
                if tag_name in str(meta_tags[tag_index]):
                    meta_dict[tag_name] = meta_tags[tag_index].get("content")
    return meta_dict

    

# %%
#Meta labels and judgment combined
#IN USE
meta_labels = ['MNC', 'Year', 'Appeal', 'File_Number', 'Judge', 'Judgment_Dated', 'Distribution', 'Subject', 'Words_Phrases', 'Legislation', 'Cases_Cited', 'Division', 'NPA', 'Pages', 'All_Parties', 'Jurisdiction', 'Reported', 'Summary', 'Corrigenda', 'Parties', 'FileName', 'Asset_ID', 'Date.published']
meta_labels_droppable = ['Year', 'Appeal', 'File_Number', 'Judge', 'Judgment_Dated', 'Distribution', 'Subject', 'Words_Phrases', 'Legislation', 'Cases_Cited', 'Division', 'NPA', 'Pages', 'All_Parties', 'Jurisdiction', 'Reported', 'Summary', 'Corrigenda', 'Parties', 'FileName', 'Asset_ID', 'Date.published']

def meta_judgment_dict(judgment_url):
    judgment_dict = {'Case name': '',
                 'Medium neutral citation': '',
                'Hyperlink (click)' : '', 
                'MNC' : '',  
                 'Year' : '',  
                 'Appeal' : '',  
                 'File_Number' : '',  
                 'Judge' : '',  
                 'Judgment_Dated' : '',  
                 'Distribution' : '',  
                 'Subject' : '',  
                 'Words_Phrases' : '',  
                 'Legislation' : '',  
                 'Cases_Cited' : '',  
                 'Division' : '',  
                 'NPA' : '',  
                 'Pages' : '',  
                 'All_Parties' : '',  
                 'Jurisdiction' : '',  
                 'Reported' : '',  
                 'Summary' : '',  
                 'Corrigenda' : '',  
                 'Parties' : '',  'FileName' : '',  
                 'Asset_ID' : '',  
                 'Date.published' : '', 
                'Judgment' : ''
                }

    
    #Attach hyperlink

    judgment_dict['Hyperlink (click)'] = link(judgment_url)
    
    page = requests.get(judgment_url)
    soup = BeautifulSoup(page.content, "lxml")
    meta_tags = soup.find_all("meta")

    #Attach meta tags
    if len(meta_tags)>0:
        for tag_index in range(len(meta_tags)):
            for tag_name in meta_labels:
                if tag_name in str(meta_tags[tag_index]):
                    judgment_dict[tag_name] = meta_tags[tag_index].get("content")

    try:
        judgment_dict['Case name'] = judgment_dict['MNC'].split('[')[0]
        judgment_dict['Medium neutral citation'] = '[' + judgment_dict['MNC'].split('[')[1]
        judgment_dict.pop('MNC')

    except:
        pass

    #Attach Judgment

    judgment_text = ''
    
    try:
        judgment_removed_bottom = str(soup.get_text()).split('Translation Services')
        judgment_raw_no_bottom = judgment_removed_bottom[0]
        judgment_raw_paras = judgment_raw_no_bottom.split('REASONS FOR JUDGMENT')
        judgment_text = ''.join(judgment_raw_paras[1:])
    except:
        judgment_text = str(soup.get_text())

    judgment_dict['Judgment'] = judgment_text

    #Check if gets taken to a PDF

    if '.pdf' in judgment_url.lower():
        judgment_dict['Case name'] = 'Not working because the judgment is in PDF.'
    
    return judgment_dict

    

# %% [markdown]
# # GPT functions and parameters

# %%
#Module and costs

GPT_model = "gpt-3.5-turbo-0125"

GPT_input_cost = 1/1000*0.0005 
GPT_output_cost = 1/1000*0.0015

#Upperbound on number of engagements with GPT

GPT_use_bound = 3

print(f"\nPrior number of GPT uses is capped at {GPT_use_bound} times.")

#Upperbound on the length of questions for GPT

answers_characters_bound = 1000

print(f"\nQuestions for GPT are capped at {answers_characters_bound} characters.")

#Upperbound on number of judgments to scrape

judgments_counter_bound = 10

print(f"\nNumber of judgments to scrape per request is capped at {judgments_counter_bound}.")

#Pause between judgment scraping

scraper_pause = 5

print(f"\nThe pause between judgment scraping is {scraper_pause} second.")



# %%
#Define function to determine eligibility for GPT use

#Define a list of privileged email addresses with unlimited GPT uses

privileged_emails = ['ben.chen@sydney.edu.au', 
                     'nehc.neb@gmail.com', 
                     'natalie.silver@sydney.edu.au', 
                     'kimberlee.weatherall@sydney.edu.au',
                     'jeffrey.gordon@sydney.edu.au', 
                     'michael.j.crawford@sydney.edu.au'
                     'genevieve.grant@monash.edu', 
                     'genevieve.grant@monash.edu.au', 
                     'm.legg@unsw.edu.au'
                    ]

def prior_GPT_uses(email_address, df_online):
    # df_online variable should be the online df_online
    prior_use_counter = 0
    for i in df_online.index:
        if ((df_online.loc[i, "Your email address"] == email_address) 
            and (int(df_online.loc[i, "Tick to use GPT"]) > 0) 
            and (len(df_online.loc[i, "Processed"])>0)
           ):
            prior_use_counter += 1
    if email_address in privileged_emails:
        return 0
    else:
        return prior_use_counter

#Define function to check whether email is educational or government
def check_edu_gov(email_address):
    #Return 1 if educational or government, return 0 otherwise
    end=email_address.split('@')[1]
    if (('.gov' in end) or ('.edu' in end) or ('.ac' in end)):
        return 1
    else:
        return 0



# %%
#Tokens estimate preliminaries
encoding = tiktoken.get_encoding("cl100k_base")
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
#Tokens estimate function
def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

#Define judgment input function for JSON approach

#Token limit covering both GTP input and GPT output is 16385, each token is about 4 characters
characters_limit_half = int((16385*4)/2-1500)
tokens_cap = int(16385 - 1500)

def judgment_prompt_json(judgment_json):
                
    judgment_content = "Based on the metadata and judgment in the following JSON: " + str(judgment_json) + ", "

    judgment_content_tokens = num_tokens_from_string(judgment_content, "cl100k_base")
    
    if judgment_content_tokens <= tokens_cap:
        
        return judgment_content

    else:
        
        meta_data_len = judgment_content_tokens - num_tokens_from_string(judgment_json['Judgment'], "cl100k_base")
        
        judgment_chars_capped = int((tokens_cap - meta_data_len)*4)
        
        judgment_string_trimmed = judgment_json['Judgment'][ :int(judgment_chars_capped/2)] + judgment_json['Judgment'][-int(judgment_chars_capped/2): ]

        judgment_json["Judgment"] = judgment_string_trimmed     
        
        judgment_content_capped = "Based on the metadata and judgment in the following JSON: " + str(judgment_json) + ","
        
        return judgment_content_capped



# %%
#Define system role content for GPT
role_content = 'You are a legal research assistant helping an academic researcher to answer questions about a public judgment. You will be provided with the judgment and metadata in string form. Please answer questions based only on information contained in the judgment and metadata. Where your answer comes from a specific paragraph in the judgment, provide the paragraph number as part of your answer. If you cannot answer any of the questions based on the judgment or metadata, do not make up information, but instead write "answer not found".'

intro_for_GPT = [{"role": "system", "content": role_content}]


# %%
#Define GPT answer function for answers in json form, YES TOKENS
#IN USE

def GPT_json_tokens(questions_json, judgment_json, API_key):
    #'question_json' variable is a json of questions to GPT
    #'jugdment' variable is a judgment_json   

    
    judgment_for_GPT = [{"role": "user", "content": judgment_prompt_json(judgment_json) + 'you will be given questions to answer in JSON form.'}]
        
    #Create answer format
    
    q_keys = [*questions_json]
    
    answers_json = {}
    
    for q_index in q_keys:
        answers_json.update({q_index: 'Your answer to the question with index ' + q_index + '. State specific paragraph numbers in the judgment or specific sections in the metadata.'})
    
    #Create questions, which include the answer format
    
    question_for_GPT = [{"role": "user", "content": str(questions_json).replace("\'", '"') + ' Give responses in the following JSON form: ' + str(answers_json).replace("\'", '"')}]
    
    #Create messages in one prompt for GPT
    messages_for_GPT = intro_for_GPT + judgment_for_GPT + question_for_GPT
    
#   return messages_for_GPT

            
    #os.environ["OPENAI_API_KEY"] = API_key

    openai.api_key = API_key
    
    #client = OpenAI()
    
    try:
        #completion = client.chat.completions.create(
        completion = openai.chat.completions.create(
            model=GPT_model,
            messages=messages_for_GPT, 
            response_format={"type": "json_object"}
        )
        
#        return completion.choices[0].message.content #This gives answers as a string containing a dictionary
        
        #To obtain a json directly, use below
        answers_dict = json.loads(completion.choices[0].message.content)
        
        #Obtain tokens
        output_tokens = completion.usage.completion_tokens
        
        prompt_tokens = completion.usage.prompt_tokens
        
        return [answers_dict, output_tokens, prompt_tokens]

    except Exception as error:
        
        for q_index in q_keys:
            answers_json[q_index] = error
        
        return [answers_json, 0, 0]



# %%
#Define GPT function for each respondent's dataframe, index by judgment then question, with input and output tokens given by GPT itself
#IN USE

#The following function DOES NOT check for existence of questions for GPT
    # To so check, active line marked as #*
def engage_GPT_json_tokens(questions_json, df_individual, GPT_activation, API_key):
    # Variable questions_json refers to the json of questions
    # Variable df_individual refers to each respondent's df
    # Variable activation refers to status of GPT activation (real or test)
    # The output is a new JSON for the relevant respondent with new columns re:
        # "Judgment length in tokens (up to 15635 given to GPT)"
        # 'GPT cost estimate (USD excl GST)'
        # 'GPT time estimate (seconds)'
        # GPT questions/answers

    #os.environ["OPENAI_API_KEY"] = API_key

    openai.api_key = API_key
    
    #client = OpenAI()
    
    question_keys = [*questions_json]
    
    for judgment_index in df_individual.index:
        
        judgment_json = df_individual.to_dict('index')[judgment_index]
        
        #Calculate and append number of tokens of judgment, regardless of whether given to GPT
        judgment_tokens = num_tokens_from_string(str(judgment_json), "cl100k_base")
        df_individual.loc[judgment_index, "Judgment length in tokens (up to 15635 given to GPT)"] = judgment_tokens       

        #Indicate whether judgment truncated
        
        df_individual.loc[judgment_index, "Judgment truncated (if given to GPT)?"] = ''       
        
        if judgment_tokens <= characters_limit_half*2/4:
            
            df_individual.loc[judgment_index, "Judgment truncated (if given to GPT)?"] = 'No'
            
        else:
            
            df_individual.loc[judgment_index, "Judgment truncated (if given to GPT)?"] = 'Yes'

        #Create columns for respondent's GPT cost, time
        df_individual.loc[judgment_index, 'GPT cost estimate (USD excl GST)'] = ''
        df_individual.loc[judgment_index, 'GPT time estimate (seconds)'] = ''
                
        #Calculate GPT start time

        GPT_start_time = datetime.now()

        #Depending on activation status, apply GPT_json function to each judgment, gives answers as a string containing a dictionary

        if int(GPT_activation) > 0:
            GPT_output_list = GPT_json_tokens(questions_json, judgment_json, API_key) #Gives [answers as a JSON, output tokens, input tokens]
            answers_dict = GPT_output_list[0]
        
        else:
            answers_dict = {}    
            for q_index in question_keys:
                #Increases judgment index by 2 to ensure consistency with Excel spreadsheet
                answer = 'Placeholder answer for ' + ' judgment ' + str(int(judgment_index) + 2) + ' ' + str(q_index)
                answers_dict.update({q_index: answer})
            
            #Own calculation of GPT costs for Placeholder answer fors

            #Calculate capped judgment tokens

            judgment_capped_tokens = num_tokens_from_string(judgment_prompt_json(judgment_json), "cl100k_base")

            #Calculate questions tokens and cost

            questions_tokens = num_tokens_from_string(str(questions_json), "cl100k_base")

            #Calculate other instructions' tokens

            other_instructions = role_content + 'you will be given questions to answer in JSON form.' + ' Give responses in the following JSON form: '

            other_tokens = num_tokens_from_string(other_instructions, "cl100k_base") + len(question_keys)*num_tokens_from_string("GPT question x:  Your answer to the question with index GPT question x. State specific paragraph numbers in the judgment or specific sections in the metadata.", "cl100k_base")

            #Calculate number of tokens of answers
            answers_tokens = num_tokens_from_string(str(answers_dict), "cl100k_base")

            input_tokens = judgment_capped_tokens + questions_tokens + other_tokens
            
            GPT_output_list = [answers_dict, answers_tokens, input_tokens]

        #Create GPT question headings and append answers to individual spreadsheets

        for question_index in question_keys:
            question_heading = question_index + ': ' + questions_json[question_index]
            df_individual.loc[judgment_index, question_heading] = answers_dict[question_index]

        #Calculate and append GPT finish time and time difference to individual df
        GPT_finish_time = datetime.now()
        
        GPT_time_difference = GPT_finish_time - GPT_start_time

        df_individual.loc[judgment_index, 'GPT time estimate (seconds)'] = GPT_time_difference.total_seconds()

        #Calculate GPT costs

        GPT_cost = GPT_output_list[1]*GPT_output_cost + GPT_output_list[2]*GPT_input_cost

        #Calculate and append GPT cost to individual df
        df_individual.loc[judgment_index, 'GPT cost estimate (USD excl GST)'] = GPT_cost
    
    return df_individual



# %%
#Obtain parameters

def run(df_master):
    df_master = df_master.fillna('')

    #Apply split and format functions for headnotes choice, court choice and GPT questions
     
    df_master['Enter your question(s) for GPT'] = df_master['Enter your question(s) for GPT'][0: answers_characters_bound].apply(split_by_line)
    df_master['questions_json'] = df_master['Enter your question(s) for GPT'].apply(GPT_label_dict)
    
    #Create judgments file
    judgments_file = []
    
    #Conduct search
    
    url_search_results = fca_search(case_name_mnc = df_master.loc[0, 'Case name or medium neutral citation'],
                     judge = df_master.loc[0, 'Judge'], 
                     reported_citation = df_master.loc[0, 'Reported citation'],
                     file_number  = df_master.loc[0, 'File number'],
                     npa = df_master.loc[0, 'National practice area'], 
                     with_all_the_words  = df_master.loc[0, 'With all the words'], 
                     with_at_least_one_of_the_words = df_master.loc[0, 'With at least one of the words'],
                     without_the_words = df_master.loc[0, 'Without the words'],
                     phrase  = df_master.loc[0, 'Phrase'], 
                     proximity = df_master.loc[0, 'Proximity'], 
                     on_this_date = df_master.loc[0, 'On this date'], 
                     after_date = df_master.loc[0, 'After date'], 
                     before_date = df_master.loc[0, 'Before date'], 
                     legislation = df_master.loc[0, 'Legislation'], 
                     cases_cited = df_master.loc[0, 'Cases cited'], 
                     catchwords = df_master.loc[0, 'Catchwords'] 
                    )
        
    judgments_counter_bound = int(df_master.loc[0, 'Maximum number of judgments'])

    judgments_links = search_results_to_judgment_links(url_search_results, judgments_counter_bound)

    for link in judgments_links:

        judgment_dict = meta_judgment_dict(link)

#        meta_data = meta_dict(link)  
#        doc_link = link_to_doc(link)
#        judgment_dict = doc_link_to_dict(doc_link)
#        judgment_dict = link_to_dict(link)
#        judgments_all_info = { **meta_data, **judgment_dict}
#        judgments_file.append(judgments_all_info)
        judgments_file.append(judgment_dict)
        pause.seconds(5)
    
    #Create and export json file with search results
    json_individual = json.dumps(judgments_file, indent=2)
    
    df_individual = pd.read_json(json_individual)
    
    #Rename column titles
    
#    try:
#        df_individual['Hyperlink (double click)'] = df_individual['Hyperlink'].apply(link)
#        df_individual.pop('Hyperlink')
#    except:
#        pass
    
    #Instruct GPT
    
    API_key = df_master.loc[0, 'Your GPT API key'] 
    
    #apply GPT_individual to each respondent's judgment spreadsheet
    
    GPT_activation = int(df_master.loc[0, 'Tick to use GPT'])

    questions_json = df_master.loc[0, 'questions_json']
            
    #Engage GPT
    df_updated = engage_GPT_json_tokens(questions_json, df_individual, GPT_activation, API_key)

    df_updated.pop('Judgment')

    if int(df_master.loc[0, 'Metadata inclusion']) == 0:
        for meta_label in meta_labels_droppable:
            try:
                df_updated.pop(meta_label)
            except:
                pass
    
    return df_updated


# %%
def search_url(df_master):
    df_master = df_master.fillna('')
    
    #Combining catchwords into new column
    
    #Conduct search
    
    url = fca_search(case_name_mnc = df_master.loc[0, 'Case name or medium neutral citation'],
                     judge = df_master.loc[0, 'Judge'], 
                     reported_citation = df_master.loc[0, 'Reported citation'],
                     file_number  = df_master.loc[0, 'File number'],
                     npa = df_master.loc[0, 'National practice area'], 
                     with_all_the_words  = df_master.loc[0, 'With all the words'], 
                     with_at_least_one_of_the_words = df_master.loc[0, 'With at least one of the words'],
                     without_the_words = df_master.loc[0, 'Without the words'],
                     phrase  = df_master.loc[0, 'Phrase'], 
                     proximity = df_master.loc[0, 'Proximity'], 
                     on_this_date = df_master.loc[0, 'On this date'], 
                     after_date = df_master.loc[0, 'After date'], 
                     before_date = df_master.loc[0, 'Before date'], 
                     legislation = df_master.loc[0, 'Legislation'], 
                     cases_cited = df_master.loc[0, 'Cases cited'], 
                     catchwords = df_master.loc[0, 'Catchwords'] 
                    )
    return url


# %% [markdown]
# # Streamlit form, functions and parameters

# %%
#Function to open url
def open_page(url):
    open_script= """
        <script type="text/javascript">
            window.open('%s', '_blank').focus();
        </script>
    """ % (url)
    html(open_script)


# %%
#Create form

with st.form("GPT_input_form") as df_responses:
    st.title("The Empirical Legal Research Kickstarter")
    st.header("A Federal Court Pilot")
    
    st.markdown("""The Empirical Legal Research Kickstarter is a web-based program designed to help kickstart empirical research involving judgments. It automates many costly, time-consuming and mundane tasks in empirical research.

The Federal Court pilot version can automatically

(1) search for and collect select judgments of the Federal Court of Australia, including the Full Court; 

(2) extract and code the judgment metadata; and

(2) use GPT — a generative AI — as a research assistant to answer your questions about each judgment.

**Complete this form to kickstart your project!**
""")
    st.caption('The Empirical Legal Research Kickstarter is the joint effort of Mike Lynch and Xinwei Luo of Sydney Informatics Hub and Ben Chen of Sydney Law School. It is partially funded by a University of Sydney Research Accelerator (SOAR) Prize awarded to Ben in 2022. Please send any enquiries to Ben at ben.chen@sydney.edu.au.')

    st.header("Your information")
#    st.markdown("""You must enter an API key if you wish to use GPT to analyse more than 10 judgments. 
#To obtain an API key, first sign up for an account with OpenAI at 
#https://platform.openai.com/signup. You can then find your API key at https://platform.openai.com/api-keys.
#""")
    name_entry = st.text_input("Your name")
    email_entry = st.text_input("Your email address")
#    gpt_api_key_entry = st.text_input("Your GPT API key")

    #Search terms

    st.header("Judgment Search Criteria")
    
    st.markdown("""This program will collect (ie scrape) the first 10 judgments satisfying your search terms.

For search tips, please visit the Federal Court Digital Law Library at https://www.fedcourt.gov.au/digital-law-library/judgments/search. This section mimics their judgments search function.
""")
    st.caption('During the pilot stage, the number of judgments to scrape is capped. Please reach out to Ben at ben.chen@sydney.edu.au should you wish to cover more judgments, courts, or tribunals.')
    
    st.subheader("Your Search Terms")

    catchwords_entry = st.text_input('Catchwords')

    legislation_entry = st.text_input('Legislation')

    cases_cited_entry = st.text_input('Cases cited')

    case_name_mnc_entry = st.text_input("Case name or medium neutral citation")
    
    judge_entry = st.text_input('Judge')

    reported_citation_entry = st.text_input('Reported citation')

    file_number_entry = st.text_input('File number')

    npa_entry = st.text_input('National practice area')

    
    with_all_the_words_entry = st.text_input('With ALL the words')

    with_at_least_one_of_the_words_entry = st.text_input('With at least one of the words')

    without_the_words_entry = st.text_input('Without the words')

    phrase_entry = st.text_input('Phrase')

    proximity_entry  = st.text_input('Proximity')

    on_this_date_entry = st.date_input('On this date', value = None, format="DD/MM/YYYY")

    after_date_entry = st.date_input('After date', value = None, format="DD/MM/YYYY")

    st.caption('Relatively earlier judgments will not be collected if they are available in PDF only. For information about judgment availability, please visit https://www.fedcourt.gov.au/digital-law-library/judgments/judgments-faq.')
    
    before_date_entry = st.date_input('Before date', value = None, format="DD/MM/YYYY")
    
    judgments_counter_bound_entry = judgments_counter_bound

    st.markdown("""You can preview your search results after you have entered some search terms.
    """)
    
    preview_button = st.form_submit_button('Preview what you will find (in a popped up window)')

    st.header("Judgment Metadata Collection")
    
    st.markdown("""Would you like to obtain judgment metadata? Such data include the name of the judge, the decision date and so on. 
    
Case names and medium neutral citations are always included with your results.
""")
    
    meta_data_entry = st.checkbox('Tick to include metadata in your results', value = False)

    st.header("Use GPT as Your Research Assistant")

    st.markdown("**You have three (3) opportunities to engage with GPT through the Empirical Legal Research Kickstarter. Would you like to use one (1) of these opportunities now?**")

    gpt_activation_entry = st.checkbox('Tick to use GPT', value = False)

    st.caption("Released by OpenAI, GPT is a family of large language models (ie a generative AI that works on language). Answers to your questions will be generated by model gpt-3.5-turbo-0125. Due to a technical limitation, the model will be instructed to 'read' up to approximately 11,726 words from each judgment.")

    st.markdown("""Please consider trying the Empirical Legal Research Kickstarter without asking GPT any questions first. You can, for instance, obtain the judgments satisfying your search criteria and extract the judgment metadata without using GPT.
""")

    st.caption("Engagement with GPT is costly and funded by a grant.  Ben's own experience suggests that it costs approximately USD \$0.003-\$0.008 (excl GST) per judgment. The exact cost for answering a question about a judgment depends on the length of the question, the length of the judgment, and the length of the answer produced (as elaborated at https://openai.com/pricing for model gpt-3.5-turbo-0125). You will be given ex-post cost estimates.")

    st.subheader("Enter your question(s) for GPT")
    
    st.markdown("""You may enter one or more questions. **Please enter one question per line or per paragraph.**

GPT is instructed to avoid giving answers which cannot be obtained from the relevant judgment itself. This is to minimise the risk of giving incorrect information (ie hallucination).

You may enter at most 1000 characters here.
    """)

    gpt_questions_entry = st.text_area("", height= 200, max_chars=1000) 

    st.header("Consent")

    st.markdown("""By submitting this form, you agree that the data and/or information this form provides will be temporarily stored on one or more of Ben Chen's electronic devices and/or one or more remote servers for the purpose of producing an output containing data in relation to judgments. Any such data and/or information may also be given to GPT for the same purpose should you choose to use GPT.

If you do not agree, then please feel free to close this form. Any data or information this form provides will neither be received by Ben Chen nor be sent to GPT.
""")
    
    consent =  st.checkbox('Yes, I agree.', value = False)

    st.header("Next Steps")

    st.markdown("""**You can submit this form to run the Empirical Legal Research Kickstarter.** The estimated waiting time to get your results is 10-20 seconds per judgment.

You can also download a record of your responeses.
    
""")

    run_button = st.form_submit_button('SUBMIT this form')

    keep_button = st.form_submit_button('DOWNLOAD your responses')




# %% [markdown]
# # Save and run

# %%
if preview_button:

    gpt_api_key_entry = ''

    df_master = create_df()

    judgments_url =  fca_search(case_name_mnc = df_master.loc[0, 'Case name or medium neutral citation'],
                     judge = df_master.loc[0, 'Judge'], 
                     reported_citation = df_master.loc[0, 'Reported citation'],
                     file_number  = df_master.loc[0, 'File number'],
                     npa = df_master.loc[0, 'National practice area'], 
                     with_all_the_words  = df_master.loc[0, 'With all the words'], 
                     with_at_least_one_of_the_words = df_master.loc[0, 'With at least one of the words'],
                     without_the_words = df_master.loc[0, 'Without the words'],
                     phrase  = df_master.loc[0, 'Phrase'], 
                     proximity = df_master.loc[0, 'Proximity'], 
                     on_this_date = df_master.loc[0, 'On this date'], 
                     after_date = df_master.loc[0, 'After date'], 
                     before_date = df_master.loc[0, 'Before date'], 
                     legislation = df_master.loc[0, 'Legislation'], 
                     cases_cited = df_master.loc[0, 'Cases cited'], 
                     catchwords = df_master.loc[0, 'Catchwords'] 
                    )

    open_page(judgments_url)


# %%
if run_button:

    #Using own GPT

    gpt_api_key_entry = st.secrets["openai"]["gpt_api_key"]

    #Create spreadsheet of responses
    df_master = create_df()

    #Obtain google spreadsheet

    conn = st.connection("gsheets", type=GSheetsConnection)
    google_record_url = "https://docs.google.com/spreadsheets/d/1Mlz_QyDl5fxoFiEgBXxqc2BOXJh8gognrBpr-4ML4_Q/edit#gid=1420440228"
    df_google = conn.read(spreadsheet=google_record_url)
    df_google = df_google.fillna('')
    df_google=df_google[df_google["Processed"]!='']


    if int(consent) == 0:
        st.write("You must click on 'Yes, I agree.' to run the Empirical Legal Research Kickstarter.")

    elif (('@' not in df_master.loc[0, 'Your email address']) & (int(df_master.loc[0]["Tick to use GPT"]) > 0)):
        st.write('You must enter a valid email address to use GPT')

    elif ((int(df_master.loc[0]["Tick to use GPT"]) > 0) & (prior_GPT_uses(df_master.loc[0, "Your email address"], df_google) >= GPT_use_bound)):
        st.write('At this pilot stage, each user may use GPT at most 3 times. Please feel free to email Ben at ben.chen@gsydney.edu.edu if you would like to use GPT again.')
    
    elif ((int(df_master.loc[0]["Tick to use GPT"]) > 0) & (len(df_master.loc[0]["Your GPT API key"]) < 20)):
        st.write("You must enter a valid API key for GPT.")

    else:

        st.write("Your results will be available for download soon. The estimated waiting time is about 2-3 minutes.")

        #Upload placeholder record onto Google sheet
        df_plaeceholdeer = pd.concat([df_google, df_master])
        conn.update(worksheet="Sheet1", data=df_plaeceholdeer, )

        #Produce results

        df_individual_output = run(df_master)

        #Keep record on Google sheet
        
        df_master["Processed"] = datetime.now()

        df_master.pop("Your GPT API key")
        
        df_to_update = pd.concat([df_google, df_master])
        
        conn.update(worksheet="Sheet1", data=df_to_update, )

        st.write("Your results are now available for download. Thank you for using the Empirical Legal Research Kickstarter.")
        
        #Button for downloading results
        output_name = df_master.loc[0, 'Your name'] + '_' + str(today_in_nums) + 'results'

        csv_output = convert_df_to_csv(df_individual_output)
        
        ste.download_button(
            label="Download your results as a CSV (for use in Excel etc)", 
            data = csv_output,
            file_name= output_name + '.csv', 
            mime= "text/csv", 
#            key='download-csv'
        )

        json_output = convert_df_to_json(df_individual_output)
        
        ste.download_button(
            label="Download your results as a JSON", 
            data = json_output,
            file_name= output_name + '.json', 
            mime= "application/json", 
        )





# %%
if keep_button:

    #Using own GPT API key here

    gpt_api_key_entry = ''
    
    df_master = create_df()

    df_master.pop("Your GPT API key")


    responses_output_name = df_master.loc[0, 'Your name'] + '_' + str(today_in_nums) + '_responses'

    #Produce a file to download

    csv = convert_df_to_csv(df_master)
    
    ste.download_button(
        label="Download as a CSV (for use in Excel etc)", 
        data = csv,
        file_name=responses_output_name + '.csv', 
        mime= "text/csv", 
#            key='download-csv'
    )

    json = convert_df_to_json(df_master)
    
    ste.download_button(
        label="Download as a JSON", 
        data = json,
        file_name= responses_output_name + '.json', 
        mime= "application/json", 
    )

