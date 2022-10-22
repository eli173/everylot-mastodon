# -*- coding: utf-8 -*-
# This file is part of everylotbot
# Copyright 2016 Neil Freeman
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import logging
#import twitter_bot_utils as tbu
#from . import __version__ as version
from .everylot import EveryLot
from mastodon import Mastodon
import yaml

dry_run = False

def main():
    print('difference made?')
    parser = argparse.ArgumentParser(description='every lot twitter bot')
    #parser.add_argument('screen_name', metavar='SCREEN_NAME', type=str, help='Twitter screen name (without @)')
    parser.add_argument('database', metavar='DATABASE', type=str, help='path to SQLite lots database')
    parser.add_argument('config', type=str, default=None, metavar='CONFIG',
                        help='config file location uhh')
    parser.add_argument('--id', type=str, default=None, help='tweet the entry in the lots table with this id')
    parser.add_argument('-s', '--search-format', type=str, default=None, metavar='STRING',
                        help='Python format string use for searching Google')
    parser.add_argument('-p', '--print-format', type=str, default=None, metavar='STRING',
                        help='Python format string use for poster to Twitter')
    #tbu.args.add_default_args(parser, version=version, include=('config', 'dry-run', 'verbose', 'quiet'))

    args = parser.parse_args()
    #print(args)
    #print(args.config)
    #return
    #api = tbu.api.API(args)
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    mast = Mastodon(access_token=config['mastotok'], api_base_url=config['mastosrv'])

    #logger = logging.getLogger(args.screen_name)
    #logger.debug('everylot starting with %s, %s', args.screen_name, args.database)

    el = EveryLot(args.database,
                  logger=logger,
                  print_format=args.print_format,
                  search_format=args.search_format,
                  id_=args.id)

    if not el.lot:
        logger.error('No lot found')
        return

    logger.debug('%s addresss: %s zip: %s', el.lot['id'], el.lot.get('address'), el.lot.get('zip'))
    logger.debug('db location %s,%s', el.lot['lat'], el.lot['lon'])

    # Get the streetview image and upload it
    # ("sv.jpg" is a dummy value, since filename is a required parameter).
    image = el.get_streetview_image(config['streetview'])
    #media = api.media_upload('sv.jpg', file=image)
    media = mast.media_post(image, mime_type='Image/PNG')
    # shit is it a png?
    # compose an update with all the good parameters
    # including the media string.
    update = el.compose(media.id)
    mast.media_update(media.id, description=update['status'])
    #print(update)
    #return
    #logger.info(update['status'])
    #mast.media_post(image,)
    if not dry_run:
        logger.debug("posting")
        posted = mast.status_post(update['status'], media_ids=update['media_ids'])
        #status = api.update_status(**update)
        try:
            el.mark_as_tweeted(posted.id)
        except AttributeError:
            el.mark_as_tweeted('1')

if __name__ == '__main__':
    main()
