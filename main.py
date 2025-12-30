import telebot
from telebot import types
import time
import os
from flask import Flask
from threading import Thread

# Flask app для поддержания активности
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

API_TOKEN = os.environ.get('BOT_TOKEN', '8381821681:AAEj3PTdkut5vSWR-BWtrXfdOmnVOwf0r5Y')

bot = telebot.TeleBot(API_TOKEN)
user_data = {}

# ID канала для проверки подписки
CHANNEL_USERNAME = '@christiecheers'
CHANNEL_ID = -1002044718119  

# Список вопросов (только 1, 4, 6, 9, 10)
questions = [
    {
        'question': 'Что значит "pitch" в разговорной речи?',
        'options': ['Бросать мяч', 'Жаловаться', 'Выбрасывать что-то ненужное'],
        'correct_answer': 2
    },
    {
        'question': 'Что значит "get moldy"?',
        'options': ['Намокнуть', 'Покрыться плесенью', 'Превратиться в крошки'],
        'correct_answer': 1
    },
    {
        'question': 'Что сказать, если ноготь слегка откололся?',
        'options': ['My nail broke.', 'My nail fell.', 'My nail chipped.'],
        'correct_answer': 2
    },
    {
        'question': 'Выбери правильное выражение:',
        'options': ['I soaked a stain before washing.', 'I dipped a stain before washing.', 'I wet a stain before washing.'],
        'correct_answer': 0
    },
    {
        'question': 'Что значит "hangnail"?',
        'options': ['Быстрый рост ногтя', 'Заусеница', 'Грибок ногтя'],
        'correct_answer': 1
    }
]

def check_subscription(user_id):
    """Проверяет, подписан ли пользователь на канал"""
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Очищаем предыдущие данные пользователя
    user_data[chat_id] = {
        'current_question': 0,
        'score': 0,
        'answers': [],
        'agreed_to_terms': False
    }

    welcome_text = """
👋 *Привет! Меня зовут Кристина*

Я репетитор по английскому и автор нескольких каналов, где помогаю людям уверенно говорить на английском в повседневных ситуациях

📊 *Хочешь проверить, насколько хорошо ты знаешь бытовую лексику?*

Чтобы начать тест, необходимо подписаться на мой канал: https://t.me/christiecheers
    """

    markup = types.InlineKeyboardMarkup(row_width=1)
    subscribe_button = types.InlineKeyboardButton(
        '📢 ПОДПИСАТЬСЯ НА КАНАЛ', 
        url='https://t.me/christiecheers'
    )
    check_button = types.InlineKeyboardButton(
        '✅ Я ПОДПИСАЛСЯ, ПРОВЕРИТЬ', 
        callback_data='check_subscription'
    )
    markup.add(subscribe_button, check_button)

    bot.send_message(
        chat_id,
        welcome_text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == 'check_subscription')
def check_subscription_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    if check_subscription(user_id):
        # Пользователь подписан, запрашиваем согласие
        agreement_text = """
📋 *СОГЛАСИЕ НА ОБРАБОТКУ ДАННЫХ*

Для участия в тесте необходимо ваше согласие на обработку данных.

*Что мы обрабатываем:*
• Ваш Telegram ID
• Результаты теста
• Ответы на вопросы

*Как мы используем данные:*
✅ Только для работы теста
✅ Не передаем третьим лицам
✅ Храним в зашифрованном виде

[Условия соглашения](https://drive.google.com/file/d/1qmFvcVHV2mO58LFdFQMwFFvPKjLT54ga/view?usp=sharing)
        """
        
        markup = types.InlineKeyboardMarkup()
        agree_button = types.InlineKeyboardButton(
            '✅ ДАЮ СОГЛАСИЕ', 
            callback_data='agree_to_terms'
        )
        markup.add(agree_button)
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=agreement_text,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    else:
        bot.answer_callback_query(
            call.id,
            "❌ Вы не подписаны на канал. Пожалуйста, подпишитесь и попробуйте снова.",
            show_alert=True
        )

