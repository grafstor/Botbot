from database import Database 

db_path = 'database/database.db'
tables_path = 'database/database_structure.sql'

db = Database(db_path)
db.execute_file(tables_path)

def addQuestion(task_id, question, question_with_hidden, display_type):
    if not getQuestionByNameTask(question, task_id):
        db('INSERT INTO questions(task_id, question, question_with_hidden, display_type) \
            VALUES(?,?,?,?)', (task_id, question, question_with_hidden, display_type)).close()

def addAnswer(question_id, answer, is_right):
    db('INSERT INTO answers(question_id, answer, is_right) \
        VALUES(?,?,?)', (question_id, answer, is_right)).close()

def addHistoryRecord(submit_date, user_id, task_id, question_id, is_in_progress, is_right):
    db('INSERT INTO history(submit_date, user_id, task_id, question_id, is_in_progress, is_right) \
        VALUES(?,?,?,?,?,?)', (submit_date, user_id, task_id, question_id, is_in_progress, is_right)).close()

def getSelectedAnswers(question_id, user_id):
    a = db('SELECT * FROM selected_answers WHERE user_id=? AND question_id=?', (user_id, question_id)).all()
    return a

def toggleAnswer(user_id, answer_id, question_id):
    if not getSelectedAnswer(user_id, answer_id):
        db('INSERT INTO selected_answers(user_id, answer_id, question_id) \
            VALUES(?,?,?)', (user_id, answer_id, question_id)).close()
    else:
        db('DELETE FROM selected_answers WHERE user_id=? AND answer_id=?', (user_id, answer_id)).close()

def getSelectedAnswer(user_id, answer_id):
    a = db('SELECT * FROM selected_answers WHERE user_id=? AND answer_id=?', (user_id, answer_id)).one()
    return a

def deselectAnswers(question_id):
    db('DELETE FROM selected_answers WHERE question_id=?', (question_id,)).close()

def getAnswerByName(question_id, answer):
    a = db('SELECT * FROM answers WHERE question_id=? AND answer=?', (question_id, answer)).one()
    return a

def addUser(user_id, first_name, last_name, tag):
    if not getUser(user_id):
        db('INSERT INTO users(user_id, first_name, last_name, tag) \
            VALUES(?,?,?,?)', (user_id, first_name, last_name, tag)).close()

def getUser(user_id):
    u = db('SELECT * FROM users WHERE user_id=?', (user_id,)).one()
    return u

def getAllUsers():
    u = db('SELECT * FROM users').all()
    return u

def clearProgress(user_id, task_id):
    db('UPDATE history SET is_in_progress=False WHERE user_id=? AND task_id=?', (user_id,task_id)).close()

def addUdarQuestion(task_id, question, slog):
    if not getQuestionByNameTask(question, task_id):
        db('INSERT INTO questions(task_id, question, hidden) \
            VALUES(?,?,?)', (task_id, question, slog)).close()

def getAnswers(question_id):
    a = db('SELECT * FROM answers WHERE question_id=?', (question_id,)).all()
    return a

def getAnswer(answer_id):
    a = db('SELECT * FROM answers WHERE id=?', (answer_id,)).one()
    return a

def getProgress(user_id, task_id):
    h = db('SELECT * FROM history WHERE user_id=? and task_id=? and is_in_progress=True', (user_id, task_id)).all()
    return h

def getHistory(user_id):
    h = db('SELECT * FROM history WHERE user_id=?', (user_id,)).all()
    return h

def getFullHistory():
    h = db('SELECT * FROM history').all()
    return h

def getQuestionByNameTask(question, task_id):
    w = db('SELECT * FROM questions WHERE question=? AND task_id=?', (question, task_id)).one()
    return w

def getQuestionsByTask(task_id):
    w = db('SELECT * FROM questions WHERE task_id=?', (task_id,)).all()
    return w

def getQuestionByName(question):
    w = db('SELECT * FROM questions WHERE question=?', (question,)).one()
    return w

def getQuestionById(id):
    w = db('SELECT * FROM questions WHERE id=?', (id,)).one()
    return w

def findQuestion(question_with_hidden, task_id):
    w = db('SELECT * FROM questions WHERE question_with_hidden=? AND task_id=?', (question_with_hidden, task_id)).one()
    return w

def setTaskPage(user_id, page):
    if not getTaskPage(user_id):
        db('INSERT INTO task_page(user_id, page) \
        VALUES(?,?)', (user_id, page)).close()
    else:
        db('UPDATE task_page SET page=? WHERE user_id=?',
         (page, user_id)).close()

def getTaskPage(user_id):
    p = db('SELECT * FROM task_page WHERE user_id=?', (user_id,)).one()
    return p

def getQuestion(id):
    w = db('SELECT * FROM questions WHERE id=?', (id,)).one()
    return w


def addTask(name):
    if not getTaskId(name):
        db('INSERT INTO tasks(name) \
            VALUES(?)', (name,)).close()

def getTaskId(name):
    id = db('SELECT id FROM tasks WHERE name=?', (name,)).one()
    return id

def getTask(id):
    # task = db('SELECT * FROM tasks WHERE name=?', (name,)).one()
    questions = db('SELECT * FROM questions WHERE task_id=?', (id,)).all()
    return questions

def getTaskInfo(id):
    # task = db('SELECT * FROM tasks WHERE name=?', (name,)).one()
    g = db('SELECT * FROM tasks WHERE id=?', (id,)).one()
    return g

def getTasks():
    rows = db('SELECT * FROM tasks').all()
    return rows

def getSelected(user_id):
    id = db('SELECT task_id FROM selected WHERE user_id=?', (user_id,)).one()
    return id

def setSelected(user_id, task_id):
    if getSelected(user_id):
        db('UPDATE selected SET task_id=? WHERE user_id=?',
         (task_id, user_id)).close()
    else:
        db('INSERT INTO selected(user_id, task_id) \
            VALUES(?, ?)', (user_id, task_id)).close()
