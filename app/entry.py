from discord.ext import commands
import settings
import datetime
import mysql.connector
from urllib.parse import urlparse
import os

bot = commands.Bot(command_prefix='/')
url = urlparse(os.environ['CLEARDB_DATABASE_URL'])
conn = mysql.connector.connect(
    host = url.hostname,
    port = 3306,
    user = url.username,
    password = url.password,
    database = url.path[1:],
)

@bot.event
async def on_ready():
    conn.ping(reconnect=True)
    print(conn.is_connected())
    print("on ready")


@bot.event
async def on_voice_state_update(member, before, after):
    conn.ping(reconnect=True)
    cur_a = conn.cursor(buffered=True)
    cur_b = conn.cursor(buffered=True)
    cur_c = conn.cursor(buffered=True)
    cur_d = conn.cursor()
    cur_e = conn.cursor()

    if before.channel == after.channel:
        return

    cur_a.execute("SELECT * FROM tmp_channels")

    if before.channel is not None:
        for row in cur_a:
            if row[0] == before.channel.id and len(before.channel.members) == 0:
                await before.channel.delete()
                cur_e.execute("DELETE FROM tmp_channels WHERE id = %s", (before.channel.id,))
                conn.commit()
                print('delete channel: {}'.format(before.channel.id))
                break

    cur_b.execute("SELECT * FROM channels")

    if after.channel is not None:
        for row in cur_b:
            if row[0] == after.channel.id:
                type_name = row[1]

                cur_c.execute("SELECT name, user_limit FROM channel_types")
                channel_types ={}
                for row in cur_c:
                    channel_types[row[0]] = row[1]

                limit = channel_types[type_name]
                channel_name = "{0}_{1}".format(type_name.upper(), datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
                category = after.channel.category
                tmp_channel = await category.create_voice_channel(channel_name, user_limit=limit)
                print("create channel: {}".format(tmp_channel.id))
                cur_d.execute("INSERT INTO tmp_channels VALUES (%s, %s)", (tmp_channel.id, type_name))
                conn.commit()

                await member.move_to(tmp_channel)


@bot.command()
async def create(ctx, type_name=None, category_name=None):
    conn.ping(reconnect=True)
    cur = conn.cursor(buffered=True)
    insert_cur = conn.cursor()

    if type_name is None or category_name is None:
        await ctx.send("チャンネルタイプとカテゴリー名は両方入力してください\nex: /create [channel_type] [category_name]")
        return

    guild = ctx.guild
    categories = guild.categories
    category = next(filter(lambda c: c.name == category_name, categories), None)
    if category is None:
        await ctx.send("{}というカテゴリー名はありません".format(category_name))
        return

    cur.execute("SELECT name FROM channel_types")

    for row in cur:
        if row[0] == type_name:
            channel_name = "VC作成({})".format(type_name.upper())
            channel = await category.create_voice_channel(channel_name)
            insert_cur.execute("INSERT INTO channels VALUES (%s, %s)", (channel.id, type_name))
            conn.commit()
            await ctx.message.delete()
            print("create management channel: {}".format(channel.id))


@bot.command()
async def link(ctx, channel_id=0, type_name=None):
    conn.ping(reconnect=True)
    cur = conn.cursor(buffered=True)
    insert_cur = conn.cursor()

    if channel_id == 0 or type_name is None:
        await ctx.send("チャンネル名とチャンネルタイプは両方入力してください\nex: /link [channel_id] [channel_type]")
        return

    guild = ctx.guild
    channel = next(filter(lambda c: c.id == channel_id, guild.voice_channels), None)
    if channel is None:
        await ctx.send("チャンネルが見つかりません: {}".format(channel_id))
        return

    cur.execute("SELECT name FROM channel_types")
    type = None
    for row in cur:
        if row[0] == type_name:
            type = type_name
            break

    if type is None:
        await ctx.send("チャンネルタイプが見つかりません: {}".format(type_name))
        return

    insert_cur.execute("INSERT IGNORE INTO channels VALUES (%s, %s)", (channel.id, type_name))
    conn.commit()

    await ctx.send("{}を管理用チャンネルとして登録しました".format(channel.name))
    print("link management channel: {}".format(channel.id))


@bot.command()
async def unlink(ctx, channel_id=0):
    conn.ping()
    cur = conn.cursor()

    if channel_id == 0:
        await ctx.send("チャンネルIDを入力してください\nex: /unlink [channel_id]")
        return

    guild = ctx.guild
    channel = next(filter(lambda c: c.id == channel_id, guild.voice_channels), None)
    if channel is None:
        await ctx.send("チャンネルが見つかりません: {}".format(channel_id))
        return

    cur.execute("DELETE FROM channels WHERE id = %s", (channel.id,))
    conn.commit()

    await ctx.send("{}を通常チャンネルに変更しました".format(channel.name))
    print("unlink management channel: {}".format(channel.id))


@bot.command()
async def register(ctx, type_name=None, limit=0):
    conn.ping(reconnect=True)
    cur = conn.cursor()

    if type_name is None:
        await ctx.send("チャンネルタイプを入力してください\nex: /register [channel_type] [limit(defaul 0)]")
        return

    if limit < 0:
        await ctx.send("人数制限を0人未満にすることはできません")
        return

    cur.execute("INSERT IGNORE INTO channel_types (name, user_limit) VALUES (%s, %s)", (type_name, limit))
    conn.commit()

    limit_message = "ありません" if limit <= 0 else "{}人です".format(limit)
    await ctx.send("{0}を新しいチャンネルタイプとして登録しました\n人数制限は{1}".format(type_name, limit_message))
    print("register channel type: {0} (limit = {1})".format(type_name, limit))


@bot.command()
async def unregister(ctx, type_name=None):
    conn.ping(reconnect=True)
    cur = conn.cursor()
    select_cur = conn.cursor(buffered=True)

    if type_name is None:
        await ctx.send("チャンネルタイプを入力してください\nex: /unregister [channel_type]")
        return

    select_cur.execute("SELECT name FROM channel_types")
    channel_type = None
    for row in select_cur:
        if row[0] == type_name:
            channel_type = type_name
            break

    if channel_type is None:
        await ctx.send("チャンネルタイプが見つかりません: {}".format(type_name))
        return

    cur.execute("DELETE FROM channel_types WHERE name = %s", (type_name,))
    conn.commit()
    await ctx.send("チャンネルタイプから{}を削除しました".format(type_name))
    print("unregister channel type: {}".format(type_name))


@bot.command(aliases=['channels'])
async def _channels(ctx):
    conn.ping(reconnect=True)
    cur = conn.cursor(buffered=True)
    delete_cur = conn.cursor()

    channel_names = ""
    voice_channels = ctx.guild.voice_channels

    cur.execute("SELECT id FROM channels")
    for row in cur:
        channel = next(filter(lambda ch: ch.id == row[0], voice_channels), None)
        if channel is None:
            print("{} is not found. delete from channels.".format(row[0]))
            delete_cur.execute("DELETE FROM channels WHERE id = %s", (row[0]))
            conn.commit()
            continue

        channel_names += channel.name + "\n"

    await ctx.send("```\nManagement Channels:\n{}\n```".format(channel_names))


@bot.command(aliases=['channel_types'])
async def _channel_types(ctx):
    conn.ping(reconnect=True)
    cur = conn.cursor()

    type_names = ""
    cur.execute("SELECT name FROM channel_types")
    for row in cur:
        type_names += row[0] + "\n"

    await ctx.send("```\nChannel Types:\n{}\n```".format(type_names))


bot.run(settings.TOKEN)