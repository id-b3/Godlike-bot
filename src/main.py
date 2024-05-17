import os
import random
import logging

import sqlite3

import discord
from discord.commands import Option
from dotenv import load_dotenv

from SheetTemplates import WOUND_TEMPLATE
from CharacterSheet import create_new_character, CharacterSelect, CharacterView


# Setup Logging
def setup_logging(debug:bool=False) -> None:
    logger = logging.getLogger('discord')
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)
    return logger

def load_db():
    # Ready the sqlite db
    db = sqlite3.connect("../data/godlike.sqlite")
    return db

def main():
    logger = setup_logging(debug=True)
    load_dotenv()
    TOKEN = os.getenv("TOKEN")

    bot = discord.Bot()
    db = load_db()

    @bot.event
    async def on_ready():
        print(f"We have logged in as {bot.user}")

    @bot.slash_command(name="user_id", description="Get User ID", guild_ids=[1200068691887407174])
    async def user_id(ctx):
        await ctx.response.send_message(f"User {ctx.author} id {ctx.author.id}", ephemeral=True)

    @bot.slash_command(name="glroll", description="Roll godlike dice.", guild_ids=[1200068691887407174])
    async def glroll(ctx, message: Option(str, description="Format: RD HD WD Reason. E.g. /glroll 4 0 1 shooting my gun", required=True), gm: Option(bool, description="Secret roll?", default=False)):

        def _save_roll(user_id: int, roll_results: list):
            cursor = db.cursor()
            try:
                for roll in roll_results:
                    # Insert a new roll result for the user
                    cursor.execute('INSERT INTO Rolls (UserID, RollValue) VALUES (?, ?)', (user_id, roll))
                # Commit the transaction
                db.commit()
            except sqlite3.Error as e:
                print(f"An error occurred: {e}")
                db.rollback()  # Rollback in case of error

            finally:
                cursor.close()

        def _roll_dice(rd: int, hd: int = 0, wg: int = 0, reason_msg: list = None, author_id: int = 0) -> str:
            regular_results = sorted([random.randint(1, 10) for _ in range(rd)])
            hard_results = ['**10**'] * hd
            wiggle_results = ['WIG'] * wg

            _save_roll(author_id, regular_results)

            combined_results = regular_results + hard_results + wiggle_results
            request_message = f"Rolling **{rd}**-rd **{hd}**-hd **{wg}**-wg\n\n"
            if reason_msg:
                request_message += f"For: *{' '.join(reason_msg)}*\n\n"
            results_string = "*" + ' '.join(map(str, combined_results)) + "*"
            return request_message + results_string

        parts = message.split()
        author_id = ctx.author.id
        try:
            regular = int(parts[0])
            hard = int(parts[1]) if len(parts) > 1 else 0
            wiggle = int(parts[2]) if len(parts) > 2 else 0
            reason = parts[3:] if len(parts) > 3 else None

            total_dice = regular + hard + wiggle
            if total_dice > 10:
                await ctx.response.send_message("Exceeded 10 dice maximum for this roll. Adjust your request", ephemeral=gm)
                return

            result = _roll_dice(regular, hard, wiggle, reason, author_id)
            await ctx.response.send_message(result, ephemeral=gm)
        except (IndexError, ValueError):
            await ctx.response.send_message("Please use a valid set of dice entries: '/glroll rd hd wd reason for rolling'", ephemeral=True)

    @bot.slash_command(name="create_talent", description="Create a new Talent.", guild_ids=[1200068691887407174])
    async def create_talent(ctx, name: Option(str, description="Talent's nickname.", required=True)):
        name = name.strip().capitalize()
        creation_response = create_new_character(db, name)
        await ctx.response.send_message(creation_response, ephemeral=True)

    @bot.slash_command(name="show_talent", description="Show character stats: /show_character *name*", guild_ids=[1200068691887407174])
    async def show_talent(ctx, name: Option(str, description="Enter the talent's nickname", required=True)):
        character = CharacterSelect(name.capitalize(), db)
        if character.character_id:
            view = CharacterView(character)
            await ctx.response.send_message(f"{name.capitalize()} Character Sheet", view=view, ephemeral=True)
        else:
            await ctx.response.send_message(f"No character found for {name.capitalize()}", ephemeral=True)

    @bot.slash_command(name="wound_template", description="Print out a blank wound template", guild_ids=[1200068691887407174])
    async def wound_template(ctx):
        await ctx.response.send_message(f"```\n{WOUND_TEMPLATE}\n```")

    bot.run(TOKEN)


if __name__ == '__main__':
    main()
