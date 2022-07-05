from flask import Flask,render_template,request,redirect
from flask import jsonify
from flask import request
import json
import requests
from textblob import TextBlob
import random
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from flask_socketio import SocketIO, emit
import regex as re
import string
import pandas as pd
lemmatizer=WordNetLemmatizer()
stop_words=stopwords.words('english')
API_KEY=["AIzaSyDQLBKAqrrI_Ol8WNrpo6A8mRLriVy_Z6Y","AIzaSyAD_h-mw_a7FoTBTQxpD-5DLxL-hZ-xCU8","AIzaSyDdM0jFmRGK6Zb2PR6Vq5NCp3r5S0cEfwk","AIzaSyBkqyLNktvpCAA15H10UPecTgdN4sN7Bl4","AIzaSyBda-pKpH1r862elXKJqytF-ax9wDzqDK4","AIzaSyB2qmVNMkHoIi67RIlUIqHL1Umc0rSJ614"]
chnl_id="UCa90xqK2odw1KV5wHU9WRhg"
# link="https://www.googleapis.com/youtube/v3/search?key="+API_KEY+"&channelId="+chnl_id+"&part=snippet,id&order=date&maxResults=20"
link_comments="https://www.googleapis.com/youtube/v3/commentThreads?key={your_api_key}&textFormat=plainText&part=snippet&videoId={video_id}&maxResults=100&pageToken={nextPageToken}"
app = Flask(__name__)
socketio = SocketIO(app)
def preProcessing(cmt):
    cmt=cmt.lower()
    cmt=re.sub(r"http\S+|ww\S+|http\S+","",cmt,flags=re.MULTILINE)
    cmt=cmt.translate(str.maketrans("","",string.punctuation))
    cmt=re.sub(r'\@\w+|\#',"",cmt)
    cmt_tokens=word_tokenize(cmt)
    stripped_words=[]
    for word in cmt_tokens:
        if word not in stop_words:
            stripped_words.append(word)
    lemmatized_words=[]
    for word in stripped_words:
        lemmatized_words.append(lemmatizer.lemmatize(word))
    return " ".join(lemmatized_words)
def videoId_playlist(playlist_id):
    url_play="https://www.googleapis.com/youtube/v3/playlistItems?"
    params={'key':API_KEY[random.randrange(0,5,1)],"part":"snippet","order":"date","maxResults":100,"playlistId":playlist_id}
    vid_ids=[]
    r=request.get(url=url_play,params=params)
    data=r.json()
    for j in range(len(data["items"])):
        vid_ids.append(data["items"][j]["snippet"]["resourceId"]["videoId"])
    return vid_ids
