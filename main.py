#!/usr/bin/env python3

import argparse
import os
from mumblepc import MumblePC


parser = argparse.ArgumentParser(
    description='Mumble Player Client, a Mumble radio bot.'
)
parser.add_argument(
    'address',
    help='Mumble server address'
)
parser.add_argument(
    'port',
    type=int,
    help='Mumble server port'
)
parser.add_argument(
    '--radio-address',
    help='URL of a radio stream to play when connected',
)
args = parser.parse_args()

PATH = os.path.abspath(os.path.dirname(__file__))

certs = {}

for certfile in ('cert', 'key'):
    target = os.path.join(PATH, 'mumblepc_%s.pem' % certfile)
    certs[certfile] = target if os.path.exists(target) else None

bot = MumblePC(
    address=args.address,
    port=args.port,
    certfile=certs['cert'],
    keyfile=certs['key'],
)

if args.radio_address:
    bot.play(args.radio_address)

bot.run()
