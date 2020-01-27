from PIL import Image
import numpy as np

from service import default_out_dir


def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))


# assets for debugging
DBG_blur_file = 'assets/4x5hard.png'
DBG_blur_file = 'assets/4x5soft.png'
DBG_blur_file = 'assets/border.png'
DBG_blur_file = 'out/test.png'

im_frame = Image.open(DBG_blur_file)
imgData = im_frame.getdata()

loaded = im_frame.load()

originalImg = np.array(imgData, np.uint8)
newImg = np.array(imgData, np.uint8)

width = imgData.size[0]
height = imgData.size[1]
nb = [
    [],
    [],
    [],
    [],
    # [],
    [],
    [],
    [],
    [],
]
for column in range(0, width):
    for row in range(0, height):
        # pixel raster around center pixel
        # 0 1 2
        # 3 c 4
        # 5 6 7
        centerIdx = column + row * width
        leftCol = clamp(column - 1, 0, width - 1)
        rightCol = clamp(column + 1, 0, width - 1)
        upperRow = clamp(row - 1, 0, height - 1)
        lowerRow = clamp(row + 1, 0, height - 1)

        nb[0] = originalImg[leftCol + upperRow * width]
        nb[1] = originalImg[column + upperRow * width]
        nb[2] = originalImg[rightCol + upperRow * width]

        nb[3] = originalImg[leftCol + row * width]
        centerPixel = originalImg[centerIdx]
        nb[4] = originalImg[rightCol + row * width]

        nb[5] = originalImg[leftCol + lowerRow * width]
        nb[6] = originalImg[column + lowerRow * width]
        nb[7] = originalImg[rightCol + lowerRow * width]

        # check alpha channel
        if centerPixel[3] == 0:

            valid_pixels = list(filter(lambda x: x[3] > 0, nb))
            lenValPix = len(valid_pixels)
            if lenValPix > 0:
                # take average of red channel
                avg = 0
                for ii in range(lenValPix):
                    avg += valid_pixels[ii][0]
                avg = int(avg / lenValPix)
                loaded[column, row] = (avg, avg, avg, 255)

        elif centerPixel[3] < 255:
            # make semitransparent areas fully visible
            loaded[column, row] = (centerPixel[0], centerPixel[1],
                                   centerPixel[2], 255)
    print("column %d of %d" % (column, width))

# pythonArray = newImg.tolist()
# newImgAsImage = Image.fromarray(pythonArray, 'RGBA')
# convertedImage = newImgAsImage.convert("RGB")
# convertedImage.save("art.png")

im_frame.save(default_out_dir + "padded.png")

im_frame.show()
print("huhu")
