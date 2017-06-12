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
    parser.add_argument('-S', '--soft', action='store_true',
        help='softsubs')
    parser.add_argument('-a', '--align',
        choices=['L', 'R'], default='R',
        help='Alignment')
    parser.add_argument('-m', '--mute', action='store_const',
        const=GES.TrackType.VIDEO, default=GES.TrackType.UNKNOWN,
        help='Stumm')
    parser.add_argument('-r', '--rotate', action='store_true',
        help='Drehen')
    helpers.add_db_arguments(parser, False)
    helpers.add_db_arguments(parser, True)    
    args = parser.parse_args()
    if args.align == 'R':
        args.align = '2'
    else:
        args.align = '0'

    Gst.init(None)
    GES.init()
    loop = GLib.MainLoop()
    discoverer = GstPbutils.Discoverer.new(600 * Gst.SECOND)
    db_generic = helpers.db(args.dbgen)
    db_ts = helpers.db(args.dbts)
    media_uri = 'file://' + args.media
    directory = args.media + '_SlicedAt_' + arrow.now().format('DDMMYYYYHHmmss')
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

    trainset_infos = helpers.trainset_infos(db_ts)
    for trainset_name in trainset_infos:
        info = trainset_infos[trainset_name]
        trainset = db_ts[trainset_name]
        trainset_start_us = helpers.endpoint(
            trainset, { '_id' : { '$ne' : info['_id'] } }, True) / 1e6
        trainset_stop_us = helpers.endpoint(trainset, {}, False) / 1e6
        #trainset_start = arrow.get(info['created'])
        trainset_stop = arrow.get(info['ended'])
        trainset_start = trainset_stop.shift(
            seconds=-(trainset_stop_us - trainset_start_us))
        clip_start = max(input_start, trainset_start)
        clip_stop = min(input_stop, trainset_stop)
        if clip_start < clip_stop:
            clip_duration = clip_stop - clip_start
            offset = trainset_start_us
            #clip_stop_us - (trainset_stop - clip_start).seconds

            clip_name = ('SLICE_' +
                info['experiment']['id'] + '_' +
                info['parcours']['id'] + '_' +
                info['parcours']['subject']['id'] + '_' +
                trainset)
            subtitle_file = clip_name + '.vtt'
            subtitle = aeidon.Subtitle(aeidon.modes.TIME)
            intro_stop = helpers.endpoint(trainset,  {'step': {"$exists": True}}, True)
            format = 'HH:mm:ss.SSS'
            subtitle.start = arrow.get(0).format(format)
            subtitle.end = arrow.get((intro_stop / 1e6) - offset).format(format)
            main_text = (trainset_name + '\n' +
                info['experiment']['id'] + ' [' +
                info['parcours']['subject']['id'] + ', ' +
                info['parcours']['observer']['id'] + ']\n \n')
            subtitle.main_text = main_text
            subtitles = aeidon.Project()
            subtitles.subtitles.append(subtitle)

            step = 1
            for exercise in helpers.exercises(db_gen, info['parcours']['id']):
                mutation = helpers.mutation(db_gen, exercise)
                filter = { 'step' :  step }
                start = helpers.endpoint(trainset, filter, True)
                stop = helpers.endpoint(trainset, {'step': {"$gt": step}}, True)
                if not stop:
                    stop = helpers.endpoint(trainset, filter, False)
                if not start:
                    step += 1
                    continue
                subtitle = aeidon.Subtitle(aeidon.modes.TIME)
                subtitle.start = arrow.get((start / 1e6) - offset).format(format)
                subtitle.end = arrow.get((stop / 1e6) - offset).format(format)
                subtitle.main_text += (main_text +
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
                
            subtitle = aeidon.Subtitle(aeidon.modes.TIME)
            concl_start = helpers.endpoint(trainset,  {'step': {"$exists": True}}, False)
            subtitle.start = arrow.get((concl_start / 1e6) - offset).format(format)
            subtitle.end = arrow.get(clip_duration.seconds + 3600).format(format)
            # +3600 is a workaround for bug in subparse
            subtitle.main_text = main_text
            subtitles.subtitles.append(subtitle)

            subtitles_ass = aeidon.files.new(aeidon.formats.WEBVTT,
                directory + '/' + subtitle_file, 'utf_8')
            #subtitles_ass.header = re.sub(
            #    '2, 30, 30, 30, 0$', args.align + ', 30, 30, 30, 0',
            #    subtitles_ass.header)
            subtitles.save_main(subtitles_ass)

            timeline = GES.Timeline.new_audio_video()
            
            if not args.soft:
                overlay_layer = timeline.append_layer()
                overlay = GES.EffectClip.new(
                    'textoverlay name=o valignment=2 font-desc="Sans" ' +
                    'auto-resize=false halignment=' + args.align +
                    ' line-alignment=' + args.align +
                    ' filesrc location=' + directory + '/' + subtitle_file + 
                    ' ! typefind ! subparse ! o.text_sink o.', 'identity')
                overlay.set_duration((clip_start - input_start).seconds * Gst.SECOND)
                overlay.set_start(0)
                overlay_layer.add_clip(overlay)
            input_layer = timeline.append_layer()
            clip = input_layer.add_asset(media, 0,
                (clip_start - input_start).seconds * Gst.SECOND,
                (clip_duration.seconds + 1) * Gst.SECOND,
                args.mute)

            if args.rotate:
                rotate = GES.Effect.new('videoflip')
                rotate.set_child_property('video-direction', 3)
                clip.add(rotate)
            timeline.commit_sync()

            pipeline = GES.Pipeline()
            pipeline.set_timeline(timeline)
            if not pipeline.set_render_settings(
                'file://' + directory + '/' + clip_name + '.mp4',
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
            if not args.soft:
                os.remove(directory + '/' + subtitle_file)


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


if __name__ == "__main__":
    main()

