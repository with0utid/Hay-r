FROM python:3.9
WORKDIR app/
RUN pip instal -r requirements.txt
CMD ['python','bot.py']