# RT - Role Message

from typing import TYPE_CHECKING, Optional, Union, Literal, Tuple, List

from discord.ext import commands
import discord

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from aiomysql import Pool
    from rtlib import Backend


class DataManager:

    TABLE = "RoleMessage"

    def __init__(self, loop: "AbstractEventLoop", pool: "Pool"):
        self.pool = pool
        loop.create_task(self._prepare_table())

    async def _prepare_table(self):
        # テーブルを作る。クラスのインスタンス化時に自動で実行される。
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"""CREATE TABLE IF NOT EXISTS {self.TABLE} (
                        GuildID BIGINT, RoleID BIGINT PRIMARY KEY NOT NULL,
                        ChannelID BIGINT, Mode TEXT, Content TEXT
                    );"""
                )

    async def write(
        self, guild_id: int, role_id: int, channel_id: int,
        mode: Literal["add", "remove"], content: str
    ) -> None:
        "データを書き込みます。"
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"""INSERT INTO {self.TABLE} VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE ChannelID = %s, Content = %s;""",
                    (guild_id, role_id, channel_id, mode,
                     content, channel_id, content)
                )

    async def reads(self, guild_id: int) -> List[Tuple[int, int, str]]:
        "データを全て読み込みます。"
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f"""SELECT RoleID, ChannelID, Mode FROM {self.TABLE}
                        WHERE GuildID = %s""",
                    (guild_id,)
                )
                return [row for row in await cursor.fetchall() if row]

    async def _read(self, cursor, guild_id, role_id, mode):
        # 渡されたカーソルを使って指定されたロールのデータを読み込みます。
        await cursor.execute(
            f"""SELECT ChannelID, Content FROM {self.TABLE}
                WHERE GuildID = %s AND RoleID = %s AND Mode = %s;""",
            (guild_id, role_id, mode)
        )
        return await cursor.fetchone()

    async def read(self, guild_id: int, role_id: int, mode: str) -> Optional[Tuple[int, str]]:
        "データを読み込みます。"
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if (row := await self._read(cursor, guild_id, role_id, mode)):
                    return row

    async def delete(self, guild_id: int, role_id: int, mode: str) -> None:
        "データを削除します。"
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                assert await self._read(cursor, guild_id, role_id, mode), "設定されていません。"
                await cursor.execute(
                    f"""DELETE FROM {self.TABLE}
                        WHERE GuildID = %s AND RoleID = %s AND Mode = %s;""",
                    (guild_id, role_id, mode)
                )


class RoleMessage(commands.Cog, DataManager):
    def __init__(self, bot: "Backend"):
        self.bot = bot
        super(commands.Cog, self).__init__(self.bot.loop, self.bot.mysql.pool)

    @commands.group(
        aliases=["rmsg", "ロールメッセージ"], extras={
            "headding": {
                "ja": "ロール付与/剥奪時に送信するメッセージ",
                "en": "Message to be sent when a role is added or removed."
            }, "parent": "ServerTool"
        }
    )
    @commands.has_permissions(manage_roles=True)
    async def rolemessage(self, ctx):
        """!lang ja
        --------
        ロールメッセージです。  
        ロールが付与または剥奪された際に特定のチャンネルに特定のメッセージを送ることができます。  

        Aliases
        -------
        rmsg, ロールメッセージ

        !lang en
        --------
        Role Message.
        You can send a specific message to a specific channel when a role is added or removed.

        Aliases
        -------
        rmsg"""
        if not ctx.invoked_subcommand:
            await ctx.reply(
                {"ja": "使用方法が違います。",
                 "en": "It is wrong way to use this feature."}
            )

    @rolemessage.command("list", aliases=["一覧", "l"])
    async def list_(self, ctx):
        """!lang ja
        --------
        設定されているロールメッセージの一覧を表示します。

        Aliases
        -------
        l, 一覧

        !lang en
        --------
        Displays list of role message registered.

        Aliases
        -------
        l"""
        await ctx.reply(
            embed=discord.Embed(
                title=self.__cog_name__,
                description="\n".join(
                    f"<#{row[1]}>：<@&{row[0]}> `{row[2]}`"
                    for row in await self.reads(ctx.guild.id)
                ), color=self.bot.colors["normal"]
            )
        )

    @rolemessage.command(aliases=["a", "追加"])
    async def add(
        self, ctx, role: Union[discord.Role, discord.Object],
        mode: Literal["add", "remove"], *, content
    ):
        """!lang ja
        -------
        ロールメッセージの設定を追加します。

        Parameters
        ----------
        role : ロールのメンションか名前またはID
            何のロールが付与または剥奪されたらメッセージを送るかです。
        mode : add または remove
            ロールが付与または剥奪どっちが起きたらメッセージを送るかです。  
            `add`にすると付与時で`remove`で剥奪時です。
        content : str
            送信内容です。

        Notes
        -----
        送信内容に以下のものが含まれている場合はそれに対応するものに置き換えられます。
        ```
        !role_name!      付与または剥奪されたロールの名前
        !role_mention!   付与または剥奪されたロールのメンション
        !member_name!    対象のメンバーの名前
        !member_mention! 対象のメンバーのメンション
        ```

        Aliases
        -------
        a, 追加

        !lang en
        --------
        Add role message settings.

        Parameters
        ----------
        role : Mention or name or ID of the role
            A message is sent when a role is granted or revoked.
        mode : add or remove
            Whether to send a message when a role is added or removed.
            If `add`, it will be sent when the role is added, and `remove` when it is removed.
        content : str
            The content to send.

        Noets
        -----
        The following will be replaced with the corresponding ones if they are included in the submitted content.
        ```
        !role_name!      A role name that added or removed
        !role_mention!   A role mention that added or removed
        !member_name!    A target member's name
        !member_mention! A target member's mention
        ```

        Aliases
        -------
        a"""
        await ctx.trigger_typing()
        await self.write(ctx.guild.id, role.id, ctx.channel.id, mode, content)
        await ctx.reply("Ok")

    @rolemessage.command(aliases=["rm", "削除"])
    async def remove(
        self, ctx, role: Union[discord.Role, discord.Object],
        mode: Literal["add", "remove"]
    ):
        """!lang ja
        --------
        設定したロールメッセージを削除します。

        Parameters
        ----------
        role : ロールのメンションか名前またはID
            対象のロールです。
        mode : add または remove
            対象のロールメッセージに設定しているモードです。

        Aliases
        -------
        rm, 削除

        !lang en
        --------
        Remove role message setting

        Parameters
        ----------
        role : Mention or name or ID of the role
            Target role
        mode : add or remove
            Role message setting mode

        Aliases
        -------
        rm"""
        await ctx.trigger_typing()
        await self.delete(ctx.guild.id, role.id, mode)
        await ctx.reply("Ok")

    async def on_role_add_remove(
        self, mode: Literal["add", "remove"],
        role: discord.Role, member: discord.Member
    ) -> None:
        # ロールメッセージを送信する。
        if ((row := await self.read(member.guild.id, role.id, mode))
                and (channel := member.guild.get_channel(row[0]))):
            await channel.send(
                row[1].replace("!role_name!", role.name) \
                    .replace("!role_mention!", role.mention) \
                    .replace("!member_name!", member.name) \
                    .replace("!member_mention!", member.mention)
            )

    @commands.Cog.listener()
    async def on_role_add(self, role, member):
        await self.on_role_add_remove("add", role, member)

    @commands.Cog.listener()
    async def on_role_remove(self, role, member):
        await self.on_role_add_remove("remove", role, member)


def setup(bot):
    bot.add_cog(RoleMessage(bot))