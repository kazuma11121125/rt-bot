# RT - Url Checker

from typing import TYPE_CHECKING

from discord.ext import commands
import discord

from rtutil import securl
from re import findall

if TYPE_CHECKING:
    from rtlib import Backend


class UrlChecker(commands.Cog):
    def __init__(self, bot: "Backend"):
        self.bot = bot
        self.runnings = []
        self.channel_runnings = []

    @commands.command(
        aliases=["check", "URLチェック", "uc", "ss"], extras={
            "parent": "Individual", "headding": {
                "ja": "渡されたURLの写真を撮り危険性をチェックします。",
                "en": "Take a picture of the URL given to you and check for danger."
            }
        }
    )
    async def securl(self, ctx: commands.Context, *, url: str, force: bool = ""):
        """!lang ja
        --------
        SecURLを使用して渡されたURLのスクリーンショットを撮り危険性をチェックします。

        Parameters
        ----------
        url : str
            調べるURLです。

        Examples
        --------
        `rt!securl http://tasuren.f5.si`

        Aliases
        -------
        ss, check, uc, URLチェック

        !lang en
        --------
        Use SecURL to take a screenshot of the passed URL and check for hazards.

        Parameters
        ----------
        url : str
            The URL to check.

        Examples
        --------
        `rt!check http://tasuren.f5.si`

        Aliases
        -------
        ss, check, uc, URLチェック"""
        if ctx.author.id in self.runnings and not force:
            return await ctx.reply(
                {"ja": "同時に実行することはできません。",
                 "en": "They cannot be run simultaneously."}
            )
        if not force:
            self.runnings.append(ctx.author.id)
            await ctx.trigger_typing()
        try:
            data = await securl.check(self.bot.session, url)
        except ValueError:
            await ctx.reply("そのウェブページへのアクセスに失敗しました。")
        else:
            warnings = {
                key: data[key]
                for key in ("viruses", "annoyUrl", "blackList")
            }
            embed = discord.Embed(
                title="SecURL",
                description=(
                    "このサイトは危険なウェブページである可能性があります！"
                    if (warn := any(warnings.values())) else "危険性はありませんでした"
                ), color=self.bot.colors["error" if warn else "normal"]
            )
            for contents, bool_ in zip(
                (
                    ("ウイルス", "未検出", "**検出**"),
                    ("迷惑サイト", "いいえ", "**はい**"),
                    ("ブラックリスト", "登録されていません。", "**登録されています。**")
                ), warnings.values()
            ):
                embed.add_field(
                    name=contents[0], value=contents[int(bool(bool_)) + 1]
                )
            embed.set_image(url=securl.get_capture(data))
            embed.set_footer(
                text="Powered by SecURL",
                icon_url="https://www.google.com/s2/favicons?domain=securl.nu"
            )
            view = discord.ui.View(timeout=1)
            view.add_item(
                discord.ui.Button(
                    label="スクリーンショット全体を見る", url=securl.get_capture(data, True)
                )
            )
            await ctx.reply(embed=embed, view=view)
        if not force:
            self.runnings.remove(ctx.author.id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.id == self.bot.user.id:
            return

        if (("http://" in message.content or "https://" in message.content
                ) and "https://discord.com" not in message.content
                and message.channel.id not in self.channel_runnings
                and not message.content.startswith(tuple(self.bot.command_prefix))):
            await message.add_reaction("<:search:876360747440017439>")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if (not reaction.message.content.endswith(self.bot.cogs["Person"].QUESTIONS)
                and reaction.message.channel.id not in self.channel_runnings
                and not user.bot):
            self.channel_runnings.append(reaction.message.channel.id)

            await reaction.message.remove_reaction(reaction.emoji, user)
            await reaction.message.remove_reaction(
                reaction.emoji, reaction.message.guild.me
            )

            urls = [
                url for url in findall(
                    r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+",
                    reaction.message.content
                ) if not url.startswith("https://discord.com")
            ]
            if len(urls) < 4:
                ctx = await self.bot.get_context(reaction.message)
                await ctx.trigger_typing()
                for url in urls:
                    self.bot.loop.create_task(self.securl(ctx, url=url, force=True))
            else:
                await reaction.message.channel.send(
                    f"{user.author.mention}, 四つ以上のURLは同時にちぇっくすることができません。"
                )
            self.channel_runnings.remove(reaction.message.channel.id)


def setup(bot):
    bot.add_cog(UrlChecker(bot))