FROM python:3.9-slim

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV REPO_URL=client-side

WORKDIR $REPO_URL

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir

EXPOSE 8080

ENTRYPOINT [ "streamlit", "run","main.py"]
