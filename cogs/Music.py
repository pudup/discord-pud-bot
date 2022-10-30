import asyncio
import os
import discord
import youtube_dl
from discord.ext import commands
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

youtube_dl.utils.bug_reports_message = lambda: ''

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
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')
        self.id = data.get('id')
        self.duration = data.get('duration')
        self.web_url = data.get('webpage_url')
        self.description = data.get('description')[slice(200)]

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, server_id):
        loop = loop or asyncio.get_event_loop()
        ytdl.params['outtmpl'] = f'songs/{server_id}/%(extractor)s-%(id)s-%(title)s.%(ext)s'
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

### END OF YOUTUBE ###


class MusicStreamer:
    def __init__(self, ctx):

        self.ctx = ctx

        self.queue = asyncio.Queue()
        self.play_next = asyncio.Event()

        self.current_track = None

        self.ctx.bot.loop.create_task(self.main_streamer_loop())

    async def audio_player_task(self):
        while True:
            self.play_next.clear()
            current = await self.queue.get()
            current.start()
            await self.play_next.wait()

    def go_next_song(self):
        self.ctx.bot.loop.call_soon_threadsafe(self.play_next.set)

    async def main_streamer_loop(self):
        await self.ctx.bot.wait_until_ready()
        while not self.ctx.bot.is_closed():
            self.play_next.clear()

            # try:
            #     async with timeout(60):
            #         source = await self.queue.get()
            # except asyncio.TimeoutError:
            #     await self.ctx.send("I ran out of time, I'm outta here")
            #     await self.ctx.cog.stop(self.ctx)
            #     return

            source = await self.queue.get()

            server = self.ctx.message.guild
            vc = server.voice_client
            try:
                vc.stop()
            except:
                pass
            vc.play(source, after=lambda _: self.ctx.bot.loop.call_soon_threadsafe(self.play_next.set))
            embed = discord.Embed(title=f"{source.title}", url=f"{source.web_url}",
                                  description=f"Playing in {self.ctx.voice_client.channel}",
                                  color=await color())
            embed.set_author(name=f"Now Playing for {self.ctx.message.author}",
                             icon_url=self.ctx.author.avatar.url)
            embed.set_thumbnail(url=f"https://i.ytimg.com/vi_webp/{source.id}/maxresdefault.webp")
            embed.add_field(name='Duration', value=str(datetime.timedelta(seconds=source.duration)))
            await asyncio.sleep(2)
            self.current_track = await self.ctx.send(embed=embed)
            # try:
            #     await delete_songs()
            # except:
            #     pass


            await self.play_next.wait()


