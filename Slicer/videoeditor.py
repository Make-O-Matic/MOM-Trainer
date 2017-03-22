#!/usr/bin/env python

import argparse
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GES', '1.0')
from gi.repository import GLib, Gst, GES
import arrow
import helpers

def main():
    parser = argparse.ArgumentParser(description='videoeditor.')
    parser.add_argument('media', help='media file')
    parser.add_argument('-s', '--start',
        help='start - "format 01.01.2000 01:02:03"',
        required=True, type=valid_date)
    helpers.add_db_arguments(parser)
    args = parser.parse_args()
    
    Gst.init(None)
    GES.init()
    loop = glib.MainLoop()

    asset = GES.UriClipAsset.request_sync('file://' + args.media)

    asset_start = arrow.get(args.start)
    asset_stop = asset_start.shift(
        microsecond=(asset.get_duration()/Gst.MSECOND))

    db = helpers.make_db(args)
    trainset_infos = helpers.get_trainset_infos(db)
    for trainset_info in trainset_infos:
        start = max(asset_start, arrow.get(trainset_info['created'])
        end = min(asset_stop, arrow.get(trainset_info['ended'])
        if start < end:
            timeline = GES.Timeline.new_audio_video()
            layer = timeline.append_layer()
            clip = layer.add_asset(asset, 0,
                (start - asset_start).microsecond * Gst.MSECOND,
                (end - start).microsecond * Gst.MSECOND,
                GES.TrackType.UNKNOWN)
            timeline.commit()
            pipeline = GES.Pipeline()
            pipeline.set_timeline(timeline)
            pipeline.set_state(Gst.State.RENDER)


def valid_date(s):
    try:
        return datetime.strptime(s, '%d.%m.%Y %H:%M:%S')
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


if __name__ == "__main__":
    main()

