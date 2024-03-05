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

# %% [markdown]
# # Preliminaries

# %%
#streamlit run /Users/Ben/Library/CloudStorage/Dropbox/Python/OpenAI/GPT_self_contained/GPT_Streamlit_Limited.py

# %%
#Preliminary modules
import os
import os.path 
import json
import pandas as pd
import datetime
from datetime import date
from datetime import datetime
from dateutil.relativedelta import *
from datetime import datetime
import time

#Streamlit
import streamlit as st
from streamlit.components.v1 import html

#NSWCaseLaw
from nswcaselaw.search import Search

#OpenAI
from openai import OpenAI
import tiktoken



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
#Create function for saving responses
def convert_df_to_json(df):
    return df.to_json(orient = 'split', compression = 'infer')

def convert_df_to_csv(df):
   return df.to_csv(index=False).encode('utf-8')


# %% [markdown]
# # CaseLaw NSW functions and parameters

# %%
#Auxiliary lists

nsw_courts =["Court of Appeal", "Court of Criminal Appeal", "Supreme Court", "All of the above Courts"]
headnotes_choices = ["Catchwords", "Before", "Decision date(s)", "Hearing date(s)", "Date(s) of order",  "Jurisdiction", "Decision", "Legislation cited", "Cases cited", "Texts cited", "Category", "Parties", "Decision date from", "Decision date to", "File number", "Representation", "Decision under appeal", "All of the above"]
search_criteria = ['Free text', 'Case name', 'Before', 'Catchwords', 'Party names', 'Medium neutral citation', 'Decision date from', 'Decision date to', 'File number', 'Legislation cited', 'Cases cited']

def search_terms_str(df):

    output = ''
    
    search_terms = df[search_criteria]

    for i in search_terms.loc[0]:
        output = output + str(i)

    return output



# %%
#function to create dataframe
def create_df():

    #submission time
    timestamp = datetime.now()

    #Personal info entries
    
    name = name_entry
    email = email_entry
    gpt_api_key = gpt_api_key_entry

    #Get API key from own secrets file
    
    
    #NSW court choices
    
    courts_list = courts_entry
    courts = ', '.join(courts_list)
    
    #Search terms
    
    body = body_entry
    title = title_entry
    before = before_entry
    catchwords = catchwords_entry
    party = party_entry
    mnc = mnc_entry


    startDate = ''

    if startDate_entry != 'None':

        try:

            startDate = startDate_entry.strftime('%d/%m/%Y')

        except:
            pass
        
    endDate = ''

    if endDate_entry != 'None':
        
        try:
            endDate = endDate_entry.strftime('%d/%m/%Y')
            
        except:
            pass
    
    
    fileNumber = fileNumber_entry
    legislationCited = legislationCited_entry
    casesCited = casesCited_entry

    #Judgment counter bound
    
    judgments_counter_bound_ticked = judgments_counter_bound_entry
    if judgments_counter_bound_ticked > 0:
        judgments_counter_bound = 10
    else:
        judgments_counter_bound = 10000

    #headnotes choice    
    headnotes_list = headnotes_entry
    headnotes = ', '.join(headnotes_list)


    #GPT choice and entry
    gpt_activation_status = gpt_activation_entry
    gpt_questions = gpt_questions_entry

    new_row = {'Processed': '',
           'Timestamp': timestamp,
           'Your name': name, 
           'Your email address': email, 
           'Your GPT API key': gpt_api_key, 
           'New South Wales Courts to cover': courts, 
           'Free text': body, 
           'Case name': title, 
           'Before' : before, 
           'Catchwords' : catchwords, 
           'Party names' : party, 
           'Medium neutral citation': mnc, 
           'Decision date from': startDate, 
           'Decision date to': endDate, 
           'File number': fileNumber, 
           'Legislation cited': legislationCited,
           'Cases cited': casesCited, 
           'Information to Collect from Judgment Headnotes': headnotes,
           'Jugdments counter bound': judgments_counter_bound, 
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

#Create list of all headnotes choices
headnotes_choices_string = 'Catchwords, Before, Decision, Decision date(s), Date(s) of order, Hearing date(s), Jurisdiction, Legislation cited, Cases cited, Texts cited, Category, Parties, File number, Representation, Decision under appeal, All of the above'
headnotes_choices_list = headnotes_choices_string.split(', ')

#Remove 'All of the above' from list of all headnotes choices
headnotes_choices_list.remove('All of the above')

#Create function to convert the string of chosen headnotes choices to a list
def headnotes_choice(x):
    y = x.split(', ')
    individual_choices = []
    if 'All of the above' in y:
        return headnotes_choices_list
    else:
        for i in y:
            individual_choices.append(i)
        return individual_choices

#Create list of all court choices in NSWCaseLaw Scraper notation

NSW_courts_string = 'Court of Appeal, Court of Criminal Appeal, Supreme Court, All of the above Courts'
NSW_courts_list = NSW_courts_string.split(', ')

#Remove 'All of the above' from list of all court choices
NSW_courts_list.remove('All of the above Courts')

#Create function to convert the string of chosen courts to a list; 13 = NSWSC, 3 = NSWCA, 4 = NSWCCA

def court_choice(x):
    y = x.split(', ')
    all_nsw_courts = [3, 4, 13]
    individual_choice = []
    if 'All of the above Courts' in y:
        return all_nsw_courts
    else:
        for i in y:
            if i == 'Court of Appeal':
                individual_choice.append(3)
            if i == 'Court of Criminal Appeal':
                individual_choice.append(4)
            if i == 'Supreme Court':
                individual_choice.append(13)           
        return individual_choice
    
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

#Tidy up dates
def date(x):
    if len(str(x)) >0:
        return str(x).split()[0]
    else:
        return str(x)

# Headnotes fields
headnotes_fields = ["Free text", "Case name", "Before", "Decision date(s)", "Catchwords", "Hearing date(s)", "Date(s) of order",  "Jurisdiction", "Decision", "Legislation cited", "Cases cited", "Texts cited", "Category", "Parties", "Medium neutral citation", "Decision date from", "Decision date to", "File number", "Representation", "Decision under appeal"]
headnotes_keys = ["body", "title", "before", "decisionDate", "catchwords", "hearingDates", "dateOfOrders", "jurisdiction", "decision", "legislationCited", "casesCited", "textsCited", "category", "parties", "mnc", "startDate", "endDate", "fileNumber", "representation", "decisionUnderAppeal"]

#Functions for tidying up headings of columns

#Tidy up hyperlink
def link(x):
    link='https://www.caselaw.nsw.gov.au'+ str(x)
    value = '=HYPERLINK("' + link + '")'
    return value

#Tidy up medium neutral citation

def mnc_cleaner(x):
    x_clean=str(x).split("[")
    y = x_clean[1]
    return '[' + y



# %%
#function to remove unnecessary columns

def remove_unwanted_columns(df_master, df_individual):

    #Reorganise columns

    old_columns = list(df_individual.columns)
    
    for i in ['Case name', 'Medium neutral citation', 'Hyperlink']:
        if i in old_columns:
            old_columns.remove(i)
    
    new_columns = ['Case name', 'Medium neutral citation', 'Hyperlink'] + old_columns
    
    df_individual = df_individual.reindex(columns=new_columns)

    #State user unwanted columns
    headnotes_exclude = []
    
    for x in headnotes_fields:
        if ((x not in df_master.loc[0, "Information to Collect from Judgment Headnotes"]) &( x not in ['Case name', 'Medium neutral citation', 'Hyperlink'])):
            headnotes_exclude.append(x)

    #Remove unwanted columns
    for y in headnotes_exclude:
        if y in df_individual.columns:
                df_individual.pop(y)

    #Remove judgment and uri columns
    try:
        df_individual.pop("judgment")
        df_individual.pop("uri")
        
    except:
        pass
        
    #Remove blank decisions under appeal cells
    
    try:
        for j in df_individual.index:
            if df_individual.loc[j, "Decision under appeal"] == {'Court or tribunal': [], 'Jurisdiction': [], 'Citation': [], 'Date of Decision': [], 'Before': [], 'File Number(s)': []}:
                df_individual.loc[j, "Decision under appeal"] = ''
    except:
        pass

    return df_individual


# %%
def search_url(df_master):
    df_master = df_master.fillna('')
    
    #Apply split and format functions for headnotes choice, court choice and GPT questions
     
    df_master['Information to Collect from Judgment Headnotes'] = df_master['Information to Collect from Judgment Headnotes'].apply(headnotes_choice)
    df_master['New South Wales Courts to cover'] = df_master['New South Wales Courts to cover'].apply(court_choice)
    df_master['Enter your question(s) for GPT'] = df_master['Enter your question(s) for GPT'][0: answers_characters_bound].apply(split_by_line)
    df_master['questions_json'] = df_master['Enter your question(s) for GPT'].apply(GPT_label_dict)
    
    #Combining catchwords into new column
    
    search_dict = {'body': df_master.loc[0, 'Free text']}
    search_dict.update({'title': df_master.loc[0, 'Case name']})
    search_dict.update({'before': df_master.loc[0, 'Before']})
    search_dict.update({'catchwords': df_master.loc[0, 'Catchwords']})
    search_dict.update({'party': df_master.loc[0, 'Party names']})
    search_dict.update({'mnc': df_master.loc[0, 'Medium neutral citation']})
    search_dict.update({'startDate': df_master.loc[0, 'Decision date from']})
    search_dict.update({'endDate': df_master.loc[0, 'Decision date to']})
    search_dict.update({'fileNumber': df_master.loc[0, 'File number']})
    search_dict.update({'legislationCited': df_master.loc[0, 'Legislation cited']})
    search_dict.update({'casesCited': df_master.loc[0, 'Cases cited']})
    df_master.loc[0, 'SearchCriteria']=[search_dict]
    
    #Do search
    
    #Create judgments file
    judgments_file = []
    
    #Conduct search
    
    query = Search(courts=df_master.loc[0, 'New South Wales Courts to cover'], 
                   body = df_master.loc[0, "SearchCriteria"]['body'], 
                   title = df_master.loc[0, "SearchCriteria"]['title'], 
                   before = df_master.loc[0, "SearchCriteria"]['before'], 
                   catchwords = df_master.loc[0, "SearchCriteria"]['catchwords'], 
                   party = df_master.loc[0, "SearchCriteria"]['party'], 
                   mnc = df_master.loc[0, "SearchCriteria"]['mnc'], 
                   startDate = date(df_master.loc[0, "SearchCriteria"]['startDate']), 
                   endDate = date(df_master.loc[0, "SearchCriteria"]['endDate']),
                   fileNumber = df_master.loc[0, "SearchCriteria"]['fileNumber'], 
                   legislationCited  = df_master.loc[0, "SearchCriteria"]['legislationCited'], 
                   casesCited = df_master.loc[0, "SearchCriteria"]['legislationCited'],
                   pause = scraper_pause
                  )
    return query.url


# %% [markdown]
# # GPT functions and parameters

# %%
#Module and costs

GPT_model = "gpt-3.5-turbo-0125"

GPT_input_cost = 1/1000*0.0005 
GPT_output_cost = 1/1000*0.0015

#Decide whether to process my own responeses only

answers_characters_bound = 1000

#Pause between judgment scraping

scraper_pause = 5


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

def judgment_prompt_json(judgment_json):
        
    judgment_to_string = " \n\n Paragraph ".join(judgment_json["judgment"])
    
    judgment_json["judgment"] = judgment_to_string
    
    judgment_content = "Based on the metadata and judgment in the following JSON: " + judgment_json["judgment"].replace("\\n\\n", '\n\n') + ", "

    if len(judgment_content) <= characters_limit_half*2:
        
        return judgment_content

    else:
        
        meta_data_len=len(judgment_content) - len(judgment_to_string)
        
        judgment_len_capped = int(characters_limit_half-meta_data_len/2)
        
        judgment_string_trimmed = judgment_to_string[ : judgment_len_capped] + judgment_to_string[-judgment_len_capped: ]

        judgment_json["judgment"] = judgment_string_trimmed        
        
        judgment_content_capped = "Based on the metadata and judgment in the following JSON: ***" + judgment_json["judgment"].replace("\\n\\n", '\n\n') + "***,"
        
        return judgment_content_capped



# %%
#Define system role content for GPT
role_content = 'You are a legal research assistant helping an academic researcher to answer questions about a public judgment. You will be provided with the judgment and metadata in JSON form. Please answer questions based only on information contained in the judgment and metadata. Where your answer comes from a specific paragraph in the judgment, provide the paragraph number as part of your answer. If you cannot answer any of the questions based on the judgment or metadata, do not make up information, but instead write "answer not found".'

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

            
    os.environ["OPENAI_API_KEY"] = API_key
    
    client = OpenAI()
    
    try:
        completion = client.chat.completions.create(
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
        return str(error)


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

    os.environ["OPENAI_API_KEY"] = API_key
    
    client = OpenAI()
    
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
            GPT_output_list = GPT_json_tokens(questions_json, judgment_json, API_key) #Gives [answers as json, output tokens, input tokens]
            answers_dict = GPT_output_list[0]
        
        else:
            answers_dict = {}    
            for q_index in question_keys:
                #Increases judgment index by 2 to ensure consistency with Excel spreadsheet
                answer = 'Test answer r ' + ' j ' + str(int(judgment_index) + 2) + ' ' + str(q_index)
                answers_dict.update({q_index: answer})
            
            #Own calculation of GPT costs for test answers

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



# %% [markdown]
# # Combined function

# %%
#Obtain parameters

def run(df_master):
    df_master = df_master.fillna('')
    
    #Apply split and format functions for headnotes choice, court choice and GPT questions
     
    df_master['Information to Collect from Judgment Headnotes'] = df_master['Information to Collect from Judgment Headnotes'].apply(headnotes_choice)
    df_master['New South Wales Courts to cover'] = df_master['New South Wales Courts to cover'].apply(court_choice)
    df_master['Enter your question(s) for GPT'] = df_master['Enter your question(s) for GPT'][0: answers_characters_bound].apply(split_by_line)
    df_master['questions_json'] = df_master['Enter your question(s) for GPT'].apply(GPT_label_dict)
    
    #Combining catchwords into new column
    
    search_dict = {'body': df_master.loc[0, 'Free text']}
    search_dict.update({'title': df_master.loc[0, 'Case name']})
    search_dict.update({'before': df_master.loc[0, 'Before']})
    search_dict.update({'catchwords': df_master.loc[0, 'Catchwords']})
    search_dict.update({'party': df_master.loc[0, 'Party names']})
    search_dict.update({'mnc': df_master.loc[0, 'Medium neutral citation']})
    search_dict.update({'startDate': df_master.loc[0, 'Decision date from']})
    search_dict.update({'endDate': df_master.loc[0, 'Decision date to']})
    search_dict.update({'fileNumber': df_master.loc[0, 'File number']})
    search_dict.update({'legislationCited': df_master.loc[0, 'Legislation cited']})
    search_dict.update({'casesCited': df_master.loc[0, 'Cases cited']})
    df_master.loc[0, 'SearchCriteria']=[search_dict]
    
    #Do search
    
    #Create judgments file
    judgments_file = []
    
    #Conduct search
    
    query = Search(courts=df_master.loc[0, 'New South Wales Courts to cover'], 
                   body = df_master.loc[0, "SearchCriteria"]['body'], 
                   title = df_master.loc[0, "SearchCriteria"]['title'], 
                   before = df_master.loc[0, "SearchCriteria"]['before'], 
                   catchwords = df_master.loc[0, "SearchCriteria"]['catchwords'], 
                   party = df_master.loc[0, "SearchCriteria"]['party'], 
                   mnc = df_master.loc[0, "SearchCriteria"]['mnc'], 
                   startDate = date(df_master.loc[0, "SearchCriteria"]['startDate']), 
                   endDate = date(df_master.loc[0, "SearchCriteria"]['endDate']),
                   fileNumber = df_master.loc[0, "SearchCriteria"]['fileNumber'], 
                   legislationCited  = df_master.loc[0, "SearchCriteria"]['legislationCited'], 
                   casesCited = df_master.loc[0, "SearchCriteria"]['legislationCited'],
                   pause = scraper_pause
                  )
    
    #Counter to limit search results to append
    counter = 0
    
    #Go through search results
    
    judgments_counter_bound = int(df_master.loc[0, "Jugdments counter bound"])
    
    for decision in query.results():
        if counter < judgments_counter_bound:
    
            decision.fetch()
            decision_v=decision.values
                                    
            #add search results to json
            judgments_file.append(decision_v)
            counter +=1
    
            time.sleep(scraper_pause)
            
        else:
            break
    
    #Create and export json file with search results
    json_individual = json.dumps(judgments_file, indent=2)
    
    df_individual = pd.read_json(json_individual)
    
    
    #Rename column titles
    
    try:
        df_individual['Hyperlink'] = df_individual['uri'].apply(link)
        df_individual.pop('uri')
    except:
        pass
    
    for col_name in headnotes_keys:
        if col_name in df_individual.columns:
            col_index = headnotes_keys.index(col_name)
            new_col_name = headnotes_fields[col_index]
            df_individual[new_col_name] = df_individual[col_name]
            df_individual.pop(col_name)
    
    #Instruct GPT
    
    #GPT model and costs

    API_key = df_master.loc[0, 'Your GPT API key'] 
    
    #apply GPT_individual to each respondent's judgment spreadsheet
    
    GPT_activation = int(df_master.loc[0, 'Tick to use GPT'])
    
    questions_json = df_master.loc[0, 'questions_json']
            
    #Engage GPT
    df_updated = engage_GPT_json_tokens(questions_json, df_individual, GPT_activation, API_key)

    return df_updated


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
    st.title("Empirical Legal Research Kickstarter")
    st.header("A New South Wales Pilot")
    st.markdown("""The Empirical Legal Research Kickstarter is a computer program designed to help kickstart empirical research involving judgments. It automates many costly, time-consuming and mundane tasks in empirical research.

The NSW pilot version can automatically

(1) search for and collect select judgments of the Supreme Court of New South Wales, including the Court of Appeal and the Court of Criminal Appeal;

(2) extract and code information from the judgment headnotes; and

(3) use GPT — a generative AI — as a research assistant to answer your questions about each judgment.

**Complete this form to kickstart your empirical project.**

:grey[The Empirical Legal Research Kickstarter is the joint effort of Mike Lynch and Xinwei Luo of Sydney Informatics Hub and Ben Chen of Sydney Law School. It is partially funded by a University of Sydney Research Accelerator (SOAR) Prize awarded to Ben in 2022. Please send any enquiries to Ben (the developer) at ben.chen@sydney.edu.au.]
""")

    st.header("Your information")
#    st.markdown("""You must enter an API key if you wish to use GPT. 
#To obtain an API key, first sign up for an account with OpenAI at 
#https://platform.openai.com/signup. You can then find your API key at https://platform.openai.com/api-keys.
#""")
    name_entry = st.text_input("Your name")
    email_entry = st.text_input("Your email address")
 #   gpt_api_key_entry = st.text_input("Your GPT API key")

    #Search terms

    st.header("Judgment Search Criteria")
    
    st.markdown("""Your search terms will identify the judgments to be collected and coded.

Pre-1999 decisions are usually not available at CaseLaw NSW and will unlikely to be collected.

For search tips, please visit CaseLaw NSW at https://www.caselaw.nsw.gov.au/search/advanced. This section mimics their Advance Search function.
    """)

    st.subheader("New South Wales Courts to cover")

    courts_entry = st.multiselect('You must select at least one court', nsw_courts)
    
    st.subheader("Your Search Terms")

    st.markdown("""*This pilot program will collect (ie scrape) the first 10 judgments satisfying your search criteria.*
    
Please reach out to Ben at ben.chen@sydney.edu.au should you wish to cover more judgments, courts, or tribunals.
""")

    body_entry = st.text_input("Free text (searches the entire judgment)") 
    
    title_entry = st.text_input("Case name")
    
    before_entry = st.text_input("Before (name of judge")
    
    catchwords_entry = st.text_input("Catchwords")
    
    party_entry = st.text_input("Party names")
    
    mnc_entry = st.text_input("Medium neutral citation (must include square brackets eg [2022] NSWSC 922)")
    
    startDate_entry = st.date_input("Decision date from (01/01/1999 the earliest)", value = None, format="DD/MM/YYYY")
    
    endDate_entry = st.date_input("Decision date to", value = None,  format="DD/MM/YYYY")
    
    fileNumber_entry = st.text_input("File number")
    
    legislationCited_entry = st.text_input("Legislation cited")
    
    casesCited_entry = st.text_input("Cases cited")
        
#    judgments_counter_bound_entry = st.checkbox('Untick to collect potentially more than 10 judgments', value = True)

    judgments_counter_bound_entry = 10

    st.markdown("""You can preview your search results on CaseLaw NSW after you have entered some search terms.
    """)
    
    preview_button = st.form_submit_button('Click to preview what you will find (in a popped up window)')

    st.header("Information to Collect from Judgment Headnotes")
    
    st.markdown("""Please select what information from judgment headnotes you would like to obtain.
Case name, link to CaseLaw NSW, and medium neutral citation are always included.
""")
    
    headnotes_entry = st.multiselect("Please select", headnotes_choices)

    st.markdown(""":grey[The code used to extract judgment headnotes is available at https://github.com/Sydney-Informatics-Hub/nswcaselaw. Such extraction does not require engagement with GPT. ]
""")
    
    st.header("Questions for GPT")

    st.markdown("""*Please consider trying the Empirical Legal Research Kickstarter without asking GPT any questions first.* You can, for instance, obtain the judgments satisfying your search criteria and extract information from the judgment headnotes without using GPT.

Engagement with GPT is costly and funded by a grant.  Ben's own experience suggests that it costs approximately USD \$0.003-\$0.008 (excl GST) per judgment. The exact cost for answering a question about a judgment depends on the length of the question, the length of the judgment, and the length of the answer produced (as elaborated at https://openai.com/pricing for model gpt-3.5-turbo-0125).
You will be given ex-post cost estimates if you choose to use GPT now.
""")

    gpt_activation_entry = st.checkbox('Tick to use GPT', value = False)

    st.subheader("Enter your question(s) for GPT")
    
    st.markdown("""You may enter one or more questions. **Please enter one question per line or per paragraph.**

GPT is instructed to avoid giving answers which cannot be obtained from the relevant judgment itself. This is to minimise the risk of giving incorrect information (ie hallucination).

You may enter at most 1000 characters here.
    """)

    gpt_questions_entry = st.text_area("", height= 200, max_chars=1000) 

    st.header("Consent")

    st.markdown("""By submitting this form, you agree that the data and/or information this form provides will be temporarily stored one one or more remote servers for the purpose of producing an output containing data in relation to judgments and sending such output to your nominated email address. Any such data and/or information may also be given to GPT for the same purpose should you choose to use GPT. You will be given a record of any such data and/or information so stored and/or given to GPT.

If you do not agree, then please feel free to close this form. Any data or information this form provides will neither be received by Ben Chen nor be sent to GPT.
""")
    
    consent =  st.checkbox('Yes, I agree.', value = False)

    st.header("Next steps")

    st.markdown("""You can now :green[run the Empirical Legal Research Kickstarter]. The estimated running time is 10-20 seconds per judgment.

You are encouraged to :blue[download a record of your responeses]. To protect your privacy, Ben (the developer) does not keep a record of your responses or results.
    
""")
    
    run_button = st.form_submit_button('Run the Empirical Legal Research Kickstarter')

    keep_button = st.form_submit_button('Download your responses')


# %% [markdown]
# # Save and run

# %%
if preview_button:

    #Using own GPT API key here

    gpt_api_key_entry = ''

    df_master = create_df()

    judgments_url = search_url(df_master)

    open_page(judgments_url)

#    st.write(judgments_url)
    

# %%
if run_button:

    if int(consent) == 0:
        st.write("You must click on 'Yes, I agree.' to run the Empirical Legal Research Kickstarter.")

    else:

        #Using own GPT 

        gpt_api_key_entry = st.secrets["openai"]["gpt_api_key"]

        df_master = create_df()

        if ((int(df_master.loc[0]["Tick to use GPT"]) > 0) & (len(df_master.loc[0]["Your GPT API key"]) < 20)):
            st.write("You must enter a valid API key for GPT.")

        else:            
            
            if len(courts_entry) == 0:
                st.write('Please select at least one court.')
        
            if search_terms_str(df_master) == 'NoneNone':
                st.write('Please enter at least one search term.')
        
            if ((len(courts_entry) > 0) & (search_terms_str(df_master) != 'NoneNone')):

                st.write("Great. A button for downloading your results will appear soon. The estimated running time is 10-20 seconds per judgment.")

                df_individual = run(df_master)
        
                df_individual_output = remove_unwanted_columns(df_master, df_individual)
        
                output_name = df_master.loc[0, 'Your name'] + '_' + str(today_in_nums) + 'results.csv'
        
                csv_output = convert_df_to_csv(df_individual_output)
                
                st.download_button(
                    label="Download your results as CSV", 
                    data = csv_output,
                    file_name= output_name, 
                    mime= "text/csv", 
                    key='download-csv'
                )


# %%
if keep_button:

    #Using own GPT API key here

    gpt_api_key_entry = ''
    
    df_master = create_df()
    
    if len(courts_entry) == 0:
        st.write('Please select at least one court.')

    if search_terms_str(df_master) == 'NoneNone':
        st.write('Please enter at least one search term.')

    if ((len(courts_entry) > 0) & (search_terms_str(df_master) != 'NoneNone')):

        responses_output_name = df_master.loc[0, 'Your name'] + '_' + str(today_in_nums) + '_responses.csv'

        csv = convert_df_to_csv(df_master)
         
        st.download_button(
            label="Download your responses as CSV", 
            data = csv,
            file_name=responses_output_name, 
            mime= "text/csv", 
            key='download-csv'
        )
