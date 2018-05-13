from av.audio.resampler import AudioResampler
from pymumble_py3 import Mumble
from pymumble_py3.constants import PYMUMBLE_CLBK_TEXTMESSAGERECEIVED
import av
import cgi
import re
import time


commands = {}


def command(func):
    commands[func.__name__] = func
    return func


_html_stripper_regexp = re.compile(r'(<!--.*?-->|<[^>]*>)')


def _strip_html(text):
    return cgi.escape(_html_stripper_regexp.sub('', text))


class MumblePC(object):
    def __init__(self, address, port, certfile, keyfile):
        self.client = client = Mumble(
            address,
            'MumblePC',
            port,
            certfile=certfile,
            keyfile=keyfile,
            reconnect=True,
        )
        client.set_codec_profile('audio')
        client.start()
        client.is_ready()
        client.set_bandwidth(200 * 1000)
        client.callbacks.add_callback(
            PYMUMBLE_CLBK_TEXTMESSAGERECEIVED,
            self.on_text
        )
        self._resampler = AudioResampler('s16p', 1, 48000)
        self._stream = None
        self.last_chunk_time = None
        self.quit = False

    def on_text(self, message):
        command = message.message

        if not command.startswith('!'):
            return

        sender = self.client.users[message.actor]

        if not self.process_command(command, sender):
            sender.send_message('Unknown command "%s"' % command)

    def process_command(self, command, sender):
        command = _strip_html(command)

        if ' ' not in command:
            command, args = command[1:], []
        else:
            command, *args = command[1:].split(' ')

        if command in commands:
            commands[command].__get__(self)(*args, sender=sender)
            return True

    @command
    def play(self, address, sender=None):
        container = av.open(address)
        stream = next(
            stream for stream in container.streams if stream.type == 'audio'
        )
        self._stream = (container, stream)

    @command
    def stop(self, sender):
        self._stream = None

    @command
    def status(self, sender):
        return sender.send_message(
            'Buffer size: %f<br>'
            'Last chunk time: %f' % (
                self.client.sound_output.get_buffer_size(),
                (time.time() - self.last_chunk_time)
                if self.last_chunk_time else 0
            )
        )

    def _update_stream(self):
        if not self._stream:
            return

        container, stream = self._stream
        resample = self._resampler.resample

        while self.client.sound_output.get_buffer_size() < .1:
            packet = next(container.demux(stream))

            for frame in packet.decode():
                frame.pts = None
                frame = resample(frame)
                self.client.sound_output.add_sound(
                    frame.to_nd_array().tobytes()
                )

                self.last_chunk_time = time.time()

    def update(self):
        self._update_stream()

    def run(self):
        while not self.quit:
            self.update()
            time.sleep(.01)
