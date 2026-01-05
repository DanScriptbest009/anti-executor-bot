import discord
from discord.ext import commands
import asyncio
from flask import Flask, request, jsonify
import os
import threading

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
app = Flask(__name__)

# Listas de baneados (se mantienen mientras el bot esté online)
banned_users = set()
blocked_execution = set()

@app.route('/report', methods=['POST'])
def report():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON recibido"}), 400

    userId = data.get('userId')
    username = data.get('username', 'Desconocido')
    displayName = data.get('displayName', 'Desconocido')
    totalArmas = data.get('totalArmas', 0)
    weaponsText = data.get('weaponsText', 'No detectado')
    gameName = data.get('gameName', 'Desconocido')
    timestamp = data.get('timestamp', 'Desconocida')

    # TU CANAL ESPECÍFICO - YA ESTÁ CORRECTO
    channel_id = 1457479963946258608
    channel = bot.get_channel(channel_id)

    if not channel:
        print("ERROR: No se encontró el canal o el bot no está conectado a Discord")
        return jsonify({"error": "Canal no encontrado"}), 500

    # Crear el embed
    embed = discord.Embed(title="⚠️ ARMAS DETECTADAS - INVENTARIO", color=0xff0000)
    embed.add_field(name="Username", value=username, inline=True)
    embed.add_field(name="DisplayName", value=displayName, inline=True)
    embed.add_field(name="UserID", value=str(userId), inline=False)
    embed.add_field(name="Total de armas", value=f"**{totalArmas}**", inline=False)
    embed.add_field(name="Inventario detallado", value=weaponsText, inline=False)
    embed.add_field(name="Juego", value=gameName, inline=False)
    embed.add_field(name="Fecha y hora", value=timestamp, inline=False)
    embed.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={userId}&width=420&height=420&format=png")
    embed.set_footer(text="Anti-Executor Bot - Control total con botones")

    # Crear los botones
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="Bloquear ejecución", style=discord.ButtonStyle.grey, custom_id=f"block_{userId}"))
    view.add_item(discord.ui.Button(label="Banear permanentemente", style=discord.ButtonStyle.red, custom_id=f"ban_{userId}"))
    view.add_item(discord.ui.Button(label="Desbanear", style=discord.ButtonStyle.green, custom_id=f"unban_{userId}"))

    # Enviar el mensaje de forma segura (fix para Flask)
    def send_discord_message():
        bot.loop.create_task(channel.send(embed=embed, view=view))

    threading.Thread(target=send_discord_message).start()

    return jsonify({"status": "Reporte enviado correctamente"}), 200

@bot.event
async def on_ready():
    print(f"¡BOT CONECTADO Y LISTO COMO {bot.user}! (ID: {bot.user.id})")
    print("Esperando reportes de Roblox...")

@bot.event
async def on_interaction(interaction):
    if interaction.type != discord.InteractionType.component:
        return

    # Solo admins pueden usar los botones
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Solo administradores pueden usar estos botones.", ephemeral=True)
        return

    custom_id = interaction.data['custom_id']
    userId = int(custom_id.split("_")[1])

    if custom_id.startswith("block_"):
        blocked_execution.add(userId)
        await interaction.response.send_message(f"🔒 Ejecución bloqueada temporalmente para UserID `{userId}`", ephemeral=True)
    elif custom_id.startswith("ban_"):
        banned_users.add(userId)
        await interaction.response.send_message(f"🔨 UserID `{userId}` baneado permanentemente del script", ephemeral=True)
    elif custom_id.startswith("unban_"):
        banned_users.discard(userId)
        blocked_execution.discard(userId)
        await interaction.response.send_message(f"✅ UserID `{userId}` desbaneado correctamente", ephemeral=True)

# Iniciar Flask y el bot de Discord
if __name__ == "__main__":
    print("Iniciando servidor Flask y bot de Discord...")
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))).start()
    bot.run(os.getenv("TOKEN"))
