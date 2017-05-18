#!/usr/bin/python

import warnings
warnings.filterwarnings('ignore')
import os
import argparse
import re
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstPbutils', '1.0')
gi.require_version('GES', '1.0')
from gi.repository import GLib, Gst, GstPbutils, GES
import arrow
import aeidon
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import helpers

def main():
    parser = argparse.ArgumentParser(description='videoeditor.')
    parser.add_argument('media', help='media file')
    parser.add_argument('-s', '--start',
        help='Startzeitpunkt UTC - Format "01.01.2000 01:02:03"',
        required=True, type=valid_datetime)
    parser.add_argument('-a', '--align',
        choices=['left', 'right'], default='right',
        help='Alignment')
    parser.add_argument('-m', '--mute', action='store_const',
        const=GES.TrackType.VIDEO, default=GES.TrackType.UNKNOWN,
        help='Stumm')
    parser.add_argument('-r', '--rotate', action='store_const',
        const=True, default=False,
        help='Drehen')
    helpers.add_db_arguments(parser)
    args = parser.parse_args()
    if args.align == 'right':
        args.align = '9'
    else:
        args.align = '7'

    Gst.init(None)
    GES.init()
    loop = GLib.MainLoop()
    GLib.log_set_handler(None, GLib.LogLevelFlags.LEVEL_CRITICAL, discard, None)
    discoverer = GstPbutils.Discoverer.new(600 * Gst.SECOND)
    db = helpers.db(args)
    media_uri = 'file://' + args.media
    directory = args.media + arrow.now().format('-DDMMYYYYHHmmss')
    os.mkdir(directory)
    encoding_profile = GstPbutils.EncodingProfile.from_discoverer(
        discoverer.discover_uri(media_uri))
    if args.rotate:
        for profile in encoding_profile.get_profiles():
            caps = profile.get_format()
            flipped_caps = caps.copy_nth(0)
            info = flipped_caps.get_structure(0)
            if info.get_value('height'):
                flipped_caps.set_value('width', info.get_value('height'))
                flipped_caps.set_value('height', info.get_value('width'))
            profile.set_format(flipped_caps)

    media = GES.UriClipAsset.request_sync(media_uri)

    input_start = args.start
    input_stop = input_start.shift(seconds=(media.get_duration()/Gst.SECOND))

    trainset_infos = helpers.trainset_infos(db)
    for trainset in trainset_infos:
        info = trainset_infos[trainset]
        clip_start_us = helpers.endpoint(
            db[trainset], { '_id' : { '$ne' : info['_id'] } }, True) / 1e6
        clip_stop_us = helpers.endpoint(db[trainset], {}, False) / 1e6
        #trainset_start = arrow.get(info['created'])
        trainset_stop = arrow.get(info['ended'])
        trainset_start = trainset_stop.shift(
            seconds=-(clip_stop_us - clip_start_us))
        clip_start = max(input_start, trainset_start)
        clip_stop = min(input_stop, trainset_stop)
        if clip_start < clip_stop:
            clip_duration = clip_stop - clip_start
            offset = clip_start_us
            #clip_stop_us - (trainset_stop - clip_start).seconds

            clip_name = ('CLIP_' + trainset + '_' +
                info['experiment']['id'] + '_' +
                info['parcours']['observer']['id'] + '_' +
                info['parcours']['subject']['id'] + '_' +
                info['parcours']['id'])
            subtitle_file = clip_name + '.ass'
            subtitle = aeidon.Subtitle(aeidon.modes.TIME)
            format = 'HH:mm:ss.SSS'
            subtitle.start = arrow.get(0).format(format)
            subtitle.end = arrow.get(clip_duration.seconds + 1).format(format)
            subtitle.main_text = (trainset + '\n' +
                info['experiment']['id'] + ' [' +
                info['parcours']['subject']['id'] + ', ' +
                info['parcours']['observer']['id'] + ']')
            subtitles = aeidon.Project()
            subtitles.subtitles.append(subtitle)

            step = 1
            for exercise in helpers.exercises(db, info['parcours']['id']):
                mutation = helpers.mutation(db, exercise)
                filter = { 'step' :  step }
                start = helpers.endpoint(db[trainset], filter, True)
                stop = helpers.endpoint(db[trainset], filter, False)
                if not start:
                    step += 1
                    continue
                subtitle = aeidon.Subtitle(aeidon.modes.TIME)
                subtitle.start = arrow.get((start / 1e6) - offset).format(format)
                subtitle.end = arrow.get((stop / 1e6) - offset).format(format)
                subtitle.main_text += ('\n' +
                    info['parcours']['id'] + '/' + str(step) + ' > ' +
                    mutation['id'])
                if 'hands' in mutation:
                    text, instruction = helpers.info(
                        db, mutation['hands'], 'left', ', ')
                    if text != None:
                        subtitle.main_text += ('\nL:' +
                            info['parcours']['subject']['hands']['left']['id'])
                    if text:
                        subtitle.main_text += ('[' + text + ']')
                    text, instruction = helpers.info(
                        db, mutation['hands'], 'right', ', ')
                    if text != None:
                        subtitle.main_text += ('\nR:' +
                            info['parcours']['subject']['hands']['right']['id'])
                    if text:
                        subtitle.main_text += ('[' + text + ']')

                subtitles.subtitles.append(subtitle)
                step += 1

            subtitles_ass = aeidon.files.new(aeidon.formats.ASS,
                directory + '/' + subtitle_file, 'utf_8')
            subtitles_ass.header = re.sub(
                '2, 30, 30, 30, 0$', args.align + ', 30, 30, 30, 0',
                subtitles_ass.header)
            subtitles.save_main(subtitles_ass)

            timeline = GES.Timeline.new_audio_video()
            input_layer = timeline.append_layer()
            clip = input_layer.add_asset(media, 0,
                (clip_start - input_start).seconds * Gst.SECOND,
                (clip_duration.seconds + 1) * Gst.SECOND,
                args.mute)
            if args.rotate:
                effect = GES.Effect.new('videoflip')
                effect.set_child_property('video-direction', 1)
                clip.add(effect)
            timeline.commit_sync()

            pipeline = GES.Pipeline()
            pipeline.set_timeline(timeline)
            if not pipeline.set_render_settings(
                'file://' + directory + '/' + clip_name + '.mp4',
                encoding_profile):
                raise argparse.ArgumentTypeError("Not a valid media file")
            pipeline.set_mode(GES.PipelineFlags.RENDER)
            pipeline.set_state(Gst.State.PLAYING)

            #compoGst.debug_bin_to_dot_file(pipeline, Gst.DebugGraphDetails.ALL, "tmp")

            bus = pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message",
                lambda bus, message: handle_message(bus, message, loop))

            loop.run()

            pipeline.set_state(Gst.State.NULL)


def valid_datetime(str):
    try:
        return arrow.get(str, 'DD.MM.YYYY HH:mm:ss')
    except ValueError:
        message = "Not a valid date and time: '{0}'.".format(str)
        raise argparse.ArgumentTypeError(message)


def handle_message(bus, message, loop):
    if message.type == Gst.MessageType.EOS:
        loop.quit()
    elif message.type == Gst.MessageType.ERROR:
        error = message.parse_error()
        print(error)
        loop.quit()

def discard(log_domain, log_level, message, user_data):
    return

if __name__ == "__main__":
    main()

