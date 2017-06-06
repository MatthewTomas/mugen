import os
from typing import Optional as Opt, List, Union

from moviepy.editor import VideoClip
from tqdm import tqdm

from mugen.utility import temp_file_enabled

DEFAULT_AUDIO_BITRATE = 320
DEFAULT_AUDIO_CODEC = 'mp3'

DEFAULT_VIDEO_PRESET = 'medium'
DEFAULT_VIDEO_CODEC = 'libx264'
DEFAULT_VIDEO_CRF = 18

DEFAULT_VIDEO_EXTENSION = '.mkv'


class VideoWriter:
    """
    Class for writing VideoClips and VideoSegments to file
    
    Parameters
    ----------   
    preset
        Sets the time that FFMPEG will spend optimizing compression while writing the video to file.
        Note that this does not impact the quality of the video, only the size of the video file. 
        So choose ultrafast when you are in a hurry and file size does not matter.
        Choices are: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow, placebo. 
          
    codec 
        Video codec to use when writing the music video to file.
        
    crf 
        Constant rate factor (quality) for the music video (0 - 51).
        
    audio_codec 
        Audio codec to use if no audio_file is provided.
        
    audio_bitrate 
        Audio bitrate (kbps) to use if no audio_file is provided.
        
    ffmpeg_params 
        Any additional ffmpeg parameters you would like to pass as a list of terms, 
        like ['-option1', 'value1', '-option2', 'value2']
    """
    preset: str
    codec: str
    crf: int
    audio_codec: str
    audio_bitrate: int
    ffmpeg_params: list

    def __init__(self, preset: str = DEFAULT_VIDEO_PRESET, codec: str = DEFAULT_VIDEO_CODEC,
                 crf: int = DEFAULT_VIDEO_CRF, audio_codec: str = DEFAULT_AUDIO_CODEC,
                 audio_bitrate: int = DEFAULT_AUDIO_BITRATE, ffmpeg_params: Opt[List[str]] = None):
        self.preset = preset
        self.codec = codec
        self.crf = crf
        self.audio_codec = audio_codec
        self.audio_bitrate = audio_bitrate
        self.ffmpeg_params = ffmpeg_params or []

    def write_video_clips_to_directory(self, video_clips: List[VideoClip], directory: str, *,
                                       file_extension: str = DEFAULT_VIDEO_EXTENSION, audio: Union[str, bool] = True,
                                       **kwargs):
        """
        Writes a list of video segments to files in the specified directory
        """
        for index, segment in enumerate(tqdm(video_clips)):
            output_path = os.path.join(directory, str(index) + file_extension)
            self.write_video_clip_to_file(segment, output_path, audio=audio, verbose=False, progress_bar=False,
                                          **kwargs)

    @temp_file_enabled('output_path', DEFAULT_VIDEO_EXTENSION)
    def write_video_clip_to_file(self, video_clip: VideoClip, output_path: Opt[str] = None, *,
                                 audio: Union[str, bool] = True, **kwargs):
        """
        Writes a video clip to file in the specified directory

        Parameters
        ----------
        video_clip

        output_path

        audio
            Audio for the video clip. Can be True to enable, False to disable, or an external audio file.

        kwargs
            List of other keyword arguments to pass to moviepy's write_videofile
        """
        # Prepend crf to ffmpeg_params
        ffmpeg_params = ['-crf', str(self.crf)] + self.ffmpeg_params
        audio_bitrate = str(self.audio_bitrate) + 'k'

        video_clip.write_videofile(output_path, audio=audio,
                                   preset=self.preset, codec=self.codec, audio_codec=self.audio_codec,
                                   audio_bitrate=audio_bitrate, ffmpeg_params=ffmpeg_params, **kwargs)

        return output_path
