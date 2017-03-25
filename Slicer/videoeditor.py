#!/usr/bin/env python

import argparse
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstPbutils', '1.0')
gi.require_version('GES', '1.0')
from gi.repository import GLib, Gst, GstPbutils, GES
import arrow
import helpers

def main():
    parser = argparse.ArgumentParser(description='videoeditor.')
    parser.add_argument('media', help='media file')
    parser.add_argument('-s', '--start',
        help='start UTC - format "01.01.2000 01:02:03"',
        required=True, type=valid_time)
    helpers.add_db_arguments(parser)
    args = parser.parse_args()

    Gst.init(None)
    GES.init()
    loop = GLib.MainLoop()
    discoverer = GstPbutils.Discoverer.new(600 * Gst.SECOND)

    media = 'file://' + args.media
    encoding_profile = GstPbutils.EncodingProfile.from_discoverer(
        discoverer.discover_uri(media))
    input = GES.UriClipAsset.request_sync(media)

    input_start = args.start
    input_stop = input_start.shift(microseconds=
        (input.get_duration()/Gst.USECOND))

    db = helpers.make_db(args)
    trainset_infos = helpers.get_trainset_infos(db)
    for trainset in trainset_infos:
        clip_start = max(input_start, arrow.get(trainset_infos[trainset]['created']))
        clip_end = min(input_stop, arrow.get(trainset_infos[trainset]['ended']))
        if clip_start < clip_end:
            timeline = GES.Timeline.new_audio_video()
            layer = timeline.append_layer()
            clip = layer.add_asset(input, 0,
                (clip_start - input_start).seconds * Gst.SECOND,
                (clip_end - clip_start).seconds * Gst.SECOND,
                GES.TrackType.UNKNOWN)
            timeline.commit()
            pipeline = GES.Pipeline()
            pipeline.set_timeline(timeline)

            #pipeline.set_state(Gst.State.NULL)
            if not pipeline.set_render_settings('file:///tmp/output.mp4',
                encoding_profile):
                raise argparse.ArgumentTypeError("Not a valid media file")
            pipeline.set_mode(GES.PipelineFlags.RENDER)
            pipeline.set_state(Gst.State.PLAYING)

            bus = pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message",
                lambda bus, message: handle_message(bus, message, loop))

            loop.run()



def valid_time(s):
    try:
        return arrow.get(s, 'DD.MM.YYYY HH:mm:ss')
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def handle_message(bus, message, loop):
    if message.type == Gst.MessageType.EOS:
        loop.quit()
    elif message.type == Gst.MessageType.ERROR:
        error = message.parse_error()
        print error
        loop.quit()


if __name__ == "__main__":
    main()

