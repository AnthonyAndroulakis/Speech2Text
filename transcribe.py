# transcribe.py, speech-to-text using google
# Anthony Androulakis, 2019
import os
import subprocess
#run this command first if you haven't yet: gcloud auth activate-service-account --key-file "My First Project-SomeNumbersHere.json"
import csv
import sys
#how to run: python3 transcribe.py gs://YourBucketNameGoesHere/howareyou.wav 1
#must have a folder named YourBucketNameGoesHere

filename = sys.argv[1]
minimumConfidence = sys.argv[2]

# cmd2 contains some common fillers. unfortunately, google speech2text does not find nonword um, uh, er, and erm fillers. To add expected words/names, place them in the phrases list below
cmd2='''
curl -s -H "Content-Type: application/json" \
    -H "Authorization: Bearer "$(gcloud auth print-access-token) \
    https://speech.googleapis.com/v1p1beta1/speech:longrunningrecognize \
    --data '{
  "config": {
    "languageCode": "en-US",
    "speechContexts":[{
         "phrases":["yea","yeah"],
         "boost": 2
    }],
    "enableWordTimeOffsets": true,
    "enableWordConfidence": true,
  },
  "audio": {
    "uri":"'''+filename+'''"
  }
}'
'''

# send speech-to-text api request to google
output1 = os.popen(cmd2).read()
numname = eval(str(output1))["name"]

cmd3='''
curl -s -k -H "Content-Type: application/json" \
    -H "Authorization: Bearer "$(gcloud auth print-access-token) \
    https://speech.googleapis.com/v1/operations/'''+numname+'''
'''

true = "true"
false = "false"
null = "null"

# wait for speech-to-text process to finish and get results
while True:
    try:
        output2 = os.popen(cmd3).read()
        combination = eval(str(output2))["response"]["results"]
        break;
    except:
        print("please wait...processing speech...")

# get transcript and print into filename.txt
transcript = []
for i in range(len(combination)):
    if float(combination[i]["alternatives"][0]["confidence"])<float(minimumConfidence): #lowest confidence allowed is 90%
        transcript.append("[LOW CONFIDENCE: "+str(combination[i]["alternatives"][0]["confidence"])[:6]+"] "+(combination[i]["alternatives"][0]["transcript"]).lstrip())
    else:
        transcript.append(combination[i]["alternatives"][0]["transcript"])
print(transcript)

textfile = filename[:filename.find('.')]+"_transcript.txt"
textfile = textfile.replace('gs://','')
with open(textfile, 'w') as f:
    for item in transcript:
        f.write("%s\n" % item.lstrip())

# get number of words
numOfWords=0
for h in range(len(combination)):
    numOfWords=numOfWords+len(combination[h]["alternatives"][0]["words"])
print("Number of words: "+str(numOfWords))

#csv file config
csvfile = filename[:filename.find('.')]+"_words.csv"
csvfile = csvfile.replace('gs://','')
csv_file = open(csvfile, "w")
writer = csv.writer(csv_file, delimiter=',')
writer.writerow(["word","start (s)","end (s)","confidence (0-1)","NOTICE"])

# get list of words and start and stop times and output to CSV
for j in range(len(combination)):
    for k in range(len(combination[j]["alternatives"][0]["words"])):
        thisword = (combination[j]["alternatives"][0]["words"][k]["word"]).lstrip()
        thisword = thisword.replace(".","")
        thisword = thisword.replace(",","")
        thisword = thisword.replace("?","")
        thisword = thisword.replace("!","")
        thisword = thisword.replace(";","")
        thisword = thisword.replace(":","")
        starttime = combination[j]["alternatives"][0]["words"][k]["startTime"]
        starttime = starttime.replace("s","")
        endtime = combination[j]["alternatives"][0]["words"][k]["endTime"]
        endtime = endtime.replace("s","")
        confidencelevel = combination[j]["alternatives"][0]["words"][k]["confidence"]
        notice=""
        if float(confidencelevel)<float(minimumConfidence):
            notice="LOW CONFIDENCE"
        currentline = [thisword,starttime,endtime,confidencelevel,notice]
        writer.writerow(currentline)
