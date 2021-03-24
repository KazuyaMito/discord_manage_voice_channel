from discord.ext import commands
import settings
import datetime

bot = commands.Bot(command_prefix='!')
channel_types = {'apex': 3, 'valorant': 5, 'other':0}
channels = {}
tmp_channels = {}

@bot.event
async def on_ready():
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


@bot.command()
async def create(ctx, type_name=None, category_name=None):
    global channel_types
    global channels

    if type_name is None or category_name is None:
        await ctx.send("チャンネルタイプとカテゴリー名は両方入力してください\nex: /create [channel_type] [category_name]")
        return

    guild = ctx.guild
    categories = guild.categories
    category = next(filter(lambda c: c.name == category_name, categories), None)
    if category is None:
        await ctx.send("{}というカテゴリー名はありません".format(category_name))
        return

    if type_name in channel_types:
        channel_name = "VC作成({})".format(type_name.upper())
        channel = await category.create_voice_channel(channel_name)
        channels[channel.id] = type_name
        await ctx.message.delete()
        print("create management channel: {}".format(channel.id))


@bot.command()
async def link(ctx, channel_name=None, type_name=None):
    global channels

    if channel_name is None or type_name is None:
        await ctx.send("チャンネル名とチャンネルタイプは両方入力してください\nex: /link [channel_name] [channel_type]")
        return

    guild = ctx.guild
    channel = next(filter(lambda c: c.name == channel_name, guild.voice_channels), None)
    if channel is None:
        await ctx.send("チャンネルが見つかりません: {}".format(channel_name))
        return

    type = next(filter(lambda t: t == type_name, channel_types.keys()), None)
    if type is None:
        await ctx.send("チャンネルタイプが見つかりません: {}".format(type_name))
        return

    channels[channel.id] = type
    await ctx.send("{}を管理用チャンネルとして登録しました".format(channel.name))
    print("register management channel: {}".format(channel.id))


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


bot.run(settings.TOKEN)