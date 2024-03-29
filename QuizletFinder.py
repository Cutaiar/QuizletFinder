from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize 
  
try: 
    from googlesearch import search 
except ImportError:  
    print("No module named 'google' found") 

import requests
import re
from time import sleep 

from bs4 import BeautifulSoup 
from termcolor import colored

import pprint

# Selenium imports may not be needed
import selenium.webdriver as webdriver
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

import os


numSites = 5
debugPrinting = False


###########################################################

#https://stackoverflow.com/questions/17645701/extract-words-surrounding-a-search-word
def searchAround(text, key ,n):
    '''Searches for text, and retrieves n words either side of the text, which are retuned seperatly'''
    word = r"\W*([\w]+)"
    groups = re.search(r'{}\W*{}{}'.format(word*n,key,word*n), text).groups()
    return groups[:n] + groups[n:]

# Get the longest non-stop word from phrase
# Credit: Trenton Morrell
def LNSW(phrase):
    stop_words = set(stopwords.words('english')) 
    word_tokens = word_tokenize(phrase) 
    filtered_sentence = [w for w in word_tokens if not w in stop_words] 
    filtered_sentence = [] 
    for w in word_tokens: 
        if w not in stop_words: 
            filtered_sentence.append(w) 
    sortedwords = sorted(filtered_sentence, key=len)
    return None if len(sortedwords) == 0 else sortedwords[-1]

def prune(phrase):
    return phrase[3:-3]

#https://stackoverflow.com/questions/1883980/find-the-nth-occurrence-of-substring-in-a-string
def findnth(haystack, needle, n):
    parts= haystack.split(needle, n+1)
    if len(parts)<=n+1:
        return -1
    return len(haystack)-len(parts[-1])-len(needle)

################################################################################################

# validate the given url
# https://repl.it/@DevinShende/Quizlet-Scraper
def get_valid_url(in_url):
    url_regex = re.compile(r"^(https://quizlet.com/)?(?P<id>\d{4,15})(/[\w-]{1,1000})?/?$")
    id_regex = re.compile(r"^\d{4,15}$")
    match = url_regex.search(in_url)
    if match:
        if debugPrinting:print("match:",match.group(0),"\n\n")
        url = "https://quizlet.com/"+match.group("id") 
        
        if debugPrinting:print("returning ",url,"\t In get_valid_input()")
        return url
    
    else:
        if debugPrinting: print("match: ",match)
        print("That is not a valid id or url. Please enter the string of numbers following \"quizlet.com\" in the url")
        sleep(0.3)
        print("For example: \"4071437\"")
        sleep(0.2)
        get_valid_url()

# Get the data from the quizlet
# https://repl.it/@DevinShende/Quizlet-Scraper
def scrape_data(url):
    """
    returns list of many dicts: each contains a term and a definition value
    """
    html = requests.get(url).text
    soup = BeautifulSoup(html,"html.parser")

    # msg_404 = "There is no set with the ID you specified" 
    msg_404 = "Page Unavailable" 
    bodyContent = soup.select("div.SetPage-terms")
    if msg_404 in str(soup.body):
        # check for 404
        print("sorry m8, that isn't a valid quizlet course")

    else:
        if debugPrinting: print("YaY!!! real web page. Scraping data....")
        # YAY real page! Now let's do the work of extracting the terms and definitions
        data = [] # data will be a list containing many dicts with term and definition keys

        content = soup.select("div.SetPage-terms")[0] # TODO: This is broke becuase soup.select gives back an empty list
        pairs = content.select("div.SetPageTerm-content")
        for pair in pairs:
            term = pair.select("span.TermText")[0].get_text()
            defn = pair.select("span.TermText")[1].get_text()
            data.append({
                "term":term,
                "definition":defn
            })
            if debugPrinting:
                print(colored("term: ","blue"),term)
                print(colored("definition: ","green"),defn)
    if debugPrinting:print("\nDONE SCRAPING DATA\n\n")
    return data

# Validate the url, and get the data from the quizlet url
# https://repl.it/@DevinShende/Quizlet-Scraper
def get_data_from(url):
    good_url = get_valid_url(url)
    if debugPrinting:print("Getting data from\t",good_url)
    data = scrape_data(url)
    return data

###########################################################

def main():
    running = True;
    while running:
        #query = "U.S. president after Lincoln, almost impeached by the Radical Republicans quizlet"
        query = input("Whats the question? (Type 'q' to quit)\n\n")
        if query == "q":
            running = False
            break
        # Get all the urls
        urls = []
        #os.environ['HTTP_PROXY'] = 'http://172.16.0.3:8888'
        for j in search(query, tld="co.in", num=numSites, stop=numSites, pause=2): 
            if ("quizlet" in j):
                n = findnth(j, "/", 3)
                jfinal = j[0:n+1]
                urls.append(jfinal)
                #print(jfinal)

        # Check data from quizlets to see if theres relevant stuff
        pp = pprint.PrettyPrinter(indent=4)
        found = False
        for url in urls:
            data = get_data_from(url) # Just doing the first one for now
            for pair in data:
                t = pair["term"]
                d = pair["definition"]
                keyword_prune = prune(query.lower())
                matchedT = re.findall(keyword_prune, t);
                matchedD = re.findall(keyword_prune, d);
                if len(matchedT) != 0 or len(matchedD) != 0:
                    found = True
                    print("\n\n -------------------------Found! (with prune)-------------------------\n\n")
                    pp.pprint(pair)
                    print("\n\n ---------------------------------------------------------------------\n\n")

            # Now do the exact same thing with lnsw method
            if not found:
                for pair in data:
                    t = pair["term"]
                    d = pair["definition"]
                    keyword_lnsw = LNSW(query)
                    if keyword_lnsw == None: 
                        print("None keyword_lnsw")
                        exit
                    matchedT = re.findall(keyword_lnsw, t);
                    matchedD = re.findall(keyword_lnsw, d);
                    if len(matchedT) != 0 or len(matchedD) != 0:
                        found = True
                        print("\n\n -------------------------Found! (with LNSW:", keyword_lnsw, ")-------------------------\n\n")
                        pp.pprint(pair)
                        print("\n\n -------------------------------------------------------------\n\n")

                #print(matches)
            #pp.pprint(data)
        if not found: print("\nNothing found.\n")

        # Open selenium window with all urls
        #browser = webdriver.Chrome(executable_path='../chromedriver.exe')
        #browser.get(urls[0])

main()