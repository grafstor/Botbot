
import copy
import math
import random
from random import randint
import datetime

import glob
import os
from os import listdir
from os.path import isfile, join

import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import db_commands as db

ADMIN_ID = ""
TOKEN = ""

MAX_LIST_LEN = 6
DATA_FOLDER = "data/"

keyboard = telebot.types.ReplyKeyboardMarkup(True)
keyboard.row('Tasks')

bot = telebot.TeleBot(TOKEN)

def add_file_to_database(filepath):
    name, _ = os.path.splitext(os.path.basename(filepath))
    name, display_type = name.split("|")
 
    db.addTask(name) 
    task_id = db.getTaskId(name)['id']

    with open(filepath, 'r', encoding="UTF-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    for line in lines:
        question, answers = parce_question(line)
        if not db.getQuestionByNameTask(question[0], task_id):
            db.addQuestion(task_id, *question, display_type)

            question_id = db.getQuestionByNameTask(question[0], task_id)["id"]
            for answer in answers:
                db.addAnswer(question_id, *answer)

def parce_question(line):
    questions = line.split('|')

    question_with_hidden = questions[1].replace('&', "\n")
    question_text = questions[2].replace('&', "\n")

    question = [
        question_text,
        question_with_hidden,
    ]

    right_indexes = list(map(int, questions[0]))

    answers = []
    for index, answer_text in enumerate(questions[3:]):
        
        is_right = index in right_indexes
        answer = [
            answer_text,
            is_right
        ]

        answers.append(answer)

    return (question, answers)

def fill_database(folder):
    filepaths_list = glob.glob(os.path.join(folder, "*.txt"))
    filepaths_list.sort()
    for filepath in filepaths_list:
        add_file_to_database(filepath)

def main():
    fill_database(DATA_FOLDER)
    bot.infinity_polling()

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    origin_text = call.message.text
    user_id = call.message.chat.id
    message_id = call.message.message_id
    answer = call.data

    answer_data = answer.split('/')

    if answer_data[0] == "menu":
        display_tasks(user_id)
    elif answer_data[0] == 'task':
        task_id = answer_data[1]
        select_task(user_id, task_id)
    elif answer_data[0] == 'random':
        send_random_question(user_id)
    elif answer_data[0] == 'сlear':
        clear_progress(user_id, message_id)
    elif answer_data[0] == 'stat':
        display_stat(user_id, message_id)
    elif answer_data[0] == "answer":
        answer_id = answer_data[1]
        process_answer(user_id, answer_id, message_id)
    elif answer_data[0] == "submit":
        question_id = answer_data[1]
        process_submit(user_id, question_id, message_id)

    elif ["page", "next"] == answer_data:
        goto_next_page(user_id, message_id)
        return
    elif ["page", "last"] == answer_data:
        goto_last_page(user_id, message_id)
        return

@bot.message_handler(content_types=['text'])
def text(message):
    user_id = message.chat.id

    user_tag = message.from_user.username
    user_first_name = message.from_user.first_name
    user_last_name = message.from_user.last_name

    db.addUser(user_id, user_first_name, user_last_name, user_tag)

    if message.text == "/start":
        bot.send_message(user_id, "The power to change was in you all along, my friend.", reply_markup=keyboard)
        with open("media/cury.gif", "rb") as gif:
            bot.send_animation(user_id, gif)
        display_tasks(user_id)

    elif message.text == "Tasks":
        display_tasks(user_id)

    elif message.text == "/admin" and str(user_id) == ADMIN_ID:
        display_users(user_id)

def display_users(user_id):
    msg = ''
    users = db.getAllUsers()

    for user in users:
        user_history = db.getHistory(user["user_id"])
        msg += f"*{user['first_name']} {user['last_name']}* @{user['tag']} - *{len(user_history)}* records\n"

    bot.send_message(user_id, msg, parse_mode='Markdown')


def pick_random_question(task_id, user_id):
    questions = db.getTask(task_id)
    stats = get_stat_questions(user_id, task_id)

    def get_question_stat(question_stat, random_question):
        for qs in question_stat:
            if qs['id'] == random_question['id']:
                return qs
        return False

    while True:
        random_question = random.choice(questions)
        question_stat = get_question_stat(stats, random_question)

        if not question_stat:
            return random_question
        else:
            rqs = question_stat['stat']
            if rqs <= 63:
                return random_question
            else:
                c_rand = (300/(rqs-60)) - 0.5*rqs + 45
                if randint(1, 99) < c_rand:
                    return random_question

def send_random_question(user_id):
    task_id = db.getSelected(user_id)['task_id']
    task_name = db.getTaskInfo(task_id)['name']

    random_question = pick_random_question(task_id, user_id)
    question_text, question_markup = form_question(random_question, user_id)

    bot.send_message(user_id, question_text, reply_markup=question_markup)

def form_question(question, user_id, save_state=False):
    question_id = question['id']
    answers = db.getAnswers(question_id)
    selected_answers = db.getSelectedAnswers(question_id, user_id)
    selected_answers = [e['answer_id'] for e in selected_answers]
    
    question_text = question['question']
    question_displaytype = question['display_type']

    question_markup = InlineKeyboardMarkup()
    question_markup.row_width = len(answers)

    list_buttons = []

    if question_displaytype == "s":
        answers.sort(key=lambda a: a['answer'])

    elif question_displaytype == "r" and not save_state:
        random.shuffle(answers)

    elif question_displaytype == "o":
        answers = answers

    for answer in answers:
        answer_id = answer['id']
        answer_text = answer['answer']

        if answer_id in selected_answers:
            answer_text = f'😁 {answer_text}'

        list_buttons.append(InlineKeyboardButton(answer_text, callback_data=f"answer/{answer_id}"))    

    question_markup.add(*list_buttons)

    if sum([answer['is_right'] for answer in answers]) > 1:
        question_markup.add(InlineKeyboardButton(f"Отправить ({len(selected_answers)})", callback_data=f"submit/{question_id}"))

    return question_text, question_markup

def process_answer(user_id, answer_id, message_id):
    answer = db.getAnswer(answer_id)

    question_id = answer['question_id']
    question = db.getQuestionById(question_id)
    task_id = question['task_id']

    answers = db.getAnswers(answer['question_id'])

    if sum([answer['is_right'] for answer in answers]) > 1:
        db.toggleAnswer(user_id, answer_id, question_id)

        question_text, question_markup = form_question(question, user_id, save_state=True)

        bot.edit_message_text(question_text, user_id, message_id, parse_mode='Markdown', reply_markup=question_markup)
    else:
        is_right = answer['is_right']
        if is_right:
            mark_correct_submission(question, user_id, message_id, task_id, question_id, is_right)
        else:
            mark_incorrect_submission(question, user_id, message_id, task_id, question_id, is_right)

        send_random_question(user_id)

def mark_correct_submission(question, user_id, message_id, task_id, question_id, is_right):
    submit_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bot.edit_message_text(question['question_with_hidden']+"\n\n😁✅", user_id, message_id, parse_mode='Markdown')
    db.addHistoryRecord(submit_date, user_id, task_id, question_id, True, is_right)

def mark_incorrect_submission(question, user_id, message_id, task_id, question_id, is_right):
    submit_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bot.edit_message_text(question['question_with_hidden']+"\n\n☹️🚫", user_id, message_id, parse_mode='Markdown')
    db.addHistoryRecord(submit_date, user_id, task_id, question_id, True, is_right)

def process_submit(user_id, question_id, message_id):
    answers = db.getAnswers(question_id)
    question = db.getQuestionById(question_id)
    task_id = question['task_id']

    selected_answers = db.getSelectedAnswers(question_id, user_id)

    right_answers = set([answer['id'] for answer in answers if answer['is_right']])
    user_answers = set([answer['answer_id'] for answer in selected_answers])

    if right_answers == user_answers:
        is_right = True
        mark_correct_submission(question, user_id, message_id, task_id, question_id, is_right)
    else:
        is_right = False
        mark_incorrect_submission(question, user_id, message_id, task_id, question_id, is_right)

    db.deselectAnswers(question_id)

    send_random_question(user_id)

def select_task(user_id, task_id):
    db.setSelected(user_id, task_id)
    task_name = db.getTaskInfo(task_id)['name']

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Start", callback_data='random'),
        InlineKeyboardButton("Clear progress", callback_data='сlear'),
        InlineKeyboardButton("Statistics", callback_data='stat'),
        )

    questions_num = len(db.getTask(task_id))
    questions = get_stat_questions(user_id, task_id)
    summ = 0
    
    for w in questions:
        summ += w['stat']

    percent = round(summ/questions_num)

    msg = f'Task: *{task_name}* \n'
    msg += f'Questions: *{questions_num}* \n'
    msg += f'Progress: *{percent}%* ({round(summ/100)}/{questions_num})\n'

    if questions:
        msg += f'\nFavorite questions: \n'

        for question in questions[:4]:
            msg += " - " + question['question_with_hidden'] + f" - {round(question['stat'])}%\n"

    bot.send_message(user_id, msg, parse_mode='Markdown', reply_markup=markup)

