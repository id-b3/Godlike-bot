import discord
from discord.ext import commands

# Prefix for commands
bot = commands.Bot(command_prefix='!')

# Character sheet template based on the provided layout
default_character_sheet = {
    'Name/Alias': '',
    'Sex': '',
    'Nation/Ethnicity': '',
    'Height': '',
    'Weight': '',
    'Age': '',
    'Date of Birth': '',
    'Date of Manifestation': '',
    'Education': '',
    'Profession': '',
    'Appearance and Personality': '',
    # You can continue adding other fields based on the complete structure you're planning to use.
}

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='character', help='Displays the default Godlike character sheet.')
async def character_sheet(ctx):
    # Building the display message for the character sheet
    character_sheet_message = '```\nGodlike Character Sheet\n----------------------\n'
    for key, value in default_character_sheet.items():
        character_sheet_message += f'{key}: {value}\n'
    character_sheet_message += '```'
    
    await ctx.send(character_sheet_message)

bot.run('YOUR_BOT_TOKEN_HERE')