#!/usr/bin/env python

import argparse
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
gi.require_version('GES', '1.0')
from gi.repository import GES
import helpers

def main():
    parser = argparse.ArgumentParser(description='videoeditor.')
    parser.add_argument('media', help='media file')
    helpers.add_db_arguments(parser)
    args = parser.parse_args()
    db = helpers.make_db(args)
    
    Gst.init(None)
    GES.init()
    asset = GES.UriClipAsset.request_sync('file://' + args.media)
    timeline = GES.Timeline.new_audio_video()     
    layer = timeline.append_layer()

    #clip = layer.add_asset(asset, start_on_timeline, start_position_asset,         
    #    duration, GES.TrackType.UNKNOWN)
    #timeline.commit()

if __name__ == "__main__":
    main()

