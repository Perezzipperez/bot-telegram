from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import sqlite3
import random
import time

# ================= CONFIGURACIÓN =================
import os
TOKEN = os.getenv("TOKEN")
ADMIN_USERNAME = "@MiUsee_nameu"
INTENTOS_INICIALES = 5
MAX_GANADORES = 2
MAX_USUARIOS = 50

# 🎯 PROBABILIDADES
PROBABILIDAD_GANAR = 0.07
PROBABILIDAD_ULTIMO_INTENTO = 0.10

# ================= MENSAJES =================
MENSAJES_MOTIVACIONALES = [
    "🔥 ¡No te rindas! Cada intento cuenta.",
    "🍀 La suerte puede cambiar en cualquier momento.",
    "✨ Los ganadores también fallaron antes.",
    "🎯 Sigue intentando, todo puede pasar.",
    "💪 La constancia trae recompensas.",
    "🌟 Hoy podría ser tu día.",
    "🚀 La suerte favorece a los valientes.",
    "🎉 Aún hay esperanza, sigue jugando.",
    "🧠 La paciencia es parte del premio.",
    "⚡ Cada intento te acerca más.",
    "🎲 El próximo puede ser el ganador.",
    "🌈 No pierdas la fe.",
    "🏆 Todo gran ganador insistió.",
    "🔥 El próximo puede sorprenderte.",
    "🧲 La suerte te está buscando.",
    "📈 Cada intento suma.",
    "🎁 Lo bueno tarda pero llega.",
    "🎯 Estuviste cerca.",
    "💎 No te detengas ahora.",
    "🌠 El premio está más cerca."
]

MENSAJE_GANADOR = "🔥🎆 ¡GANASTE! 🎆🔥\n👉 Ve al DM del Administrador"
MENSAJE_FIN_INTENTOS = "😌 Has usado todos tus intentos.\n🍀 Suerte para el próximo sorteo"
MENSAJE_ULTIMO_INTENTO = "⚠️ ÚLTIMO INTENTO ⚠️\n🔥 Todo o nada..."

