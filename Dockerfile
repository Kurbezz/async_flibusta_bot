FROM python:3.8.2
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt
COPY ./source/ /usr/src/app/
CMD cd /usr/src/app/ && python main.py