def clear_progress(user_id, message_id):
    task_id = db.getSelected(user_id)['task_id']
    task_name = db.getTaskInfo(task_id)['name']

    db.clearProgress(user_id, task_id)

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Back", callback_data='task/'+str(task_id)))

    bot.edit_message_text(f"Progress in task *{task_name}* cleared", user_id, message_id, parse_mode='Markdown', reply_markup=markup)

def display_tasks(user_id):
    tasks = db.getTasks()
    markup = create_tasks_markup(user_id, tasks)
    bot.send_message(user_id, f"Сhoose from *{len(tasks)}* tasks",parse_mode='Markdown', reply_markup=markup)

def get_stat_questions(user_id, task_id):
    progress = db.getProgress(user_id, task_id)
    questions = db.getQuestionsByTask(task_id)

    stat_questions = []
    
    for i in range(len(questions)):
        question_progress = [r for r in progress if r['question_id'] == questions[i]['id']]
        if question_progress:
            true_answers = sum([record['is_right'] for record in question_progress])
            wrong_answers = len(question_progress) - true_answers

            if wrong_answers == 0:
                questions[i]['stat'] = 100
            else:
                questions[i]['stat'] = true_answers*100/(wrong_answers+true_answers)

            stat_questions.append(questions[i])

    stat_questions.sort(key=lambda a: a['stat'])

    return stat_questions

