import discord
from discord.ext import commands
from discord.utils import get
import yt_dlp as youtube_dl
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 대기열 및 현재 상태 관리
queue = []
repeat_mode = "off"  # off, track, all
first_track_played = False  # 첫 번째 트랙이 재생되었는지 여부
played_tracks = []  # 재생된 트랙을 기록할 리스트
volume_level = 0.5  # 기본 볼륨 (50%)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def 재생(ctx, *, query: str):
    await ctx.message.delete(delay=5)
    channel = ctx.author.voice.channel
    if not channel:
        await ctx.send("음성 채널에 먼저 접속해주세요!")
        return

    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if not voice_client:
        voice_client = await channel.connect()

    if "youtube.com" in query or "youtu.be" in query:
        url = query
    else:
        # YouTube 검색 실행
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            if 'entries' in info and len(info['entries']) > 0:
                url = info['entries'][0]['webpage_url']
            else:
                await ctx.send("노래를 찾을 수 없습니다. 다시 시도해주세요.")
                return

    # 유튜브에서 오디오 다운로드 및 스트리밍 설정
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['url']
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url2), volume=volume_level)

    # 첫 번째 트랙인 경우 대기열에 추가하지 않음
    global first_track_played
    if not first_track_played:
        first_track_played = True  # 첫 번째 트랙이 재생되었음을 기록
        await ctx.send(f"재생 중: {info['title']}")
        voice_client.play(source, after=lambda e: asyncio.ensure_future(play_next(ctx)))
    else:
        queue.append({'title': info['title'], 'url': url})
        await ctx.send(f"대기열에 추가됨: {info['title']}")

# 다음 트랙 재생
async def play_next(ctx):
    global queue, repeat_mode, first_track_played, played_tracks
    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if not queue:
        if voice_client:
            await voice_client.disconnect()
        await ctx.send("대기열이 비어 있습니다. 음성 채널을 떠납니다.")
        return

    next_track = queue.pop(0)
    played_tracks.append(next_track)
    if repeat_mode == "track":
        queue.insert(0, next_track)
    elif repeat_mode == "all":
        queue.append(next_track)

    ydl_opts = {'format': 'bestaudio', 'quiet': True}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(next_track['url'], download=False)
        url2 = info['url']
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url2), volume=volume_level)

    voice_client.play(source, after=lambda e: asyncio.ensure_future(play_next(ctx)))
    await ctx.send(f"재생 중: {next_track['title']}")

# 대기열 출력
@bot.command()
async def 대기열(ctx):
    await ctx.message.delete(delay=5)
    if not queue:
        await ctx.send("대기열이 비어 있습니다.")
    else:
        queue_list = '\n'.join([f"{i + 1}. {track['title']}" for i, track in enumerate(queue)])
        await ctx.send(f"현재 대기열:\n{queue_list}")

# 대기열에서 노래 삭제
@bot.command()
async def 삭제(ctx, index: int):
    await ctx.message.delete(delay=5)
    if not queue:
        await ctx.send("대기열이 비어 있습니다. 삭제할 곡이 없습니다.")
        return

    if index < 1 or index > len(queue):
        await ctx.send("유효하지 않은 번호입니다. 대기열 번호를 다시 확인해주세요.")
        return

    removed_song = queue.pop(index - 1)
    await ctx.send(f"대기열에서 '{removed_song['title']}'가 삭제되었습니다.")

# 재생 기록 출력
@bot.command()
async def 재생기록(ctx):
    await ctx.message.delete(delay=5)
    if not played_tracks:
        await ctx.send("재생 기록이 없습니다.")
    else:
        played_tracks_list = '\n'.join([f"{i + 1}. {track['title']}" for i, track in enumerate(played_tracks)])
        await ctx.send(f"재생된 곡들:\n{played_tracks_list}")

# 멈춤 명령어
@bot.command()
async def 멈춰(ctx):
    await ctx.message.delete(delay=5)
    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send("음악을 멈추고 채널에서 퇴장합니다.")
    else:
        await ctx.send("봇이 음성 채널에 있지 않습니다.")

# 노래 넘기기
@bot.command()
async def 넘기기(ctx):
    await ctx.message.delete(delay=5)
    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if not voice_client or not voice_client.is_playing():
        await ctx.send("현재 재생 중인 노래가 없습니다.")
        return

    voice_client.stop()
    await ctx.send("현재 노래를 넘깁니다.")
    await play_next(ctx)

# 반복 모드 설정
@bot.command()
async def 반복(ctx, mode: str):
    await ctx.message.delete(delay=5)
    global repeat_mode
    if mode in ["off", "track", "all"]:
        repeat_mode = mode
        await ctx.send(f"반복 모드가 '{mode}'로 설정되었습니다.")
    else:
        await ctx.send("올바른 옵션을 입력해주세요: off, track, all")

# 볼륨 조절 명령어
@bot.command()
async def 볼륨(ctx, level: int):
    global volume_level
    await ctx.message.delete(delay=5)

    if level < 0 or level > 200:
        await ctx.send("볼륨은 0에서 200 사이로 설정해주세요.")
        return

    volume_level = level / 200
    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.source:
        voice_client.source.volume = volume_level
    await ctx.send(f"볼륨이 {level}%로 설정되었습니다.")

bot.run(os.getenv("DISCORD_TOKEN"))  # 봇 토큰을 입력하세요.
