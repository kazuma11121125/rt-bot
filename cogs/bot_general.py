# RT - Bog General

from discord.ext import commands


class BotGeneral(commands.Cog):
    def __init__(self, bot):
        self.bot, self.rt = bot, bot.data


def setup(bot):
    bot.add_cog(BotGeneral(bot))
