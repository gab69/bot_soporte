import json
import asyncio
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters


nest_asyncio.apply()

# Cargar los datos 
with open('datos.json', 'r', encoding='utf-8') as file:
    datos = json.load(file)

# Variable global para controlar el estado del bot
bot_activo = True

# Función para manejar el comando /cmds
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Ver comandos", callback_data='ver_comandos')],
        [InlineKeyboardButton("Descargar comandos", callback_data='descargar_comandos')],
        [InlineKeyboardButton("Detener bot", callback_data='detener_bot')], 
        [InlineKeyboardButton("⬅️ Volver", callback_data='volver_inicio')]  
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Verificar si el mensaje proviene de un comando o de un callback
    if update.message:
        await update.message.reply_text('Selecciona una opción:', reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text('Selecciona una opción:', reply_markup=reply_markup)

# Función para manejar la selección de "Ver comandos"
async def ver_comandos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Hardware", callback_data='hardware')],
        [InlineKeyboardButton("Software", callback_data='software')],
        [InlineKeyboardButton("⬅️ Volver", callback_data='volver_inicio')]  # Botón para volver al menú principal
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Selecciona el tipo de comando:", reply_markup=reply_markup)

# Función para manejar la selección de "Hardware" o "Software"
async def tipo_comando(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    tipo = query.data
    clasificaciones = set(item['Clasificación'] for item in datos if item['Tipo'] == tipo.capitalize())

    keyboard = [
        [InlineKeyboardButton(clasificacion, callback_data=f'{tipo}_{clasificacion}')] for clasificacion in clasificaciones
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Volver", callback_data='ver_comandos')])  # Botón para volver al menú anterior
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=f"Selecciona la clasificación para {tipo.capitalize()}:", reply_markup=reply_markup)

# Función para manejar la selección de una clasificación
async def clasificacion_comando(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    tipo, clasificacion = query.data.split('_')
    comandos = [item for item in datos if item['Tipo'] == tipo.capitalize() and item['Clasificación'] == clasificacion]

    mensaje = f"Comandos de {tipo.capitalize()} - {clasificacion}:\n\n"
    for comando in comandos:
        mensaje += f"Código: {comando['Código']}\nProblema: {comando['Problema']}\n\n"

    keyboard = [
        [InlineKeyboardButton("⬅️ Volver", callback_data=f'{tipo}')]  # Botón para volver al menú anterior
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=mensaje, reply_markup=reply_markup)

# Función para manejar la selección de "Descargar comandos"
async def descargar_comandos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    with open('comandos.pdf', 'rb') as file:
        await context.bot.send_document(chat_id=query.message.chat_id, document=file, filename='comandos.pdf')

# Función para manejar comandos específicos (por ejemplo, /SOFNET2)
async def comando_especifico(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Obtener el comando ingresado (por ejemplo, "/SOFNET2")
    comando = update.message.text[1:]  # Elimina el "/" del comando

    # Buscar el comando en los datos
    for item in datos:
        if item['Código'] == comando:
            mensaje = f"Solución para {comando}:\n\n{item['Solución']}"
            await update.message.reply_text(mensaje)
            return

    # Si no se encuentra el comando
    await update.message.reply_text(f"No se encontró el comando: {comando}")

# Función para manejar la navegación de "Volver"
async def volver(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == 'volver_inicio':
        # Volver al menú principal
        await cmds(update, context)
    elif callback_data == 'ver_comandos':
        # Volver al menú de "Ver comandos"
        await ver_comandos(update, context)
    else:
        # Volver al menú de "Hardware" o "Software"
        await tipo_comando(update, context)

# Función para manejar la detención del bot
async def detener_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global bot_activo
    query = update.callback_query
    await query.answer()

    bot_activo = False
    await query.edit_message_text(text="El bot se ha detenido. ¡Hasta luego!")
    await context.application.stop()

# Función principal
async def main() -> None:

    application = Application.builder().token("PON AQUI TU API DEL BOT DE TELEGRAM").build()

    # Manejadores de comandos y callbacks
    application.add_handler(CommandHandler("start", start))  # Maneja el comando /cmds
    application.add_handler(CallbackQueryHandler(ver_comandos, pattern='^ver_comandos$'))
    application.add_handler(CallbackQueryHandler(descargar_comandos, pattern='^descargar_comandos$'))
    application.add_handler(CallbackQueryHandler(tipo_comando, pattern='^(hardware|software)$'))
    application.add_handler(CallbackQueryHandler(clasificacion_comando, pattern='^(hardware|software)_'))
    application.add_handler(CallbackQueryHandler(volver, pattern='^(volver_inicio|ver_comandos|hardware|software)$'))  # Maneja la navegación de "Volver"
    application.add_handler(CallbackQueryHandler(detener_bot, pattern='^detener_bot$'))  # Maneja la detención del bot

    # Manejador para comandos específicos (por ejemplo, /SOFNET2)
    application.add_handler(MessageHandler(filters.TEXT & filters.COMMAND, comando_especifico))

    # Iniciar el bot
    await application.run_polling()

# Ejecutar el bot
if __name__ == '__main__':
    try:
        # Ejecutar el bucle de eventos
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot detenido.")