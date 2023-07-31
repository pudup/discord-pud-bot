import asyncio
import os
import discord
import yt_dlp
from discord.ext import commands
from discord import app_commands
import aiohttp
from youtube_search import YoutubeSearch
import datetime
from utils.utils import color
import azapi


# import itertools
# from async_timeout import timeout
# import json


# TODO: Add docstrings and comments to this cog
# This COG currently has no comments or docstrings and might be difficult to read through. Will be added later

# HELPER FUNCTIONS

async def delete_songs(server_id):
    """Deletes everything in the 'songs' folder. Keeps storage space down. Songs are re-downloaded when needed"""
    files = os.listdir(f"songs/{server_id}")
    for file in files:
        os.remove(f"songs/{server_id}/" + file)
    os.rmdir(f"songs/{server_id}/")


async def search_youtube(query):
    """Returns the url to the first video in a YouTube search query"""
    results = YoutubeSearch(query, max_results=1).to_dict()
    return f"https://www.youtube.com/{results[0]['url_suffix']}"


async def is_link(query):
    """
    Checks if a given string is an http(s) link or not
    Used by the play function to check if given input is a song name or a direct link
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(query) as response:
                if response:
                    return True
    except:
        return False


async def get_lyrics(title, artist):
    """
    azapi api for lyrics
    Returns requests lyrics, title and artist in that order
    """
    lyrics_api = azapi.AZlyrics('google', accuracy=0.5)

    if artist != "":
        lyrics_api.artist = artist
    lyrics_api.title = title

    lyrics_api.getLyrics(save=False, ext='lrc')

    return lyrics_api.lyrics, lyrics_api.title, lyrics_api.artist


# END OF HELPERS

# YOUTUBE FUNCTIONS ###

# Most of the functions here are just copied and pasted from ytdl docs and don't really need modifications
# I've written comments for whatever modifications I've made

yt_dlp.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    # 'outtmpl': 'songs/%(extractor)s-%(id)s-%(title)s.%(ext)s', # I've removed this part so that I can specify the
    # location
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

        # Here is why I removed the outtmpl format option
        # This helps separate the song folder for different servers running the bot at the same time
        # Keeps the bot from deleting the song folder of another server
        ytdl.params['outtmpl'] = f'songs/{server_id}/%(title)s.%(ext)s'
        with yt_dlp.YoutubeDL(ytdl_format_options) as ydl:
            data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=not stream))
            # Not sure why I need to make a different yt_dlp object here, but it doesn't work without it

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


# END OF YOUTUBE #


class MusicStreamer:
    """
    The object that is responsible to actually playing the music on a voice channel
    It also handles queues
    Not very complicated
    """

    def __init__(self, interaction):

        self.interaction = interaction

        self.queue = asyncio.Queue()  # The playlist queue
        self.play_next = asyncio.Event()

        self.current_track = None

        self.task_loop = self.interaction.client.loop.create_task(
            self.main_streamer_loop())  # The song streaming task loop

    async def cleanup(self):
        self.play_next.clear()
        self.task_loop.cancel()
        while not self.queue.empty():
            self.queue.get_nowait()
            self.queue.task_done()

    async def audio_player_task(self):
        """
        Gets the next song from the queue and plays it
        Waits for the next in the queue after finishing the track
        """
        while True:
            self.play_next.clear()
            current = await self.queue.get()
            current.start()
            await self.play_next.wait()

    async def main_streamer_loop(self):
        """
        The main loop function
        Handles playing the current song and moving to the next after it ends

        """
        await self.interaction.client.wait_until_ready()
        while not self.interaction.client.is_closed():
            self.play_next.clear()

            # This part is commented out because it was a bit buggy
            # It was used as a timeout for the bot if it was playing nothing for 60 seconds
            # It was written without much thought and should prolly be rewritten so that's what you should do
            # Don't use it
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

            # Commented out because it can sometimes delete songs that are being downloaded. Written naively anwyay.
            # try:
            #     await delete_songs()
            # except:
            #     pass

            await self.play_next.wait()


class Music(commands.Cog, name='Music',
            description="play, queue, next, pause, resume, skipto, dequeue, stop, playsingle, lyrics"):
    """
    A cog for the music functionality in voice channels
    Works with YouTube and SoundCloud for now
    """

    def __init__(self, client):

        self.client = client
        self.streamers = {}  # To keep track of different streamer objects per server. Isn't strictly needed afaik.

    def get_streamer(self, interaction):
        """
        Returns the streamer object for the current server
        Creates one if it doesn't exist and adds it to the streamers hashmap
        """
        server = interaction.guild
        try:
            streamer = self.streamers[server.id]
        except Exception:
            streamer = MusicStreamer(interaction)
            self.streamers[server.id] = streamer

        return streamer

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        Constantly monitors the voice channel that it is in and leaves the channel if it is alone
        """
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
                await self.streamers[server.id].cleanup()
                del self.streamers[server.id]

    @app_commands.command(name='move', description=f'Move to user voice channel.')
    @app_commands.guild_only()
    async def move(self, interaction: discord.Interaction) -> None:
        """
        A command to get the bot to move to the voice channel that you are in
        Useful if the bot is already playing in another voice channel but otherwise not required
        """
        await interaction.response.defer(thinking=True)
        if interaction.user.voice is None:
            await interaction.followup.send(f"Connect to a voice channel first")
            return
        else:
            vchannel = interaction.user.voice.channel

        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)

        if voice is None:
            await interaction.followup.send(
                f"Joining {interaction.user.mention} in {interaction.user.voice.channel}")
            await vchannel.connect()
        else:
            if interaction.client in vchannel.members:
                await interaction.followup.send(
                    f"I'm already connected to your channel {interaction.user.mention}. ```/stop``` me first")
                return
            else:
                await interaction.followup.send(
                    f"Moving to {interaction.user.voice.channel} with {interaction.user}")
                await vchannel.connect()

    @app_commands.command(name='playsingle', description='Play a track without using the queue')
    @app_commands.guild_only()
    @app_commands.describe(track="Song name or link (youtube/soundcloud)")
    async def playsingle(self, interaction: discord.Interaction, track: str) -> None:
        """
        A command to play a single link or query without using the playlist queue
        """
        responded = False
        await interaction.response.defer(thinking=True)
        if interaction.user.voice is None:
            await interaction.followup.send(f"{interaction.user.mention}\nConnect to a voice channel first")
            return
        else:
            vchannel = interaction.user.voice.channel

        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)

        if voice is None:
            await interaction.followup.send(
                f"Joining {interaction.user.mention} in {interaction.user.voice.channel}")
            await vchannel.connect()
            responded = True
        else:
            if interaction.client.user not in vchannel.members:
                await interaction.followup(f"I'm already playing in {vchannel}. Use /move first")
                return

        server = interaction.guild
        vc = server.voice_client

        if not await is_link(track):
            if responded:
                getting_message = await interaction.followup.send(
                    f"{interaction.user.mention} " + "\n" + f"Tryna find {track}...")
            else:
                getting_message = await interaction.followup.send(
                    f"{interaction.user.mention} " + "\n" + f"Tryna find {track}...")
            track = await search_youtube(track)
        else:
            if responded:
                getting_message = await interaction.followup.send(
                    f"{interaction.user.mention} " + "\n" + f"Getting this link <{track}>...")
            else:
                getting_message = await interaction.followup.send(
                    f"{interaction.user.mention} " + "\n" + f"Getting this link <{track}>...")

        vc.stop()
        streamer = await YTDLSource.from_url(url=track, loop=self.client.loop, server_id=interaction.guild.id)
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
        await asyncio.sleep(int(streamer.duration))
        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice is None:
            return
        vchannel = interaction.guild.voice_client
        if not interaction.guild.voice_client.is_playing():
            await vchannel.disconnect()
            try:
                await delete_songs(interaction.guild.id)
            except:
                pass
            server = interaction.guild
            if server.id in self.streamers:
                await self.streamers[server.id].cleanup()
                del self.streamers[server.id]
        else:
            return

    @app_commands.command(name='next', description='Play next track in the playlist')
    @app_commands.guild_only()
    async def skip(self, interaction: discord.Interaction) -> None:
        """
        Skips to the next song in the playlist
        All it really does is end the current track and the streamer loop handles the rest
        """
        await interaction.response.defer(thinking=True)
        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        server = interaction.guild

        if voice is None:
            await interaction.followup.send(
                f"{interaction.user.mention} I'm not currently playing anything.\nUse ```/play``` first")
            return

        streamer = self.get_streamer(interaction)
        if not streamer.queue._queue:
            await interaction.followup.send("Reached end of queue")
            vc = server.voice_client
            if vc.is_playing():
                vc.stop()
                if server.id in self.streamers:
                    await self.streamers[server.id].cleanup()
                    del self.streamers[server.id]
            return

        vc = server.voice_client
        if vc.is_playing():
            await interaction.followup.send("Skipping to next song")
            vc.stop()
            return

    @app_commands.command(name='skipto', description="Skip to a specific song in the playlist")
    @app_commands.guild_only()
    @app_commands.describe(number="Queue number (use /queue)")
    async def skipto(self, interaction: discord.Interaction, number: str) -> None:
        """
        Skips to a specific track in the playlist
        """
        await interaction.response.defer(thinking=True)
        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice is None:
            await interaction.followup.send("Not currently connected to/playing anything")
            return

        streamer = self.get_streamer(interaction)
        server = interaction.guild
        if not streamer.queue._queue:
            await interaction.followup.send("There's nothing in the queue")
            return

        try:
            number = int(number)
        except:
            await interaction.followup.send("Invalid Entry")
            return
        try:
            for _ in range(number - 1):
                del streamer.queue._queue[0]

            embed_queue = discord.Embed(title='Skipping to', color=await color())
            embed_queue.add_field(name=f'Track {number}', value=streamer.queue._queue[0].title, inline=False)
            await interaction.followup.send(embed=embed_queue)
            vc = server.voice_client

            if vc.is_playing():
                vc.stop()
                return

        except:
            await interaction.followup.send("You provided a bad playlist index")

    @app_commands.command(name='play', description='Either plays a given song or adds one to the playlist')
    @app_commands.guild_only()
    @app_commands.describe(track="Song name or link (youtube/soundcloud)")
    async def play(self, interaction: discord.Interaction, track: str) -> None:
        """
        The main music command
        Executes all the relevant functions for searching for the track, downloading it and starting the streamer loop
        If a track is already playing, it adds the new one to the playlist instead
        """
        await interaction.response.defer(thinking=True)
        if interaction.user.voice is None:
            await interaction.followup.send(f"{interaction.user.mention}\nConnect to a voice channel first")
            return
        else:
            vchannel = interaction.user.voice.channel

        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)

        if voice is None:
            await interaction.followup.send(
                f"Joining {interaction.user.mention} in {interaction.user.voice.channel}")
            await vchannel.connect()
        else:
            if interaction.client.user not in vchannel.members:
                await interaction.followup.send(f"I'm already playing in {vchannel}. Use /move first")
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
            await interaction.followup.send(
                f"{interaction.user.mention} " + "\n" + f"Tryna find {track}...")
            track = await search_youtube(track)
            source = await YTDLSource.from_url(url=track, loop=self.client.loop, server_id=interaction.guild.id)
            await streamer.queue.put(source)
        else:
            await interaction.followup.send(
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

    @app_commands.command(name='dequeue', description='This command removes a track from the queue')
    @app_commands.guild_only()
    @app_commands.describe(number="Queue number (use /queue)")
    async def dequeue(self, interaction: discord.Interaction, number: str = "-1") -> None:
        """
        Removes a specific track from the queue
        It clears the entire queue if a value isn't provided
        """
        await interaction.response.defer(thinking=True)
        try:
            number = int(number)
        except:
            await interaction.followup.send("Enter a number")
            return

        streamer = self.get_streamer(interaction)
        if not streamer.queue._queue:
            await interaction.followup.send("Queue is empty already")
            return
        if number <= -1:
            for _ in range(len(streamer.queue._queue)):
                del streamer.queue._queue[0]
            await interaction.followup.send("The queue has been emptied")
            return
        number = number - 1

        try:
            del streamer.queue._queue[number]
            embed_queue = discord.Embed(title='Current queue', color=await color())

            for num, song in enumerate(streamer.queue._queue):
                embed_queue.add_field(name=f'Track {num + 1}', value=song.title, inline=False)
            await interaction.followup.send(embed=embed_queue)
            return
        except:
            await interaction.followup.send("You provided a bad queue index")
            return

    @app_commands.command(name='queue', description='This command returns the tracks in the playlist')
    @app_commands.guild_only()
    async def queue(self, interaction: discord.Interaction) -> None:
        """
        Prints out the entire queue in a nice embed to whoever requests it
        """
        await interaction.response.defer(thinking=True)
        streamer = self.get_streamer(interaction)
        if streamer.queue._queue:
            embed_queue = discord.Embed(title='Current queue', color=await color())
            for num, song in enumerate(streamer.queue._queue):
                embed_queue.add_field(name=f'Track {num + 1}', value=song.title, inline=False)
            await interaction.followup.send(embed=embed_queue)
        else:
            await interaction.followup.send("Your queue is empty")

    @app_commands.command(name='stop', description='Stops playback, clears playlist and leaves the voice channel')
    @app_commands.guild_only()
    async def stop(self, interaction: discord.Interaction) -> None:
        """
        Stops the streamer loop, destroys it, leaves the channel and deletes the song folder
        """
        await interaction.response.defer(thinking=True)
        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice is None:
            await interaction.followup.send("But I no start :<")
            return
        vchannel = interaction.guild.voice_client
        await interaction.followup.send("Kbye")
        await vchannel.disconnect()
        try:
            await delete_songs(interaction.guild.id)
        except:
            pass
        server = interaction.guild
        if server.id in self.streamers:
            await self.streamers[server.id].cleanup()
            del self.streamers[server.id]

    @app_commands.command(name='pause', description='Pause currently playing track')
    @app_commands.guild_only()
    async def pause(self, interaction: discord.Interaction) -> None:
        """
        Pauses the voice loop using the inbuilt method
        """
        await interaction.response.defer(thinking=True)
        if interaction.guild.voice_client:
            if interaction.guild.voice_client.is_playing():
                await interaction.followup.send("Music Paused")
                interaction.guild.voice_client.pause()
            else:
                await interaction.followup.send("Already paused")
        else:
            await interaction.followup.send("Not currently playing")

    @app_commands.command(name='resume', description='Resume currently playing track')
    @app_commands.guild_only()
    async def resume(self, interaction: discord.Interaction) -> None:
        """
        Resumes paused audio using the inbuilt method.
        Doesn't have a check for if anything is paused so does nothing if music isn't paused
        """
        await interaction.response.defer(thinking=True)
        if interaction.guild.voice_client:
            if not interaction.guild.voice_client.is_playing():
                await interaction.followup.send(
                    "Music Resumed (May not play anything if there's nothing paused)")
                interaction.guild.voice_client.resume()
            else:
                await interaction.followup.send("Already playing")
        else:
            await interaction.followup.send("Not currently playing")

    @app_commands.command(name='lyrics', description='Get the lyrics to a song')
    @app_commands.describe(title="Song name", artist="Artist name")
    async def lyrics(self, interaction: discord.Interaction, title: str, artist: str = "") -> None:
        """
        Gets the lyrics to requested song using azapi
        """
        await interaction.response.defer(thinking=True)
        # This response is here to avoid the discord slash command 3 second timeout.

        # Getting lyrics
        song_lyrics, song_title, song_artist = await get_lyrics(title, artist)

        # Building the embed
        embed = discord.Embed(color=await color())
        embed.set_author(name=f"Lyrics for {interaction.user}", icon_url=interaction.user.display_avatar)
        embed.title(f"{song_title} by {song_artist}")
        embed.description(song_lyrics)

        # Sending the embed
        await interaction.followup.send(embed=embed)

async def setup(client):  # Required function to enable this cog
    await client.add_cog(Music(client))