def gettingComments(chnl_id):
    url="https://www.googleapis.com/youtube/v3/search?"
    params={"key":API_KEY[random.randrange(0,5,1)],"channelId":chnl_id,"part":"id","order":"date","maxResults":100}
    video_ids=[]
    r=requests.get(url=url,params=params)
    data=r.json()
    print(data['items'][0])
    # data=json.load(data)
    for i in range(len(data["items"])):
        try:
            data["items"][i]["id"]["videoId"]
            video_ids.append(data["items"][i]["id"]["videoId"])
        except:
            pass
        try:
            data["items"][i]["playlistId"]
            v_ids = videoId_playlist(data["items"][i]["playlistId"])
            for k in range(len(v_ids)):
                video_ids.append(v_ids[k])
        except:
            pass
    while(1):
        try:
            data["nextPageToken"]
            tkn = data["nextPageToken"]
            params={"key":API_KEY[random.randrange(0,5,1)],"channelId":chnl_id,"part":"id","maxResults":100,"pageToken":tkn}
            r=requests.get(url=url,params=params)
            data=r.json()
            for i in range(len(data["items"])):
                video_ids.append(data["items"][i]["id"]["videoId"])
        except:
            break
    # print(video_ids)
    print(len(video_ids))
    length=len(video_ids)
    comments=[]
    # url_cmt = "https://www.googleapis.com/youtube/v3/commentThreads"
    # params = {"key": API_KEY, "textFormat": "plainText", "part": "snippet", "videoId":"9IDvInOaSgM","maxResults": 500}
    # r = requests.get(url=url_cmt, params=params)
    # data = r.json()
    # print(data["items"][0]["snippet"]["topLevelComment"]["snippet"]["textDisplay"])
    for j in range(len(video_ids)):
        print("completion:"+str(((j+1)/length)*100)+"Current Video URL: https://www.youtube.com/watch?v="+str(video_ids[j])+"  No. of comments scraped: "+str(len(comments)))
        if(len(comments)>1000000):
            break
        url_cmt = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {"key": API_KEY[random.randrange(0,5,1)], "textFormat": "plainText", "part": "snippet", "videoId":video_ids[j],"maxResults": 200}
        r = requests.get(url=url_cmt, params=params)
        data = r.json()
        try:
            data["items"]
            for k in range(len(data["items"])):
                comments.append(data["items"][k]["snippet"]["topLevelComment"]["snippet"]["textDisplay"])
        except:
            pass
        p=2
        while(p):
            try:
                data["nextPageToken"]
                tkn=data["nextPageToken"]
                params={"key": API_KEY[random.randrange(0,5,1)], "textFormat": "plainText", "part": "snippet", "videoId":video_ids[j],"maxResults": 200,"pageToken":tkn}
                r = requests.get(url=url_cmt, params=params)
                data=r.json()
                try:
                    data["items"]
                    for l in range(len(data["items"])):
                        comments.append(data["items"][l]["snippet"]["topLevelComment"]["snippet"]["textDisplay"])
                    p-=1
                except:
                    pass
            except:
                try:
                    data["items"]
                    for l in range(len(data["items"])):
                        comments.append(data["items"][l]["snippet"]["topLevelComment"]["snippet"]["textDisplay"])
                    break
                except:
                    break
    # print(comments)
    return comments
def get_sentiments(cmt):
    analysis=TextBlob(cmt)
    return analysis.sentiment.polarity
@app.route('/',methods=['GET',"POST"])
def index():
    if request.method == "POST":
        print(request.form["id1"] + request.form["id2"])
        id1=request.form["id1"]
        id2=request.form["id2"]
        # return redirect('/')
        return redirect('/'+id1+"/"+id2)
    return render_template("home.html")

