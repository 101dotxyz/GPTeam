from quart import Quart, request
import fixieai
import os
import psycopg2
import requests
from discord_interactions import verify_key_decorator, InteractionType, InteractionResponseType

DATABASE_URL = os.getenv("DATABASE_URL")
CLIENT_PUBLIC_KEY = os.getenv("CLIENT_PUBLIC_KEY")

db = psycopg2.connect(DATABASE_URL, sslmode='require')

app = Quart(__name__)

TELEGRAM_API_URL = os.getenv("TELEGRAM_API_URL")


def send_message(chat_id, text):
    url = TELEGRAM_API_URL + 'sendMessage'
    data = {'chat_id': chat_id, 'parse_mode': 'Markdown', 'text': text}
    print(data)
    response = requests.post(url, data=data)
    return response.json()


def send_image(chat_id, image_url):
    url = TELEGRAM_API_URL + 'sendPhoto'
    data = {'chat_id': chat_id, 'photo': image_url}
    print(data)
    response = requests.post(url, data=data)
    return response.json()


def send_video(chat_id, video_url):
    url = TELEGRAM_API_URL + 'sendVideo'
    data = {'chat_id': chat_id, 'video': video_url}
    print(data)
    response = requests.post(url, data=data)
    return response.json()


def run() -> None:
    app.run()


@app.route('/', methods=['POST'])
async def webhook():
    data = await request.get_json()
    print(data)
    message = data['message']
    chat_id = data['message']['chat']['id']
    text = message.get('text')
    if text:
        # check if db has a session for this chat_id
        # if not, create a new session
        # if yes, get the session
        cur = db.cursor()

        if text == "/clear":
            cur.execute("DELETE FROM sessions WHERE chat_id = %s",
                        (str(chat_id),))
            db.commit()
            cur.close()
            send_message(chat_id, "Session cleared")
            return 'OK'

        cur.execute("SELECT * FROM sessions WHERE chat_id = %s",
                    (str(chat_id),))
        session = cur.fetchone()
        client = fixieai.get_client()
        if session is None:
            fixie_session = client.create_session()
            print(f"New User: {chat_id}")
            print(f"Created new session: {fixie_session.session_id}")
            cur.execute("INSERT INTO sessions (chat_id, session_id) VALUES (%s, %s) RETURNING id",
                        (str(chat_id), fixie_session.session_id, ))
            db.commit()
        else:
            print(f"Existing User: {chat_id}")
            print(f"Using session: {session[2]}")
            fixie_session = client.get_session(session[2])

        # check the messages table if theres a message for this chat_id and message_id
        # if yes, return
        cur.execute("SELECT * FROM messages WHERE chat_id = %s AND message_id = %s",
                    (str(chat_id), str(message['message_id'])))
        if cur.fetchone() is not None:
            cur.close()
            return 'OK'
        else:
            cur.execute("INSERT INTO messages (chat_id, message_id) VALUES (%s, %s) RETURNING id",
                        (str(chat_id), str(message['message_id']), ))
            db.commit()

        cur.close()

        response = fixie_session.query(text)
        send_message(chat_id, response)

        embeds = fixie_session.get_embeds()
        for embed in embeds:
            # check if responspse contains "#" + embed['key']
            if ('#' + str(embed['key'])) in response:
                # check if embed['embed']['conetentType'] is image or video MIME type
                if 'image' in embed['embed']['contentType']:
                    send_image(chat_id, embed['embed']['url'])
                elif 'video' in embed['embed']['contentType']:
                    send_video(chat_id, embed['embed']['url'])

    return 'OK'


@app.route('/interactions', methods=['POST'])
@verify_key_decorator(CLIENT_PUBLIC_KEY)
def interactions():
    data = request.json
    print(data)
    if data['type'] == InteractionType.PING:
        return {'type': InteractionResponseType.PONG}
    elif data['type'] == InteractionType.APPLICATION_COMMAND:
        if data['data']['name'] == 'hello':
            return {'type': InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    'data': {'content': 'Hello World!'}}
    return {'type': InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {'content': 'Hello World!'}}
