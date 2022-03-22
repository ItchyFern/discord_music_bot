from multiprocessing import Process, Manager
import discord
from discord.ext import commands
import youtube_dl
import asyncio
from requests import get


FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

class music(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = {}
        self.stopped = {}
        

    @commands.command(aliases=['j'])
    async def join(self, ctx):
        # if the author of the command is not in a voice channel
        if ctx.author.voice is None:
            # let them know they aren't in a voice channel
            await ctx.send("You're not in a voice channel")
        voice_channel = ctx.author.voice.channel
        # if the bot is not in a voice channel
        if ctx.voice_client is None:
            # wait for it to join a channel
            await voice_channel.connect()
        # if the bot is in a voice channel but its the wrong channel
        else:
            # wait for the bot to move to the right channel
            await ctx.voice_client.move_to(voice_channel)

    @commands.command(aliases=['d', 'l', 'leave'])
    async def disconnect(self, ctx):
        # inform the user of the action
        await ctx.send("Disconnecting now, I will miss you!")
        # wait for the bot to leave the voice channel its in
        # delete queue
        self.queue[ctx.message.guild.id] = []

        # set stopped variable
        self.stopped[ctx.message.guild.id] = True
        # wait for the bot to leave the voice channel its in
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()

    @commands.command(aliases=['p'])
    async def play(self, ctx, *args):

    
        print(args)
        if not len(args) > 0:
            await ctx.send("You need to tell me what to play!")
            return
        # if bot is not connected
        if ctx.voice_client is None:
            await ctx.send("I'm not connected to a voice channel!")
            return
        # if the bot is currently playing a song, stop the song
        # ctx.voice_client.stop()

        
        YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True', 'ratelimit': "100K"}          

        #declare voice chat
        vc = ctx.voice_client

        # connect the args
        search = " ".join(args)

        # Send message to inform users that bot is looking for music
        bot_msg = await ctx.send(f"Searching for \"{search}\"")

        # get information for stream
        manager = Manager()
        info_dict = manager.dict()
        p = Process(target=get_yt_info, args=(YDL_OPTIONS, search, info_dict, ))
        p.start()
        p.join()
        #if the length of the queue is not greater than 0 build an empty queue
        if not len(self.queue.get(ctx.message.guild.id, [])) > 0:
            self.queue[ctx.message.guild.id] = []
        # add the new song to the queue
        print("After join\n", info_dict)
        self.queue[ctx.message.guild.id].append(info_dict)

        await bot_msg.edit(content=f"Successfully added {info_dict['title']} to the queue!")

        # send the stream of audio directly through the voice chat
        # lambda function to add in the play_next function
        if not vc.is_playing():
            print(f'Attempting to play: {info_dict["title"]}')
            source = await discord.FFmpegOpusAudio.from_probe(self.queue[ctx.message.guild.id][0]["url"], **FFMPEG_OPTIONS)
            vc.play(source=source, after=lambda e: asyncio.run(self.play_next(ctx)))           

    @commands.command(aliases=['s'])
    async def stop(self, ctx):
        # delete queue
        self.queue[ctx.message.guild.id] = []
        # set stopped variable
        self.stopped[ctx.message.guild.id] = True
        # inform the user of the action
        await ctx.send("Stopping music!")
        # wait for the bot to leave the voice channel its in
        #await ctx.voice_client.stop()
        ctx.voice_client.stop()
        
    
    @commands.command()
    async def pause(self, ctx):
        # inform the user of the action
        await ctx.send("Pausing music!")
        # wait for the bot to leave the voice channel its in
        # await ctx.voice_client.pause()
        ctx.voice_client.pause()

    @commands.command(aliases=['r'])
    async def resume(self, ctx):
         # inform the user of the action
        ctx.send("Resuming music!")
        # wait for the bot to leave the voice channel its in
        # await ctx.voice_client.resume()
        ctx.voice_client.resume()
       
    
    @commands.command()
    async def skip(self, ctx):
        if len(self.queue.get(ctx.message.guild.id, [])) > 1:
            await ctx.send("Playing next song.")
            #await ctx.voice_client.stop()
        else:
            await ctx.send("No more songs in the queue.")
        ctx.voice_client.stop()

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        # initialize return string that will hold what the bot will reply with
        if len(self.queue.get(ctx.message.guild.id, [])) > 0:
            
            embed = embed_builder(self.queue[ctx.message.guild.id])
            
            await ctx.send(embed=embed)
        else:
            ret = "There's nothing in my queue right now!"
            
            await ctx.send(ret)

    # UTILITY FUNCTION FOR PLAYING NEXT SONG
    async def play_next(self, ctx):
        vc = ctx.voice_client
        if len(self.queue.get(ctx.message.guild.id, [])) >= 2:
            del self.queue[ctx.message.guild.id][0]
            print(f'Attempting to play next: {self.queue[ctx.message.guild.id][0]["title"]}')
            source = await discord.FFmpegOpusAudio.from_probe(self.queue[ctx.message.guild.id][0]["url"], **FFMPEG_OPTIONS)
            if vc.is_playing():
                vc.stop()
            vc.play(source=source, after=lambda e: asyncio.run(self.play_next(ctx)))
        else:
            #if it wasn't manually stopped
            if not self.stopped.get(ctx.message.guild.id, False):
                asyncio.sleep(90) #wait 1 minute and 30 seconds
                if not vc.is_playing():
                    asyncio.run_coroutine_threadsafe(vc.disconnect(), self.client.loop)
                    asyncio.run_coroutine_threadsafe(ctx.send("No more songs in queue."), self.client.loop)
            #if it was manually stopped, reset the stopped variable
            else:
                self.stopped[ctx.message.guild.id] = False

def embed_builder(queue):
    embed = discord.Embed()
    embed.title = "Music Player Queue"
    for i, item in enumerate(queue):
        embed.add_field(name=f'{i}. {item["title"]}', value=f"https://www.youtube.com/watch?v={item['id']}", inline=False)
    return embed

def get_yt_info(YDL_OPTIONS, search, info_dict):
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        # search 
        try:
            get(search) 
        except:
            info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
        else:
            info = ydl.extract_info(search, download=False)
    
        
        # print("\n\n\n\n", info, "\n\n\n\n")
        url2 = info['formats'][0]['url']

        # clear youtube cache
        ydl.cache.remove()
    
    info_dict["url"] = url2 
    info_dict["title"] = info["title"]
    info_dict["id"] = info["id"]
    print(info_dict)



def setup(client):
    client.add_cog(music(client))