@app.route("/<id1>/<id2>",methods=['GET'])
def videoID(id1,id2):
    # text = "Snide comparisons@@@ to gelatin #be damned, it's a concept with the most devastating of potential www.youtube.com consequences, not unlike the grey!!... goo scenario proposed by technological theorists fearful of artificial intelligence run rampant!!!."
    # changed=preProcessing(text)
    # print(changed)
    # print(get_sentiments(changed))
    cmt_1=gettingComments(id1)
    cmt_2=gettingComments(id2)

    neg_pol_1=0
    neg_pol_2=0
    pos_pol_1=0
    pos_pol_2=0
    neu_pol_1=0
    neu_pol_2=0
    pol_1=[]
    pol_2=[]
    for cmt in cmt_1:
        cmt=preProcessing(cmt)
        pol_1.append(get_sentiments(cmt))
        if(get_sentiments(cmt)<0):
            neg_pol_1+=1
        elif(get_sentiments(cmt)>0):
            pos_pol_1+=1
        else:
            neu_pol_1+=1
    for cmt in cmt_2:
        cmt=preProcessing(cmt)
        pol_2.append(get_sentiments(cmt))
        if(get_sentiments(cmt)<0):
            neg_pol_2+=1
        elif(get_sentiments(cmt)>0):
            pos_pol_2+=1
        else:
            neu_pol_2+=1
    data_1 = {"comment": cmt_1,"polarity":pol_1}
    data_2 = {"comment": cmt_2,"polarity":pol_2}
    dataframe_1=pd.DataFrame(data_1)
    dataframe_2=pd.DataFrame(data_2)
    #Edit channel name
    dataframe_1.to_csv("", encoding='utf-8', index=False)
    dataframe_2.to_csv("", encoding='utf-8', index=False)

    total_1=neu_pol_1+neg_pol_1+pos_pol_1
    percent_neg_1=(neg_pol_1/total_1)*100
    percent_neu_1=(neu_pol_1/total_1)*100
    percent_pos_1=(pos_pol_1/total_1)*100
    total_2 = neu_pol_2 + neg_pol_2 + pos_pol_2
    percent_neg_2 = (neg_pol_2 / total_2) * 100
    percent_neu_2 = (neu_pol_2 / total_2) * 100
    percent_pos_2 = (pos_pol_2 / total_2) * 100

    print(neg_pol_1,pos_pol_1,neu_pol_1,neg_pol_2,pos_pol_2,neu_pol_2)
    url_chnl = "https://youtube.googleapis.com/youtube/v3/channels?"
    params1 = {"part": "snippet,statistics", "id": id1, "key": API_KEY[random.randrange(0, 5, 1)]}
    params2 = {"part": "snippet,statistics", "id": id2, "key": API_KEY[random.randrange(0, 5, 1)]}
    r1 = requests.get(url=url_chnl, params=params1)
    r2 = requests.get(url=url_chnl, params=params2)
    data1 = r1.json()
    data2 = r2.json()
    print(data1["items"][0]["statistics"]["subscriberCount"])
    data = {"title1": data1["items"][0]["snippet"]["title"], "title2": data2["items"][0]["snippet"]["title"],
            "sub1": data1["items"][0]["statistics"]["subscriberCount"],
            "sub2": data2["items"][0]["statistics"]["subscriberCount"],
            "img1": data1["items"][0]["snippet"]["thumbnails"]["high"]["url"],
            "img2": data2["items"][0]["snippet"]["thumbnails"]["high"]["url"],
            "percent_neg_1":percent_neg_1,
            "percent_neu_1":percent_neu_1,
            "percent_pos_1":percent_pos_1,
            "percent_neg_2":percent_neg_2,
            "percent_neu_2":percent_neu_2,
            "percent_pos_2":percent_pos_2}
    return render_template("result.html", value=data)

@app.route('/result/<id1>/<id2>',methods=["GET"])
def results(id1,id2):
    url_chnl = "https://youtube.googleapis.com/youtube/v3/channels?"
    params1 = {"part": "snippet,statistics", "id": id1, "key": API_KEY[random.randrange(0, 5, 1)]}
    params2 = {"part": "snippet,statistics", "id": id2, "key": API_KEY[random.randrange(0, 5, 1)]}
    r1 = requests.get(url=url_chnl, params=params1)
    r2 = requests.get(url=url_chnl, params=params2)
    data1 = r1.json()
    data2 = r2.json()
    print(data1["items"][0]["statistics"]["subscriberCount"])
    data = {"title1": data1["items"][0]["snippet"]["title"], "title2": data2["items"][0]["snippet"]["title"],
            "sub1": data1["items"][0]["statistics"]["subscriberCount"],
            "sub2": data2["items"][0]["statistics"]["subscriberCount"],
            "img1": data1["items"][0]["snippet"]["thumbnails"]["high"]["url"],
            "img2": data2["items"][0]["snippet"]["thumbnails"]["high"]["url"],
            "percent_neg_1":10,
            "percent_neu_1":40,
            "percent_pos_1":50,
            "percent_neg_2":30,
            "percent_neu_2":10,
            "percent_pos_2":60}
    return render_template("result.html", value=data)


@socketio.on('connect')
def connect():
    emit('message', {'hello': "Hello"})

if __name__=="__main__":
    socketio.run(app,debug=True)