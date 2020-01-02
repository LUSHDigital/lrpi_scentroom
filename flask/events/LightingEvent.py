import os, math
from colorsys import rgb_to_hsv
import json
from pysrt import SubRipFile, SubRipItem, SubRipTime
from pydub import AudioSegment


_CONSISTENT_SRT_NAME = "01_scentroom"
_IDLE_NAME = "idle"
_RGB_R_TUNING = 1.0
_RGB_G_TUNING = 1.0
_RGB_B_TUNING = 1.0
_JSON_INDENT = 2

class LightingEvent:

    #set colour value on init
    def __init__(self, col_val):
        if col_val is not None:
            #convert hex value to rgb
            self.hex = col_val
            col_val = col_val.lstrip('#')
            rgb = tuple(int(col_val[i:i+2], 16) for i in (0, 2, 4))
            r = float(rgb[0])
            g = float(rgb[1])
            b = float(rgb[2])
            self.r = float(rgb[0])
            self.g = float(rgb[1])
            self.b = float(rgb[2])
            #convert rgb value to hsv
            h,s,v = rgb_to_hsv(r,g,b)
            self.rgb_col_val = str(int(_RGB_R_TUNING*r)) + ', ' + str(int(_RGB_G_TUNING*g)) + ', ' + str(int(_RGB_B_TUNING*b)) + ', ' + str(int(255))
            self.hsv_col_val = str(h) + ',' + str(s) + ',' + str(v)
            self.rgbw_col_val = self.rgb_to_rgbw(r,g,b)

    def to_json_file(self, path="/media/usb/uploads/content.json"):
        with open(path, 'r+') as f:
            content = json.load(f)
            content['color_hex'] = self.hex # <--- add `id` value.
            f.seek(0)        # <--- should reset file position to the beginning.
            json.dump(content, f, indent=_JSON_INDENT)
            f.truncate()     # remove remaining part

    def to_idle_mp3(self, path, file_name=_IDLE_NAME):
        """ Create a silent mp3 file for the idle loop for the Scentroom """
        silent_audio_left = AudioSegment.silent(duration=15000, frame_rate=44100)
        silent_audio_right = AudioSegment.silent(duration=15000, frame_rate=44100)
        silent_audio = AudioSegment.from_mono_audiosegments(silent_audio_left, silent_audio_right)
        completeName = os.path.join(path, file_name + ".mp3")
        silent_audio.export(completeName, format="mp3", bitrate="128k", tags={"album": "Scentrooms", "artist": "Lushroom Pi", "title": "Silence"})

    # creates srt file with col val at path for playing when the scentroom is idle
    def to_idle_srt(self, path, file_name=_IDLE_NAME, hue=False, dmx=True):
        """ Create a lighting SRT file with the idle colour loop for the Scentroom """
        print("Output to idle SRT file " +str(self.hsv_col_val )+ " " +str(self.rgb_col_val) )
        if (self.hsv_col_val is not None) or (self.rgb_col_val is not None):
            completeName = os.path.join(path, file_name + ".srt")
            print(completeName)
            encoding="utf_8"
            srtFile = SubRipFile(path=completeName)
            t = 0
            k = 0
            t_incr = 0.025
            for j in [math.sin(i/70.0) for i in range(100)]:
                r = int(self.r * j)
                g = int(self.g * j)
                b = int(self.b * j)
                rgb_col_val = str(int(_RGB_R_TUNING*r)) + ', ' + str(int(_RGB_G_TUNING*g)) + ', ' + str(int(_RGB_B_TUNING*b)) + ', ' + str(int(0))
                rgbw_col_val = self.rgb_to_rgbw(r,g,b)
                cmds_str = "DMX1(" + rgbw_col_val + ", " + rgb_col_val + ")\n"
                item = SubRipItem(k, text=cmds_str)
                item.start.seconds = t
                item.end.seconds = t#+t_incr
                t += t_incr
                k += 1
                if srtFile!=None:
                    srtFile.append(item)
            t += t_incr
            k += 1
            for j in [math.sin(i/70.0) for i in range(100,0,-1)]:
                r = int(self.r * j)
                g = int(self.g * j)
                b = int(self.b * j)
                rgb_col_val = str(int(_RGB_R_TUNING*r)) + ', ' + str(int(_RGB_G_TUNING*g)) + ', ' + str(int(_RGB_B_TUNING*b)) + ', ' + str(int(0))
                rgbw_col_val = self.rgb_to_rgbw(r,g,b)
                cmds_str = "DMX1(" + rgbw_col_val + ", " + rgb_col_val + ")\n"
                item = SubRipItem(k, text=cmds_str)
                item.start.seconds = t
                item.end.seconds = t#+t_incr
                t += t_incr
                k += 1
                if srtFile!=None:
                    srtFile.append(item)
            t += t_incr
            cmds_str = "DMX1(0,0,0,0,0,0,0,0)"
            item = SubRipItem(k, text=cmds_str)
            item.start.seconds = t
            item.end.seconds = t#+t_incr
            if srtFile!=None:
                srtFile.append(item)
                srtFile.save(completeName, encoding=encoding)
            return True
        return False

    # creates srt file with col val at path
    def to_srt(self, path, file_name=_CONSISTENT_SRT_NAME, hue=False, dmx=True):

        print("Output to SRT file " +str(self.hsv_col_val )+ " " +str(self.rgb_col_val) )
        if (self.hsv_col_val is not None) or (self.rgb_col_val is not None):
            completeName = os.path.join(path, file_name + ".srt")
            #srt file for write operation
            srt_file = open(completeName, "w")
            #srt seq num
            srt_file.write("1\n")
            #srt marker
            srt_file.write("00:00:00,000 --> 00:02:00,000\n")
            #srt HUE col val
            if hue:
                srt_file.write("HUE1(" + self.hsv_col_val + ");\n")
            #srt DMX col val
            if dmx:
                srt_file.write("DMX1(" + self.rgbw_col_val + ", " + self.rgb_col_val + ")\n")
            srt_file.close()
            return True

        return False


    #converts rgb values to rgbw
    def rgb_to_rgbw(self, Ri, Gi, Bi):
        Wo = min(Ri,Gi,Bi)
        Ro = Ri - Wo
        Go = Gi - Wo
        Bo = Bi - Wo
        return(str(int(Ro)) + ', ' + str(int(Go)) + ', ' + str(int(Bo)) + ', ' + str(int(Wo)))
