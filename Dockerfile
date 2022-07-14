FROM python:3.9-slim-buster
COPY ./project/requirements.txt /
RUN pip install --no-cache-dir -r requirements.txt &&\
 pip install -U pip setuptools wheel &&\
 pip install -U spacy &&\
 python -m spacy download nl_core_news_md
COPY ./project /project
WORKDIR /project
CMD ["python", "app.py"]