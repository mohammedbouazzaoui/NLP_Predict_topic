import pathlib
import pandas as pd
import nlp.keywords as kw
import scrapping.scrape as s


file_links = pathlib.Path(__file__).parent / "data/KPMG Tax Case - Data Set.xlsx"

file_keywords = pathlib.Path(__file__).parent / "data/tax_keywords_nl.pkl"
file_scores = pathlib.Path(__file__).parent / "data/tax_docscores_nl.pkl"
file_dataframe = pathlib.Path(__file__).parent / "data/Staatsblad.pkl"

SCRAPPING = True
KEYWORDING = True


def scrapping():
    # Cleaning Data
    df_raw = pd.read_excel(file_links)
    df_raw.drop_duplicates(inplace=True)
    df_raw.reset_index(drop=True, inplace=True)
    df_raw
    df = df_raw.copy(deep=True)

    # Scrape urls & save content to file
    s.scrape_urls(df)


# Create keywords of scrapped files
def keywording():
    df = pd.read_pickle(file_dataframe)
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    print(df)
    kw.create_initial_keywordlist(df, file_keywords, file_scores)


def main():
    if SCRAPPING:
        scrapping()
    if KEYWORDING:
        keywording()


if __name__ == "__main__":
    main()
