import discord
from discord.ext import commands
import asyncio
from flask import Flask, request, jsonify
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
app = Flask(__name__)

# Listas de baneados (en memoria mientras el bot esté encendido)
banned_users = set()
blocked_execution = set()

@app.route('/report', methods=['POST'])
def report():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON"}), 400

    userId = data.get('userId')
    username = data.get('username', 'Desconocido')
    displayName = data.get('displayName', 'Desconocido')
    totalArmas = data.get('totalArmas', 0)
    weaponsText = data.get('weaponsText', 'No detectado')
    gameName = data.get('gameName', 'Desconocido')
    timestamp = data.get('timestamp', 'Desconocida')

    # <<< CAMBIA ESTE ID POR EL DE TU CANAL DE NOTIFICACIONES >>>
    channel_id = 1457479963946258608  # ← PON TU ID REAL AQUÍ
    channel = bot.get_channel(channel_id)

    if not channel:
        return jsonify({"error": "Canal no encontrado"}), 500

    embed = discord.Embed(title="⚠️ ARMAS DETECTADAS - INVENTARIO", color=0xff0000)
    embed.add_field(name="Username", value=username, inline=True)
    embed.add_field(name="DisplayName", value=displayName, inline=True)
    embed.add_field(name="UserID", value=str(userId), inline=False)
    embed.add_field(name="Total de armas", value=f"**{totalArmas}**", inline=False)
    embed.add_field(name="Inventario detallado", value=weaponsText, inline=False)
    embed.add_field(name="Juego", value=gameName, inline=False)
    embed.add_field(name="Fecha y hora", value=timestamp, inline=False)
    embed.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={userId}&width=420&height=420&format=png")
    embed.set_footer(text="Anti-Executor Bot - Botones interactivos")

    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="Bloquear ejecución", style=discord.ButtonStyle.grey, custom_id=f"block_{userId}"))
    view.add_item(discord.ui.Button(label="Banear", style=discord.ButtonStyle.red, custom_id=f"ban_{userId}"))
    view.add_item(discord.ui.Button(label="Desbanear", style=discord.ButtonStyle.green, custom_id=f"unban_{userId}"))

    asyncio.create_task(channel.send(embed=embed, view=view))
    return jsonify({"status": "enviado"}), 200

@bot.event
async def on_interaction(interaction):
    if interaction.type != discord.InteractionType.component:
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Solo administradores pueden usar estos botones.", ephemeral=True)
        return

    custom_id = interaction.data['custom_id']
    userId = int(custom_id.split("_")[1])

    if custom_id.startswith("block_"):
        blocked_execution.add(userId)
        await interaction.response.send_message(f"🔒 Ejecución bloqueada para `{userId}`", ephemeral=True)
    elif custom_id.startswith("ban_"):
        banned_users.add(userId)
        await interaction.response.send_message(f"🔨 `{userId}` baneado permanentemente", ephemeral=True)
    elif custom_id.startswith("unban_"):
        banned_users.discard(userId)
        blocked_execution.discard(userId)
        await interaction.response.send_message(f"✅ `{userId}` desbaneado", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}!")

# Iniciar Flask en un hilo separado
if __name__ == "__main__":
    import threading
    threading.Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": int(os.environ.get("PORT", 8080))}).start()
    bot.run(os.getenv("TOKEN"))
