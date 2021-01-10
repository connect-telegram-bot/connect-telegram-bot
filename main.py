import database
import password_generator 
import configparser as cfg

import logging

import telegram
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
	Updater,
	CommandHandler,
	MessageHandler,
	Filters,
	ConversationHandler,
	CallbackContext,
	CallbackQueryHandler
)

logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CHOOSING, GROUPID_IN, PASSKEY_IN, SELECTGROUP, ACCEPT_MESSAGE_AND_FORWARD, SELECTOPTION = range(6)
development_feedback_id = None # id of the development_feedback group 
bug_report_group_id     = None # id of the bug report group 

menu_private_keyboard = ReplyKeyboardMarkup(
	[["📤Send Files To My Students"], 
        ["➕Add a group of students", "🔧Manage student groups"], 
        ["📞contact", "📚help"]]
	, one_time_keyboard=True, resize_keyboard= True)

def get_full_name(update:Update)->str:
	'''
	returns the full name of a teacher, given an update
	'''
	name = update.effective_user.first_name
	if update.effective_user.last_name:
		name += ' ' + update.effective_user.last_name
	return name
	
def shortid2id(shortid:str)->int:
	r = database.execute("SELECT id FROM groups WHERE short_id = ?",[shortid,])
	#since short_id column is UNIQUE there will only be one row.
	r = r.fetchone()
	if r is None:
		#no such shortid exists in the database
		return None
	return r[0]	

#the parameter can't be 'id' since 'id' is keyword in python
#so you have to use _id
def id2shortid(_id:int)->str: 
	r = database.execute("SELECT short_id FROM groups WHERE id = ?",[_id,])
	#since id column is PRIMARY KEY there will only be one row.
	r = r.fetchone()
	if r is None:
		#no such shortid exists in the database
		return None
	return r[0]	

def valid_short_id_generator()->str:
	while True:
		short_id = password_generator.short_id_generator()
		r = database.execute("SELECT * FROM groups WHERE short_id = ?", [short_id,] ).fetchall()
		if len(r) == 0:
			return short_id
 
def is_it_a_new_half_member(h_id: int, h_name: str) -> None:
	d = database.execute("SELECT * FROM halfMember WHERE id = ? ",[h_id,] ) 
	d = d.fetchone()
	if d is None: 
		# this user is a new user
		# so, add him/her to the database... 
		database.execute("INSERT INTO halfMember (id,name) VALUES (?,?)",[h_id,h_name])
		return None

	if (h_name != d[1]):
		database.execute("UPDATE halfMember SET name = ? WHERE id = ?",[h_name,h_id]) 	
	return None


def get_parser():
	config_file = "config.cfg"
	parser = cfg.ConfigParser()
	parser.read(config_file)
	return parser

def read_token(parser:cfg.ConfigParser, key:str):
	return parser.get('creds',key)

def bot_getting_into_a_group(update: Update, context: CallbackContext) -> None:
	for user in update.message.new_chat_members:
		if user.id == update.message.bot.id:
			database.execute("INSERT INTO groups (id,name,short_id) VALUES (?,?,?)",
				[update.effective_chat.id, update.effective_chat.title,valid_short_id_generator()] )
			update.message.reply_text("Enter the command /help to see what this bot can do.")
			break
				
def bot_getting_kicked_out(update: Update, context: CallbackContext) -> None:
	'''if the bot got kicked out of the group, deletes the group from the database
	and all of the corresponding half-members to this group'''
	message = update.message
	if message.left_chat_member.id == message.bot.id:
		database.execute(f"DELETE FROM groups WHERE id = {update.effective_chat.id}")

def add_new_group(update: Update, context: CallbackContext) -> int:
	update.message.reply_text("Send me the 'Group ID' you want to pair with: ",
		reply_markup=ReplyKeyboardRemove())
	return GROUPID_IN 

def get_group_id(update: Update, context: CallbackContext) -> int:
	shortid = update.message.text
	groupid = shortid2id(shortid)
	if groupid == None:
		update.message.reply_text("Invalid!",reply_markup=menu_private_keyboard)
		return ConversationHandler.END

	context.user_data['groupid'] = groupid
	passkey = password_generator.password_generate()
	context.user_data['passkey'] = passkey
	
	name = get_full_name(update) 
	group_message = f"Teacher: <b>{name}</b> is trying to pair with this group.\
		Tell him/her this key if you want him/her to pair. Ignore Otherwise. \nPASSKEY: <b>  {passkey} </b> " 	
	context.bot.send_message(groupid,group_message,parse_mode='HTML')
	update.message.reply_text("Passkey: ")
	return PASSKEY_IN 		

