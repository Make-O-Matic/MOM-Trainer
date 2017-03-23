#!/usr/bin/env python

import argparse
import datetime
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
        required=True, type=valid_time)
    helpers.add_db_arguments(parser)
    args = parser.parse_args()

    Gst.init(None)
    GES.init()
    loop = GLib.MainLoop()

    input = GES.UriClipAsset.request_sync('file://' + args.media)

    input_start = arrow.get(args.start)
    input_stop = input_start.shift(microseconds=
        (input.get_duration()/Gst.MSECOND))

    db = helpers.make_db(args)
    trainset_infos = helpers.get_trainset_infos(db)
    for trainset in trainset_infos:
        clip_start = max(input_start, arrow.get(trainset_infos[trainset]['created']))
        clip_end = min(input_stop, arrow.get(trainset_infos[trainset]['ended']))
        if clip_start < clip_end:
            timeline = GES.Timeline.new_audio_video()
            layer = timeline.append_layer()
            clip = layer.add_asset(video, 0,
                (clip_start - input_start).microsecond * Gst.MSECOND,
                (clip_end - clip_start).microsecond * Gst.MSECOND,
                GES.TrackType.UNKNOWN)
            timeline.commit()
            pipeline = GES.Pipeline()
            pipeline.set_timeline(timeline)

            bus = pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message", handle_message)

            pipeline.set_render_settings('file:///home/gil/output.mp4')
            pipeline.set_mode(GES.PipelineFlags.SMART_RENDER)
            pipeline.set_state(Gst.State.PLAYING)
            loop.run()


def valid_time(s):
    try:
        return datetime.datetime.strptime(s, '%d.%m.%Y %H:%M:%S')
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def handle_message(bus, message):
    if message.type == Gst.MessageType.EOS:
        loop.quit()
    elif message.type == Gst.MessageType.ERROR:
        error = message.parse_error()
        loop.quit()

if __name__ == "__main__":
    main()

