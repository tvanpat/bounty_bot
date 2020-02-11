
import discord
import asyncio
from pymongo import MongoClient
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient import discovery

# Import Creds for DB access
class Creds():
    def __init__(self,user, password, database, gsheet, bottoken):
        self.user= user
        self.password = password
        self.database = database
        self.gsheet = gsheet
        self.bottoken = bottoken


def load_creds():
    with open('creds.json') as json_file:
        data = json.load(json_file)
    cred = Creds(data['user'], data['password'], data['database'], data['gsheet'], data['bottoken'])
    return cred

#
def bounties_insert_new(new_bounties):
    cred=load_creds()
    con_string = '''mongodb+srv://{}:{}@bountycbl-nxean.mongodb.net/test?retryWrites=true&w=majority'''.format(cred.user, cred.password)
    client = MongoClient(con_string)
    db = client.get_database(cred.database)
    db.bounties.insert_many(new_bounties)
    client.close()

def bounties_insert_gsheet(new_bounty):
    cred=load_creds()
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name('gcreds.json', scope)
    service = discovery.build('sheets', 'v4', credentials=credentials)
    spreadsheet_id = cred.gsheet
    range_ = 'sheet1!A2'
    value_input_option = 'RAW'
    insert_data_option = 'INSERT_ROWS'
    value_range_body = {"values": new_bounty}
    request = service.spreadsheets().values().append(spreadsheetId=spreadsheet_id,
                                                 range=range_,
                                                 valueInputOption=value_input_option,
                                                 insertDataOption=insert_data_option,
                                                 body=value_range_body)
    response = request.execute()


def bounties_query():
    cred=load_creds()
    con_string = '''mongodb+srv://{}:{}@bountycbl-nxean.mongodb.net/test?retryWrites=true&w=majority'''.format(cred.user, cred.password)
    client = MongoClient(con_string)
    db = client.get_database(cred.database)
    bounties=db.bounties
    bl = list(bounties.find({},{}))
    client.close()
    return bl

def find_bounty(myquery):
    cred=load_creds()
    con_string = '''mongodb+srv://{}:{}@bountycbl-nxean.mongodb.net/test?retryWrites=true&w=majority'''.format(cred.user, cred.password)
    client = MongoClient(con_string)
    db = client.get_database(cred.database)
    bountycol=db['bounties']
    mydoc = bountycol.find(myquery)
    client.close()
    return mydoc

def update_db_bounty(u_list):
    for i in u_list:
        #(c_id, c_guild, c_name, c_reason)
        cred=load_creds()
        con_string = '''mongodb+srv://{}:{}@bountycbl-nxean.mongodb.net/test?retryWrites=true&w=majority'''.format(cred.user, cred.password)
        client = MongoClient(con_string)
        db = client.get_database(cred.database)
        bountycol=db['bounties']
        bountycol.update_one({'_id':i[0]},{'$push':{'bans':{'guildid':i[1], 'guildname':i[2],'reason':i[3]}}})
        client.close()

def update_gbounty(u_list):
    for i in u_list:
        #(c_id, c_guild, c_name, c_reason)
        scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
        gcreds = ServiceAccountCredentials.from_json_keyfile_name('gcreds.json', scope)
        gclient = gspread.authorize(gcreds)
        sheet = gclient.open("bountylist").sheet1
        cell = sheet.find(str(i[0]))
        c_loc = cell.row
        banned_guilds = sheet.row_values(c_loc)[2]
        new_ban = '({},{})'.format(i[2], i[3])
        banned_guilds = banned_guilds + new_ban
        sheet.update_cell(c_loc, 3, banned_guilds)


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # create the background task and run it in the background
        self.bg_task = self.loop.create_task(self.my_background_task())

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        game = discord.Game("Hunting Bounties")
        await client.change_presence(activity=game)
        print('------')

    async def my_background_task(self):
        await self.wait_until_ready()
        while not self.is_closed():
            #print('loop start')
            db_bounties = []
            new_bounties = []
            g_new_bounties = []
            update_bounties = []
            tstbl = bounties_query()
            for i in tstbl:
                x = i.get('_id','')
                if x not in db_bounties:
                    db_bounties.append(x)
            guild_list =[]
            async for guild in client.fetch_guilds(limit=150):
                if (guild.name, guild.id) not in guild_list:
                    guild_list.append((guild.name, guild.id))
            print(guild_list)
            for i in guild_list:
                print(i)
                guild = client.get_guild(i[1])
                try:
                    bans = await guild.bans()
                    if len(bans) >= 1:
                        for ban in bans:
                            if ban[1].id not in db_bounties: #This part will add new bounties
                                #print(i, ban)
                                id = ban[1].id
                                name = ban[1]
                                nb = {'_id':ban[1].id, 'name': ban[1].name, 'bans': [{'guildid': guild.id, 'guildname':guild.name, 'reason': ban[0]}]}
                                new_bounties.append(nb) #
                                db_bounties.append(ban[1].id) #Aappend the new banned id number to the db_table, next iteration this list will be emptied anyways
                                gbans = '({},{})'.format(guild.name, ban[0])
                                g_sheetupdate = [str(ban[1].id), ban[1].name, gbans]
                                g_new_bounties.append(g_sheetupdate)

                            else:
                                #Build the query to check if current guild is in bounty's list of banned guild_list
                                query={ "_id": ban[1].id}
                                ban_guilds = []
                                tstq=find_bounty(query) #Call the find_bounty and return all bans for the bounty
                                for x in tstq:
                                    x_bans = x['bans']
                                    for i in x_bans:
                                        ban_guilds.append(i['guildid']) #Add all banned guilds to temp list
                                if guild.id not in ban_guilds:     #if bounty has a banned guild that is not in the list update Mongo and Update the google sheet1
                                    c_id= ban[1].id
                                    c_guild=guild.id
                                    c_name=guild.name
                                    c_reason=ban[0]
                                    update_bounties.append((c_id, c_guild, c_name, c_reason))
                except Exception as e:
                    print(f' Issue with {guild}, likely bot permssions')



            if len(new_bounties) >= 1:
                bounties_insert_new(new_bounties) # Uncomment out for run
                bounties_insert_gsheet(g_new_bounties)
                update_db_bounty(update_bounties)
                update_gbounty(update_bounties)

            #print('loop end')
            await asyncio.sleep(300) # task runs every 60 seconds

cred=load_creds()
client = MyClient()
client.run(cred.bottoken) #Add bot token to creds
