import pytube
import pymongo
from pymongo import MongoClient
import requests
import feedparser
import telepot
from telepot.loop import MessageLoop
from apscheduler.schedulers.blocking import BlockingScheduler
import datetime as dt

baseLocation = 'Location Here'
location = ''#Leave blank
playlist = False
playlistName = ''
commandProgress = 0
chat_ID = 1103067075
#connecting to mongo
client = MongoClient('DB IP')
db = client.pytube#replace pytube with name of db
queue = db.queue#replace pytube with name of video queue collection
posts = db.youtubers#replace pytube with name of youtuber list collection
commandName = ""#leave this blank
bot_id = '*ID Here*'


def message(msg):
    print(msg)
    bot.sendMessage(chat_ID,msg)
def download(url):
    global location
    global playlist
    Title = False
    while Title == False:
        youtube = pytube.YouTube(url)
        video = youtube.streams.first()
        if(video.title == 'YouTube'):
            Title = False
            message('name not found retrying...')
        else:
            Title = True
            message('name found, downloading: '+ video.title)
    video.download(location)
    message('done')
    
def togglePlaylist(name):
    global location
    global playlist
    if(playlist == True):
        location = baseLocation
        playlist = False
    else:
        location = baseLocation + "/" + name
        print(location)
        playlist = True

def getLatestVideo(chid):
    RSS = feedparser.parse("https://www.youtube.com/feeds/videos.xml?channel_id="+ chid)
    entry = RSS.entries[0]
    return(entry.title)
    
def addYoutuber(name, chid):
    post = {"Name": name,
            "ChannelID": chid,
            "Latest_Video": getLatestVideo(chid)
        }
    post_id = posts.insert_one(post).inserted_id
    print("Added")

def deleteYoutuber(name):
    result = db.youtubers.delete_one({'Name': name})
    print("Deleted")

def checkLatest(name):
    current = posts.find_one({"Name": name})
    chid = current['ChannelID']
    RSS = feedparser.parse("https://www.youtube.com/feeds/videos.xml?channel_id="+ chid)
    entry = RSS.entries[0]
    if(current['Latest_Video'] != entry.title):
        print(entry.link)
        bot.sendMessage(chat_ID,"New video from " + name +" downloading now...")
        download(entry.link)
        posts.update_one({"_id":current['_id']},{"$set":{"Latest_Video":entry.title}})
    else:
        bot.sendMessage(chat_ID,"No New Video From "+ name)
        
def checkAll():
    cursor = db.youtubers
    for document in cursor.find():
        checkLatest(document["Name"])

def addToQueue(link):
    post = {"link": link}
    post_id = queue.insert_one(post).inserted_id

def downloadQueue():
    cursor = db.queue
    for document in cursor.find():
        download(document["link"])
        result = db.queue.delete_one({'link': document["link"]})


def smartCheck():
    global doNotDisturb
    if( 23 <= dt.datetime.now().hour <= 24):
        check()
    elif(0 <= dt.datetime.now().hour <= 5):
        check()
        downloadQueue()
    print('Half an hour has passed')



   
bot = telepot.Bot(bot_id)
print(bot.getMe())

def handle(msg):
    global commandProgress
    global playlist
    global commandName
    chat_id = msg['chat']['id']
    command = msg['text']
    if(commandProgress == 0):
        if command == '/download':
            bot.sendMessage(chat_id,"Send the link for the video you wish to download")
            commandProgress = 1
        elif command == '/playlist':
            if(playlist == False):
                bot.sendMessage(chat_id,"Send the name of the playlist you would like to add to")
                commandProgress = 2
            else:
                togglePlaylist("")
                bot.sendMessage(chat_id,"Playlist diabled")
        elif command == '/queue':
            bot.sendMessage(chat_id,"Send the link for the video you wish to queue")
            commandProgress = 3
        elif command == '/check':
            checkAll()
        elif command == '/ping':
            bot.sendMessage(chat_id,"Pong")
            print(chat_id)
        elif command == '/deletetuber':
            bot.sendMessage(chat_id,"Tell me the name of the youtuber you want to remove")
            i = 1
            cursor = db.youtubers
            for document in cursor.find():
               bot.sendMessage(chat_id, str(i)  + " " + document["Name"])
               i = i + 1
            commandProgress = 6
        elif command == '/listtubers':
            cursor = db.youtubers
            for document in cursor.find():
                bot.sendMessage(chat_id,document["Name"])
                commandProgress = 0
        elif command == '/addtuber':
            bot.sendMessage(chat_id,"Send in the youtubers name")
            commandProgress = 4
    elif(commandProgress == 1):
        download(command)
        commandProgress = 0
    elif(commandProgress == 2):
        togglePlaylist(command)
        bot.sendMessage(chat_id,"Playlist enabled")
        commandProgress = 0
    elif(commandProgress == 3):
        addToQueue(command)
        bot.sendMessage(chat_id,"Added")
        commandProgress = 0
    elif(commandProgress == 4):
        commandName = command
        bot.sendMessage(chat_id,"Got it, now send the channels ID")
        commandProgress = 5
    elif(commandProgress == 5):
        chid = command
        addYoutuber(commandName,chid)
        bot.sendMessage(chat_id,"Added!")
        commandProgress = 0
    elif(commandProgress == 6):
        i = 1
        cursor = db.youtubers
        for document in cursor.find():
            if(i == int(command)):
                deleteYoutuber(document["Name"])
                bot.sendMessage(chat_id,"Removed")
            i = i + 1
        commandProgress = 0

MessageLoop(bot, handle).run_as_thread()    
    

scheduler = BlockingScheduler()
scheduler.add_job(smartCheck, 'interval', hours=0.5)
scheduler.start()   
        

    
    


    
