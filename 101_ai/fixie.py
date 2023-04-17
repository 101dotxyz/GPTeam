from fixieai.client.session import Session
import fixieai
import os
import psycopg2


client = fixieai.get_client()
session = client.get_session("functional-ubiquitous-gull")
# session.query("what is the last thing I said to you?")
response = session.get_embeds()
embed = response[0]
print(response)
