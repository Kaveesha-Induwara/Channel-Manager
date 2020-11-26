import time
import logging
from Config import Config
from pyrogram import Client, filters
from sql_helpers import forceSubscribe_sql as sql
from pyrogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, UsernameNotOccupied, ChatAdminRequired, PeerIdInvalid

logging.basicConfig(level=logging.INFO)

static_data_filter = filters.create(lambda _, __, query: query.data == "onUnMuteRequest")
@Client.on_callback_query(static_data_filter)
def _onUnMuteRequest(client, cb):
  user_id = cb.from_user.id
  chat_id = cb.message.chat.id
  chat_db = sql.fs_settings(chat_id)
  if chat_db:
    channel = chat_db.channel
    chat_member = client.get_chat_member(chat_id, user_id)
    if chat_member.restricted_by:
      if chat_member.restricted_by.id == (client.get_me()).id:
          try:
            client.get_chat_member(channel, user_id)
            client.unban_chat_member(chat_id, user_id)
            if cb.message.reply_to_message.from_user.id == user_id:
              cb.message.delete()
          except UserNotParticipant:
            client.answer_callback_query(cb.id, text="❗ අපේ 'channel' එකට join වෙලා Unmute me Button එක ආපහු ඔබන්න", show_alert=True)
      else:
        client.answer_callback_query(cb.id, text="❗ You are muted by admins for other reasons.", show_alert=True)
    else:
      if not client.get_chat_member(chat_id, (client.get_me()).id).status == 'administrator':
        client.send_message(chat_id, f"❗ **{cb.from_user.mention} එයාව Unmute කරගන්න හදනවා... නමුත් මට ඔහුව unmute කරන්න බැහැ! මොකද මම මේ ගෲප් එක ඇඩ්මින් නෙවෙයි😕 මාව ආපහු ඇඩ්මින් දාන්න.**\n__#Leaving this chat...__")
        client.leave_chat(chat_id)i am
      else:
        client.answer_callback_query(cb.id, text="‼️අවවාදයයි : ඔයාට නිදහසේ කතා කරන්න පුළුවන්කම තියෙද්දි බටන් එක ක්ලික් කරන්න එපා🚫.", show_alert=True)



@Client.on_message(filters.text & ~filters.private & ~filters.edited, group=1)
def _check_member(client, message):
  chat_id = message.chat.id
  chat_db = sql.fs_settings(chat_id)
  if chat_db:
    user_id = message.from_user.id
    if not client.get_chat_member(chat_id, user_id).status in ("administrator", "creator") and not user_id in Config.SUDO_USERS:
      channel = chat_db.channel
      try:
        client.get_chat_member(channel, user_id)
      except UserNotParticipant:
        try:
          sent_message = message.reply_text(
              "ආයුබෝවන් {}, ඔයා අපේ [channel](https://t.me/{}) එක තාම Subscribe කරල නෑ.😭  කරුණාකරල ඒකට [join](https://t.me/{}) වෙලා පහල තියන UNMUTE ME Button එක touch කරන්න..".format(message.from_user.mention, channel, channel),
              disable_web_page_preview=True,
              reply_markup=InlineKeyboardMarkup(
                  [[InlineKeyboardButton("UnMute Me", callback_data="onUnMuteRequest")]]
              )
          )
          client.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=False))
        except ChatAdminRequired:
          sent_message.edit("❗ **මම මේ ගෲප් එක ඇඩ්මින් නෙවෙයි.**\n__මාව Ban user permission එක්ක ඇඩ්මින් කෙනෙක් කරන්න.\n#Leaving this chat...__")
          client.leave_chat(chat_id)
      except ChatAdminRequired:
        client.send_message(chat_id, text=f"❗ **මම @{channel}**\n__එකේ ඇඩ්මින් නෙවෙයි😕 මාව Channel එකේ Admin කරලා ආපහු මාව add කරන්න.\n#Leaving this chat...__")
        client.leave_chat(chat_id)


@Client.on_message(filters.command(["forcesubscribe", "fsub"]) & ~filters.private)
def config(client, message):
  user = client.get_chat_member(message.chat.id, message.from_user.id)
  if user.status is "creator" or user.user.id in Config.SUDO_USERS:
    chat_id = message.chat.id
    if len(message.command) > 1:
      input_str = message.command[1]
      input_str = input_str.replace("@", "")
      if input_str.lower() in ("off", "no", "disable"):
        sql.disapprove(chat_id)
        message.reply_text("❌ **Channel Manager is Disabled Successfully.**")
      elif input_str.lower() in ('clear'):
        sent_message = message.reply_text('**Unmuting all members who are muted by me...**')
        try:
          for chat_member in client.get_chat_members(message.chat.id, filter="restricted"):
            if chat_member.restricted_by.id == (client.get_me()).id:
                client.unban_chat_member(chat_id, chat_member.user.id)
                time.sleep(1)
          sent_message.edit('✅ **UnMuted all members who are muted by me.**')
        except ChatAdminRequired:
          sent_message.edit('❗ **මම මේ ගෲප් එක ඇඩ්මින් නෙවෙයි.**\n__මට Members ලව unmute කරන්න බැහැ ... මාව Ban user permission එක්ක ඇඩ්මින් කෙනෙක් කරන්න.__')
      else:
        try:
          client.get_chat_member(input_str, "me")
          sql.add_channel(chat_id, input_str)
          message.reply_text(f"✅ **Channel Manager is Enabled**\n__Channel Manager is enabled, මේ ගෲප් එකේ මැසේජ් කිරීම සඳහා සියලු සාමාජිකයින් මේ [channel](https://t.me/{input_str}) එක Subscribe කළ යුතුයි.__", disable_web_page_preview=True)
        except UserNotParticipant:
          message.reply_text(f"❗ **Not an Admin in the Channel**\n__මම [channel](https://t.me/{input_str}). එකේ ඇඩ්මින් නෙවෙයි😕 මේ ගෘප් එකේ ක්‍රියාකිරීම සඳහා මාව චැනල් එකේ admin කිරීම අනිවාර්යය.__", disable_web_page_preview=True)
        except (UsernameNotOccupied, PeerIdInvalid):
          message.reply_text(f"❗ **Invalid Channel Username.**")
        except Exception as err:
          message.reply_text(f"❗ **ERROR:** ```{err}```")
    else:
      if sql.fs_settings(chat_id):
        message.reply_text(f"✅ **Chanel Manager is enabled in this chat.**\n__For this [Channel](https://t.me/{sql.fs_settings(chat_id).channel})__", disable_web_page_preview=True)
      else:
        message.reply_text("❌ **Channel Manager is disabled in this chat.**")
  else:
      message.reply_text("❗ **Group Creator Required**\n__මේ සඳහා ඔබ ගෲප් එකේ අයිතිකාරයා විය යුතුයි.__")