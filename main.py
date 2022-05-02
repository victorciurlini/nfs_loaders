import io
import base64
from Google import Create_Service
from googleapiclient.http import MediaIoBaseUpload
import urllib.request
import os

def construct_service(api_service):
    CLIENT_SERVICE_FILE = 'config\credentials.json'
    try:
        if api_service == 'gmail':
            CLIENT_FILE = 'config\credentials.json'
            API_NAME= 'gmail'
            API_VERSION = 'v1'
            SCOPES = ['https://mail.google.com/']
            return Create_Service(CLIENT_FILE, API_NAME, API_VERSION, SCOPES)
    except Exception as e:
        print(e)
        return None

def search_email(service, QUERY_STRING, label_ids=[]):
    try:
        message_list_response = service.users().messages().list(
            userId='me',
            labelIds=label_ids,
            q=QUERY_STRING).execute()
        message_items = message_list_response.get('messages')
        nextPageToken = message_list_response.get('nextPageToken')
        
        while nextPageToken:
            message_list_response = service.users().messages().list(
                userId='me',
                labelIds=label_ids,
                q=QUERY_STRING,
                pageToken=nextPageToken).execute()
            message_items = message_list_response.get('messages')
            nextPageToken = message_items.get('nextPageToken')
            
            message_items.extend(message_list_response.get('messages'))
            nextPageToken = message_items.get('nextPageToken')

        return message_items
    except Exception as e:
        print(e)
        return None

def get_message_detail(service, message_id, format='metadata', metadata_headers=[]):
    try:
        message_detail = service.users().messages().get(
            userId='me',
            id=message_id,
            format=format,
            metadataHeaders=metadata_headers
        )
        return message_detail

    except Exception as e:
        print(e)
        return None

def get_file_data(service, message_id, attachment_id, file_name):
    response = service.users().messages().attachments().get(
        userId='me',
        messageId=message_id,
        id=attachment_id
    ).execute()

    file_data = base64.urlsafe_b64decode(response.get('data').encode('UTF-8'))

    return file_data

if __name__ == '__main__':

    QUERY_STRING='has:attachment'
    SAVE_LOCATION = f'{os.getcwd()}\\nfs'


    gmail_service = construct_service('gmail')
    email_messages = search_email(gmail_service, QUERY_STRING)
    for email_message in email_messages:
        messageId = email_message['threadId']
        messageSubject = f'(No Subject) ({messageId})'
        messageDetail = get_message_detail(
            gmail_service, email_message['id'], format='full',metadata_headers=['parts']
        )
        messageDetailPayload = messageDetail.execute()
        messageDetailPayload = messageDetailPayload['payload']
        
        for item in messageDetailPayload['headers']:
            if item['name'] == 'Subject':
                if item['value']:
                    messageSubject = '{0} ({1})'.format(item['value'], messageId)
                else:
                    messageSubject = '(No Subject) ({0})'.format(messageId)
        if 'parts' in messageDetailPayload:
            for msgPayload in messageDetailPayload['parts']:
                mime_type = msgPayload['mimeType']
                file_name = msgPayload['filename']
                body = msgPayload['body']
                if 'attachmentId' in body:
                    attachment_id = body['attachmentId']
                    attachment_content = get_file_data(gmail_service, email_message['id'], attachment_id, file_name)
                    
                    with open(os.path.join(SAVE_LOCATION, file_name), 'wb') as _f:
                        _f.write(attachment_content)
                        print(f'File {file_name} is saved at {SAVE_LOCATION}')