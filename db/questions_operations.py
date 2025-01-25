import encrypter
from db.connection import execute_query

def add_question(user_id, message):
    execute_query('INSERT INTO questions (user_id, message) VALUES (%s, %s)', (encrypter.encode(user_id), encrypter.encode(message)))

def get_questions():
    return execute_query('SELECT * FROM questions', fetchall=True)

def get_question(id):
    return execute_query('SELECT * FROM questions WHERE id = %s', (id,), fetchone=True)