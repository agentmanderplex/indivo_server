"""
Indivo Views -- Messaging
"""

from base import *

import datetime

import markdown
from indivo.lib import mdx_linkexpander
from django.db import IntegrityError

def _get_subject(request):
  subject = []
  subject.append(request.POST.get('subject', "[no subject]"))
  return ''.join(subject)

@transaction.commit_on_success
@handle_integrity_error('Duplicate external id. Each message requires a unique message_id')
def account_send_message(request, account):
  """
  account messages have no attachments for now
  """
  Message.objects.create( 
    account             = account, 
    sender              = request.principal, 
    recipient           = account, 
    external_identifier = request.POST.get('message_id', None), 
    subject             = _get_subject(request),
    body                = request.POST.get('body', "[no body]"),
    severity            = request.POST.get('severity', 'low'))
  
  account.notify_account_of_new_message()
  return DONE

@transaction.commit_on_success
@handle_integrity_error('Duplicate external id. Each message requires a unique message_id')
def record_send_message(request, record, message_id):
  record.send_message(
    external_identifier = message_id, 
    sender              = request.principal.effective_principal,
    subject             = _get_subject(request),
    body                = request.POST.get('body',    '[no body]'),
    body_type           = request.POST.get('body_type',    'plaintext'),
    num_attachments     = request.POST.get('num_attachments', 0),
    severity            = request.POST.get('severity', 'low'))
  
  return DONE

@transaction.commit_on_success
@handle_integrity_error('Duplicate attachment number. Each attachment number must be unique and 1-indexed')
def record_message_attach(request, record, message_id, attachment_num):
  # there may be more than one message here
  messages = Message.objects.filter(about_record = record, external_identifier = message_id)
  
  for message in messages:
    message.add_attachment(attachment_num, request.raw_post_data)

  return DONE

@marsloader()
def record_inbox(request, record, limit, offset, status, order_by):
  messages = record.get_messages().order_by(order_by)
  return render_template('messages', {'messages' : messages})


@marsloader()
def account_inbox(request, account, limit, offset, status, order_by):
  messages = account.message_as_recipient.order_by(order_by)

  if not request.GET.get('include_archive', False):
    messages = messages.filter(archived_at=None)

  return render_template('messages', {'messages' : messages})


def account_inbox_message(request, account, message_id):
  message = account.message_as_recipient.get(id = message_id)

  # if message not read, mark it read
  if not message.read_at:
    message.read_at = datetime.datetime.utcnow()
    message.save()

  # markdown
  if message.body_type == 'markdown':
    ext = mdx_linkexpander.MessageLinkExpanderExtension({
        'APP_BASE':'foobar',
        'message_id': message_id
        })
    message.body = markdown.Markdown(safe_mode=True, output_format='html4', extensions = [ext]).convert(message.body)

  return render_template('message', {'message' : message})


def account_inbox_message_attachment_accept(request, account, message_id, attachment_num):
  message = account.message_as_recipient.get(id = message_id)
  
  # this might fail, if the document doesn't validate
  try:
    message.get_attachment(int(attachment_num)).save_as_document(account)
  except ValueError as e:
    return HttpResponseBadRequest(str(e))
  else:
    return DONE

def account_message_archive(request, account, message_id):
  """
  set a message's archival date as now, unless it's already set
  """
  message = account.message_as_recipient.get(id = message_id)
  if not message.archived_at:
    message.archived_at = datetime.datetime.utcnow()
    message.save()
  return DONE


@marsloader()
def account_notifications(request, account, limit, offset, status, order_by):
  notifications = Notification.objects.filter(account = account).order_by(order_by)
  return render_template('notifications', {'notifications' : notifications})
