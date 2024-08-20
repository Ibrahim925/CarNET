import cv2
import numpy as np
import cvlib as cv
import time
import websockets
import json


def thresholding(img):
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_white = np.array([0, 55, 48])
    upper_white = np.array([179, 255, 255])
    mask_white = cv2.bitwise_not(cv2.inRange(img_hsv, lower_white, upper_white))
    return mask_white


def warp_img(img, points, w, h, inv=False):
    pts1 = np.float32(points)
    pts2 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    if inv:
        matrix = cv2.getPerspectiveTransform(pts2, pts1)
    else:
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
    img_warp = cv2.warpPerspective(img, matrix, (w, h))
    return img_warp


def nothing(a):
    pass


def initialize_trackbars(initial_trackbar_vals, wt=480, ht=240):
    cv2.namedWindow("Trackbars")
    cv2.resizeWindow("Trackbars", 360, 240)
    cv2.createTrackbar(
        "Width Top", "Trackbars", initial_trackbar_vals[0], wt // 2, nothing
    )
    cv2.createTrackbar("Height Top", "Trackbars", initial_trackbar_vals[1], ht, nothing)
    cv2.createTrackbar(
        "Width Bottom", "Trackbars", initial_trackbar_vals[2], wt // 2, nothing
    )
    cv2.createTrackbar(
        "Height Bottom", "Trackbars", initial_trackbar_vals[3], ht, nothing
    )


def val_trackbars(wt=480):
    width_top = cv2.getTrackbarPos("Width Top", "Trackbars")
    height_top = cv2.getTrackbarPos("Height Top", "Trackbars")
    width_bottom = cv2.getTrackbarPos("Width Bottom", "Trackbars")
    height_bottom = cv2.getTrackbarPos("Height Bottom", "Trackbars")
    points = np.float32(
        [
            (width_top, height_top),
            (wt - width_top, height_top),
            (width_bottom, height_bottom),
            (wt - width_bottom, height_bottom),
        ]
    )
    return points


def draw_points(img, points):
    for x in range(4):
        cv2.circle(
            img, (int(points[x][0]), int(points[x][1])), 15, (0, 0, 255), cv2.FILLED
        )
    return img


def get_histogram(img, min_per=0.1, display=False, region=1):
    if region == 1:
        hist_values = np.sum(img, axis=0)
    else:
        hist_values = np.sum(img[img.shape[0] // region :, :], axis=0)

    max_value = np.max(hist_values)
    min_value = min_per * max_value

    index_array = np.where(hist_values >= min_value)
    base_point = int(np.average(index_array))

    if display:
        img_hist = np.zeros((img.shape[0], img.shape[1], 3), np.uint8)
        for x, intensity in enumerate(hist_values):
            cv2.line(
                img_hist,
                (x, img.shape[0]),
                (x, int(img.shape[0] - intensity // 255 // region)),
                (255, 0, 255),
                1,
            )
            cv2.circle(
                img_hist, (base_point, img.shape[0]), 20, (0, 255, 255), cv2.FILLED
            )
        return base_point, img_hist

    return base_point


def stack_images(scale, img_array):
    rows = len(img_array)
    cols = len(img_array[0])
    rows_available = isinstance(img_array[0], list)
    width = img_array[0][0].shape[1]
    height = img_array[0][0].shape[0]
    if rows_available:
        for x in range(0, rows):
            for y in range(0, cols):
                if img_array[x][y].shape[:2] == img_array[0][0].shape[:2]:
                    img_array[x][y] = cv2.resize(
                        img_array[x][y], (0, 0), None, scale, scale
                    )
                else:
                    img_array[x][y] = cv2.resize(
                        img_array[x][y],
                        (img_array[0][0].shape[1], img_array[0][0].shape[0]),
                        None,
                        scale,
                        scale,
                    )
                if len(img_array[x][y].shape) == 2:
                    img_array[x][y] = cv2.cvtColor(img_array[x][y], cv2.COLOR_GRAY2BGR)
        image_blank = np.zeros((height, width, 3), np.uint8)
        hor = [image_blank] * rows
        for x in range(0, rows):
            hor[x] = np.hstack(img_array[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if img_array[x].shape[:2] == img_array[0].shape[:2]:
                img_array[x] = cv2.resize(img_array[x], (0, 0), None, scale, scale)
            else:
                img_array[x] = cv2.resize(
                    img_array[x],
                    (img_array[0].shape[1], img_array[0].shape[0]),
                    None,
                    scale,
                    scale,
                )
            if len(img_array[x].shape) == 2:
                img_array[x] = cv2.cvtColor(img_array[x], cv2.COLOR_GRAY2BGR)
        hor = np.hstack(img_array)
        ver = hor
    return ver


def is_object_detected(img):
    # Detect common objects in the image using cvlib
    _, label, _ = cv.detect_common_objects(img, model="yolov3-tiny")

    # If any labels are detected, return True
    if label:
        return True

    # No objects detected
    return False


async def handle_object_on_lane(droid):
    uri = "ws://localhost:9000"

    async with websockets.connect(uri) as websocket:
        # Emit the event
        await websocket.send(json.dumps({"type": "event", "event": "object_detected"}))
        print("Obstacle event sent")

        # Await response from the server
        response = await websocket.recv()
        data = json.loads(response)
        print(data)
        if data["action"] == "accept":
            print("User accepted. Executing actions.")
            # User accepted, execute the specific actions
            droid.set_speed(10)
            time.sleep(1.2)
            droid.set_speed(0)
            droid.spin(-90, 1)
            droid.set_speed(20)
            time.sleep(2)
            droid.set_speed(0)
            droid.spin(90, 1)
            droid.set_speed(20)
            time.sleep(3.2)
            droid.set_speed(0)
            droid.spin(90, 1)
            droid.set_speed(20)
            time.sleep(2.3)
            droid.set_speed(0)
            droid.spin(-90, 1)
            return True
        elif data["action"] == "deny":
            print("User declined. Skipping actions.")
            return False
