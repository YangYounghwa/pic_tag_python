

from PIL import Image


class ResizePad:
    def __init__(self,size=(256,128),fill=0):
        self.target_h, self.target_w = size
        self.fill = fill
    def __call__(self,img):
        orig_w, orig_h = img.size
        scale = min(self.target_w/orig_w, self.target_h/orig_h)
        new_w, new_h = int(orig_w * scale),int(orig_h*scale)

        img = img.resize((new_w,new_h), Image.BILINEAR)

        new_img = Image.new("RGB",(self.target_w,self.target_h),(self.fill,)*3)
        paste_x = (self.target_w-new_w)//2
        paste_y = (self.target_h-new_h)//2
        new_img.paste(img,(paste_x,paste_y))

        return new_img