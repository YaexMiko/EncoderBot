import os
import time
import ffmpeg
from subprocess import Popen, PIPE
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

def get_codec(filepath, channel='v:0'):
    """
    Get the codec information for a specific channel (video or audio) in a file.
    """
    output = check_output(['ffprobe', '-v', 'error', '-select_streams', channel,
                            '-show_entries', 'stream=codec_name,codec_tag_string', '-of', 
                            'default=nokey=1:noprint_wrappers=1', filepath])
    return output.decode('utf-8').split()

def encode(filepath, progress_callback=None):
    """
    Encode a video file to HEVC (x265) format with progress updates.
    """
    basefilepath, extension = os.path.splitext(filepath)
    output_filepath = basefilepath + '.[HEVC].mp4'
    assert output_filepath != filepath, "Output filepath should not be the same as input filepath"
    
    # If the output file already exists, overwrite it
    if os.path.isfile(output_filepath):
        print(f'File "{output_filepath}" already exists, overwriting 🐭')
        os.remove(output_filepath)
    
    print(f'Processing file: {filepath}')
    
    # Always encode to HEVC, even if the video is already in HEVC format
    video_opts = '-c:v libx265 -crf 28 -tag:v hvc1 -preset ultrafast -threads 8'
    
    # Get the audio channel codec
    audio_codec = get_codec(filepath, channel='a:0')
    if not audio_codec:
        audio_opts = ''  # No audio stream
    elif audio_codec[0] == 'aac':
        audio_opts = '-c:a copy'  # Copy AAC audio stream
    else:
        audio_opts = '-c:a aac -b:a 128k'  # Transcode non-AAC audio to AAC
    
    # Run FFMPEG command to encode the video
    command = ['ffmpeg', '-i', filepath] + video_opts.split() + audio_opts.split() + [output_filepath]
    process = Popen(command, stderr=PIPE, universal_newlines=True)
    
    total_duration = get_duration(filepath)
    start_time = time.time()
    
    for line in process.stderr:
        if 'time=' in line:
            time_str = line.split('time=')[1].split()[0]
            current_time = sum(float(x) * 60 ** i for i, x in enumerate(reversed(time_str.split(':'))))
            progress = (current_time / total_duration) * 100
            elapsed_time = time.time() - start_time
            eta = (elapsed_time / progress) * (100 - progress) if progress > 0 else 0
            
            if progress_callback:
                progress_callback(progress, eta)
    
    process.wait()
    
    # Remove the original file after encoding
    os.remove(filepath)
    
    return output_filepath

def get_thumbnail(in_filename, path, ttl):
    """
    Generate a thumbnail from a video file at a specific time.
    """
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
        print(f'Error generating thumbnail: {e.stderr.decode()}')
        return None

def get_duration(filepath):
    """
    Get the duration of a video file in seconds.
    """
    metadata = extractMetadata(createParser(filepath))
    if metadata and metadata.has("duration"):
        return metadata.get('duration').seconds
    return 0

def get_width_height(filepath):
    """
    Get the width and height of a video file.
    """
    metadata = extractMetadata(createParser(filepath))
    if metadata and metadata.has("width") and metadata.has("height"):
        return metadata.get("width"), metadata.get("height")
    return 1280, 720  # Default resolution if metadata is not available
