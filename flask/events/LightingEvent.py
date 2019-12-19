import os
from colorsys import rgb_to_hsv
import json

_CONSISTENT_SRT_NAME = "01_scentroom"
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

    #creates srt file with col val at path
    def to_srt(self, path, file_name=_CONSISTENT_SRT_NAME, hue=False, dmx=True):

        print(str(self.hsv_col_val )+ " " +str(self.rgb_col_val) )
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