def get_pass_key(update: Update, context: CallbackContext) -> int:
	user_input_for_passkey = update.message.text
	if user_input_for_passkey != context.user_data['passkey']:
		update.message.reply_text("Invalid password!",reply_markup=menu_private_keyboard)
		context.user_data.clear()
		return ConversationHandler.END

	groupid = context.user_data['groupid']
	memberid = update.effective_user.id
	database.execute("INSERT INTO groups_halfMember (groupid, halfMemberid) VALUES (?,?)", [groupid,memberid])

	update.message.reply_text("Success!",reply_markup=menu_private_keyboard)
	context.user_data.clear()
	return ConversationHandler.END
 
def get_group_list_keyboard(user_id):
	keyboard = []
	r = database.execute(f"SELECT id,name FROM groups WHERE id IN (SELECT groupid FROM groups_halfMember WHERE halfMemberid = {user_id})")
	r = r.fetchall()
	for row in r:
		# row[0] is id   of groups table
		# row[1] is name of groups table	
		keyboard.append( [InlineKeyboardButton(row[1], callback_data=str(row[0]) )] )		
	return keyboard 
	
def send_messageto_group(update: Update, context: CallbackContext) -> int:
	keyboard = get_group_list_keyboard(update.effective_user.id)	
	if len(keyboard) == 0:
		keyboard = [["➕Add a group of students"]]
		update.message.reply_text(
		"You haven't paired with any student groups, please click on the button below to add one or tap on /start to get the whole menu.",
		reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
		return ConversationHandler.END
 	
	update.message.reply_text("<b>Student Groups</b> that you have paired with: ", 
				parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
	return SELECTGROUP 

def are_you_sure(update: Update, context: CallbackContext) -> int:
	update.message.reply_text(
		"Are you sure you want to unpair from <b>ALL</b> student groups?",
		parse_mode='HTML',
		reply_markup=InlineKeyboardMarkup([ 
			[InlineKeyboardButton('YES', callback_data='YES'), 
			InlineKeyboardButton('NO',callback_data='NO')] 
	]))	
	return SELECTOPTION

def contact_devs(update: Update, context: CallbackContext) -> int:
	update.message.reply_text("What kind of message do you want to send to the developers? Tap on /cancel if there is none.",
		reply_markup=InlineKeyboardMarkup([
			[InlineKeyboardButton('Bug Report', callback_data='BUG'), 
			 InlineKeyboardButton('Feedback',callback_data='FEED')]
	]))
	return SELECTOPTION
	
def bug_or_feed(update: Update, context: CallbackContext) -> int:
	query = update.callback_query
	query.answer()
	if query.data == 'BUG':
		context.user_data['BUG'] = True
		query.edit_message_text("Please explain the bug(🐞) you encountered")
	else:
		context.user_data['BUG'] = False
		query.edit_message_text("Please write your feedback")
	return ACCEPT_MESSAGE_AND_FORWARD	

def report_to_devs(update: Update, context: CallbackContext) -> int:
	if context.user_data['BUG']:
		update.message.forward(bug_report_group_id)
		update.message.reply_text("Done! Your bug report is successfully sent to"
					" the developers! Thank you!",reply_markup=menu_private_keyboard)
	else:
		update.message.forward(development_feedback_id)
		update.message.reply_text("Done! Your feedback is successfully sent to"
					" the developers! Thank you!",reply_markup=menu_private_keyboard)
	return ConversationHandler.END
 
def group_selector(update: Update, context: CallbackContext) -> int:
	query = update.callback_query
	query.answer()
	groupid = query.data
	if groupid is None:
		return ConversationHandler.END
	context.user_data['groupid'] = groupid				
	
	r = database.execute(f"SELECT name FROM groups WHERE id={groupid}")
	r = r.fetchall()

	if len(r) == 0:
		query.edit_message_text(text="INVALID DATA ENTERED!")
		return ConversationHandler.END 

	groupname = r[0][0]
	query.edit_message_text(text="The following message that you are going to type in"
				f" is going to be forwarded to the group <b>{groupname}</b>.",
				parse_mode='HTML')
	return ACCEPT_MESSAGE_AND_FORWARD

def group_selector_to_delete(update: Update, context: CallbackContext) -> int:
	query = update.callback_query
	query.answer()

	try:
		groupid = int(query.data)
	except:
		return ConversationHandler.END
	userid  = update.effective_user.id
	
	if groupid is None:
		return ConversationHandler.END

	p = database.execute(f"SELECT name FROM groups WHERE id={groupid}")
	p = p.fetchall()

	if len(p) == 0:
		query.edit_message_text(text="INVALID DATA ENTERED! Please contact the developers if you see this message."
				" A screenshot would be appreciated.")
		return ConversationHandler.END 

	r = database.execute(f"DELETE FROM groups_halfMember WHERE groupid = {groupid} AND halfMemberid = {userid}")

	groupname = p[0][0]	

	# i know it is not efficient. but its ok.
	# how often will teachers unpair from their group of students.

	query.edit_message_text(text=f"You have sucessfully unpaired from the group: <b> {groupname} </b>!",parse_mode='HTML')
	context.bot.send_message(userid,"MENU: ",reply_markup=menu_private_keyboard)
	return ConversationHandler.END	
		
def accept_message_and_forward(update: Update, context: CallbackContext) -> int:
	update.message.forward(int(context.user_data['groupid']))
	update.message.reply_text("Sent!",reply_markup=menu_private_keyboard)
	context.user_data.clear()
	return ConversationHandler.END
	 
def cancel(update: Update, context: CallbackContext) -> int:
	context.user_data.clear()	
	update.message.reply_text("/cancel called!! shutting down!!",
		reply_markup=ReplyKeyboardRemove())

	return ConversationHandler.END

def get_id(update: Update, context: CallbackContext) -> int:
	short_id = id2shortid(update.effective_chat.id)	
	update.message.reply_text(f"Group ID: <b>{short_id}</b>",parse_mode='HTML')	

def get_half_members(update: Update, context: CallbackContext) -> int:
	'''
	returns all of the teachers that are paried to this group.
	'''
	group_id = update.effective_chat.id
	r = database.execute(f"SELECT name FROM halfMember WHERE id IN (SELECT halfMemberid FROM groups_halfMember WHERE groupid = {group_id})")
	r = r.fetchall()	

	msg = ""

	if len(r) == 0:
		msg += "No teachers are paired with this group. To pair, the teachers themselves need to talk to the bot."	
	else:
		msg += "List of teachers that are paired to this group" + '\n'
		counter = 1
		for row in r:
			# row[0] - name of halfMember
			msg += str(counter) + ") " + row[0] + '\n'
			counter += 1  		
		msg += '\n'
	
	update.message.reply_text(msg,parse_mode='HTML')

def unknown_(update: Update, context: CallbackContext) -> None:
	return None

def get_help_group(update: Update, context: CallbackContext) -> None:
	msg  = "<b>Bot Settings</b>" + '\n'
	msg += "/id   - Get the <b>ID</b> of the group [Useful for pairing to a teacher]" + '\n'
	msg += "/list - List all teachers that are paired to this group" + '\n'
	msg += "/help - Gives this page" + '\n'	
	update.message.reply_text(msg, parse_mode='HTML')

def get_help_private(update: Update, context: CallbackContext) -> None:
	msg  = "<b>Bot Commands</b>" + '\n'
	msg += "/start  - to start talking to the bot" + '\n'	
	msg += "/cancel - to stop talking to the bot" + '\n'
	msg += "/delete - to unpair from a <b>single group of students</b>" + '\n' 
	msg += "/clear  - to unpair from <b>all groups</b>" + '\n'
	msg += "/list   - to list all groups that you have paired with" + '\n' 
	msg += "/contact -to send message to the developers" + '\n'
	msg += "/help   - to output this help message" + '\n'
	update.message.reply_text(msg, parse_mode='HTML',reply_markup=menu_private_keyboard)

def delete_half_group(update: Update, context: CallbackContext) -> None:
	keyboard = get_group_list_keyboard(update.effective_user.id)
	if len(keyboard) == 0:
		update.message.reply_text("You haven't paired with any student's group. Use /help to see a list of commands.")
		return ConversationHandler.END
	
	update.message.reply_text("From which group do you want to unpair? Enter /cancel if there is none.",
			reply_markup=InlineKeyboardMarkup(keyboard))
	return SELECTGROUP 

def delete_all_half_group(update: Update, context: CallbackContext) -> None:
	#check if it is a yes or no
	query = update.callback_query
	query.answer()
	
	userid = update.effective_user.id

	user_choice = query.data
	if user_choice == 'YES':	
		# if it is 'YES'	
		user_id = update.effective_user.id	
		database.execute(f"DELETE FROM groups_halfMember WHERE halfMemberid = {user_id}")	
		query.edit_message_text("Done!")
		context.bot.send_message(userid,"MENU: ",reply_markup=menu_private_keyboard)
		
	elif user_choice == 'NO':
		query.edit_message_text("Deletion canceled.")	
		context.bot.send_message(userid,"MENU: ",reply_markup=menu_private_keyboard)
	else:
		#raise ZeroDivisionError("HAHAHAHA IMPOSSIBLE!!!")
		query.edit_message_text("An error occured!!! Please send a contact the developers by pressing /contact."
			" A screenshot would be appreciated.")	
		
	return ConversationHandler.END 

def list_half_groups(update: Update, context: CallbackContext) -> None:
	user_id = update.effective_user.id	

	r = database.execute(f"SELECT name FROM groups WHERE id IN (SELECT groupid FROM groups_halfMember WHERE halfMemberid = {user_id})")
	r = r.fetchall()

	msg = ""	
	if len(r) == 0:
		msg += "You haven't paired with any student groups."  
	else:	
		msg += "You have paired with the following <b>student groups</b>" + '\n' 	
		counter = 1
		for row in r:
			# row[0] - name of halfGroup
			msg += str(counter) + ") " + row[0] + '\n'
			counter += 1  		
		msg += '\n'
	update.message.reply_text(msg,reply_markup=menu_private_keyboard, parse_mode='HTML')	


def Manage_student_groups(update: Update, context: CallbackContext):
	keyboard = [["📋list", "🗑delete", "⛔clear"], ["↩back"]]
	update.message.reply_text("Usage: \n "
	"<b>list</b>: to list all student groups you have paired with \n "
	"<b>delete</b>: to unpair from a single student group \n"
	"<b>clear</b>: to unpair from all student groups",
	reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard= True),
	parse_mode='HTML')


def start(update: Update, context: CallbackContext): 
	name = get_full_name(update)
	is_it_a_new_half_member(update.effective_user.id, name);

	update.message.reply_text(f"Hello teacher <b>{name}</b>, use /help for help: ",
		reply_markup=menu_private_keyboard, parse_mode='HTML')
	return None

def group_id_change(update: Update, context: CallbackContext) -> None:
	message = update.message

	if message.migrate_to_chat_id:	
		new_id = message.migrate_to_chat_id
		old_id = update.effective_chat.id 
		database.execute(f"UPDATE groups SET id = {new_id} WHERE id = {old_id}") 
	
def main():
	global development_feedback_id, bug_report_group_id

	####[init database once]#####
	database.start_connection()
	#############################

	parser = get_parser()

	botname = read_token(parser,'botname') 
	development_feedback_id = int(read_token(parser,'development_feedback_id'))
	bug_report_group_id = int(read_token(parser,'bug_report_group_id'))	

	updater = Updater(read_token(parser,"token"),use_context=True)
	dispatcher = updater.dispatcher

	# creating group handlers [executed by students]
	register_group_handler = MessageHandler(Filters.status_update.new_chat_members, bot_getting_into_a_group)
	removed_group_handler  = MessageHandler(Filters.status_update.left_chat_member, bot_getting_kicked_out)
	change_of_groupid_handler = MessageHandler(Filters.status_update.migrate, group_id_change)  
	group_help_handler = MessageHandler(Filters.chat_type.groups & Filters.command & Filters.regex(f'^/help(@{botname})?$') ,get_help_group)
	id_handler = MessageHandler(Filters.chat_type.groups & Filters.command & Filters.regex(f'^/id(@{botname})?$'),get_id)
	list_handler = MessageHandler(Filters.chat_type.groups & Filters.command & Filters.regex(f'^/list(@{botname})?$'),get_half_members)
	unknown_handler = MessageHandler(Filters.chat_type.groups, unknown_) #ignore all other commands from the group 

	# creating private handlers [executed by teachers]
	private_help_handler = MessageHandler(Filters.chat_type.private & Filters.regex('^(📚help)|(/help)$'),get_help_private)
	delete_private_handler = ConversationHandler(
		entry_points=[MessageHandler(Filters.chat_type.private & Filters.regex('^(🗑delete)|(/delete)$'),delete_half_group)],
		states = {
			SELECTGROUP: [  		
				CallbackQueryHandler(group_selector_to_delete,pattern='^-?[0-9]+$')		
			],
		},
		fallbacks=[CommandHandler('cancel',cancel)]
	) 

	clear_private_handler = ConversationHandler(
		entry_points=[MessageHandler(Filters.chat_type.private & Filters.regex('^(⛔clear)|(/clear)$'),are_you_sure)],
		states = {
			SELECTOPTION: [
				CallbackQueryHandler(delete_all_half_group, pattern='^(YES)|(NO)$')
			],
		},
		fallbacks=[CommandHandler('cancel',cancel)]
	)
	list_private_handler = MessageHandler(Filters.chat_type.private & Filters.regex('^(📋list)|(/list)$'), list_half_groups)

	contact_handler = ConversationHandler(
		entry_points=[MessageHandler(Filters.chat_type.private & Filters.regex('^(📞contact)|(/contact)$'), contact_devs)],
		states = {
			SELECTOPTION: [
				CallbackQueryHandler(bug_or_feed, pattern='^(BUG)|(FEED)$')
			],
			ACCEPT_MESSAGE_AND_FORWARD: [
				MessageHandler(Filters.chat_type.private & ~Filters.command, report_to_devs)		
			],
		},
		fallbacks=[CommandHandler('cancel',cancel)]
	)

	back_handler = MessageHandler(Filters.chat_type.private & Filters.regex('^↩back$'), start)
	start_handler = MessageHandler(Filters.chat_type.private & Filters.regex('^/start$'), start) 

	send_files_conv_handler = ConversationHandler( 
		allow_reentry=True,
		entry_points=[MessageHandler(Filters.chat_type.private & Filters.regex('^📤Send Files To My Students$'),send_messageto_group)],
		states={	
			SELECTGROUP: [
				CallbackQueryHandler(group_selector,pattern='^-?[0-9]+$')		
			],	
			ACCEPT_MESSAGE_AND_FORWARD: [
				MessageHandler(Filters.chat_type.private & ~Filters.command, accept_message_and_forward)	
			],
		},
		fallbacks=[CommandHandler('cancel',cancel)]
	)

	manage_handler = MessageHandler(Filters.chat_type.private & Filters.regex('^🔧Manage student groups$'), Manage_student_groups)

	add_group_conv_handler = ConversationHandler(
		allow_reentry=True,
		entry_points=[MessageHandler(Filters.chat_type.private & Filters.regex('^➕Add a group of students$'),add_new_group)],
		states={
			GROUPID_IN: [
				MessageHandler(Filters.chat_type.private & Filters.regex('^[a-z]{5}$'),get_group_id),
			],
			PASSKEY_IN: [
				MessageHandler(Filters.chat_type.private & Filters.regex('^[0-9]{5}$'),get_pass_key),
			],
		},
		fallbacks=[CommandHandler('cancel',cancel)]
	)		
			
	#group handlers getting dispatched
	dispatcher.add_handler(register_group_handler)
	dispatcher.add_handler(removed_group_handler)	
	dispatcher.add_handler(change_of_groupid_handler) #for the conversion of group to super group	
	dispatcher.add_handler(id_handler)
	dispatcher.add_handler(list_handler)
	dispatcher.add_handler(group_help_handler)
	dispatcher.add_handler(unknown_handler) # [warning] this should be last!!
	

	#private handlers getting dispatched
	dispatcher.add_handler(back_handler)
	dispatcher.add_handler(private_help_handler)
	dispatcher.add_handler(delete_private_handler)
	dispatcher.add_handler(clear_private_handler)
	dispatcher.add_handler(list_private_handler)
	dispatcher.add_handler(contact_handler)
	dispatcher.add_handler(add_group_conv_handler)
	dispatcher.add_handler(send_files_conv_handler)
	dispatcher.add_handler(manage_handler)
	dispatcher.add_handler(start_handler)
		

	updater.start_polling()
	updater.idle()
	
	##########[end database once]############
	database.stop_connection()
	#########################################	

if __name__ == '__main__':
	main()

