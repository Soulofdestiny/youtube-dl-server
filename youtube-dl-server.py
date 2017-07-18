#!/usr/bin/env python3
import json
import os
import subprocess
import youtube_dl
from queue import Queue
from bottle import route, run, Bottle, request, static_file
from threading import Thread

app = Bottle()

@app.route('/')
def dl_queue_list():
    return static_file('index.html', root='./')

@app.route('/static/:filename#.*#')
def server_static(filename):
    return static_file(filename, root='./static')

@app.route('/q', method='GET')
def q_size():
    return { "success" : True, "size" : json.dumps(list(dl_q.queue)) }

@app.route('/q', method='POST')
def q_put():
    url = request.forms.get("url")
    action = request.forms.get("action")
    if "" != url:
        if "," in url:
            for url in url.split(","):
                dl_q.put({"url" : url, "action" : action})
        else:
            dl_q.put({"url" : url, "action" : action})
        print("Added url " + url + " to the download queue")
        return { "success" : True, "url" : url }
    else:
        return { "success" : False, "error" : "dl called without a url" }

def dl_worker():
    while not done:
        item = dl_q.get()
        download(item)
        dl_q.task_done()

def download(item):
    url = item["url"]
    action = item["action"]
    print("Starting download of " + url)
    if action in "bestaudio":
        print("downloading url as audio")
        ydl_opts = { "format" : "bestaudio" }
    elif action in "mp3":
        print("downloading url as mp3")
        ydl_opts = { "format" : "bestaudio",
                     "postprocessors" : [{
                        "key" : "FFmpegExtractAudio",
                        "preferredcodec" : "mp3",
                        "preferredquality" : "192"
                        }]
                    }
    elif action in "video":
        print("downloading url as video")
        ydl_opts = { "format" : "bestvideo" }
        ydl_opts = {}
    else:
        ydl_opts = {}
    ydl = youtube_dl.YoutubeDL(ydl_opts)
    with ydl:
        ydl.download([url])
    print("Finished downloading " + url)

dl_q = Queue();
done = False;
dl_thread = Thread(target=dl_worker)
dl_thread.start()

print("Started download thread")

app.run(host='0.0.0.0', port=8080, debug=True)
done = True
dl_thread.join()
