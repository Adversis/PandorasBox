# PandorasBox

#### Pandoras Box is a tool to find Enterprise Box accounts and enumerate for shared files and folders

#### Writeup can be found here: [adversis.io](https://adversis.io)

#### [@adversis_io](https://twitter.com/adversis_io)
 
## Pre-Requisites
Non-Standard Python Libraries:

* requests
* argparse

Created with Python 3.6

### Install with virtualenv
```virtualenv-3.6 venv
source venv/bin/activate
pip install -r requirements.txt
```

## General

This tool can be used to enumerate for companies that currently have a Box enterprise account, and then to brute force files and folders inside those account that are shared publicly. 

  `-l` : Feed a line delimited target list to check for a Box account and begin enumeration.
  
  `-w` : Feed a word list to brute force documents in the identified target Box account.

  `-t` switch, you can set the number of threads you want to use. Be careful here, Box does enforce rate limiting and your IP may get blocked. 

  `-s` : By supplying a Slack WebHook URL, you can send results to Slack.

  `-c` : You can give the tool a known shared Box file. This allows the tool to verify access to Box, if access to the known Box is denied, then Box is rate limiting your requests and you will need to change you IP. The defaul Box belongs to Dell and was found by a Google Dork. If this Box file gets taken down, a new Box file will have to be supplied. A work around would be to simply put google.com here. 

The example worlist is an exact copy of: https://github.com/first20hours/google-10000-english/blob/master/google-10000-english.txt

## Usage:

    usage: pandoras_box.py [-h] -l TARGETLIST [-w WORDLIST] [-v] [-t THREADS]
                           [-s WEBHOOK_URL] [-c LOCKOUT_CHECK]

    optional arguments:
      -h, --help        show this help message and exit
      -l TARGETLIST     Provide a list of targets to check Box accounts for.
      -w WORDLIST       Provide a wordlist for the file/folder bruteforce.
      -v                Output all webrequests to logfile. Caution size!
      -t THREADS        Number of threads.
      -s WEBHOOK_URL    Slack Web Hook URL
      -c LOCKOUT_CHECK  URL of known shared Box account to verify you are not
                        being blocked.
                    
  
  
  
