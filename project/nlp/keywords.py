from pydoc import doc
from typing import Tuple
import pandas as pd
import spacy
import sys
import inspect

# Load model
nlp = spacy.load("nl_core_news_md")
stopwords = nlp.Defaults.stop_words

DEBUG = False
if DEBUG:

    def getname():
        return sys._getframe(1).f_code.co_name


def nlp_cleanandlemmatize(
    txtdoc: str, list_wordstoskip: str = "", onlynouns: bool = True
) -> Tuple[dict, list]:
    if DEBUG:
        print("In function: ", getname(), inspect.signature(globals()[getname()]))

    LANG = "nl"
    # words to discard
    months = {
        "nl": [
            "januari",
            "februari",
            "maart",
            "april",
            "mei",
            "juni",
            "augustus",
            "september",
            "oktober",
            "november",
            "december",
        ],
        "fr": [
            "janvier",
            "fevrier",
            "mars",
            "avril",
            "mai",
            "juin",
            "juillet",
            "aout",
            "septembre",
            "octobre",
            "decembre",
        ],
    }
    days = {
        "nl": [
            "maandag",
            "dinsdag",
            "woensdag",
            "donderdag",
            "vrijdag",
            "zaterdag",
            "zondag",
        ],
        "fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
    }
    #
    nlp.max_length = 10000000
    nlp_doc = nlp(txtdoc)
    list_allwordslemmatized = []
    dict_uniqwords = {}
    list_tokens = []
    # filter
    for token in nlp_doc:
        lemma_lower = token.lemma_.lower()
        if token in stopwords:
            continue
        if token.is_punct or token.is_space or token.is_stop:
            continue
        if token.text.isdecimal():
            continue
        if True in [char.isdigit() for char in token.text]:
            continue
        if token.text[-1] == ".":
            continue
        if len(token.text) <= 2:
            continue
        if lemma_lower in months[LANG]:
            continue
        if lemma_lower in days[LANG]:
            continue
        if lemma_lower in list_wordstoskip:
            continue
        # pass only nouns
        if token.pos_ != "NOUN":
            continue
        # create dict of unique words with count
        if lemma_lower not in dict_uniqwords:
            dict_uniqwords[lemma_lower] = 1
            # save tokens for vector comparison
            list_tokens.append(token)
        else:
            dict_uniqwords[lemma_lower] += 1
    return dict_uniqwords, list_tokens
    # end of filter------------------------


# compare a token against a tokenslist
def token_compare(token_totest, list_tokens, min_score: int = 0.6):
    if DEBUG:
        print("In function: ", getname(), inspect.signature(globals()[getname()]))

    # return list of tokens with similarity >= min_score
    list_tokens_toreturn = []
    tot_similar_word = 0
    istax = False
    for token in list_tokens:
        similar = token_totest.similarity(token)
        # only addup the scores >= min_score
        if similar >= min_score:
            list_tokens_toreturn.append([token_totest, token, similar])
            # positive for tax
            istax = True
            tot_similar_word += similar
    return istax, tot_similar_word, list_tokens_toreturn


def create_list_of_keywords(
    dataframe: pd.DataFrame,
    numberofdocumenttoscan: int = 50,
    similar_doc: int = 0,
    min_score: float = 0.6,
    list_keywords: list = [],
) -> Tuple[list, list, list]:
    if DEBUG:
        print("In function: ", getname(), inspect.signature(globals()[getname()]))

    list_keep_tax_words = []
    list_keep_pointer_taxdocs = []
    list_keep_pointer_alldocs = []

    # take all docs if 0
    if numberofdocumenttoscan == 0:
        numberofdocumenttoscan = len(dataframe)

    for n in range(numberofdocumenttoscan):

        print("Documents analyzed: ", numberofdocumenttoscan, n)

        txtdoc = dataframe["cleantextnl"].values[n]
        list_wordstoskip = ["blabla", "blablabla"]  # add here words to discard
        dict_uniqwords, list_tokens = nlp_cleanandlemmatize(
            txtdoc, list_wordstoskip
        )  # get tokens

        # tokenize and check
        tot_similar_doc = 0  # keep score for onlytax docs (istax=True)
        tot_similar_doc_all = 0  # keep score for all docs
        istax_doc = False

        for word in list_keywords:
            token_word = nlp(word)
            istax, tot_similar_word, list_res_tokens = token_compare(
                token_word, list_tokens, min_score
            )
            # if DEBUG: print("DEBUG",istax, tot_similar_word, list_res_tokens)
            tot_similar_doc_all += tot_similar_word

            if istax:
                for taxtoken in list_res_tokens:
                    if taxtoken[1].lemma_.lower() not in list_keep_tax_words:
                        list_keep_tax_words.append(taxtoken[1].lemma_.lower())
                tot_similar_doc += tot_similar_word
            istax_doc |= istax

        # store score for all
        list_keep_pointer_alldocs.append([n, tot_similar_doc_all])

        # store score for taxdocs
        if istax_doc and (tot_similar_doc >= similar_doc):
            list_keep_pointer_taxdocs.append([n, tot_similar_doc])

    return list_keep_pointer_taxdocs, list_keep_tax_words, list_keep_pointer_alldocs


