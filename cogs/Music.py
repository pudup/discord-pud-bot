import asyncio
import json
import os
import discord
import yt_dlp
from discord.ext import commands
from discord import app_commands
import aiohttp
from youtube_search import YoutubeSearch
import datetime
import random
import itertools
from async_timeout import timeout

### HELPER FUNCTIONS

prefix = os.getenv('PREFIX')


async def color():
    random_number = random.randint(0, 16777215)
    hex_number = hex(random_number)
    return int(hex_number, base=16)


async def delete_songs(server_id):
    files = os.listdir(f"songs/{server_id}")
    for file in files:
        os.remove(f"songs/{server_id}/" + file)
    os.rmdir(f"songs/{server_id}/")


async def search_youtube(query):
    results = YoutubeSearch(query, max_results=1).to_dict()
    return f"https://www.youtube.com/{results[0]['url_suffix']}"


async def is_link(query):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(query) as response:
                if response:
                    return True
    except:
        return False


### END OF HELPERS

### YOUTUBE FUNCTIONS ###

yt_dlp.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    # 'outtmpl': 'songs/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')
        self.id = data.get('id')
        self.duration = data.get('duration')
        self.web_url = data.get('webpage_url')
        self.description = data.get('description')[slice(200)] + "..."

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, server_id):
        loop = loop or asyncio.get_event_loop()
        ytdl.params['outtmpl'] = f'songs/{server_id}/%(title)s.%(ext)s'
        with yt_dlp.YoutubeDL(ytdl_format_options) as ydl:
            data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=not stream))
            # Not sure why I need to make a different yt_dlp object here, but it doesn't work without it

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


### END OF YOUTUBE ###


class MusicStreamer:
    def __init__(self, interaction):

        self.interaction = interaction

        self.queue = asyncio.Queue()
        self.play_next = asyncio.Event()

        self.current_track = None

        self.interaction.client.loop.create_task(self.main_streamer_loop())

    async def audio_player_task(self):
        while True:
            self.play_next.clear()
            current = await self.queue.get()
            current.start()
            await self.play_next.wait()

    def go_next_song(self):
        self.interaction.client.loop.call_soon_threadsafe(self.play_next.set)

    async def main_streamer_loop(self):
        await self.interaction.client.wait_until_ready()
        while not self.interaction.client.is_closed():
            self.play_next.clear()

            # try:
            #     async with timeout(60):
            #         source = await self.queue.get()
            # except asyncio.TimeoutError:
            #     await self.ctx.send("I ran out of time, I'm outta here")
            #     await self.ctx.cog.stop(self.ctx)
            #     return

            source = await self.queue.get()

            server = self.interaction.guild
            vc = server.voice_client
            try:
                vc.stop()
            except:
                pass
            try:
                vc.play(source, after=lambda _: self.interaction.client.loop.call_soon_threadsafe(self.play_next.set))
            except:
                return
            embed = discord.Embed(title=f"{source.title}", url=f"{source.web_url}",
                                  description=f"Playing in {vc.channel}",
                                  color=await color())
            embed.set_author(name=f"Now Playing for {self.interaction.user}",
                             icon_url=self.interaction.user.display_avatar)
            embed.set_thumbnail(url=f"https://i.ytimg.com/vi_webp/{source.id}/maxresdefault.webp")
            embed.add_field(name='Duration', value=str(datetime.timedelta(seconds=source.duration)))
            await asyncio.sleep(2)
            self.current_track = await self.interaction.followup.send(embed=embed)
            # try:
            #     await delete_songs()
            # except:
            #     pass

            await self.play_next.wait()


