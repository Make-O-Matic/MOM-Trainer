#!/usr/bin/env python

import os
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

    subtitle_header = '''[Script Info]
PlayResY: 1024

[V4 Styles]

[Events]
Format: Start, End, Text
'''

    db = helpers.make_db(args)
    trainset_infos = helpers.get_trainset_infos(db)
    for trainset in trainset_infos:
        info = trainset_infos[trainset]
        clip_start = max(input_start, arrow.get(info['created']))
        clip_end = min(input_stop, arrow.get(info['ended']))
        if clip_start < clip_end:
            clip_file = ('CLIP_' + trainset + '_' +
                info['experiment']['id'] + '_' +
                info['parcours']['observer']['id'] + '_' +
                info['parcours']['subject']['id'] + '_' +
                info['parcours']['id'])
            subtitle_file = clip_file + '.ass'
            subtitles = open(subtitle_file, 'w')
            subtitles.write(subtitle_header)

            for exercise in helpers.get_exercises(db, info['parcours']['id']):
                mutation = helpers.get_mutation(db, exercise)
                subtitles.write('0:00:01.00,0:00:02.00,' + mutation['id'] + '\n')

            subtitles.close()

            timeline = GES.Timeline.new_audio_video()
            layer = timeline.append_layer()
            layer.add_asset(input, 0,
                (clip_start - input_start).seconds * Gst.SECOND,
                (clip_end - clip_start).seconds * Gst.SECOND,
                GES.TrackType.UNKNOWN)
            subtitle_overlay = GES.EffectClip.new('filesrc location=' +
                subtitle_file + ' ! subtitleoverlay', '')
            layer.add_clip(subtitle_overlay)
            timeline.commit()

            pipeline = GES.Pipeline()
            pipeline.set_timeline(timeline)
            if not pipeline.set_render_settings(
                'file://' + os.getcwd() + '/' + clip_file + '.mp4',
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
        exit()
    elif message.type == Gst.MessageType.ERROR:
        error = message.parse_error()
        print(error)
        loop.quit()


if __name__ == "__main__":
    main()

