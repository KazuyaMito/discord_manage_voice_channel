from discord.ext import commands
import settings
from enum import Enum

bot = commands.Bot(command_prefix='/')
channel_type = {'apex': 3, 'valorant': 5}
channels = [range(0)]

@bot.event
async def on_ready():
    print("on ready")

# ユーザーのボイス状態が変わったら入るところ
@bot.event
async def on_voice_state_update(member, before, after):
    # チャンネルが変わっていない場合は何もしない
    if before.channel == after.channel:
        return

    # チャンネルから退出してきたとき
    # チャンネルの人数が0人になったら
    if before.channel is not None and len(before.channel.members) == 0:
        # チャンネルを消す
        if before.channel is not None:
            await before.channel.delete()
    # チャンネルに入ってきたとき
    # elif after.channel is not None:


@bot.command()
async def create(ctx, type_name):
    global channel_type
    global channels

    guild = ctx.guild
    if type_name in channel_type:
        limit = channel_type[type_name]
        channel_name = "VC作成({})".format(type_name.upper())
        channel = await guild.create_voice_channel(channel_name, user_limit=limit)
        channels.append(channel)


bot.run(settings.TOKEN)