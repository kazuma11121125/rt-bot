# RT - Channel Status

from discord.ext import commands, tasks
import discord

from rtlib import mysql, DatabaseLocker


class DataManager(DatabaseLocker):
    def __init__(self, db: mysql.MySQLManager):
        self.db: mysql.MySQLManager = db

    async def init_table(self) -> None:
        async with self.db.get_cursor() as cursor:
            await cursor.create_table(
                "channelStatus", {
                    "GuildID": "BIGINT", "ChannelID": "BIGINT",
                    "Text": "TEXT"
                }
            )

    async def load(self, guild_id: int) -> list:
        async with self.db.get_cursor() as cursor:
            await cursor.cursor.execute(
                """SELECT * FROM channelStatus
                    WHERE GuildID = ?""", (guild_id,)
            )
            return await cursor.cursor.fetchall()

    async def load_all(self) -> list:
        async with self.db.get_cursor() as cursor:
            await cursor.cursor.execute(
                "SELECT * FROM channelStatus"
            )
            return await cursor.cursor.fetchall()

    async def save(self, guild_id: int, channel_id: int, text: str) -> None:
        target = {"GuildID": guild_id, "ChannelID": channel_id}
        change = {"Text": text}
        async with self.db.get_cursor() as cursor:
            if await cursor.exists("channelStatus", target):
                await cursor.update_data("channelStatus", change, target)
            else:
                target.update(change)
                await cursor.insert_data("channelStatus", target)

    async def delete(self, guild_id: int, channel_id: int) -> None:
        target = {"GuildID": guild_id, "ChannelID": channel_id}
        async with self.db.get_cursor() as cursor:
            if await cursor.exists("channelStatus", target):
                await cursor.delete("channelStatus", target)


class ChannelStatus(commands.Cog, DataManager):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        super(commands.Cog, self).__init__(
            await self.bot.mysql.get_database()
        )
        await self.init_table()
        self.status_updater.start()

    @commands.command(extras={
        "headding": {
            "ja": "チャンネルにメンバー数などを表示する。",
            "en": "..."
        }, "parent": "ServerUseful"
    })
    @commands.has_permissions(manage_channels=True)
    async def status(self, ctx, *, text):
        """!lang ja
        --------
        テキストチャンネルにメンバー数などを表示させます。  
        実行したチャンネルに設定されます。

        Parameters
        ----------
        text : 文字列またはオフにする際はoff
            チャンネル名に表示するものです。  
            下のメモにあるものを置くことで自動でそれに対応するメンバー数などに置き換わります。

        Notes
        -----
        ```
        !ch! テキストチャンネル数
        !mb! メンバー数 (Botを含める。)
        !bt! Bot数
        !us! ユーザー数 (Botを含めない。)
        ```

        Examples
        --------
        `rt!status メンバー数：!mb!`

        !lang en
        --------
        ..."""
        if text.lower() in ("false", "off", "disable", "0"):
            await self.delete(ctx.guild.id, ctx.channel.id)
            content = {"ja": "", "en": ""}
        else:
            await self.save(ctx.guild.id, ctx.channel.id, text)
            content = {
                "ja": "\n五分に一回ステータスを更新するのでしばらく時間がかかる可能性があります。",
                "en": "\n..."
            }
        await ctx.reply(
            {"ja": f"設定しました。{content['ja']}",
             "en": f"I have set.{content['en']}"}
        )

    def cog_unload(self):
        self.status_updater.cancel()

    def replace_text(self, template: str, guild: discord.Guild) -> str:
        # テンプレートにあるものを情報に交換する。
        text = template.replace("!ch!", str(len(guild.text_channels)))
        text = text.replace("!mb!", str(len(guild.members)))
        if "!us!" in template or "!bt!" in template:
            bots, users = [], []
            for member in guild.members:
                if member.bot:
                    bots.append(member)
                else:
                    users.append(member)
            text = text.replace("!bt!", str(len(bots)))
            text = text.replace("!us!", str(len(users)))
        return text

    @tasks.loop(minutes=5)
    async def status_updater(self):
        for _, channel_id, text in await self.load_all():
            channel = self.bot.get_channel(channel_id)
            if channel:
                if channel.name != (
                        text := self.replace_text(text, channel.guild)
                    ):
                    await channel.edit(name=text, reason="ステータス更新のため。")


def setup(bot):
    bot.add_cog(ChannelStatus(bot))