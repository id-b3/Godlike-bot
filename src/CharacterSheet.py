import sqlite3
import tabulate
import discord
from discord.ui import Select, View, Button, Modal, InputText

from SheetTemplates import WOUND_TEMPLATE


class CharacterSelect(Select):
    def __init__(self, name: str, db: sqlite3.Connection):
        options = [
            discord.SelectOption(label="Stats", description="Character stats"),
            discord.SelectOption(label="Skills", description="Character skills"),
            discord.SelectOption(label="Talents", description="Character talents"),
            discord.SelectOption(label="Health", description="Character wounds and will"),
            discord.SelectOption(label="Info", description="Character info", value="CharacterInfo"),
        ]
        super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options)
        self.name = name.capitalize()
        self.db = db
        self.character_id = self.get_character_from_db()

    def get_character_from_db(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT CharacterID FROM CharacterInfo WHERE Nickname=?", (self.name,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def get_character_data(self, tab: str, format_result: bool = True) -> object:
        cursor = self.db.cursor()
        cursor.execute(f"SELECT * FROM {tab} WHERE CharacterID=?", (self.character_id,))
        result = cursor.fetchone()
        cursor.close()
        if not result:
            return None
        elif not format_result:
            return result[1:]

        column_names = [description[0] for description in cursor.description[1:]]
        data = dict(zip(column_names, result[1:]))
        formatted_output = tabulate.tabulate(data.items(), headers=[tab, "Value"], tablefmt="heavy_outline")
        return formatted_output

    async def callback(self, interaction: discord.Interaction):
        label = self.values[0]
        data = self.get_character_data(label, format_result=(label != "Health"))

        if data:
            self.view.clear_items()
            self.view.add_item(self)
            content = f"```{data}```"

            if label == "Health":
                content = f"Current wounds:\n**o** healthy **s** shock **x** killing\n```\n{data[0]}```\n*Current Will:* **{data[2]}**\n*Status:* **{data[1]}**"
                edit_wounds_button = Button(label="Edit Wounds", style=discord.ButtonStyle.primary)
                edit_wounds_button.callback = self.edit_wounds
                self.view.add_item(edit_wounds_button)
            elif label == "Stats":
                edit_stats_button = Button(label="Edit Stats", style=discord.ButtonStyle.primary)
                edit_stats_button.callback = self.edit_stats
                self.view.add_item(edit_stats_button)

            await interaction.response.edit_message(content=content, view=self.view)
        else:
            await interaction.response.edit_message(content="No data available for this category.")

    async def edit_wounds(self, interaction: discord.Interaction):
        [wounds, status, will] = self.get_character_data("Health", format_result=False)
        modal = WoundsModal("Edit Wounds", self.character_id, self.db, wounds, status, will)
        await interaction.response.send_modal(modal)

    async def edit_stats(self, interaction: discord.Interaction):
        stats = self.get_character_data("Stats", format_result=False)
        modal = StatsModal("Edit Stats", self.character_id, self.db, stats)
        await interaction.response.send_modal(modal)


class WoundsModal(Modal):
    def __init__(self, title: str, character_id: int, db: sqlite3.Connection, current_wounds: str, current_status: str,
                 current_will: str):
        super().__init__(title=title)
        self.character_id = character_id
        self.db = db
        self.add_item(InputText(label="Wounds", value=current_wounds, style=discord.InputTextStyle.long))
        self.add_item(InputText(label="Current Will", placeholder="Enter current will points", value=current_will, ))
        self.add_item(InputText(label="Health Status", placeholder="Enter new health status", value=current_status))

    async def callback(self, interaction: discord.Interaction):
        cursor = self.db.cursor()
        cursor.execute("UPDATE Health SET WoundSlot=?, HealthStatus=?, CurrentWill=? WHERE CharacterID=?", (
            self.children[0].value, self.children[2].value, self.children[1].value, self.character_id))
        self.db.commit()
        cursor.close()
        await interaction.response.edit_message(
            content="Health updated.",
            view=None,
            delete_after=5
        )


class StatsModal(Modal):
    def __init__(self, title: str, character_id: int, db: sqlite3.Connection, stats: list):
        super().__init__(title=title)
        self.character_id = character_id
        self.db = db
        stats_as_str = [str(stat) for stat in stats]
        stats_string = ",".join(stats_as_str)
        print(stats_string)
        self.add_item(InputText(label="Stats", value=stats_string))

    async def callback(self, interaction: discord.Interaction):
        cursor = self.db.cursor()
        stats = self.children[0].value.split(',')
        stats = [int(stat) for stat in stats]
        print(stats)
        cursor.execute(
            "UPDATE Stats SET Brains=?, Body=?, Command=?, Coordination=?, Cool=?, Sense=?, BaseWill=? WHERE CharacterID=?",
            (stats[0], stats[1], stats[2], stats[3], stats[4], stats[5], stats[6], self.character_id,))
        self.db.commit()
        cursor.close()
        await interaction.response.edit_message(
            content="Stats updated.",
            view=None,
            delete_after=5
        )


class CharacterView(View):
    def __init__(self, character: CharacterSelect):
        super().__init__(timeout=180)
        self.character = character
        self.add_item(character)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not self.character.values:
            await interaction.response.send_message("Please select a category before editing.", ephemeral=True)
            return False
        return True


def create_new_character(db: sqlite3.Connection, character_name: str) -> str:
    cursor = db.cursor()
    try:
        # Check if the character already exists
        cursor.execute('''SELECT 1 FROM CharacterInfo WHERE Nickname = ?''', (character_name,))
        if cursor.fetchone():
            return f"Character {character_name} already exists."

        # Insert a new character into the CharacterInfo table
        cursor.execute('''INSERT INTO CharacterInfo (Nickname, FullName, Sex, NationEthnicity, Height, Weight, Age, 
                          DateOfManifestation, Education, Profession, Description) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (character_name, 'John Doe', 'Male', 'American', '172cm', '70kg', 20, '1944', 'Highschool',
                        'Private', 'Soldier'))

        # Get the CharacterID of the newly created character
        character_id = cursor.lastrowid

        # Insert default stats for the new character into the Stats table
        cursor.execute('''INSERT INTO Stats (CharacterID, Brains, Body, Command, Coordination, Cool, Sense, BaseWill)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                       (character_id, 1, 1, 1, 1, 1, 1, 2))

        # Insert default health status for the new character into the Health table
        cursor.execute(
            '''INSERT INTO Health (CharacterID, WoundSlot, HealthStatus, CurrentWill) VALUES (?, ?, ?, ?)''',
            (character_id, WOUND_TEMPLATE, "Alive", 2))

        # Commit the changes to the database
        db.commit()

        return f"New character '{character_name}' created successfully."
    except sqlite3.Error as error:
        print(f"Error while creating new character: {error}")
        db.rollback()
        return "Failed to create new character."
    finally:
        cursor.close()
