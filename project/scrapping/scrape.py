import pandas as pd
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import html2text
import requests
import pathlib

file_dataframe = pathlib.Path(__file__).parent / "../data/Staatsblad.pkl"


def scrape_urls(df: pd.DataFrame, language: str = "nl", pnt: int = 0) -> None:
    # Prepare dataframe
    df["cleantextnl"] = np.nan

    # Scrape the dutch URLS
    for url in df["Link NL"]:

        # Link is correct
        if type(url) != float:
            # generate the correct url
            htmllanguage = "language=" + language
            url = url.replace("language=nl", htmllanguage)
            url2 = url.replace(".pl?", "_body.pl?")

            # try to access the url
            try:
                response = requests.get(url2, timeout=5)

                # Get the text from the html
                soup = BeautifulSoup(response.content, "html").text
                dummy = html2text.html2text(soup)

                dummy = dummy.split("---|---|---|---|---|---")
                dummy = dummy[0].split("begin |  |  eerste woord |  laatste woord |  |")

                cleantext = dummy[0]

                # Input the cleaned text into the dataframe & Save it to file
                txtlabel = "cleantext" + language
                df[txtlabel][pnt] = cleantext
                pnt += 1

                df.to_pickle(file_dataframe)

            # if the connections times out continue with the rest of the urls
            except requests.RequestException:
                print("scraping :", pnt, url)
                print("RequestException")
                pnt += 1
                continue

        # Link is Nan
        else:
            print("scraping :", pnt, url)
            pnt += 1

    # Save final dataframe
    df.reset_index(drop=True, inplace=True)
    print(df)
    df.to_pickle(file_dataframe)
    print("Done Scraping")
