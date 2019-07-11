import pyttsx3
import threading
from time import sleep
from threading import Thread
import os
import subprocess

beat_to_play = "beat.mp3"
slowdown_rate = 35
intro = 5


def play_mp3(path):
    subprocess.call('mpg123 -q '+beat_to_play, shell=True)


engine = pyttsx3.init()

def letters(input):
    valids = []
    for character in input:
        if character.isalpha() or character == "," or character == "'" or character == " ":
            valids.append(character)
    return ''.join(valids)

lyrics = open("neural_rap.txt").read().split("\n") #this reads lines from a file called 'neural_rap.txt'
rate = engine.getProperty('rate')
engine.setProperty('rate', rate - slowdown_rate)
voices = engine.getProperty('voices')

wholesong = ""
for i in lyrics:
    wholesong += i + " ... "


def sing():

    print(wholesong)
    for line in wholesong.split(" ... "):
        if line == "..." or line == "":
            for i in range(3):
                os.system("say ...")
        else:
            os.system("say "+str(line))
    engine.runAndWait()

def beat():
    play_mp3(beat_to_play)


Thread(target=beat).start()
sleep(intro) 
Thread(target=sing).start()
