from telegram.ext import Updater , CommandHandler ,Filters , MessageHandler
from telegram.utils.helpers import mention_markdown
import logging
from decouple import config
import os
import sys
import psycopg2
import re
TOKEN = config("TOKEN")
PORT = config("PORT",5000)
APP_URL = config("APP_URL")
DATABASE_URL = config("DATABASE_URL")
CON = psycopg2.connect(DATABASE_URL,sslmode='require')
CURS = CON.cursor()

logging.basicConfig(filename='app.log',level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname) - %(message)')
def insert_query(query):
      CURS.execute(query)
      res = CON.commit()
      return 1
def fetch_query(query):
  CURS.execute(query)
  res = CURS.fetchall()
  return res
  
def is_already_opted(group_id, member_id):
    query = f"SELECT COUNT(*) FROM chat_ids WHERE group_id='{group_id}' and member_id='{member_id}';"
    count = fetch_query(query)
    if count[0][0]>0:
      return True
    else:
      return False
def tag_all(update,context):
  if update.message.chat.type in ["group","supergroup"] :
    update.message.reply_text("Tagging everyone")
    group_id = update.message.chat_id
    query = f"SELECT member_id, first_name FROM chat_ids WHERE group_id='{group_id}';"
    try:
      members = fetch_query(query)
      print(members)
      tagging_message = "Hi "
      for member in members:
        member_id,first_name=member
        tagging_message+=mention_markdown(int(member_id),first_name)
        tagging_message+=" "
    except:
       tagging_message = "Sorry I am Unable to tag anyone"
    update.message.reply_text(tagging_message,parse_mode="Markdown")
  else:
    update.message.reply_text("This command is not for private chat")

def opt_in(update,context):
  if update.message.chat.type in ["group","supergroup"]:
    group_id = update.message.chat_id
    member_id = update.message.from_user.id
    username = update.message.from_user.username
    first_name = update.message.from_user.first_name
    group_name = update.message.chat.title
    if is_already_opted(group_id,member_id):
      update.message.reply_text("You are already opted for this")
      return
    query = f"INSERT INTO chat_ids (group_id,group_name, member_id, username,first_name) VALUES('{group_id}','{group_name}','{member_id}','{username}','{first_name}');"
    if insert_query(query):
      update.message.reply_text("You are successfully opted in to get metioned by this bot")
    else:
      update.message.reply_text("Sorry Something bad happened")
      
  else:
    update.message.reply_text("This command is not for private chat")
    
def add_data(update, context):
  try:
    text = update.message.text.split()
    group_id = int(text[1])
    member_id = int(text[2])
  except:
    update.message.reply_text("Unable to process your request. Please send your request in proper format.\nadd <group_id> <member_id>")
    return
  try:
   chat = context.bot.get_chat(group_id)
  except:
   update.message.reply_text("Please Provide right group id")
  if chat.type == "personal":
     update.message.reply_text("Please Provide right group id")
     return
  group_name = chat.title
  try:
     member = context.bot.get_chat_member(group_id,member_id)
     print(member.to_json())
  except:
     update.message.reply_text("No user found with this user id")
     
  if not member.status == "member":
     update.message.reply_text(f"This user is not in {group_name}.Please Provide right user id")
     return
  user = member.user
  first_name = user.first_name
  username = user.username
  if is_already_opted(group_id,member_id):
     update.message.reply_text(text=f"{mention_markdown(member_id,first_name)} is already opted for mention in {group_name}.",parse_mode="Markdown")
     return
  else:
     query = f"INSERT INTO chat_ids (group_id,group_name, member_id, username,first_name) VALUES('{group_id}','{group_name}','{member_id}','{username}','{first_name}');"
     if insert_query(query):
       update.message.reply_text(text=f"{mention_markdown(member_id,first_name)} is successfully opted in to get metioned by this bot", parsemode="Markdown")
     else:
       update.message.reply_text("Sorry Something bad happened")
       
def main():
  updater = Updater(token=TOKEN,use_context=True)
  dispatcher = updater.dispatcher
  
  
  tag_handler = CommandHandler("tag_all",tag_all)
  opt_in_handler = CommandHandler("opt_in",opt_in)
  man_opt_handler = MessageHandler(Filters.regex(re.compile("^add",re.IGNORECASE)),add_data)
  dispatcher.add_handler(tag_handler)
  dispatcher.add_handler(opt_in_handler)
  dispatcher.add_handler(man_opt_handler)
  updater.start_webhook(listen="0.0.0.0",port=int(PORT),url_path=TOKEN) 
  updater.bot.setWebhook(APP_URL+"/"+TOKEN)
  updater.idle()
if __name__ == '__main__':
    main()
  
