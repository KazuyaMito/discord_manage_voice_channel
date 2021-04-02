from discord.ext import commands
import settings
import datetime
import mysql.connector

bot = commands.Bot(command_prefix='/')
tmp_channels = {}
conn = mysql.connector.connect(
    host='docker-mysql',
    port='3306',
    user='root',
    password='',
    database='docker_db'
)

@bot.event
async def on_ready():
    conn.ping(reconnect=True)
    print(conn.is_connected())
    print("on ready")


@bot.event
async def on_voice_state_update(member, before, after):
    global channels
    global tmp_channels
    global channel_types

    if before.channel == after.channel:
        return

    if before.channel is not None and before.channel.id in tmp_channels.keys():
        if len(before.channel.members) == 0:
            await before.channel.delete()
            del tmp_channels[before.channel.id]
            print('delete channel: {}'.format(before.channel.id))

    if after.channel is not None and after.channel.id in channels.keys():
        type_name = channels[after.channel.id]

        limit = channel_types[type_name]
        channel_name = "{0}_{1}".format(type_name.upper(), datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        category = after.channel.category
        tmp_channel = await category.create_voice_channel(channel_name, user_limit=limit)
        print("create channel: {}".format(tmp_channel.id))
        tmp_channels[tmp_channel.id] = type_name
        await member.move_to(tmp_channel)


@bot.command(aliases=['hoge'])
async def create(ctx, type_name=None, category_name=None):
    global channel_types
    global channels

    conn.ping(reconnect=True)
    cur = conn.cursor(buffered=True)
    insert_cur = conn.cursor(buffered=True)

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
    global channels

    if channel_id == 0 or type_name is None:
        await ctx.send("チャンネル名とチャンネルタイプは両方入力してください\nex: /link [channel_id] [channel_type]")
        return

    guild = ctx.guild
    channel = next(filter(lambda c: c.id == channel_id, guild.voice_channels), None)
    if channel is None:
        await ctx.send("チャンネルが見つかりません: {}".format(channel_id))
        return

    type = next(filter(lambda t: t == type_name, channel_types.keys()), None)
    if type is None:
        await ctx.send("チャンネルタイプが見つかりません: {}".format(type_name))
        return

    channels[channel.id] = type
    await ctx.send("{}を管理用チャンネルとして登録しました".format(channel.name))
    print("link management channel: {}".format(channel.id))


@bot.command()
async def unlink(ctx, channel_id=0):
    global channels

    if channel_id == 0:
        await ctx.send("チャンネルIDを入力してください\nex: /unlink [channel_id]")
        return

    guild = ctx.guild
    channel = next(filter(lambda c: c.id == channel_id, guild.voice_channels), None)
    if channel is None:
        await ctx.send("チャンネルが見つかりません: {}".format(channel_id))
        return

    del channels[channel.id]
    await ctx.send("{}を通常チャンネルに変更しました".format(channel.name))
    print("unlink management channel: {}".format(channel.id))


@bot.command()
async def register(ctx, type_name=None, limit=0):
    global channel_types

    if type_name is None:
        await ctx.send("チャンネルタイプを入力してください\nex: /register [channel_type] [limit(defaul 0)]")
        return

    if limit < 0:
        await ctx.send("人数制限を0人未満にすることはできません")
        return

    channel_types[type_name] = limit
    limit_message = "ありません" if limit <= 0 else "{}人です".format(limit)

    await ctx.send("{0}を新しいチャンネルタイプとして登録しました\n人数制限は{1}".format(type_name, limit_message))
    print("register channel type: {0} (limit = {1})".format(type_name, limit))


@bot.command()
async def unregister(ctx, type_name=None):
    global channel_types

    if type_name is None:
        await ctx.send("チャンネルタイプを入力してください\nex: /unregister [channel_type]")
        return

    channel_type = next(filter(lambda t: t == type_name, channel_types.keys()), None)
    if channel_type is None:
        await ctx.send("チャンネルタイプが見つかりません: {}".format(type_name))
        return

    del channel_types[channel_type]
    await ctx.send("チャンネルタイプから{}を削除しました".format(type_name))
    print("unregister channel type: {}".format(type_name))


@bot.command(aliases=['channels'])
async def _channels(ctx):
    global channels

    channel_names = ""
    voice_channels = ctx.guild.voice_channels
    for c in channels.keys():
        channel = next(filter(lambda ch: ch.id == c, voice_channels), None)
        if channel is None:
            print("{} is not found. delete from channels.".format(c))
            del channels[c]
            continue

        channel_names += channel.name + "\n"

    await ctx.send("```\nManagement Channels:\n{}\n```".format(channel_names))


@bot.command(aliases=['channel_types'])
async def _channel_types(ctx):
    global channel_types

    type_names = ""
    for t in channel_types.keys():
        type_names += t + "\n"

    await ctx.send("```\nChannel Types:\n{}\n```".format(type_names))


bot.run(settings.TOKEN)