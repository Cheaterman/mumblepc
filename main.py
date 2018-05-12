#!/usr/bin/env python3

from av.audio.resampler import AudioResampler
from pymumble_py3 import Mumble
import av
import io
import subprocess
import sys


CHUNK_SIZE = 1024

mumble_address, mumble_port, radio_address = sys.argv[1:]

client = Mumble(mumble_address, 'MumblePC', int(mumble_port))
client.start()
client.is_ready()

container = av.open(radio_address)
stream = next(
    stream for stream in container.streams if stream.type == 'audio'
)
resampler = AudioResampler('s16p', 1, 48000)

quit = False

while not quit:
    for packet in container.demux(stream):
        for frame in packet.decode():
            frame.pts = None
            frame = resampler.resample(frame)
            rawchunk = frame.to_nd_array().tobytes()
            client.sound_output.add_sound(rawchunk)
    quit = True
