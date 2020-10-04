from telegram.ext import Updater , CommandHandler
from telegram.utils.helpers import mention_markdown
import logging
from decouple import config
import os
import sys
import psycopg2
TOKEN = config("TOKEN")
PORT = config("PORT",5000)
APP_URL = config("APP_URL")
#SSL_REQUIRE = bool(config("SSLMODE"))
DATABASE_URL = config("DATABASE_URL")
CON = psycopg2.connect(DATABASE_URL)
CURS = CON.cursor()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname) - %(message)')
def insert_query(query):
  try:
      CURS.execute(query)
      res = CON.commit()
      return 1
  except:
      return 0
def fetch_query(query):
  CURS.execute(query)
  res = CURS.fetchall()
  return res
  
def tag_all(update,context):
  if update.message.chat.type=="group":
    update.message.reply_text("Tagging everyone")
    group_id = update.message.chat_id
    query = f"SELECT member_id, first_name FROM chat_ids WHERE group_id='{group_id}';"
    print(query)
    try:
      members = fetch_query(query)
      print(members)
      tagging_message = "Hi "
      for member in members:
        member_id,first_name=member
        tagging_message+=mention_markdown(int(member_id),first_name)
    
    except:
       tagging_message = "Sorry I am Unable to tag anyone"
    update.message.reply_text(tagging_message,parse_mode="Markdown")
  else:
    update.message.reply_text("This command is not for private chat")

def opt_in(update,context):
  def is_already_opted(group_id, member_id):
    query = f"SELECT COUNT(*) FROM chat_ids WHERE group_id='{group_id}' and member_id='{member_id}';"
    print(query)
    count = fetch_query(query)
    print(count)
    if count[0][0]>0:
      return True
    else:
      return False
  if update.message.chat.type=="group":
    group_id = update.message.chat_id
    member_id = update.message.from_user.id
    username = update.message.from_user.username
    first_name = update.message.from_user.first_name
    group_name = update.message.chat.title
    if is_already_opted(group_id,member_id):
      update.message.reply_text("You are already opted for this")
      return
    query = f"INSERT INTO chat_ids (group_id,group_name, member_id, username,first_name) VALUES({group_id},'{group_name}',{member_id},'{username}','{first_name}');"
    print(query)
    if insert_query(query):
      update.message.reply_text("You are successfully opted in to get metioned by this bot")
    else:
      update.message.reply_text("Sorry Something bad happened")
      
  else:
    update.message.reply_text("This command is not for private chat")
    


def main():
  updater = Updater(token=TOKEN,use_context=True)
  dispatcher = updater.dispatcher
  
  
  tag_handler = CommandHandler("tag_all",tag_all)
  opt_in_handler = CommandHandler("opt_in",opt_in)
  
  dispatcher.add_handler(tag_handler)
  dispatcher.add_handler(opt_in_handler)
  updater.start_webhook(listen="0.0.0.0",port=int(PORT),url_path=TOKEN) 
  updater.bot.setWebhook(APP_URL+"/"+TOKEN)
  updater.idle()
if __name__ == '__main__':
    main()
  