def create_pickle_keywords_and_docscores(
    dataframe: pd.DataFrame,
    list_keywords: list = ["belasting"],
    file_keywords: str = "",
    file_docscores: str = "",
) -> Tuple[list, list]:
    if DEBUG:
        print("In function: ", getname(), inspect.signature(globals()[getname()]))

    # settings : [numberofdocumenttoscan (0 for all), min similarity score for doc to get into the taxlist, min similarity score for keywords]):
    settings = [
        [5, 5, 0.97],  # step1
        [10, 10, 0.95],  # step2
        [15, 20, 0.90],  # step3
        [0, 40, 0.87],  # step4 All documents
    ]

    numberofsteps = len(settings)
    for step in range(numberofsteps):
        (
            list_keep_pointer_taxdocs,
            list_keep_tax_words,
            list_keep_pointer_alldocs,
        ) = create_list_of_keywords(
            dataframe,
            settings[step][0],
            settings[step][1],
            settings[step][2],
            list_keywords,
        )
        list_keywords += list_keep_tax_words
        # no duplicates
        list_keywords = list(set(list_keywords))
        list_docscores = list_keep_pointer_alldocs

        # no file no pickle
        if file_keywords != "":
            df_keywords = pd.DataFrame(list_keywords, columns=["keywords"])
            df_keywords.to_pickle(file_keywords)

        if file_docscores != "":
            df_docscores = pd.DataFrame(
                list_keep_pointer_alldocs, columns=["docpointer", "docscores"]
            )
            df_docscores.to_pickle(file_docscores)

    return list_keywords, list_docscores


def create_initial_keywordlist(
    dataframe: pd.DataFrame,
    keywords_file: str,
    docscores_file: str,
    language: str = "nl",
    list_keywords: list = ["belasting", "tax", "fisc"],
) -> None:
    # create keyword list picklefile and docscores picklefile
    # read all docs
    if language == "nl":
        # start search for nl keywords
        keywords, docscores = create_pickle_keywords_and_docscores(
            dataframe, list_keywords, keywords_file, docscores_file,
        )
    else:
        print("Language selection not supported for now!")


# unsupervised keyword search
def get_keywordsunsupervised(txt: str, sim: float = 0.90) -> dict:
    # input a text
    # output relevant keywords
    doc = nlp(txt)

    chnk = []
    for chunk in doc.noun_chunks:
        chnk.append(chunk)

    sim_low = sim
    txt_keywords = ""
    list_keywordswithscores = []
    for c in chnk:
        word_simil = 0
        for t in chnk:
            simil = c.similarity(t)
            if simil >= sim_low and simil < 1:
                word_simil += simil

        if word_simil > 1:
            list_keywordswithscores.append([c, word_simil])
            txt_keywords = txt_keywords + c.lemma_ + " "

    dict_txt, list_tokens = nlp_cleanandlemmatize(
        txtdoc=txt_keywords, list_wordstoskip="", onlynouns=True
    )
    return dict_txt


def score_text(
    txt: str,
    language: str = "nl",
    min_score: float = 0.3,
    file_keywords: str = "../data/tax_keywords_nl.pkl",
) -> float:
    if DEBUG:
        print("In function: ", getname(), inspect.signature(globals()[getname()]))

    if language == "nl":
        df_keywords = pd.read_pickle(file_keywords)
        list_keywords = list(df_keywords["keywords"])

        # clean txt / get tokens
        dict_uniqwords, list_tokens = nlp_cleanandlemmatize(txt, [])

        docscore = 0
        count = 0
        for word in list_keywords:
            token_word = nlp(word)
            for token in list_tokens:
                similar = token_word.similarity(token)

                # similarity > min_score to be taken into account
                if similar >= min_score:
                    print(f"Token: {token.text: <50} score : {similar}")
                    docscore += similar
                    count += 1
        if not count:
            count = 1
        docscore = docscore / count
    else:
        print("Language selection not supported for now!")

    return round(docscore, 2) if docscore != 0 else -1


def score_text_byvector(
    txt: str,
    language: str = "nl",
    min_score: float = 0.3,
    file_keywords: str = "../data/tax_keywords_nl.pkl",
) -> float:
    if language != "nl":
        print("Language selection not supported for now!")
        return -1

    df_keywords = pd.read_pickle(file_keywords)
    list_keywords = list(df_keywords["keywords"])

    txt_keywords = ""
    for t in list_keywords:
        txt_keywords += " " + t
    token_txt = nlp(txt_keywords)

    # clean txt
    txt_doc = ""
    dict_uniqwords, list_tokens = nlp_cleanandlemmatize(txt, [])
    for i in list_tokens:
        txt_doc += " " + (i.lemma_).lower()
    token_doc = nlp(txt_doc)

    docscore = token_doc.similarity(token_txt)

    return round(docscore, 2) if docscore != 0 else -1


def get_topic_byvector(txt: str, language: str = "nl") -> float:
    if language != "nl":
        print("Language selection not supported for now!")
        return -1
    list_topic_keywords = [
        ["inkomstenbelasting"],
        ["personenbelasting"],
        ["vennootschapsbelasting"],
        ["rechtspersonenbelasting"],
        ["belasting van niet-inwoners"],
        ["belasting op de toegevoegde waarde"],
        ["internationale belastingrecht"],
        ["registratierechten"],
        ["successierechten"],
        ["douanerechten"],
        ["verkeersbelasting"],
        ["loonbelasting"],
        ["dividendbelasting"],
        ["erfbelasting"],
        ["schenkbelasting"],
        ["kansspelbelasting"],
        ["gokbelasting"],
        ["vermogensrendementsheffing"],
    ]

    # clean text
    txt_doc = ""
    dict_uniqwords, list_tokens = nlp_cleanandlemmatize(txt, [])
    for i in list_tokens:
        txt_doc += " " + (i.lemma_).lower()

    #
    topicscore = []
    for list_keywords in list_topic_keywords:
        txt_keywords = ""
        for t in list_keywords:
            txt_keywords += " " + t
        token_txt = nlp(txt_keywords)
        token_doc = nlp(txt_doc)

        topicscore.append([round(token_doc.similarity(token_txt),2), list_keywords])
        topicscore.sort(reverse=True)

    return topicscore
