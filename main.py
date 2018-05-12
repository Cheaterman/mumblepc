#!/usr/bin/env python

from pymumble_py3 import Mumble
import subprocess
import sys


CHUNK_SIZE = 1024

mumble_address, mumble_port, radio_address = sys.argv[1:]

client = Mumble(mumble_address, 'MumblePC', int(mumble_port))
client.start()
client.is_ready()

process = subprocess.Popen(
    ('ffmpeg -i %s -ac 1 -f s16le -ar 48000 -' % radio_address).split(),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    bufsize=CHUNK_SIZE,
)

while process:
    rawchunk = process.stdout.read(CHUNK_SIZE)

    if rawchunk:
        client.sound_output.add_sound(rawchunk)
    else:
        process.kill()
        process = None
