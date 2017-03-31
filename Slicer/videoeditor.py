#!/usr/bin/env python

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
import helpers

def main():
    parser = argparse.ArgumentParser(description='videoeditor.')
    parser.add_argument('media', help='media file')
    parser.add_argument('-s', '--start',
        help='start UTC - format "01.01.2000 01:02:03"',
        required=True, type=valid_time)
    parser.add_argument('-a', '--align',
        choices=['left', 'right'], default='right',
        help='Alignment')
    helpers.add_db_arguments(parser)
    args = parser.parse_args()
    if args.align == 'right':
        args.align = '9'
    else:
        args.align = '7'

    Gst.init(None)
    GES.init()
    loop = GLib.MainLoop()
    discoverer = GstPbutils.Discoverer.new(600 * Gst.SECOND)

    media_uri = 'file://' + args.media
    encoding_profile = GstPbutils.EncodingProfile.from_discoverer(
        discoverer.discover_uri(media_uri))
    input = GES.UriClipAsset.request_sync(media_uri)

    input_start = args.start
    input_stop = input_start.shift(seconds=(input.get_duration()/Gst.SECOND))

    db = helpers.make_db(args)
    trainset_infos = helpers.get_trainset_infos(db)
    for trainset in trainset_infos:
        info = trainset_infos[trainset]
        clip_start_us = helpers.get_endpoint(
            db[trainset], { '_id' : { '$ne' : info['_id'] } }, True) / 1e6
        clip_stop_us = helpers.get_endpoint(db[trainset], {}, False) / 1e6
        #trainset_start = arrow.get(info['created'])
        trainset_stop = arrow.get(info['ended'])
        trainset_start = trainset_stop.shift(
            seconds=-(clip_stop_us - clip_start_us))
        clip_start = max(input_start, trainset_start)
        clip_stop = min(input_stop, trainset_stop)
        if clip_start < clip_stop:
            clip = ('CLIP_' + trainset + '_' +
                info['experiment']['id'] + '_' +
                info['parcours']['observer']['id'] + '_' +
                info['parcours']['subject']['id'] + '_' +
                info['parcours']['id'])
            subtitle_file = clip + '.ass'
            subtitles = aeidon.Project()

            offset = clip_start_us
            #clip_stop_us - (trainset_stop - clip_start).seconds
            print(trainset)
            step = 1
            for exercise in helpers.get_exercises(db, info['parcours']['id']):
                mutation = helpers.get_mutation(db, exercise)
                filter = { 'step' :  step }
                start = helpers.get_endpoint(db[trainset], filter, True)
                stop = helpers.get_endpoint(db[trainset], filter, False)
                if not start:
                    step += 1
                    continue
                format = 'HH:mm:ss.SSS'
                subtitle = aeidon.Subtitle(aeidon.modes.TIME)
                subtitle.start = arrow.get((start / 1e6) - offset).format(format)
                subtitle.end = arrow.get((stop / 1e6) - offset).format(format)
                subtitle.main_text = (trainset + '\n' +
                    info['experiment']['id'] + ' [' +
                    info['parcours']['subject']['id'] + ', ' +
                    info['parcours']['observer']['id'] + ']\n' +
                    info['parcours']['id'] + '/' + str(step) + ' > ' +
                    mutation['id'] + '\nR:' +
                    info['parcours']['subject']['hands']['right']['id'])
                if 'hands' in mutation:
                    host, spot, gesture, instruction = helpers.get_info(
                        db, mutation['hands'], 'right')
                    subtitle.main_text += ('[' +
                        host + '>' + spot + ', ' + gesture + ']')
                subtitle.main_text += ('\nL:' +
                    info['parcours']['subject']['hands']['left']['id'])
                if 'hands' in mutation:
                    host, spot, gesture, instruction = helpers.get_info(
                        db, mutation['hands'], 'left')
                    subtitle.main_text += ('[' +
                        host + '>' + spot + ', ' + gesture + ']')

                subtitles.subtitles.append(subtitle)
                step += 1

            subtitles_ass = aeidon.files.new(aeidon.formats.ASS,
                subtitle_file, 'utf_8')
            subtitles_ass.header = re.sub(
                '2, 30, 30, 30, 0$', args.align + ', 0, 0, 0, 0',
                subtitles_ass.header)
            subtitles.save_main(subtitles_ass)

            timeline = GES.Timeline.new_audio_video()
            layer = timeline.append_layer()
            layer.add_asset(input, 0,
                (clip_start - input_start).seconds * Gst.SECOND,
                ((clip_stop - clip_start).seconds + 1) * Gst.SECOND,
                GES.TrackType.UNKNOWN)
            subtitle_overlay = GES.EffectClip.new('filesrc location=' +
                subtitle_file + ' ! subtitleoverlay', '')
            layer.add_clip(subtitle_overlay)
            timeline.commit()

            pipeline = GES.Pipeline()
            pipeline.set_timeline(timeline)
            if not pipeline.set_render_settings(
                'file://' + os.getcwd() + '/' + clip + '.mp4',
                encoding_profile):
                raise argparse.ArgumentTypeError("Not a valid media file")
            pipeline.set_mode(GES.PipelineFlags.RENDER)
            pipeline.set_state(Gst.State.PLAYING)

            bus = pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message",
                lambda bus, message: handle_message(bus, message, loop))

            loop.run()

            pipeline.set_state(Gst.State.NULL)


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
        print(error)
        loop.quit()


if __name__ == "__main__":
    main()

