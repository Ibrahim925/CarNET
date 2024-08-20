import time
import numpy as np
import cv2
from spherov2 import scanner
from spherov2.sphero_edu import SpheroEduAPI
import asyncio
import utils


def get_lane_curve(img, display=2):
    img_copy = img.copy()
    img_result = img.copy()

    img_thresh = utils.thresholding(img)

    h_t, w_t, _ = img.shape
    points = utils.val_trackbars()
    img_warp = utils.warp_img(img_thresh, points, w_t, h_t)

    img_warp_points = utils.draw_points(img_copy, points)

    object_detected = utils.is_object_detected(img)

    middle_point, img_hist = utils.get_histogram(
        img_warp, display=True, min_per=0.9, region=4
    )
    curve_average_point = utils.get_histogram(img_warp, min_per=0.9)

    curve_raw = curve_average_point - middle_point

    curve_list.append(curve_raw)
    if len(curve_list) > num_to_avg:
        curve_list.pop(0)
    curve = int(sum(curve_list) / len(curve_list))

    if display != 0:
        img_inv_warp = utils.warp_img(img_warp, points, w_t, h_t, inv=True)
        img_inv_warp = cv2.cvtColor(img_inv_warp, cv2.COLOR_GRAY2BGR)
        img_inv_warp[0 : h_t // 3, 0:w_t] = 0, 0, 0
        img_lane_color = np.zeros_like(img)
        img_lane_color[:] = 0, 255, 0
        img_lane_color = cv2.bitwise_and(img_inv_warp, img_lane_color)
        img_result = cv2.addWeighted(img_result, 1, img_lane_color, 1, 0)
        mid_y = 450
        cv2.putText(
            img_result,
            str(curve),
            (w_t // 2 - 80, 85),
            cv2.FONT_HERSHEY_COMPLEX,
            2,
            (255, 255, 255),
            3,
        )
        cv2.line(
            img_result,
            (w_t // 2, mid_y),
            (w_t // 2 + (curve * 3), mid_y),
            (255, 0, 255),
            5,
        )
        cv2.line(
            img_result,
            ((w_t // 2 + (curve * 3)), mid_y - 25),
            (w_t // 2 + (curve * 3), mid_y + 25),
            (0, 255, 0),
            5,
        )
        for x in range(-30, 30):
            w = w_t // 20
            cv2.line(
                img_result,
                (w * x + int(curve // 50), mid_y - 10),
                (w * x + int(curve // 50), mid_y + 10),
                (0, 0, 255),
                2,
            )
    if display == 2:
        img_stacked = utils.stack_images(
            0.7,
            (
                [img, img_warp_points, img_warp],
                [img_hist, img_lane_color, img_result],
            ),
        )
        cv2.imshow("", img_stacked)
    elif display == 1:
        cv2.imshow("Result", img_result)

    return curve, object_detected


def main():
    try:
        cap = None

        toy = scanner.find_toy()

        print("Toy found")

        with SpheroEduAPI(toy) as droid:
            cap = cv2.VideoCapture(1)

            print("Video capture obtained")

            initial_trackbar_values = [40, 120, 11, 201]

            utils.initialize_trackbars(initial_trackbar_values)

            print("Trackbars initialized")

            curr_angle = 0

            while True:
                success, frame = cap.read()

                if not success:
                    continue

                frame = cv2.resize(frame, (480, 240))

                curve, object_on_lane = get_lane_curve(frame)

                if curve < 0:
                    curve += 1

                if object_on_lane:
                    droid.roll(int(curr_angle), 20, 0.7)
                    moved = asyncio.run(utils.handle_object_on_lane(droid))

                    if not moved:
                        break
                    else:
                        continue

                curr_angle += curve

                droid.roll(int(curr_angle), 20, 1)

                time.sleep(0.5)

                key = cv2.waitKey(1)

                if key == 27:
                    break

    except scanner.ToyNotFoundError:
        print("Could not find toy")

    finally:
        cv2.destroyAllWindows()
        if not cap is None:
            cap.release()


if __name__ == "__main__":
    num_to_avg = 10
    curve_list = []
    SENSITIVITY = 2
    main()
