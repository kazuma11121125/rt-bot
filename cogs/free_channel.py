# RT - Free Channel

from discord.ext import commands
import discord

from asyncio import sleep


async def freechannel(ctx: commands.Context) -> bool:
    # フリーチャンネルか確かめるためのコマンドに付けるデコレータです。
    if isinstance(ctx.channel, discord.TextChannel):
        return (ctx.channel.topic and "RTフリーチャンネル" in ctx.channel.topic
                and str(ctx.author.id) in ctx.channel.topic
                and "作成者" in ctx.channel.topic and ctx.channel.category)
    else:
        return ctx.category is not None

class FreeChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown = {
            "make": {},
            "remove": {},
            "rename": {}
        }

    @commands.group(
        extras={
            "headding": {
                "ja": "実行したチャンネルをフリーチャンネル作成専用のチャンネルにします。",
                "en": "..."
            },
            "parent": "ServerPanel"
        },
        name="freechannel",
        aliases=["fc", "FreeChannel", "自由チャンネル", "114514チャンネル"]
    )
    async def freechannel_(self, ctx):
        """!lang ja
        --------
        フリーチャンネルのコマンドです。

        !lang en
        --------
        ..."""
        if not ctx.invoked_subcommand:
            await ctx.send(
                {"ja": f"{ctx.author.mention}, 使用方法が違います。",
                 "en": f"{ctx.author.mention}, ..."},
                delete_after=5, target=ctx.author.id
            )

    @freechannel_.command(aliases=["add", "rg"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def register(self, ctx, max_channel: int = 4, lang="ja"):
        """!lang ja
        --------
        実行したチャンネルをフリーチャンネル作成専用のチャンネルにします。  
        このコマンドを実行したチャンネルに`text:チャンネル名`と送るとチャンネルが作られる感じです。  
        ボイスチャンネルの場合は`voice:チャンネル名`にすれば良いです。  

        Warnings
        --------
        このコマンドを実行できるのは`チャンネル管理`権限を持っている人のみです。  
        また作成されるフリーチャンネルはこのコマンドを実行したチャンネルのカテゴリー内です。  
        よってこのコマンドはカテゴリーの中にあるチャンネルでのみ実行可能です。

        Parameters
        ----------
        max_channel : int, default 4
            個人個人が作れる最大チャンネル数です。  
            入力しない場合は4となります。
        lang : str, default ja
            フリーチャンネルの説明のパネルを日本語か英語どっちで表示するかです。  
            入力しない場合は`ja`で日本語になっており英語にしたい場合は`en`にしてください。

        Aliases
        -------
        `rg`"""
        if ctx.channel.category is None:
            await ctx.reply(
                {"ja": "カテゴリーのあるチャンネルでのみこのコマンドは実行可能です。",
                 "en": "..."}
            )
            return
        if (ctx.channel.topic and "RTフリーチャンネル" in ctx.channel.topic
                and "作成者" not in ctx.channel.topic):
            await ctx.send(
                {"ja": f"{ctx.author.mention}, 既にフリーチャンネル作成用チャンネルとなっています。",
                 "en": f"{ctx.author.mention}, ..."},
                delete_after=5, target=ctx.author.id
            )
            return

        title = {"ja": "フリーチャンネル", "en": "Free Channel"}
        description = {
            "ja": """好きなチャンネル名を送信することでそのチャンネルを作成することができます。
**#** 作成方法
テキストチャンネル：このチャンネルで`text チャンネル名`
ボイスチャンネル：このチャンネルで`voice チャンネル名`
**#** 改名方法
テキストチャンネル：そのフリーチャンネルで`rt!rename 改名後の名前`
ボイスチャンネル：適当なチャンネルで`rt!rename ボイスチャンネル名 改名後の名前`
※作成されるボイスチャンネルの名前には作成した人のIDが含まれますが、このIDは改名時にチャンネル名に入れる必要はないです。
**#** 削除方法
テキストチャンネル：そのフリーチャンネルで`rt!remove`
ボイスチャンネル：適当なチャンネルで`rt!remove ボイスチャンネル名`
※作成されるボイスチャンネルの名前には作成した人のIDが含まれますが、このIDは削除時にチャンネル名に入れる必要はないです。""",
            "en": "..."
        }

        footer = {"ja": f"一人{max_channel}個までチャンネルを作成可能です。",
                  "en": f"{max_channel}..."}
        embed = discord.Embed(
            title=title[lang],
            description=description[lang],
            color=self.bot.colors["normal"]
        )
        embed.set_footer(text=footer[lang])

        await ctx.webhook_send(
            username=ctx.author.display_name, avatar_url=ctx.author.avatar.url,
            embed=embed
        )
        await sleep(0.4)
        await ctx.channel.edit(
            topic=(f"RTフリーチャンネル\n作成可能チャンネル数：{max_channel}"
                   + "\nこのトピックは消さないでください。/ 英語版をここに")
        )

    @freechannel_.command(name="remove")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def remove_(self, ctx):
        if (ctx.channel.topic and "RTフリーチャンネル" in ctx.channel.topic
                and "作成者" not in ctx.channel.topic):
            await ctx.channel.edit(topic=None)
            await sleep(0.4)
            await ctx.reply({"ja": "フリーチャンネル作成用チャンネルを無効化しました。",
                             "en": "..."})
        else:
            await ctx.reply(
                {"ja": "ここはフリーチャンネル作成用チャンネルではありません。",
                 "en": "..."}
            )

    @commands.command()
    @commands.check(freechannel)
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def remove(self, ctx, name=None):
        await ctx.trigger_typing()
        if name is None:
            await ctx.channel.delete()
        else:
            for channel in ctx.channel.category.voice_channels:
                if channel.name == f"{name}-{ctx.author.id}":
                    await channel.delete()
                    await ctx.reply(
                        {"ja": "チャンネルを削除しました。",
                        "en": "..."}
                    )
                    break
            else:
                await ctx.reply(
                    {"ja": "チャンネルが見つかりませんでした。",
                     "en": "..."}
                )

    @commands.command()
    @commands.check(freechannel)
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def rename(self, ctx, name: str, *, after: str = None):
        await ctx.trigger_typing()
        if after is None:
            await ctx.channel.edit(name=name)
        else:
            for channel in ctx.channel.category.voice_channels:
                if channel.name == f"{name}-{ctx.author.id}":
                    await channel.edit(name=f"{after}-{ctx.author.id}")
                    break
            else:
                await ctx.reply(
                    {"ja": "チャンネルが見つかりませんでした。",
                     "en": "..."}
                )
        await ctx.reply(
            {"ja": "チャンネル名を変更しました。",
             "en": "..."}
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if (not message.guild or not hasattr(message.channel, "topic")
                and not message.content):
            return

        topic = message.channel.topic if message.channel.topic else ""
        if ("RTフリーチャンネル" in topic and "作成者" not in topic
                and message.channel.category):
            # フリーチャンネルでのユーザーへの返信の場合は
            if not (message.author.id == self.bot.user.id
                    and ">," in message.content):
                await message.delete()

            # もしフリーチャンネルでのユーザーへのRTの返信じゃないそれかBotならコマンドの実行はさせない。
            if message.author.bot or not message.content.startswith(("text", "voice")):
                return
            else:
                await message.channel.trigger_typing()

            # 作成に必要な情報を変数に入れる。max_channelは最大チャンネル数。
            max_channel = int(topic[22:topic.find("\nこ")])
            user_id = str(message.author.id)
            now = {
                "text": [channel
                         for channel in message.channel.category.text_channels
                         if channel.topic and user_id in channel.topic],
                "voice": [channel
                          for channel in message.channel.category.voice_channels
                          if channel.name.endswith("-" + user_id)]
            }

            if message.content.startswith(("text ", "voice ")):
                # チャンネルの作成。
                mode = "text" if message.content[0] == "t" else "voice"

                if len(now[mode]) >= max_channel:
                    await message.channel.send(
                        {"ja": f"{message.author.mention}, あなたはチャンネルをこれ以上作れません。",
                         "en": f"{message.author.mention}, ..."},
                         delete_after=5, target=message.author.id
                    )
                    return 

                if mode == "text":
                    coro = message.channel.category.create_text_channel(
                        message.content[5:], topic=f"RTフリーチャンネル, 作成者：{user_id}"
                    )
                    mode = ("テキスト", "text")
                else:
                    coro = message.channel.category.create_voice_channel(
                        "".join((message.content[6:], "-", user_id))
                    )
                    mode = ("ボイス", "voice")

                await coro
                await message.channel.send(
                    {"ja": f"{message.author.mention}, {mode[0]}チャンネルを作成しました。",
                     "en": f"{message.author.mention}, {mode[1]}..."},
                    delete_after=5, target=message.author.id
                )


def setup(bot):
    bot.add_cog(FreeChannel(bot))