@bot.callback_query_handler(func=lambda call: call.data == 'agree_to_terms')
def agree_to_terms(call):
    chat_id = call.message.chat.id
    
    if chat_id not in user_data:
        user_data[chat_id] = {
            'current_question': 0,
            'score': 0,
            'answers': [],
            'agreed_to_terms': True
        }
    else:
        user_data[chat_id]['agreed_to_terms'] = True
    
    # Начинаем тест
    user_data[chat_id]['current_question'] = 0
    user_data[chat_id]['score'] = 0
    user_data[chat_id]['answers'] = []
    
    start_test_text = """
✅ *Отлично! Вы успешно подписаны и дали согласие.*

Теперь давайте начнем тест! Вам предстоит ответить на 5 вопросов по бытовой лексике.

👇 *Готовы начать?*
    """
    
    markup = types.InlineKeyboardMarkup()
    start_test_button = types.InlineKeyboardButton(
        '🚀 НАЧАТЬ ТЕСТ', 
        callback_data='start_test'
    )
    markup.add(start_test_button)
    
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=start_test_text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == 'start_test')
def start_test(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    # Проверяем подписку еще раз
    if not check_subscription(user_id):
        bot.answer_callback_query(
            call.id,
            "❌ Вы отписались от канала. Пожалуйста, подпишитесь снова.",
            show_alert=True
        )
        return
    
    # Проверяем согласие
    if chat_id not in user_data or not user_data[chat_id].get('agreed_to_terms', False):
        bot.answer_callback_query(
            call.id,
            "❌ Вы не дали согласие на обработку данных.",
            show_alert=True
        )
        return
    
    send_question(chat_id)

def send_question(chat_id):
    if chat_id not in user_data:
        bot.send_message(chat_id, "Пожалуйста, начните заново с команды /start")
        return

    user_state = user_data[chat_id]
    current_question = user_state['current_question']

    if current_question < len(questions):
        question_data = questions[current_question]

        markup = types.InlineKeyboardMarkup()

        for i, option in enumerate(question_data['options']):
            emoji = ['🟡', '🔵', '🟢'][i]
            button = types.InlineKeyboardButton(
                f"{emoji} {option}",
                callback_data=f'answer_{current_question}_{i}'
            )
            markup.add(button)

        question_text = f"""
📝 *Вопрос {current_question + 1}/{len(questions)}*

{question_data['question']}

👇 *Выбери правильный вариант:*
        """

        msg = bot.send_message(
            chat_id,
            question_text,
            reply_markup=markup,
            parse_mode='Markdown'
        )

        user_state['last_message_id'] = msg.message_id

    else:
        show_results(chat_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('answer_'))
def handle_answer(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    if chat_id not in user_data:
        bot.answer_callback_query(call.id, "❌ Начните тест заново: /start")
        return

    # Проверяем подписку перед каждым ответом
    if not check_subscription(user_id):
        bot.answer_callback_query(
            call.id,
            "❌ Вы отписались от канала. Пожалуйста, подпишитесь снова.",
            show_alert=True
        )
        return

    user_state = user_data[chat_id]
    current_question = user_state['current_question']

    parts = call.data.split('_')
    question_index = int(parts[1])
    answer_index = int(parts[2])

    if question_index == current_question:
        question_data = questions[question_index]
        is_correct = (answer_index == question_data['correct_answer'])

        if is_correct:
            user_state['score'] += 1

        user_state['answers'].append({
            'question_index': question_index,
            'answer_index': answer_index,
            'is_correct': is_correct
        })

        user_state['current_question'] += 1

        if is_correct:
            bot.answer_callback_query(call.id, "✅ Правильно!")
        else:
            correct_answer = question_data['options'][question_data['correct_answer']]
            bot.answer_callback_query(call.id, f"❌ Правильно: {correct_answer}")

        send_question(chat_id)

def show_results(chat_id):
    user_state = user_data[chat_id]
    score = user_state['score']
    total_questions = len(questions)

    if score == total_questions:
        level = "🎉 ОТЛИЧНО!"
        message = "Ты прекрасно ориентируешься в бытовой лексике!"
        emoji = "🌟"
    elif score >= total_questions * 0.8:  # 4 из 5
        level = "💪 ОЧЕНЬ ХОРОШО!"
        message = "Отличный результат! Почти идеально!"
        emoji = "✨"
    elif score >= total_questions * 0.6:  # 3 из 5
        level = "📊 ХОРОШО!"
        message = "Солидный запас слов, но есть куда расти!"
        emoji = "📚"
    elif score >= total_questions * 0.4:  # 2 из 5
        level = "🎯 НЕПЛОХО!"
        message = "Базовый уровень есть, но нужно практиковаться!"
        emoji = "💪"
    else:
        level = "🌱 НАЧАЛЬНЫЙ!"
        message = "Есть над чем поработать! Начни с основ!"
        emoji = "🔄"

    result_text = f"""
{emoji} *ТЕСТ ЗАВЕРШЁН!*

📊 *ТВОЙ РЕЗУЛЬТАТ:*
{level}

✅ *Правильных ответов:* {score}/{total_questions}
{message}
    """

    bot.send_message(chat_id, result_text, parse_mode='Markdown')

    # Предложение премиум контента
    premium_text = """
🎊 *ХОЧЕШЬ ЕЩЁ БОЛЬШЕ ПОЛЕЗНОЙ ЛЕКСИКИ?*

Присоединяйся к моему *ЗАКРЫТОМУ ТЕЛЕГРАММ КАНАЛУ!*

*Темы, которые уже ждут тебя:*
☀️ Summer vocabulary
🏖 Beach and vacation
🧹 Cleaning routines
🚽 Toilet and bathroom
🧖🏻‍♀️ Personal hygiene
🩸 Period and health
💅🏻 Beauty and self-care
📚 Education and learning
🍽 Kitchen tools and equipment

*Что ты получаешь:*
🎯 70+ слов и выражений по каждой теме
📝 Практические примеры
✅ Тесты и упражнения
📚 Подборка материалов
🔄 *ПОЖИЗНЕННЫЙ ДОСТУП*

💸 *Всего 690 рублей*

👇 *Нажми кнопку, чтобы узнать как получить доступ:*
    """

    markup = types.InlineKeyboardMarkup()
    premium_button = types.InlineKeyboardButton(
        '💎 ПОЛУЧИТЬ ПОЛНЫЙ ДОСТУП',
        callback_data='get_premium_info'
    )
    markup.add(premium_button)

    bot.send_message(chat_id, premium_text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'get_premium_info')
def handle_premium_info(call):
    chat_id = call.message.chat.id

    premium_info = """
💫 *ОФОРМЛЕНИЕ ДОСТУПА*

Для получения доступа к премиум каналу:

1. *Перейдите по ссылке для оплаты:*
   https://payform.ru/ah8YSST/

2. *Заполните форму оплаты:*
   - Укажите ваше имя и email
   - Оплатите 690 рублей

3. *После успешной оплаты:*
   - Ссылка на закрытый канал придет на указанную почту
   - Если возникли проблемы - напишите в поддержку
    """

    markup = types.InlineKeyboardMarkup()
    pay_button = types.InlineKeyboardButton(
        '💳 ОПЛАТИТЬ 690₽',
        url='https://payform.ru/ah8YSST/'
    )
    support_button = types.InlineKeyboardButton(
        '💬 НАПИСАТЬ В ПОДДЕРЖКУ',
        url='https://t.me/christie_cheers'
    )
    markup.add(pay_button)
    markup.add(support_button)

    bot.send_message(chat_id, premium_info, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    # Игнорируем все другие сообщения
    pass

def run_bot():
    print("Бот запущен...")
    print(f"⚠️ ВНИМАНИЕ: Не забудьте заменить CHANNEL_ID на реальный ID канала")
    print("Инструкция по получению ID канала в комментариях кода")
    keep_alive()  # Запускаем Flask сервер
    
    while True:
        try:
            print("Запускаем polling...")
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            print(f"Ошибка: {e}")
            print("Перезапуск через 10 секунд...")
            time.sleep(10)

# Запускаем бота
if __name__ == "__main__":
    run_bot()
