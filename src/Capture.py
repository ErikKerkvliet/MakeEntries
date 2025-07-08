import os
import os.path
import urllib
import random
from urllib.parse import unquote


class Capture:

    def __init__(self, glv, f):
        self.glv = glv
        path = f'{self.glv.app_folder}/{self.glv.vndb_id}/samples'
        rand = random.randint(0, 10000000000)
        temp_path = f'{path}/.{rand}tmp'

        f = urllib.parse.unquote(f)

        if not os.path.isdir(temp_path):
            command = f'mkdir {temp_path}'
            os.system(command)

        videos = f.split("' '")

        for video in videos:
            video = video.strip().strip("'").strip('"')
            command = f'ffprobe -i "{video}" -show_entries format=duration -v quiet -of csv="p=0"'

            duration = os.popen(command).readlines()
            if not duration:
                raise ValueError(f"ffprobe gaf geen resultaat terug voor: {video}")
            between = float(duration[0]) / 23
            per_second = 1 / between

            command = f'ffmpeg -i "{video}" -r {per_second} -vf scale=-1:120 -vcodec png "{temp_path}/capture_tmp-%002d.png"'
            os.system(command)

            out = video.split('/')[-1][:-4]

            command = f'montage -geometry +3+1 -shadow {temp_path}/capture_tmp*.png "{path}/{out}.jpg"'
            os.system(command)

        command = f'rm -rf {temp_path}'
        os.system(command)