class Music(commands.Cog, name='Music', description="play, queue, skip, pause, resume, skipto, dequeue, stop"):

    def __init__(self, client):

        self.client = client
        self.streamers = {}





    def get_streamer(self, ctx):
        server = ctx.message.guild
        try:
            streamer = self.streamers[server.id]
        except Exception as e:
            streamer = MusicStreamer(ctx)
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


    @commands.command(name='move', help=f'Move to user voice channel.')
    async def move(self, ctx):
        if ctx.guild is None:
            await ctx.send("This isn't available in DMs")
            return
        if ctx.message.author.voice is None:
            await ctx.send(f"{ctx.message.author.mention}\nConnect to a voice channel first")
            return
        else:
            vchannel = ctx.message.author.voice.channel

        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)

        if voice is None:
            await ctx.send(f"Joining {ctx.message.author.mention} in {ctx.message.author.voice.channel}")
            await vchannel.connect()
        else:
            if ctx.bot.user in vchannel.members:
                await ctx.send(
                    f"I'm already connected to your channel {ctx.message.author.mention}. ```{prefix}stop``` me first")
                return
            else:
                await ctx.send(f"Moving to {ctx.message.author.voice.channel} with {ctx.message.author.mention}")
                await ctx.voice_client.move_to(vchannel)




    ##TODO Playsingle
    @commands.command(name='playsingle', help='Play a track without using the queue')
    async def playsingle(self, ctx, *, args=""):
        if ctx.guild is None:
            await ctx.send("This isn't available in DMs")
            return

        if args == "":
            await ctx.send(f"Play/Add what?\nTry ```{prefix}play https://www.youtube.com/watch?v=dQw4w9WgXcQ``` or ```{prefix}add ncs```")
            return

        if ctx.message.author.voice is None:
            await ctx.send(f"{ctx.message.author.mention}\nConnect to a voice channel first")
            return
        else:
            vchannel = ctx.message.author.voice.channel


        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)

        if voice is None:
            await ctx.send(f"Joining {ctx.message.author.mention} in {ctx.message.author.voice.channel}")
            await vchannel.connect()
        else:
            if ctx.bot.user not in vchannel.members:
                await ctx.send(f"I'm already playing in {vchannel}. Use {prefix}move first")
                return
        if not args:
            await ctx.send(f"Play what?\nTry ```{prefix}playsingle https://www.youtube.com/watch?v=dQw4w9WgXcQ``` or ```{prefix}playsingle ncs```")
            return

        server = ctx.message.guild
        vc = server.voice_client


        if not await is_link(args):
            getting_message = await ctx.send(f"{ctx.message.author.mention} " + "\n" + f"Tryna find {args}...")
            args = await search_youtube(args)
        else:
            getting_message = await ctx.send(f"{ctx.message.author.mention} " + "\n" + f"Getting this link <{args}>...")



        async with ctx.typing():
            vc.stop()
            streamer = await YTDLSource.from_url(url=args, loop=self.client.loop, server_id=ctx.guild.id)
            self.streamers[server.id] = streamer
            vc.play(streamer, after=lambda e: print(":<"))#self.playnext(ctx))

        embed = discord.Embed(title=f"{streamer.title}", url=f"{streamer.web_url}",
                              description=f"Playing in {ctx.voice_client.channel}",
                              color=await color())
        embed.set_author(name=f"Now Playing for {ctx.message.author}",
                         icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=f"https://i.ytimg.com/vi_webp/{streamer.id}/maxresdefault.webp")
        embed.add_field(name='Duration', value=str(datetime.timedelta(seconds=streamer.duration)))
        await ctx.send(embed=embed)
        await getting_message.delete()
        await asyncio.sleep(5)
        try:
            await delete_songs(ctx.guild.id)
        except:
            pass




    ##TODO Next
    @commands.command(name='skip', help='Play next track in the playlist')
    async def skip(self, ctx):

        if ctx.guild is None:
            await ctx.send("This isn't available in DMs")
            return

        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        server = ctx.message.guild


        if voice is None:
            await ctx.send(f"{ctx.message.author.mention} I'm not currently playing anything.\nUse ```{prefix}play``` first")
            return

        streamer = self.get_streamer(ctx)
        if not streamer.queue._queue:
            await ctx.send("Reached end of queue")
            vc = server.voice_client
            if vc.is_playing():
                vc.stop()
                if server.id in self.streamers:
                    del self.streamers[server.id]
            return

        vc = server.voice_client
        if vc.is_playing():
            vc.stop()
            return


    @commands.command(name='skipto', brief='This skips to a specific song in the playlist', description="This skips to a specific song in the playlist")
    async def skipto(self, ctx, num=-1):
        if ctx.guild is None:
            await ctx.send("This isn't available in DMs")
            return
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice is None:
            await ctx.send("Not currently connected/playing anything")
            return

        streamer = self.get_streamer(ctx)
        server = ctx.message.guild
        if not streamer.queue._queue:
            await ctx.send("There's nothing in the queue")
            return

        num = int(num) - 1
        if num <= -1:
            await ctx.send(f"Gimme a track number. Get the playlist with ```{prefix}queue```")
            return

        try:
            for _ in range(num):
                del streamer.queue._queue[0]

            embed_queue = discord.Embed(title='Skipping to', color=await color())
            embed_queue.add_field(name=f'Track {num + 1}', value=streamer.queue._queue[0].title, inline=False)
            message = await ctx.send(embed=embed_queue)
            await asyncio.sleep(3)
            await message.delete()
            vc = server.voice_client
            if vc.is_playing():
                vc.stop()
                return


        except:
            await ctx.send("You provided a bad playlist index")



    @commands.command(name='play', help='This command either plays a given song or adds one to the playlist', aliases=['add'])
    async def play(self, ctx, *, args=""):
        if ctx.guild is None:
            await ctx.send("This isn't available in DMs")
            return
        if args == "":
            await ctx.send(f"Play/Add what?\nTry ```{prefix}play https://www.youtube.com/watch?v=dQw4w9WgXcQ``` or ```{prefix}add ncs```")
            return
        if ctx.message.author.voice is None:
            await ctx.send(f"{ctx.message.author.mention}\nConnect to a voice channel first")
            return
        else:
            vchannel = ctx.message.author.voice.channel

        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)

        if voice is None:
            await ctx.send(f"Joining {ctx.message.author.mention} in {ctx.message.author.voice.channel}")
            await vchannel.connect()
        else:
            if ctx.bot.user not in vchannel.members:
                await ctx.send(f"I'm already playing in {vchannel}. Use {prefix}move first")
                return

        streamer = self.get_streamer(ctx)
        server = ctx.message.guild
        vc = server.voice_client

        if not streamer.queue._queue:
            send_embed = False
        else:
            send_embed = True
        if not send_embed and vc.is_playing():
            send_embed = True

        if not await is_link(args):
            getting_message = await ctx.send(f"{ctx.message.author.mention} " + "\n" + f"Tryna find {args}...")
            args = await search_youtube(args)
            source = await YTDLSource.from_url(url=args, loop=self.client.loop, server_id=ctx.guild.id)
            await streamer.queue.put(source)
        else:
            getting_message = await ctx.send(f"{ctx.message.author.mention} " + "\n" + f"Getting this link <{args}>...")
            source = await YTDLSource.from_url(url=args, loop=self.client.loop, server_id=ctx.guild.id)
            await streamer.queue.put(source)


        if send_embed:
            embed = discord.Embed(title=f"{source.title}", url=f"{source.web_url}",
                                  description=f"{source.description}",
                                  color=await color())
            embed.set_author(name=f"Added to playlist by {ctx.message.author}",
                             icon_url=ctx.author.avatar.url)
            embed.set_thumbnail(url=f"https://i.ytimg.com/vi_webp/{source.id}/maxresdefault.webp")
            embed.add_field(name='Duration', value=str(datetime.timedelta(seconds=source.duration)))
            embed.add_field(name='Help?', value=f"Use {prefix}queue to see entire playlist")

            await ctx.send(embed=embed)
        await getting_message.delete()


    @commands.command(name='dequeue', help='This command removes a track from the queue')
    async def dequeue(self, ctx, num=-1):
        if ctx.guild is None:
            await ctx.send("This isn't available in DMs")
            return
        streamer = self.get_streamer(ctx)
        server = ctx.message.guild
        if not streamer.queue._queue:
            await ctx.send("Queue is empty already")
            return
        if num <= -1:
            del streamer.queue._queue
            await ctx.send("The queue has been emptied")
            return
        try:
            num = int(num) - 1
        except:
            await ctx.send("That isn't a number")

        try:
            del streamer.queue._queue[int(num)]
            embed_queue = discord.Embed(title='Current queue', color=await color())

            for num, song in enumerate(streamer.queue._queue):
                embed_queue.add_field(name=f'Track {num + 1}', value=song.title, inline=False)
            await ctx.send(embed=embed_queue)
        except:
            await ctx.send("You provided a bad queue index")

    @commands.command(name='queue', help='This command returns the tracks in the playlist')
    async def queue(self, ctx):
        streamer = self.get_streamer(ctx)
        if streamer.queue._queue:
            embed_queue = discord.Embed(title='Current queue', color=await color())
            for num, song in enumerate(streamer.queue._queue):
                embed_queue.add_field(name=f'Track {num + 1}', value=song.title, inline=False)
            await ctx.send(embed=embed_queue)
        else:
            await ctx.send("Your queue is empty")


    ##TODO Stop
    @commands.command(name='stop', help='Stops playback, clears playlist and leaves the voice channel')
    async def stop(self, ctx):

        if ctx.guild is None:
            await ctx.send("This isn't available in DMs")
            return
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice is None:
            await ctx.send("But I no start :<")
            return
        vchannel = ctx.message.guild.voice_client
        await ctx.send("Kbye")
        await vchannel.disconnect()
        try:
            await delete_songs(ctx.guild.id)
        except:
            pass
        server = ctx.message.guild
        if server.id in self.streamers:
            del self.streamers[server.id]

    ##TODO Pause
    @commands.command(name='pause', help='Pause currently playing track')
    async def pause(self, ctx):
        if ctx.guild is None:
            await ctx.send("This isn't available in DMs")
            return
        if ctx.voice_client:
            if ctx.voice_client.is_playing():
                await ctx.send("Music Paused")
                ctx.voice_client.pause()
            else:
                await ctx.send("Already paused")
        else:
            await ctx.send("Not currently playing")

    ##TODO Resume
    @commands.command(name='resume', help='Resume currently playing track')
    async def resume(self, ctx):
        if ctx.guild is None:
            await ctx.send("This isn't available in DMs")
            return
        if ctx.voice_client:
            if not ctx.voice_client.is_playing():
                await ctx.send("Music Resumed (May not play anything if there's nothing paused)")
                ctx.voice_client.resume()
            else:
                await ctx.send("Already playing")
        else:
            await ctx.send("Not currently playing")


async def setup(client):
    await client.add_cog(Music(client))

