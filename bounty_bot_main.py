
import discord
import asyncio
import requests
import os
from dotenv import load_dotenv
load_dotenv()

# bottoken = os.getenv('devbot')
bottoken = os.getenv('probot')


def get_bounty_guilds():
    url = os.getenv('devbounties')
    bans = {}
    r = requests.get(url)
    data = r.json()
    for d in data['result']:
        b_guilds = []
        for i in d['banned_guilds']:
            b_guilds.append(i['guild_id'])
        bans[d['bounty']] = b_guilds
    return bans


def post_new_bounty(new_insert):
    url = os.getenv('devnewbounty')
    try:
        r = requests.post(url, json=new_insert)
    except Exception as e:
        print(e)


def update_bounty(update_insert):
    url = os.getenv('devupdatebounty')
    try:
        r = requests.post(url, json=update_insert)

    except Exception as e:
        print(e)


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # create the background task and run it in the background
        self.bg_task = self.loop.create_task(self.update_bounties())

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        game = discord.Game("Hunting Bounties")
        await client.change_presence(activity=game)
        print('------')

    async def update_bounties(self):
        await self.wait_until_ready()
        while not self.is_closed():
            guild_list = []
            async for guild in client.fetch_guilds(limit=150):
                if (guild.name, guild.id) not in guild_list:
                    guild_list.append((guild.name, guild.id))

            for i in guild_list:
                dbbans = get_bounty_guilds()
                guild = client.get_guild(i[1])
                try:
                    bans = await guild.bans()
                    if len(bans) >= 1:
                        for ban in bans:
                            id = str(ban[1].id)
                            banid = dbbans.get(id, None)
                            if banid is None:
                                name = str(ban[1].name)
                                discriminator = str(ban[1].discriminator)
                                bot = str(ban[1].bot)
                                avatarurl = str(ban[1].avatar_url)
                                reason = str(ban[0])
                                new_insert = {"bounty_id": id, "bounty_name": name, "discriminator": discriminator, "bot": bot,
                                              "bounty_avatar": avatarurl, "guild_id": i[1], "guild_name": i[0], "reason": reason}
                                post_new_bounty(new_insert)

                            else:
                                if i[1] not in banid:
                                    update_insert = {
                                        "bounty_id": id, "guild_id": i[1], "guild_name": i[0], "reason": str(ban[0])}

                                    update_bounty(update_insert)
                except Exception as e:
                    print(e)

            await asyncio.sleep(60)  # task runs every 60 seconds


client = MyClient()
client.run(bottoken)

# TODO:
