FROM python:3.8.5

RUN pip install --no-cache-dir -U pip wheel

COPY requirements.txt /usr/src/app/

RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

COPY ./source/ /usr/src/app/

CMD cd /usr/src/app/ && python main.py