class Music(commands.Cog, name='Music', description="play, queue, skip, pause, resume, skipto, dequeue, stop"):

    def __init__(self, client):

        self.client = client
        self.streamers = {}

    def get_streamer(self, interaction):
        server = interaction.guild
        try:
            streamer = self.streamers[server.id]
        except Exception as e:
            streamer = MusicStreamer(interaction)
            self.streamers[server.id] = streamer

        return streamer

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        voice_state = member.guild.voice_client
        if voice_state is None:
            # Exiting if the bot it's not connected to a voice channel
            return

        if len(voice_state.channel.members) == 1:
            await voice_state.disconnect()
            try:
                await delete_songs(member.guild.id)
            except:
                pass
            server = member.guild
            if server.id in self.streamers:
                del self.streamers[server.id]

    @app_commands.command(name='move', description=f'Move to user voice channel.')
    @app_commands.guild_only()
    async def move(self, interaction: discord.Interaction) -> None:
        # if ctx.guild is None:
        #     await ctx.send("This isn't available in DMs")
        #     return
        if interaction.user.voice is None:
            await interaction.response.send_message(f"Connect to a voice channel first")
            return
        else:
            vchannel = interaction.user.voice.channel

        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)

        if voice is None:
            await interaction.response.send_message(
                f"Joining {interaction.user.mention} in {interaction.user.voice.channel}")
            await vchannel.connect()
        else:
            if interaction.client in vchannel.members:
                await interaction.response.send_message(
                    f"I'm already connected to your channel {interaction.user.mention}. ```/stop``` me first")
                return
            else:
                await interaction.response.send_message(
                    f"Moving to {interaction.user.voice.channel} with {interaction.user}")
                await vchannel.connect()

    ##TODO Playsingle
    @app_commands.command(name='playsingle', description='Play a track without using the queue')
    @app_commands.guild_only()
    @app_commands.describe(track="Song name or link (youtube/soundcloud)")
    async def playsingle(self, interaction: discord.Interaction, track: str) -> None:
        # if ctx.guild is None:
        #     await ctx.send("This isn't available in DMs")
        #     return

        # if args == "":
        #     await ctx.send(
        #         f"Play/Add what?\nTry ```{prefix}play https://www.youtube.com/watch?v=dQw4w9WgXcQ``` or ```{prefix}add ncs```")
        #     return
        responded = False
        if interaction.user.voice is None:
            await interaction.response.send_message(f"{interaction.user.mention}\nConnect to a voice channel first")
            return
        else:
            vchannel = interaction.user.voice.channel

        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)

        if voice is None:
            await interaction.response.send_message(
                f"Joining {interaction.user.mention} in {interaction.user.voice.channel}")
            await vchannel.connect()
            responded = True
        else:
            if interaction.client.user not in vchannel.members:
                await interaction.response.send_message(f"I'm already playing in {vchannel}. Use /move first")
                return
        # if not args:
        #     await interaction.response.send_message(
        #         f"Play what?\nTry ```{prefix}playsingle https://www.youtube.com/watch?v=dQw4w9WgXcQ``` or ```{prefix}playsingle ncs```")
        #     return

        server = interaction.guild
        vc = server.voice_client

        if not await is_link(track):
            if responded:
                getting_message = await interaction.followup.send(
                    f"{interaction.user.mention} " + "\n" + f"Tryna find {track}...")
            else:
                getting_message = await interaction.response.send_message(
                    f"{interaction.user.mention} " + "\n" + f"Tryna find {track}...")
            track = await search_youtube(track)
        else:
            if responded:
                getting_message = await interaction.followup.send(
                    f"{interaction.user.mention} " + "\n" + f"Getting this link <{track}>...")
            else:
                getting_message = await interaction.response.send_message(
                    f"{interaction.user.mention} " + "\n" + f"Getting this link <{track}>...")
        async with interaction.channel.typing():
            vc.stop()
            streamer = await YTDLSource.from_url(url=track, loop=self.client.loop, server_id=interaction.guild.id)
            self.streamers[server.id] = streamer
            vc.play(streamer, after=lambda e: print(":<"))  # self.playnext(ctx))

        embed = discord.Embed(title=f"{streamer.title}", url=f"{streamer.web_url}",
                              description=f"Playing in {interaction.user.voice.channel}",
                              color=await color())
        embed.set_author(name=f"Now Playing for {interaction.user}",
                         icon_url=interaction.user.display_avatar)
        embed.set_thumbnail(url=f"https://i.ytimg.com/vi_webp/{streamer.id}/maxresdefault.webp")
        embed.add_field(name='Duration', value=str(datetime.timedelta(seconds=streamer.duration)))
        await interaction.followup.send(embed=embed)
        await getting_message.delete()
        await asyncio.sleep(5)
        try:
            await delete_songs(interaction.guild.id)
        except:
            pass

    ##TODO Next
    @app_commands.command(name='next', description='Play next track in the playlist')
    @app_commands.guild_only()
    async def skip(self, interaction: discord.Interaction) -> None:

        # if ctx.guild is None:
        #     await ctx.send("This isn't available in DMs")
        #     return

        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        server = interaction.guild

        if voice is None:
            await interaction.response.send_message(
                f"{interaction.user.mention} I'm not currently playing anything.\nUse ```/play``` first")
            return

        streamer = self.get_streamer(interaction)
        if not streamer.queue._queue:
            await interaction.response.send_message("Reached end of queue")
            vc = server.voice_client
            if vc.is_playing():
                vc.stop()
                if server.id in self.streamers:
                    del self.streamers[server.id]
            return

        vc = server.voice_client
        if vc.is_playing():
            await interaction.response.send_message("Skipping to next song")
            message = await interaction.original_response()
            await message.delete(delay=2)
            vc.stop()
            return

    @app_commands.command(name='skipto', description="Skip to a specific song in the playlist")
    @app_commands.guild_only()
    @app_commands.describe(number="Queue number (use /queue)")
    async def skipto(self, interaction: discord.Interaction, number: str) -> None:
        # if ctx.guild is None:
        #     await ctx.send("This isn't available in DMs")
        #     return
        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice is None:
            await interaction.response.send_message("Not currently connected to/playing anything")
            return

        streamer = self.get_streamer(interaction)
        server = interaction.guild
        if not streamer.queue._queue:
            await interaction.response.send_message("There's nothing in the queue")
            return

        # num = int(num) - 1
        # if num <= -1:
        #     await ctx.send(f"Gimme a track number. Get the playlist with ```{prefix}queue```")
        #     return
        try:
            number = int(number)
        except:
            await interaction.response.send_message("Invalid Entry")
            return
        try:
            for _ in range(number - 1):
                del streamer.queue._queue[0]

            embed_queue = discord.Embed(title='Skipping to', color=await color())
            embed_queue.add_field(name=f'Track {number}', value=streamer.queue._queue[0].title, inline=False)
            await interaction.response.send_message(embed=embed_queue)
            message = await interaction.original_response()
            await message.delete(delay=3)
            vc = server.voice_client

            if vc.is_playing():
                vc.stop()
                return


        except:
            await interaction.response.send_message("You provided a bad playlist index")

    @app_commands.command(name='play', description='Either plays a given song or adds one to the playlist')
    @app_commands.guild_only()
    @app_commands.describe(track="Song name or link (youtube/soundcloud)")
    async def play(self, interaction: discord.Interaction, track: str) -> None:
        # if ctx.guild is None:
        #     await ctx.send("This isn't available in DMs")
        #     return
        # if args == "":
        #     await ctx.send(
        #         f"Play/Add what?\nTry ```{prefix}play https://www.youtube.com/watch?v=dQw4w9WgXcQ``` or ```{prefix}add ncs```")
        #     return
        responded = False
        if interaction.user.voice is None:
            await interaction.response.send_message(f"{interaction.user.mention}\nConnect to a voice channel first")
            return
        else:
            vchannel = interaction.user.voice.channel

        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)

        if voice is None:
            await interaction.response.send_message(
                f"Joining {interaction.user.mention} in {interaction.user.voice.channel}")
            await vchannel.connect()
            responded = True
        else:
            if interaction.client.user not in vchannel.members:
                await interaction.response.send_message(f"I'm already playing in {vchannel}. Use /move first")
                return

        streamer = self.get_streamer(interaction)
        server = interaction.guild
        vc = server.voice_client

        if not streamer.queue._queue:
            send_embed = False
        else:
            send_embed = True
        if not send_embed and vc.is_playing():
            send_embed = True

        if not await is_link(track):
            if responded:
                getting_message = await interaction.followup.send(
                    f"{interaction.user.mention} " + "\n" + f"Tryna find {track}...")
            else:
                getting_message = await interaction.response.send_message(
                    f"{interaction.user.mention} " + "\n" + f"Tryna find {track}...")
            track = await search_youtube(track)
            source = await YTDLSource.from_url(url=track, loop=self.client.loop, server_id=interaction.guild.id)
            await streamer.queue.put(source)
        else:
            if responded:
                getting_message = await interaction.followup.send(
                    f"{interaction.user.mention} " + "\n" + f"Getting this link <{track}>...")
            else:
                getting_message = await interaction.response.send_message(
                    f"{interaction.user.mention} " + "\n" + f"Getting this link <{track}>...")
            source = await YTDLSource.from_url(url=track, loop=self.client.loop, server_id=interaction.guild.id)
            await streamer.queue.put(source)

        if send_embed:
            embed = discord.Embed(title=f"{source.title}", url=f"{source.web_url}",
                                  description=f"{source.description}",
                                  color=await color())
            embed.set_author(name=f"Added to playlist by {interaction.user}",
                             icon_url=interaction.user.display_avatar)
            embed.set_thumbnail(url=f"https://i.ytimg.com/vi_webp/{source.id}/maxresdefault.webp")
            embed.add_field(name='Duration', value=str(datetime.timedelta(seconds=source.duration)))
            embed.add_field(name='Help?', value=f"Use /queue to see entire playlist")

            await interaction.followup.send(embed=embed)
        await getting_message.delete()

    @app_commands.command(name='dequeue', description='This command removes a track from the queue')
    @app_commands.guild_only()
    @app_commands.describe(number="Queue number (use /queue)")
    async def dequeue(self, interaction: discord.Interaction, number: str = "-1") -> None:
        # if ctx.guild is None:
        #     await ctx.send("This isn't available in DMs")
        #     return
        try:
            number = int(number)
        except:
            await interaction.response.send_message("Enter a number")
            return

        streamer = self.get_streamer(interaction)
        server = interaction.guild
        if not streamer.queue._queue:
            await interaction.response.send_message("Queue is empty already")
            return
        if number <= -1:
            for _ in range(len(streamer.queue._queue)):
                del streamer.queue._queue[0]
            await interaction.response.send_message("The queue has been emptied")
            return
        number = number - 1

        try:
            del streamer.queue._queue[number]
            embed_queue = discord.Embed(title='Current queue', color=await color())

            for num, song in enumerate(streamer.queue._queue):
                embed_queue.add_field(name=f'Track {num + 1}', value=song.title, inline=False)
            await interaction.response.send_message(embed=embed_queue)
            return
        except:
            await interaction.response.send_message("You provided a bad queue index")
            return

    @app_commands.command(name='queue', description='This command returns the tracks in the playlist')
    @app_commands.guild_only()
    async def queue(self, interaction: discord.Interaction) -> None:
        streamer = self.get_streamer(interaction)
        if streamer.queue._queue:
            embed_queue = discord.Embed(title='Current queue', color=await color())
            for num, song in enumerate(streamer.queue._queue):
                embed_queue.add_field(name=f'Track {num + 1}', value=song.title, inline=False)
            await interaction.response.send_message(embed=embed_queue)
        else:
            await interaction.response.send_message("Your queue is empty")

    ##TODO Stop
    @app_commands.command(name='stop', description='Stops playback, clears playlist and leaves the voice channel')
    @app_commands.guild_only()
    async def stop(self, interaction: discord.Interaction) -> None:

        # if ctx.guild is None:
        #     await ctx.send("This isn't available in DMs")
        #     return
        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice is None:
            await interaction.response.send_message("But I no start :<")
            return
        vchannel = interaction.guild.voice_client
        await interaction.response.send_message("Kbye")
        await vchannel.disconnect()
        try:
            await delete_songs(interaction.guild.id)
        except:
            pass
        server = interaction.guild
        if server.id in self.streamers:
            del self.streamers[server.id]

    ##TODO Pause
    @app_commands.command(name='pause', description='Pause currently playing track')
    @app_commands.guild_only()
    async def pause(self, interaction: discord.Interaction) -> None:
        # if ctx.guild is None:
        #     await ctx.send("This isn't available in DMs")
        #     return
        if interaction.guild.voice_client:
            if interaction.guild.voice_client.is_playing():
                await interaction.response.send_message("Music Paused")
                interaction.guild.voice_client.pause()
            else:
                await interaction.response.send_message("Already paused")
        else:
            await interaction.response.send_message("Not currently playing")

    ##TODO Resume
    @app_commands.command(name='resume', description='Resume currently playing track')
    @app_commands.guild_only()
    async def resume(self, interaction: discord.Interaction) -> None:
        # if ctx.guild is None:
        #     await ctx.send("This isn't available in DMs")
        #     return
        if interaction.guild.voice_client:
            if not interaction.guild.voice_client.is_playing():
                await interaction.response.send_message(
                    "Music Resumed (May not play anything if there's nothing paused)")
                interaction.guild.voice_client.resume()
            else:
                await interaction.response.send_message("Already playing")
        else:
            await interaction.response.send_message("Not currently playing")


async def setup(client):
    await client.add_cog(Music(client))