def display_stat(user_id, message_id):
    task_id = db.getSelected(user_id)['task_id']
    task_name = db.getTaskInfo(task_id)['name']
    questions = get_stat_questions(user_id, task_id)
    msg = f'Task *{task_name}* statistics:\n\n'

    for w in questions:
        msg += w['question_with_hidden'] + f" - {round(w['stat'])}%\n"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Back", callback_data='task/'+str(task_id)))

    bot.edit_message_text(msg, user_id, message_id, parse_mode='Markdown', reply_markup=markup)

def create_tasks_markup(user_id, tasks):
    markup = InlineKeyboardMarkup()

    bottom_buttons = []

    if len(tasks)>MAX_LIST_LEN:
        max_n = math.ceil(len(tasks)/MAX_LIST_LEN)

        page = db.getTaskPage(user_id)
        
        if not page: 
            db.setTaskPage(user_id, 1)
            page = 1
        else:
            page = page['page']

        tasks = tasks[MAX_LIST_LEN*(page-1):MAX_LIST_LEN*page]

        bottom_buttons = [
                InlineKeyboardButton('￩', callback_data="page/last"),
                InlineKeyboardButton(f'{page}/{max_n}', callback_data="lol"),
                InlineKeyboardButton('￫', callback_data="page/next")
            ]
    
    for g in tasks:
        task_id = g['id']
        task_name = g['name']
        task_name = get_task_name(user_id, task_id, task_name)
        markup.row(InlineKeyboardButton(task_name, callback_data="task/"+str(task_id)))
    
    markup.row(*bottom_buttons)

    return markup


def goto_next_page(user_id, message_id):   
    page = db.getTaskPage(user_id)['page']
    tasks = db.getTasks()
    max_n = math.ceil(len(tasks)/MAX_LIST_LEN)

    if page+1 > max_n: 
        db.setTaskPage(user_id, 1)
    else:
        db.setTaskPage(user_id, page+1)

    markup = create_tasks_markup(user_id, tasks)
    bot.edit_message_text(f"Сhoose from *{len(tasks)}* tasks", user_id, message_id,parse_mode='Markdown', reply_markup=markup)

def goto_last_page(user_id, message_id):
    page = db.getTaskPage(user_id)['page']
    tasks = db.getTasks()
    max_n = math.ceil(len(tasks)/MAX_LIST_LEN)

    if page-1 == 0: 
        db.setTaskPage(user_id, max_n)
    else:
        db.setTaskPage(user_id, page-1)

    markup = create_tasks_markup(user_id, tasks)
    bot.edit_message_text(f"Сhoose from *{len(tasks)}* tasks", user_id, message_id,parse_mode='Markdown', reply_markup=markup)

def get_task_name(user_id, task_id, task_name):
    questions_num = len(db.getTask(task_id))
    questions = get_stat_questions(user_id, task_id)

    summ = 0
    for w in questions:
        summ += w['stat']

    percent = round((summ*100)/(questions_num*100))

    task_name = f"{task_name} ({str(questions_num)} слов) {percent}%" 

    return task_name

if __name__ == "__main__":
    main()  