# ================= BASE DE DATOS =================
conn = sqlite3.connect("sorteo.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    attempts INTEGER,
    has_won INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS raffle (
    id INTEGER PRIMARY KEY,
    winners INTEGER,
    active INTEGER
)
""")

cursor.execute("SELECT * FROM raffle WHERE id=1")
if cursor.fetchone() is None:
    cursor.execute("INSERT INTO raffle VALUES (1,0,1)")
conn.commit()

# ================= UTILIDADES =================
def get_keyboard(username):
    kb = [
        ["🎰 Jugar"],
        ["📊 Mis intentos", "🏆 Ganadores"],
        ["📜 Reglas"]
    ]
    if f"@{username}" == ADMIN_USERNAME:
        kb.append(["👁 Ver todos los usuarios"])
        kb.append(["🔄 Reiniciar intentos"])
        kb.append(["🧹 Reiniciar ganadores"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# ================= ANIMACIONES =================
def slot_real(update, context):
    context.bot.send_dice(chat_id=update.effective_chat.id, emoji="🎰")
    time.sleep(random.uniform(0.8, 1.4))

def explosion_visual(update, context):
    msg = update.message.reply_text("💥")
    frames = ["💥💥", "🔥🎆🔥", "🏆🎉🏆", "🔥 GANADOR 🔥"]
    for f in frames:
        time.sleep(0.4)
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            text=f
        )

# ================= FUNCIONES =================
def intentos(update, context):
    user = update.effective_user
    cursor.execute(
        "SELECT attempts, has_won FROM users WHERE telegram_id=?",
        (user.id,)
    )
    attempts, has_won = cursor.fetchone()
    estado = "🏆 Ganador" if has_won else "🎯 En juego"
    update.message.reply_text(
        f"📊 Tus intentos\n🎯 Intentos: {attempts}\n📌 Estado: {estado}"
    )

def ganadores(update, context):
    cursor.execute("SELECT username FROM users WHERE has_won=1")
    rows = cursor.fetchall()
    if not rows:
        update.message.reply_text("😌 Aún no hay ganadores.")
        return
    msg = "🏆 GANADORES 🏆\n\n"
    for r in rows:
        if r[0]:
            msg += f"👤 @{r[0]}\n"
    update.message.reply_text(msg)

def reglas(update, context):
    update.message.reply_text(
        "📜 REGLAS DEL SORTEO\n\n"
        f"🎰 Intentos iniciales: {INTENTOS_INICIALES}\n"
        f"🏆 Máx. ganadores: {MAX_GANADORES}\n"
        f"🎯 Probabilidad base: 7%\n"
        f"🔥 Último intento: 10%\n\n"
        "⚠️ Solo puedes ganar una vez."
    )

# 👁 FUNCIÓN ADMIN: VER TODOS LOS USUARIOS + INTENTOS
def ver_todos_los_usuarios(update, context):
    if f"@{update.effective_user.username}" != ADMIN_USERNAME:
        return

    cursor.execute("SELECT username, attempts, has_won FROM users")
    rows = cursor.fetchall()

    ganaron = "🏆 USUARIOS QUE GANARON\n\n"
    no_ganaron = "❌ USUARIOS QUE NO GANARON\n\n"

    for username, attempts, has_won in rows:
        if not username:
            continue

        if attempts <= 0:
            estado_intentos = "🚫 Sin intentos"
        else:
            estado_intentos = f"🎯 Intentos: {attempts}"

        if has_won:
            ganaron += f"@{username} — {estado_intentos}\n"
        else:
            no_ganaron += f"@{username} — {estado_intentos}\n"

    update.message.reply_text(ganaron + "\n" + no_ganaron)

# ================= BOT =================
def start(update, context):
    user = update.effective_user

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] >= MAX_USUARIOS:
        update.message.reply_text("⛔ Máximo de participantes alcanzado.")
        return

    cursor.execute("SELECT * FROM users WHERE telegram_id=?", (user.id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users VALUES (?,?,?,?)",
            (user.id, user.username, INTENTOS_INICIALES, 0)
        )
        conn.commit()

    update.message.reply_text(
        "🎉 Bienvenido al SORTEO 🎉",
        reply_markup=get_keyboard(user.username)
    )

def jugar(update, context):
    user = update.effective_user

    cursor.execute("SELECT winners, active FROM raffle WHERE id=1")
    winners, active = cursor.fetchone()
    if not active or winners >= MAX_GANADORES:
        update.message.reply_text("⛔ No hay sorteos activos.")
        return

    cursor.execute(
        "SELECT attempts, has_won FROM users WHERE telegram_id=?",
        (user.id,)
    )
    attempts, has_won = cursor.fetchone()

    if has_won:
        update.message.reply_text("🎉 Ya ganaste.")
        return

    if attempts <= 0:
        update.message.reply_text(MENSAJE_FIN_INTENTOS)
        return

    slot_real(update, context)
    attempts -= 1

    prob = PROBABILIDAD_ULTIMO_INTENTO if attempts == 0 else PROBABILIDAD_GANAR

    if random.random() <= prob:
        explosion_visual(update, context)
        cursor.execute(
            "UPDATE users SET attempts=?, has_won=1 WHERE telegram_id=?",
            (attempts, user.id)
        )
        cursor.execute("UPDATE raffle SET winners=winners+1 WHERE id=1")
        conn.commit()
        update.message.reply_text(MENSAJE_GANADOR)
    else:
        cursor.execute(
            "UPDATE users SET attempts=? WHERE telegram_id=?",
            (attempts, user.id)
        )
        conn.commit()

        if attempts == 0:
            update.message.reply_text(MENSAJE_FIN_INTENTOS)
        elif attempts == 1:
            update.message.reply_text(MENSAJE_ULTIMO_INTENTO)
        else:
            update.message.reply_text(
                f"❌ No ganaste\n{random.choice(MENSAJES_MOTIVACIONALES)}\n🎯 Intentos: {attempts}"
            )

def reiniciar_intentos(update, context):
    if f"@{update.effective_user.username}" != ADMIN_USERNAME:
        return
    cursor.execute(
        "UPDATE users SET attempts=? WHERE has_won=0",
        (INTENTOS_INICIALES,)
    )
    conn.commit()
    update.message.reply_text("🔄 Intentos reiniciados.")

def reiniciar_ganadores(update, context):
    if f"@{update.effective_user.username}" != ADMIN_USERNAME:
        return
    cursor.execute(
        "UPDATE users SET attempts=?, has_won=0",
        (INTENTOS_INICIALES,)
    )
    cursor.execute("UPDATE raffle SET winners=0, active=1 WHERE id=1")
    conn.commit()
    update.message.reply_text("🧹 Sorteo reiniciado.")

# ================= MAIN =================
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.regex("🎰 Jugar"), jugar))
    dp.add_handler(MessageHandler(Filters.regex("📊 Mis intentos"), intentos))
    dp.add_handler(MessageHandler(Filters.regex("🏆 Ganadores"), ganadores))
    dp.add_handler(MessageHandler(Filters.regex("📜 Reglas"), reglas))
    dp.add_handler(MessageHandler(Filters.regex("👁 Ver todos los usuarios"), ver_todos_los_usuarios))
    dp.add_handler(MessageHandler(Filters.regex("🔄 Reiniciar intentos"), reiniciar_intentos))
    dp.add_handler(MessageHandler(Filters.regex("🧹 Reiniciar ganadores"), reiniciar_ganadores))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
