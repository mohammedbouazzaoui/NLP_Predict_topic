import os
import pandas as pd
from tokenize import String
from threading import Thread

from flask import Flask, render_template, request, flash
from werkzeug.utils import secure_filename
import pathlib
import nlp.keywords as kw

ALLOWED_EXTENSIONS = set(["txt"])
UPLOAD_FOLDER = pathlib.Path(__file__).parent / "static/uploads/"
KEYWORD_FILE = pathlib.Path(__file__).parent / "data/tax_keywords_nl.pkl"
DOCSCORES_FILE = pathlib.Path(__file__).parent / "data/tax_docscores_nl.pkl"
FILES = pathlib.Path(__file__).parent / "data/Staatsblad.pkl"


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Check to see if file is allowed
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def route_api():
    if request.method == "GET":
        return render_template("index.html")

    if request.method == "POST":

        # if there is a text given in the form
        if "text" in request.form:
            text = request.form["text"]
            print(text)

            # If they want to predict the tax score
            if request.form["action"] == "Predict":
                # result = kw.score_text(text, file_keywords=KEYWORD_FILE)
                prediction = kw.get_topic_byvector(text)
                result_v = kw.score_text_byvector(text, file_keywords=KEYWORD_FILE)
                return render_template("index.html", result=result_v, prediction=prediction)
            # If they want to generate the keywords
            if request.form["action"] == "Keywords":
                keywords = kw.get_keywordsunsupervised(text)
                keywords = dict(
                    sorted(keywords.items(), key=lambda item: item[1], reverse=True)
                )
                return render_template("index.html", keywords=keywords)

        # If there is no text & no file uploaded
        if "file" not in request.files:
            flash("No file uploaded")
            return render_template("index.html")

        # If there is no text & a file uploaded
        file = request.files["file"]

        # If the file is not an allowed file
        if file.filename == "":
            flash("No File selected")
            return render_template("index.html")

        # IF the file is an allowed file
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"] / filename)
            print(f"path = {path}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            _file = open(os.path.join(app.config["UPLOAD_FOLDER"], filename), "r", encoding='latin-1')
            content = _file.read()
            print(f"Content : {content}")

            # If they want to predict the tax score
            if request.form["action"] == "Predict":
                
                prediction = kw.get_topic_byvector(content)
                result_v = kw.score_text_byvector(content, file_keywords=KEYWORD_FILE)
                return render_template("index.html", result=result_v, prediction=prediction)

            # If they want to generate the keywords
            if request.form["action"] == "Keywords":
                keywords = kw.get_keywordsunsupervised(content)
                keywords = dict(
                    sorted(keywords.items(), key=lambda item: item[1], reverse=True)
                )
                return render_template("index.html", keywords=keywords)

        else:
            flash("Filetype not allowed")
            return render_template("index.html")


@app.route("/loading", methods=["GET", "POST"])
def loading():
    if request.method == "POST":

        keywords = request.form["keywords"]
        keywords = keywords.split(",")
        print(keywords)
        thread = Thread(target=create_new_keywords, args=(keywords,))
        thread.start()
        print("Started")
        return render_template("loading.html")


@app.route("/complete")
def create_new_keywords(keywords):
    df = pd.read_pickle(FILES)
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    kw.create_initial_keywordlist(
        df, KEYWORD_FILE, DOCSCORES_FILE, list_keywords=keywords
    )
    # flash('NEW KEYWORDS GENERATED')
    return render_template("index.html")


if __name__ == "__main__":
    app.secret_key = "super_secret_key"
    app.config["SESSION_TYPE"] = "filesystem"
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True, debug=True)
