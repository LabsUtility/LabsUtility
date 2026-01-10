import discord
from discord.ext import commands
from discord import app_commands
import traceback

class CalculatorView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.expression = "0"
        self.message = None
        self.build_buttons()

    def embed(self):
        return discord.Embed(
            title="Calculator",
            description=f"```{self.expression}```",
            color=discord.Color.blurple()
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This calculator is not yours.", ephemeral=True
            )
            return False
        return True

    def append(self, value: str):
        if self.expression == "0" and value.isdigit():
            self.expression = value
        else:
            self.expression += value

    def backspace(self):
        self.expression = self.expression[:-1] or "0"

    def clear(self):
        self.expression = "0"

    def evaluate(self):
        try:
            self.expression = str(eval(self.expression))
        except Exception:
            self.expression = "Error"

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception as e:
                print(f"[Calculator Timeout Edit Error]: {e}")

    def build_buttons(self):
        rows = {
            0: ["(", ")", "^", "%", "AC"],
            1: ["7", "8", "9", "Ã·", "DC"],
            2: ["4", "5", "6", "X", "â«"],
            3: ["1", "2", "3", "-", ""],
            4: [".", "0", "=", "+", ""],
        }

        for row, labels in rows.items():
            for label in labels:
                if label == "":
                    self.add_item(
                        discord.ui.Button(
                            label="â",
                            style=discord.ButtonStyle.secondary,
                            disabled=True,
                            row=row
                        )
                    )
                    continue

                btn = discord.ui.Button(
                    label=label,
                    style=discord.ButtonStyle.secondary,
                    row=row
                )
                btn.callback = self.make_callback(label)
                self.add_item(btn)

    def make_callback(self, label: str):
        async def callback(interaction: discord.Interaction):
            try:
                if label in {"AC", "DC"}:
                    self.clear()
                elif label == "â«":
                    self.backspace()
                elif label == "=":
                    self.evaluate()
                elif label == "Ã·":
                    self.append("/")
                elif label == "X":
                    self.append("*")
                elif label == "^":
                    self.append("**")
                else:
                    self.append(label)

                await interaction.response.edit_message(
                    embed=self.embed(), view=self
                )

            except Exception as e:
                print("[Calculator Button Error]:", e)
                traceback.print_exc()
                try:
                    await interaction.response.send_message(
                        f"Button error:\n```{e}```", ephemeral=True
                    )
                except discord.InteractionResponded:
                    await interaction.followup.send(
                        f"Button error:\n```{e}```", ephemeral=True
                    )
        return callback


class Calculator(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="calculator", description="Open an interactive calculator")
    async def calculator(self, interaction: discord.Interaction):
        view = CalculatorView(interaction.user.id)
        await interaction.response.send_message(embed=view.embed(), view=view)
        view.message = await interaction.original_response()


async def setup(bot: commands.Bot):
    await bot.add_cog(Calculator(bot))
