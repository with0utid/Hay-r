from telegram.ext import Updater , CommandHandler ,Filters , MessageHandler
from telegram.utils.helpers import mention_markdown
from telegram import ReplyKeyboardMarkup,ReplyKeyboardRemove, InlineKeyboardButton
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
CHAT_IDS ={}
logging.basicConfig(filename='app.log',level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname) - %(message)')
def insert_query(query):
      CURS.execute(query)
      res = CON.commit()
      return 1
def fetch_query(query):
  CURS.execute(query)
  res = CURS.fetchall()
  return res

def start(update, context):
  text = update.message.text.split()
  print(text)
  if len(text) == 2:
    group_id = int(text[1])
    print(group_id)
    CHAT_IDS[update.message.chat_id] = group_id
    reply_keyboard = [["Done👍"]]
    update.message.reply_text("Now forward me messages of the members to add them in my database.",reply_markup=ReplyKeyboardMarkup(reply_keyboard))
def is_already_opted(group_id, member_id):
    query = f"SELECT COUNT(*) FROM chat_ids WHERE group_id='{group_id}' and member_id='{member_id}';"
    count = fetch_query(query)
    if count[0][0]>0:
      return True
    else:
      return False
      
      
def add_to_database(update,group,member):
   group_id = group.id
   group_name = group.title
   member_id = member.id
   username = member.username
   first_name = member.first_name
   query = f"INSERT INTO chat_ids (group_id,group_name, member_id, username,first_name) VALUES('{group_id}','{group_name}','{member_id}','{username}','{first_name}');"
   if insert_query(query):
      update.message.reply_text(text=f"{mention_markdown(int(member_id),first_name)} successfully opted in to get metioned in {group_name}", parse_mode="Markdown")
   else:
      update.message.reply_text("Sorry Something bad happened")
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
    group = update.message.chat
    member  = update.message.from_user
    if is_already_opted(group.id,member.id):
      update.message.reply_text("You are already opted for this")
      return
    add_to_database(update, group,member)
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
     add_to_database(update,group,chat)
def add_by_message(update,context):
  if update.message.chat.type == "private":
    update.message.reply_text("This function is not available for personal chat")
    return
  group_id = update.message.chat_id
  #button = InlineKeyboardButton(text="Click here",url=f"https://t.me/super_tagger_bot?start={group_id}")
  update.message.reply_text(text=f"<a href='https://t.me/super_tagger_bot?start={group_id}'>Click here to add </a>",parse_mode="HTML")
  
def forward_handler(update,context):
  if not update.message.chat.type == "private":
    print(update.message.chat.type)
    return
  chat_id = update.message.chat_id
  if chat_id not in CHAT_IDS or CHAT_IDS[chat_id] is None:
    #update.message.reply_text("First go to any group and send /add_by_message command there , then click on the link and forward me message of any member to add them to database")
    return
  if update.message.text=="Done👍":
    update.message.reply_text(text="Okay :)",reply_markup=ReplyKeyboardRemove())
    CHAT_IDS[chat_id] =None
    return
  if update.message.forward_from is None:
    update.message.reply_text("I can't add this member. Either you haven't forward message or user is not accessible by me because of privacy (add link to forwarded messages)")
    return
  member = update.message.forward_from
  group_id = CHAT_IDS[chat_id]
  group = context.bot.getChat(group_id)
  if is_already_opted(group_id,member.id):
         update.message.reply_text(text=f"{mention_markdown(member.id,member.first_name)} is already opted for mention in {group.title}.",parse_mode="Markdown")
         return
  add_to_database(update,group,member)
  
  
def get_status(update, context):
    if update.message.chat.type == "private":
      update.message.reply_text("This function is not available for personal chat")
      return
    group_id = update.message.chat_id
    query = f"SELECT first_name FROM chat_ids WHERE group_id='{group_id}'"
    print(query)
    first_names = fetch_query(query)
    print(first_names)
  
  
def main():
  updater = Updater(token=TOKEN,use_context=True)
  dispatcher = updater.dispatcher
  
  start_handler = CommandHandler('start',start)
  tag_handler = CommandHandler("tag_all",tag_all)
  opt_in_handler = CommandHandler("opt_in",opt_in)
  man_opt_handler = MessageHandler(Filters.regex(re.compile("^add",re.IGNORECASE)),add_data)
  forward_opt_handler = CommandHandler('add_by_message',add_by_message)
  forward_message_handler = MessageHandler(Filters.all,forward_handler)
  status_handler = CommandHandler('get_status',get_status)
  
  dispatcher.add_handler(start_handler)
  dispatcher.add_handler(tag_handler)
  dispatcher.add_handler(opt_in_handler)
  dispatcher.add_handler(man_opt_handler)
  dispatcher.add_handler(forward_opt_handler)
  dispatcher.add_handler(forward_message_handler)
#  dispatcher.add_handler(status_handler)
  if len(sys.argv)>1 and sys.argv[1]=="-p":
    print("start polling")
    updater.start_polling()
  else:
    updater.start_webhook(listen="0.0.0.0",port=int(PORT),url_path=TOKEN) 
    updater.bot.setWebhook(APP_URL+"/"+TOKEN)
    updater.idle()
if __name__ == '__main__':
    print("Starting",sys.argv)
    main()
  
