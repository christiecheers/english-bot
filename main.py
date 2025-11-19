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

questions = [
    {
        'question': 'Что значит "pitch" в разговорной речи?',
        'options': ['Бросать мяч', 'Жаловаться', 'Выбрасывать что-то ненужное'],
        'correct_answer': 2
    },
    {
        'question': 'Какая фраза звучит естественнее, если хочешь протереть стол?',
        'options': ['I removed streaks from the table.', 'I wiped the table clean.', 'I cleaned up streaks.'],
        'correct_answer': 1
    },
    {
        'question': 'Выбери естественное выражение после уборки:',
        'options': ['Everything is sparkling!', 'Everything shines like a diamond!', 'Everything is bright.'],
        'correct_answer': 0
    },
    {
        'question': 'Что значит "get moldy"?',
        'options': ['Намокнуть', 'Покрыться плесенью', 'Превратиться в крошки'],
        'correct_answer': 1
    },
    {
        'question': 'Что сказать, если сожгла волосы плойкой?',
        'options': ['I singed my hair with a curling iron.', 'I burned my hair with a hair straightener.', 'I fried my hair.'],
        'correct_answer': 0
    },
    {
        'question': 'Что сказать, если ноготь слегка откололся?',
        'options': ['My nail broke.', 'My nail fell.', 'My nail chipped.'],
        'correct_answer': 2
    },
    {
        'question': 'Выбери естественное выражение:',
        'options': ['My hair is frizzy today.', 'My hair is electric today.', 'My hair is wild today.'],
        'correct_answer': 0
    },
    {
        'question': 'Что значит "razor burn"?',
        'options': ['Ожог от солнца', 'Раздражение от бритвы', 'След от утюга'],
        'correct_answer': 1
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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_data[message.chat.id] = {
        'current_question': 0,
        'score': 0,
        'answers': []
    }

    welcome_text = """
🎓 *Добро пожаловать в English Test Bot!* 🎓

━━━━━━━━━━━━━━━━━
👋 *Привет! Меня зовут Кристина*
━━━━━━━━━━━━━━━━━

Я репетитор по английскому и автор нескольких каналов, где помогаю людям уверенно говорить на английском в повседневных ситуациях

📊 *Хочешь проверить, насколько хорошо ты знаешь бытовую лексику?*

✅ Пройди короткий тест из 10 вопросов
⏱ Это займёт меньше 2 минут!
🎯 Узнай свой реальный уровень

*Проверь, насколько свободно ты ориентируешься в английском для:*
🏠 Домашних дел и уборки
💅 Ухода за собой и гигиены
🍽 Повседневных ситуаций
🛒 Бытовых моментов

*После прохождения теста ты получишь МИНИ УРОК В ПОДАРОК по быту!*

👇 *Жми "НАЧАТЬ ТЕСТ" и узнай, насколько твой английский приближен к реальной жизни!*
    """

    markup = types.InlineKeyboardMarkup()
    start_test_button = types.InlineKeyboardButton('🚀 НАЧАТЬ ТЕСТ', callback_data='start_test')
    markup.add(start_test_button)

    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == 'start_test')
def start_test(call):
    chat_id = call.message.chat.id

    if chat_id not in user_data:
        user_data[chat_id] = {
            'current_question': 0,
            'score': 0,
            'answers': []
        }

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

    if chat_id not in user_data:
        bot.answer_callback_query(call.id, "❌ Начните тест заново: /start")
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
    elif score >= total_questions * 0.8:
        level = "💪 ОЧЕНЬ ХОРОШО!"
        message = "Отличный результат! Почти идеально!"
        emoji = "✨"
    elif score >= total_questions * 0.6:
        level = "📊 ХОРОШО!"
        message = "Солидный запас слов, но есть куда расти!"
        emoji = "📚"
    elif score >= total_questions * 0.4:
        level = "🎯 НЕПЛОХО!"
        message = "Базовый уровень есть, но нужно практиковаться!"
        emoji = "💪"
    else:
        level = "🌱 НАЧАЛЬНЫЙ!"
        message = "Есть над чем поработать! Начни с основ!"
        emoji = "🔄"

    result_text = f"""
{emoji} *ТЕСТ ЗАВЕРШЁН!*

━━━━━━━━━━━━━━━━━
📊 *ТВОЙ РЕЗУЛЬТАТ:*
{level}
━━━━━━━━━━━━━━━━━

✅ *Правильных ответов:* {score}/{total_questions}
{message}
    """

    bot.send_message(chat_id, result_text, parse_mode='Markdown')

    # Сразу предлагаем мини-урок после теста
    lesson_text = """
🎁 *БОНУС ДЛЯ ТЕБЯ!*

━━━━━━━━━━━━━━━━━
🚀 *БЕСПЛАТНЫЙ МИНИ-УРОК*
━━━━━━━━━━━━━━━━━

*Прокачай свой английский для кулинарии и не только!*

👇 *Нажми кнопку, чтобы получить мини-урок:*
    """

    markup = types.InlineKeyboardMarkup()
    mini_lesson_button = types.InlineKeyboardButton(
        '🍽 ПОЛУЧИТЬ МИНИ-УРОК',
        callback_data='get_mini_lesson'
    )
    markup.add(mini_lesson_button)

    bot.send_message(chat_id, lesson_text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'get_mini_lesson')
def send_mini_lesson(call):
    chat_id = call.message.chat.id

    # Список слов
    vocabulary_text = """
📚 *МИНИ-УРОК: КУЛИНАРНАЯ ЛЕКСИКА*

🍽 *Вкусы и текстура:*
▪️ zesty — с ярким вкусом (цитрусовый, пикантный)
▪️ tangy — с лёгкой кислинкой
▪️ crunchy on the outside, soft inside — хрустящий снаружи, мягкий внутри
▪️ melt-in-your-mouth — тающий во рту
▪️ robust — насыщенный, богатый вкус
▪️ pungent — резкий, острый (например, чеснок)
▪️ fluffy — пышный, воздушный
▪️ creamy — сливочный, кремовый
▪️ bland — безвкусный, пресный
▪️ smooth — гладкий, однородный
▪️ sour — кислый

🔪 *Глаголы (действия):*
▪️ drizzle — сбрызнуть, полить сверху
▪️ fold in — аккуратно вмешать
▪️ sear — обжарить до корочки
▪️ marinate — мариновать
▪️ zest — натереть цедру
▪️ whip up — приготовить на скорую руку
▪️ whisk up - взбить
▪️ toss — перемешать (салат)
▪️ peel — почистить
▪️ chop nuts — порезать / покрошить
▪️ cool off — остыть, остудить
▪️ plate everything — выложить всё на тарелку

🥣 *Существительные и выражения:*
▪️ cutting board — разделочная доска
▪️ leftovers — остатки еды
▪️ clove (garlic) — зубчик чеснока
▪️ grater — тёрка
▪️ skewer — шпажка
▪️ meal prepping — подготовка еды заранее
▪️ heaping amount of — с горкой (например, ложка с горкой)
    """

    bot.send_message(chat_id, vocabulary_text, parse_mode='Markdown')

    # Кнопка для перехода к упражнениям
    exercises_text = """
🎯 *Отлично! Теперь закрепим знания на практике*

👇 *Переходи к упражнениям:*
    """

    markup = types.InlineKeyboardMarkup()
    exercises_button = types.InlineKeyboardButton(
        '📝 ПЕРЕЙТИ К УПРАЖНЕНИЯМ',
        callback_data='get_exercises'
    )
    markup.add(exercises_button)

    bot.send_message(chat_id, exercises_text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'get_exercises')
def send_exercises(call):
    chat_id = call.message.chat.id

    exercises_text = """
🎯 *ПРАКТИЧЕСКИЕ УПРАЖНЕНИЯ:*

• [🍳 Cooking Vocabulary Flashcards](https://fliktop.ru/christina.sedova/playlist/cards/net-nazvaniya/ffe8b6f4-03d9-4d11-a125-770b66d9bea0/?open=true)
• [✅ Choose the Correct Option](https://fliktop.ru/christina.sedova/playlist/cards/choose-the-correct-option/95dae03b-ca13-4d58-bd9d-48b14b436ed4/?open=true)
    """

    bot.send_message(chat_id, exercises_text, parse_mode='Markdown')

    # Кнопка для дополнительных материалов
    materials_text = """
📚 *Хочешь углубить знания?*

Изучи дополнительные материалы по теме:
    """

    markup = types.InlineKeyboardMarkup()
    materials_button = types.InlineKeyboardButton(
        '🔍 ПОЛУЧИТЬ ДОПОЛНИТЕЛЬНЫЕ МАТЕРИАЛЫ',
        callback_data='get_materials'
    )
    markup.add(materials_button)

    bot.send_message(chat_id, materials_text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'get_materials')
def send_materials(call):
    chat_id = call.message.chat.id

    materials_text = """
🔍 *ДОПОЛНИТЕЛЬНЫЕ МАТЕРИАЛЫ:*

🎥 *YouTube:*
• [Korean Beef Bulgogi Recipe](https://youtu.be/mhDJNfV7hjk?si=4Ui4A0Ka7_888Rtd)
• [Easy Cooking Techniques](https://www.youtube.com/watch?v=LYzRXCzxDeY)
• [Kitchen Vocabulary](https://www.youtube.com/watch?v=HR61Hwt2qUA)
• [Food Preparation Tips](https://www.youtube.com/watch?v=ZJy1ajvMU1k)
• [Quick Meal Ideas](https://www.youtube.com/watch?v=OTAwvdRJn6M)

📖 *Статьи:*
• [Korean Beef Bulgogi Recipe](https://www.recipetineats.com/korean-beef-bulgogi-rice-bowls-the-easy-way/)
• [Creamy Greek Salad Dressing](https://lisagcooks.com/creamy-greek-salad-dressing/)
    """

    bot.send_message(chat_id, materials_text, parse_mode='Markdown')

    # Кнопка "Хочу больше уроков" после материалов
    more_lessons_text = """
✨ *Понравился урок?*

Хочешь получать такие уроки регулярно по разным темам?
    """

    markup = types.InlineKeyboardMarkup()
    more_lessons_button = types.InlineKeyboardButton(
        '🚀 ХОЧУ БОЛЬШЕ УРОКОВ',
        callback_data='want_more_lessons'
    )
    markup.add(more_lessons_button)

    bot.send_message(chat_id, more_lessons_text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'want_more_lessons')
def offer_premium_content(call):
    chat_id = call.message.chat.id

    premium_text = """
🎊 *ХОЧЕШЬ ЕЩЁ БОЛЬШЕ ПОЛЕЗНОЙ ЛЕКСИКИ?*

В этом мини-уроке ты увидел только 30 слов по кулинарии, но на моём закрытом канале более 70 слов и выражений по каждой теме!

Я приглашаю тебя в мой *ЗАКРЫТЫЙ ТЕЛЕГРАММ КАНАЛ!*

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

@bot.callback_query_handler(func=lambda call: call.data == 'restart_test')
def restart_test(call):
    chat_id = call.message.chat.id
    user_data[chat_id] = {
        'current_question': 0,
        'score': 0,
        'answers': []
    }

    send_question(chat_id)

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    if message.text and message.text.startswith('/'):
        return

    markup = types.InlineKeyboardMarkup()
    start_button = types.InlineKeyboardButton('🚀 НАЧАТЬ ТЕСТ', callback_data='start_test')
    markup.add(start_button)

    bot.send_message(
        message.chat.id,
        "🎓 *Нажмите кнопку ниже, чтобы начать тест по английскому!*",
        reply_markup=markup,
        parse_mode='Markdown'
    )

def run_bot():
    print("Бот запущен...")
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
