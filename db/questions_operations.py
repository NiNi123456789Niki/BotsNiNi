import encrypter
from db.connection import execute_query

def add_question(user_id, message):
    """
    Adds a new question to the database.

    Args:
        user_id (str): The user ID of the user asking the question.
        message (str): The question message.

    The function encodes both the user_id and the message before inserting them into the 'questions' table.
    """
    execute_query('INSERT INTO questions (user_id, message) VALUES (%s, %s)', (encrypter.encode(user_id), encrypter.encode(message)))

def get_questions():
    """
    Retrieves all questions from the database.

    Returns:
        list: A list of all questions, where each question is a dictionary or tuple
              representing a row from the 'questions' table. Returns None if no questions are found.

    Fetches all rows from the 'questions' table.
    """
    return execute_query('SELECT * FROM questions', fetchall=True)

def get_question(id):
    """
    Retrieves a specific question from the database based on its ID.

    Args:
        id (int): The ID of the question to retrieve.

    Returns:
        dict or tuple: A dictionary or tuple representing the row from the 'questions' table
                       corresponding to the given ID. Returns None if no question with the given ID is found.

    Fetches a single row from the 'questions' table where the ID matches the provided ID.
    """
    return execute_query('SELECT * FROM questions WHERE id = %s', (id,), fetchone=True)


def delete_question(qu_id):
    """
    Deletes a question from the database based on its ID.

    Args:
        qu_id (int): The ID of the question to delete.

    Deletes the row from the 'questions' table where the ID matches the provided qu_id.
    """
    execute_query('DELETE FROM questions WHERE id = %s', (qu_id,))


def delete_question_with_tid(tid):
    """
    Deletes all questions from the database associated with a given user ID (telegram ID).

    Args:
        tid (str): The telegram ID of the user whose questions should be deleted.

    Encodes the telegram ID and deletes all rows from the 'questions' table
    where the user_id matches the encoded telegram ID.
    """
    execute_query('DELETE FROM questions WHERE user_id = %s', (encrypter.encode(tid),))