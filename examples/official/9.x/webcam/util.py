import numpy as np
import cv2 as cv
from scipy import ndimage
import math

# https://stackoverflow.com/questions/19068085/shift-image-content-with-opencv
def shiftX(image, shift):
    for i in range(image.shape[1] -1, image.shape[1] - shift, -1):
        image = np.roll(image, -1, axis=1)
        image[:, -1] = 0
    
    return image

def shiftY(image, shift):
    for i in range(image.shape[0] -1, image.shape[0] - shift, -1):
        image = np.roll(image, -1, axis=0)
        image[-1, :] = 0
    
    return image

def is_moving(current_frame, previous_frame):
    frame_diff = cv.absdiff(current_frame, previous_frame)

    diff_gray = cv.cvtColor(frame_diff, cv.COLOR_BGR2GRAY)

    diff_blur = cv.GaussianBlur(diff_gray, (5,5), 0)

    _, thresh = cv.threshold(diff_blur, 20, 255, cv.THRESH_BINARY)

    thresh = cv.dilate(thresh, None, iterations=2)

    contours, _ = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    total = 0
    for contour in contours:
        x, y, w, h = cv.boundingRect(contour)
        total += cv.contourArea(contour)

    if total > (current_frame.shape[0] * current_frame.shape[1] * 0.5):
        return True

    return False

def rotate_image(image, angle, center = None, scale = 1.0):
    rotated = ndimage.rotate(image, angle)
    rotated = rotated[0: image.shape[0], 0: image.shape[1]]
    return rotated

def concat_images(images, axis=1):
    if axis == 0:
        return np.concatenate(images, axis=0)
    elif axis == 1:
        return np.concatenate(images, axis=1)
    else:
        raise ValueError('axis must be 0 or 1')

def rotate_point(point, rotationDiff):
    x = (point[0] * math.cos(rotationDiff)) - (point[1] * math.sin(rotationDiff))
    y = (point[0] * math.sin(rotationDiff)) + (point[1] * math.cos(rotationDiff))
    return (x, y)

def zoom_image(image, zoom_factor):
    height, width = image.shape[:2]
    new_height = int(height * zoom_factor)
    new_width = int(width * zoom_factor)
    zoomed = cv.resize(image, (new_width, new_height))
    zoomed = zoomed[0: image.shape[0], 0: image.shape[1]]
    return zoomed

def transform_point(points, matrix):
    """Transforms the point using the given matrix."""
    all = []
    for point in points:
        x, y = point
        transformed = np.dot(matrix, [x, y, 1])
        
        all.append((int(transformed[0] / transformed[2]), int(transformed[1] / transformed[2])))
    
    return all

def perspective_correction(img, pts):
    # Define the 4 points where the image will be warped to.
    # For a typical use-case, this would be a rectangle.
    # We'll use the dimensions of the input image, but you can adjust this
    # as needed to set the dimensions of the output image.
    rect = np.array([
        [0, 0],
        [img.shape[1] - 1, 0],
        [img.shape[1] - 1, img.shape[0] - 1],
        [0, img.shape[0] - 1]
    ], dtype="float32")

    # Compute the perspective transform matrix
    matrix = cv.getPerspectiveTransform(pts, rect)

    # Perform the perspective warp
    warped = cv.warpPerspective(img, matrix, (img.shape[1], img.shape[0]))

    return warped