import discord


class Menu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

    @discord.ui.button(label="This is a button", style=discord.ButtonStyle.grey)
    async def button(self, interaction: discord.Interaction, Button: discord.ui.Button):
        # await interaction.response.defer(thinking=True)

        Button.style = discord.ButtonStyle.green
        Button.label = "And now it's a green button"
        await interaction.response.edit_message(view=self)

        await interaction.followup.send("You've clicked a button")
