#!/usr/bin/env python

#PandorasBox is a tool to find box accounts and enumerate for shared files.

from argparse import ArgumentParser
import codecs
import requests
import xmltodict
import sys
import os
import time
import shutil
import traceback
from queue import Queue
from threading import Thread, Lock
import json
import re
import logging

bucket_q = Queue()
download_q = Queue()
grep_list = None
arguments = None
i = 0

def slack(data):
    if arguments.webhook_url:
        slack_data = {'text': data}

        response = requests.post(
            arguments.webhook_url, data=json.dumps(slack_data),
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code != 200:
            raise ValueError(
                'Request to slack returned an error %s, the response is:\n%s'
                % (response.status_code, response.text)
            )
    else:
        nothing = 'nothing'

def logAndPrint(string):
    print(string)
    logging.info(string.strip('\n'))

def fetch(url):
    global i
    try:
        if arguments.verbose:
            logging.info('Fetching ' + url)

        response = requests.get(url)
        #if response.status_code == 403 or response.status_code == 404:
        #    status403(url)
        if response.status_code == 200 and '/login?' not in response.url:
            size = (re.findall(r'itemSize\": *([\d,]+)\"', str(response.content)))
            filename = (re.findall(r'\"name\": *\"([A-Z a-z \- \d ^\. \\ \_,()&]+)\"\,\"itemSize', str(response.content)))
            boxname = (re.findall(r'\"name\": *\"([A-Z a-z \- \d ^\. \\ \_,()&]+)\"\,\"created', str(response.content)))
            orgOwner = (re.findall(r'\"ownerEnterpriseName\":\"([A-Z a-z \- \d ^\. \\ \_,()]+)\"\,\"ownerEnterpriseID', str(response.content)))
            totalSize = 0
            counter = 1
            pageCount = 1
            pageCountRe=(re.findall(r'pageCount\": *([\d,]+)\"', str(response.content)))
            if pageCountRe:
                pageCount = pageCountRe[0].rstrip(',')

            for item in size:
                totalSize = totalSize + int(item.rstrip(','))
            #print("\n[+] Found Unprotected Box at " + url)
            #logging.info("\n[+] Found Unprotected Box at " + url)
            logAndPrint("\n[+] Found Unprotected Box at " + url)

            if orgOwner:
                logAndPrint("--> Organization: " + orgOwner[0])
                #print("--> Organization: " + orgOwner[0])
                #logging.info("Organization: " + orgOwner[0])

            slack_data = "[+] Found Unprotected Box at " + url
            slack(slack_data)
            for name in boxname:
                logAndPrint("--> Box Name: " + name)
                #print("--> Box Name: " + name)
                #logging.info("--> Box Name: " + name)
            for file in filename:
                logAndPrint("------> " + file)
                #print("------> " + file)
                #logging.info("------> " + file)

            # This spits output between other found boxes and files so you lose track of what's what
            #if int(pageCount) > 1:
            #    print("------> Plus an additional " + str(pageCount-1) + " pages")
            #    humanSize = getSize(totalSize)
            #    #while int(pageCount) > counter:
            #    #    newUrl = ""
            #    #    counter += 1
            #    #    newUrl = url + "?page=" + str(counter)
            #    #    #print(newUrl)
            #    #    response = requests.get(newUrl)
            #    #    size = (re.findall(r'itemSize\": *([\d,]+)\"', str(response.content)))
            #    #    filename = (re.findall(r'\"name\": *\"([A-Z a-z \- \d ^\. \\ \_,()&]+)\"\,\"itemSize', str(response.content)))
            #    #    for file in filename:
            #    #        print("------> " + file)
            #    #        logging.info("------> " + file)
            #    #    for item in size:
            #    #        totalSize = totalSize + int(item.rstrip(','))
            #    #        humanSize = getSize(totalSize)
            #else:
            #    humanSize = getSize(totalSize)

            #print("------= Total Box Size: %s\n" % humanSize)

            humanSize = getSize(totalSize)

            logAndPrint("--> Box size (1st page): " + humanSize)
            #print("--> Box size (1st page): " + humanSize + "\n")
            #logging.info("Total Box Size: " + humanSize + " Size in Bytes: " + str(totalSize))

            if int(pageCount) > 1:
                logAndPrint("--> Plus an additional " + str(int(pageCount)-1) + " pages")

        #if response.status_code == 200 and '/login?' in response.url:
        #    print("Found Protected Box at " + url)
        i = i + 1
    except Exception as e:
        print("[-] Error in getting " + url)
        if arguments.verbose:
                logging.info(e)

def getSize(B):
   'Return the given bytes as a human friendly KB, MB, GB, or TB string'
   B = float(B)
   KB = float(1024)
   MB = float(KB ** 2) # 1,048,576
   GB = float(KB ** 3) # 1,073,741,824
   TB = float(KB ** 4) # 1,099,511,627,776

   if B < KB:
      return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
   elif KB <= B < MB:
      return '{0:.2f} KB'.format(B/KB)
   elif MB <= B < GB:
      return '{0:.2f} MB'.format(B/MB)
   elif GB <= B < TB:
      return '{0:.2f} GB'.format(B/GB)
   elif TB <= B:
      return '{0:.2f} TB'.format(B/TB)

def bucket_worker():
    global i
    while True:
        item = bucket_q.get()
        try:
            fetch(item)
            if i == 25:
                 check_block = requests.get(arguments.lockout_check)
                 if check_block.status_code != 200:
                    input("I think you hit the rate limit, change your IP and press enter to resume. you may also want to reduce your threads and run this target again")
                    slack_data ="You seem to be rate limited or blocked, pausing scan"
                    slack(slack_data)
                 i = 0

        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            print(e)
        bucket_q.task_done()

def downloadWorker():
    #print('Download worker running...')
    while True:
        item = download_q.get()
        try:
            downloadFile(item)
        except Exception as e:
            test = 6
            #traceback.print_exc(file=sys.stdout)
            #print("")
        download_q.task_done()

#def get_size(content):
#    print(content.json())

def print_banner():
        print('''\nDescription:
        BoxFinder is a tool to find box accounts and enumerate for shared files.

        '''
        )

def status403(line):
    print(line.rstrip() + " is not a box.", end = '\r')
#    print('')

def queue_up_download(filepath):
    download_q.put(filepath)
    print('Collectable: {}'.format(filepath))
    write_interesting_file(filepath)


def status200(response,grep_list,line):
    print("Pilfering "+line.rstrip() + '...')
    objects=xmltodict.parse(response.text)
    Keys = []
    interest=[]
    try:
        for child in grep_list:
            Keys.append(child['Key'])
    except:
        pass
    hit = False
    for words in Keys:
        words = (str(words)).rstrip()
        collectable = line+'/'+words
        if grep_list != None and len(grep_list) > 0:
            for grep_line in grep_list:
                grep_line = (str(grep_line)).rstrip()
                if grep_line in words:
                    queue_up_download(collectable)
                    break
        else:
            queue_up_download(collectable)

def main():
    global arguments
    global grep_list
    global i
    parser = ArgumentParser()
    parser.add_argument("-l", dest="targetlist", required=True, help="Provide a list of targets to check Box accounts for.")
    parser.add_argument("-w", dest="wordlist", required=False, help="Provide a wordlist for the file/folder bruteforce.")
    parser.add_argument("-v", dest="verbose", action='store_true', default=False, required=False, help="Output all webrequests to logfile. Caution size!")
    parser.add_argument("-t", dest="threads", type=int, required=False, default=1, help="Number of threads.")
    parser.add_argument("-s", dest="webhook_url", required=False, help="Slack Web Hook URL")
    parser.add_argument("-c", dest="lockout_check", required=False, default='https://dell.app.box.com/v/BootableR710', help="URL of known shared Box account to verify you are not being blocked.")

    if len(sys.argv) == 1:
        print_banner()
        parser.error("No arguments given.")
        parser.print_usage
        sys.exit()

    # output parsed arguments into a usable object
    arguments = parser.parse_args()

    # start logging
    LOG_FILENAME = "pandoras_box_"+str(int(time.time()))+".log"
    logging.basicConfig(level=logging.INFO, filename=LOG_FILENAME, filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

    # specify primary variables
    with open(arguments.wordlist, "r") as grep_file:
        grep_content = grep_file.readlines()
    grep_list = [ g.strip() for g in grep_content ]

    # start up bucket workers
    for i in range(0,arguments.threads):
        #print('Starting thread...')
        t = Thread(target=bucket_worker)
        t.daemon = True
        t.start()

    # start download workers
    for i in range(1, arguments.threads):
        t = Thread(target=downloadWorker)
        t.daemon = True
        t.start()

    with open(arguments.targetlist) as f:
        try:
            for line in f:
                bucket = 'https://'+line.rstrip()+'.account.box.com'
                response = requests.get(bucket)
                if bucket.lower() in response.text or 'Part of' in response.text:
                    logAndPrint("[+] Found Box Account at " + bucket)
                    #print("[+] Found Box Account at " + bucket)
                    #logging.info("[+] Found Box Account at " + bucket)
                    slack_data="[+] Found Box Account at " + bucket
                    slack(slack_data)
                    for name in grep_list:
                        box = bucket + '/v/' + name
                        #print('Queuing {}'.format(box) + '...')
                        bucket_q.put(box)

            else:
                a = 5
                #print("No Box account at " + bucket)
        except:
            print("Error getting " + bucket)

    bucket_q.join()
    print("[+] Scan is complete! Results saved to " + LOG_FILENAME)
    slack("Scan is complete!")

if __name__ == "__main__":
    main()

