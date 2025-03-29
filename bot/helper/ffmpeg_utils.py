import os
import sys
import json
import time
import ffmpeg
from subprocess import call, check_output
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from ffmpeg_progress_yield import FfmpegProgress

def get_codec(filepath, channel='v:0'):
    output = check_output(['ffprobe', '-v', 'error', '-select_streams', channel,
                         '-show_entries', 'stream=codec_name,codec_tag_string', '-of', 
                         'default=nokey=1:noprint_wrappers=1', filepath])
    return output.decode('utf-8').split()

def encode(filepath, crf=28, preset='medium', audio_bitrate='128k', progress_callback=None):
    basefilepath, extension = os.path.splitext(filepath)
    output_filepath = basefilepath + '.[HEVC]' + '.mp4'
    assert(output_filepath != filepath)
    if os.path.isfile(output_filepath):
        print('Skipping "{}": File Already Exists 🐭'.format(output_filepath))
        return None
    print(filepath)
    
    video_codec = get_codec(filepath, channel='v:0')
    if video_codec == []:
        print('Skipping No Video Codec Reported 🐭')
        return None
        
    if video_codec[0] == 'hevc':
        if video_codec[1] == 'hvc1':
            print('Skipping :( Already In HEVC')
            return None
        else:
            video_opts = '-c:v copy -tag:v hvc1'
    else:
        video_opts = f'-c:v libx265 -crf {crf} -tag:v hvc1 -preset {preset} -threads 8'
    
    audio_codec = get_codec(filepath, channel='a:0')
    if audio_codec == []:
        audio_opts = ''
    elif audio_codec[0] == 'aac':
        audio_opts = '-c:a copy'
    else:
        audio_opts = f'-c:a aac -b:a {audio_bitrate}'
    
    cmd = ['ffmpeg', '-i', filepath] + video_opts.split() + audio_opts.split() + [output_filepath]
    
    if progress_callback:
        ff = FfmpegProgress(cmd)
        for progress in ff.run_command_with_progress():
            progress_callback(progress)
    else:
        call(cmd)
    
    os.remove(filepath)
    return output_filepath

def get_thumbnail(in_filename, path, ttl, custom_thumbnail=None):
    if custom_thumbnail:
        return custom_thumbnail
        
    out_filename = os.path.join(path, str(time.time()) + ".jpg")
    open(out_filename, 'a').close()
    try:
        (
            ffmpeg
            .input(in_filename, ss=ttl)
            .output(out_filename, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return out_filename
    except ffmpeg.Error as e:
        return None

def get_duration(filepath):
    metadata = extractMetadata(createParser(filepath))
    if metadata.has("duration"):
        return metadata.get('duration').seconds
    else:
        return 0

def get_width_height(filepath):
    metadata = extractMetadata(createParser(filepath))
    if metadata.has("width") and metadata.has("height"):
        return metadata.get("width"), metadata.get("height")
    else:
        return 1280, 720
