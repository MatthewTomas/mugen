import logging
import pprint
import shutil

import essentia
import essentia.standard
import numpy as np

import mugen.audio.utility as a_util
import mugen.constants as c
import mugen.exceptions as ex
import mugen.paths as paths
import mugen.utility as util


def get_beat_stats(audio_file):
    """
    Extracts beat locations and intervals from an audio file
    """
    print("Processing audio beat patterns...")

    # Load audio
    audio = a_util.load_audio(audio_file)
    
    # Get beat stats from audio
    rhythm_extractor = essentia.standard.RhythmExtractor2013()
    duration_extractor = essentia.standard.Duration()

    rhythm = rhythm_extractor(audio)
    duration = duration_extractor(audio)
    beat_intervals = rhythm[4]

    # Fill in start and end intervals
    start_interval = rhythm[1][0]
    end_interval = duration - rhythm[1][len(rhythm[1]) - 1]
    beat_intervals = np.concatenate([[start_interval], beat_intervals, [end_interval]])
   
    beat_stats = {'bpm':rhythm[0], 'beat_locations':rhythm[1], 'bpm_estimates':rhythm[3], 
                  'beat_intervals':beat_intervals}

    logging.debug("\n")
    logging.debug("Beats per minute: {}".format(pprint.pformat(beat_stats['bpm'])))
    logging.debug("Beat locations: {}".format(pprint.pformat(beat_stats['beat_locations'].tolist())))
    logging.debug("Beat intervals: {}".format(pprint.pformat(beat_stats['beat_intervals'].tolist())))
    logging.debug("BPM estimates: {}".format(pprint.pformat(beat_stats['bpm_estimates'].tolist())))
    logging.debug("\n")

    return beat_stats

def get_beat_interval_groups(beat_intervals, speed_multiplier, speed_multiplier_offset):
    """
    Group together beat intervals based on speed_multiplier by
    -> splitting individual beat intervals for speedup
    -> combining adjacent beat intervals for slowdown
    -> using original beat interval for normal speed
    """
    beat_interval_groups = [] 
    beat_intervals = beat_intervals.tolist()
    
    total_beat_intervals_covered = 0
    for index, beat_interval in enumerate(beat_intervals):
        if index < total_beat_intervals_covered:
            continue

        beat_interval_group, num_beat_intervals_covered = get_beat_interval_group(beat_interval, index, beat_intervals, 
                                                                                  speed_multiplier, speed_multiplier_offset)
        beat_interval_groups.append(beat_interval_group)
        total_beat_intervals_covered += num_beat_intervals_covered

    logging.debug("\nbeat_interval_groups: {}\n".format(pprint.pformat(beat_interval_groups)))

    return beat_interval_groups

""" HELPER FUNCTIONS """

def get_beat_interval_group(beat_interval, index, beat_intervals, 
                            speed_multiplier, speed_multiplier_offset):
    """
    Assign beat intervals to groups based on speed_multiplier
    """
    # Combine adjacent beat intervals
    if speed_multiplier < 1:
        desired_num_intervals = speed_multiplier.denominator
        # Apply offset to first group
        if index == 0 and speed_multiplier_offset:
            desired_num_intervals -= speed_multiplier_offset

        remaining_intervals = len(beat_intervals) - index
        if remaining_intervals < desired_num_intervals:
            desired_num_intervals = remaining_intervals

        interval_combo = sum(beat_intervals[index:index + desired_num_intervals])
        interval_combo_numbers = range(index, index + desired_num_intervals)
        beat_interval_group = {'intervals':[interval_combo], 'beat_interval_numbers':interval_combo_numbers}
        num_beat_intervals_covered = desired_num_intervals
    # Split up the beat interval
    elif speed_multiplier > 1:
        speedup_factor = speed_multiplier.numerator
        interval_fragment = beat_interval/speedup_factor
        interval_fragments = [interval_fragment] * speedup_factor
        beat_interval_group = {'intervals':interval_fragments, 'beat_interval_numbers':index}
        num_beat_intervals_covered = 1
    # Use the original beat interval
    else:
        beat_interval_group = {'intervals':[beat_interval], 'beat_interval_numbers':index}
        num_beat_intervals_covered = 1

    return beat_interval_group, num_beat_intervals_covered

def flatten_beat_interval_groups(beat_interval_groups):
    flattened_beat_locations = []

    for beat_interval_group in beat_interval_groups:
        for interval in beat_interval_group['intervals']:
            prev_beat_location = flattened_beat_locations[-1] if flattened_beat_locations else 0
            next_beat_location = prev_beat_location + interval
            flattened_beat_locations.append(next_beat_location)

    return flattened_beat_locations

def create_temp_offset_audio_file(audio_file, offset):
    """
    Create a temporary new audio file with the given offset to use for the music video
    """
    output_path = paths.generate_temp_file_path(paths.file_extension_from_path(audio_file))

    # Generate new temporary audio file with offset
    ffmpeg_cmd = [
            util.get_ffmpeg_binary(),
            '-i', audio_file,
            '-ss', str(offset),
            '-acodec', 'copy',
            output_path
          ]
          
    try:
        util.execute_ffmpeg_command(ffmpeg_cmd)
    except ex.FFMPEGError as e:
        print(f"Failed to create temporary audio file with specified offset {offset}. Error Code: {e.return_code}, "
              f"Error: {e}")
        raise

    return output_path

def create_temp_marked_audio_file(audio_file, beat_locations):
    output_path = paths.generate_temp_file_path(paths.ESSENTIA_ONSETS_AUDIO_EXTENSION)

    # Load audio
    audio = a_util.load_audio(audio_file)
    onsets_marker = essentia.standard.AudioOnsetsMarker(onsets = beat_locations)
    mono_writer = essentia.standard.MonoWriter(filename = output_path, bitrate = c.DEFAULT_AUDIO_BITRATE)

    # Create preview audio file
    marked_audio = onsets_marker(audio)
    mono_writer(marked_audio)

    return output_path

def preview_audio_beats(audio_file, beat_locations):
    marked_audio_file = create_temp_marked_audio_file(audio_file, beat_locations)
    shutil.move(marked_audio_file, paths.audio_preview_path(audio_file))