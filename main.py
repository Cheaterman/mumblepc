#!/usr/bin/env python3

from av.audio.resampler import AudioResampler
from pymumble_py3 import Mumble
from pymumble_py3.constants import PYMUMBLE_CLBK_TEXTMESSAGERECEIVED
import av
import os
import sys
import time


CHUNK_SIZE = 1024
PATH = os.path.abspath(os.path.dirname(sys.argv[0]))

mumble_address, mumble_port, radio_address = sys.argv[1:]


def on_text(message):
    command = message.message

    if not command.startswith('!'):
        return

    author = client.users[message.actor]

    if command == '!status':
        return author.send_message(
            'Buffer size: %f<br>'
            'Last chunk time: %f' % (
                client.sound_output.get_buffer_size(),
                (time.time() - last_chunk_time) if last_chunk_time else 0
            )
        )

    author.send_message('Unknown command "%s"' % command)


client = Mumble(
    mumble_address,
    'MumblePC',
    int(mumble_port),
    certfile=os.path.join(PATH, 'mumblepc_cert.pem'),
    keyfile=os.path.join(PATH, 'mumblepc_key.pem'),
    reconnect=True,
)
client.set_codec_profile('audio')
client.start()
client.is_ready()
client.set_bandwidth(200 * 1000)
client.callbacks.add_callback(PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, on_text)

container = av.open(radio_address)
stream = next(
    stream for stream in container.streams if stream.type == 'audio'
)
resampler = AudioResampler('s16p', 1, 48000)

last_chunk_time = None
quit = False

while not quit:
    for packet in container.demux(stream):
        for frame in packet.decode():
            frame.pts = None
            frame = resampler.resample(frame)
            rawchunk = frame.to_nd_array().tobytes()
            client.sound_output.add_sound(rawchunk)
            last_chunk_time = time.time()

    quit = True
