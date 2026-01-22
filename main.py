from pypylon import pylon
import cv2, time, threading, os

from config_loader import update_settings


class camera_control:
    def __init__(self):
        self.camera = pylon.InstantCamera(
            pylon.TlFactory.GetInstance().CreateFirstDevice()
        )
        self.camera.Open()
        self.camera_mutex = threading.Lock()

        update_settings(self.camera)
        self.run_in_thread(self.auto_pic_snapper, 60)
        self.check_for_input()

    def snap_pic(self, user: bool = False) -> None:
        with self.camera_mutex:
            self.camera.StartGrabbingMax(1)

            grabResult = self.camera.RetrieveResult(
                5000, pylon.TimeoutHandling_ThrowException
            )

        if grabResult.GrabSucceeded():
            img = grabResult.Array

            if user:
                while True:
                    user_input = input(
                        "Press s to save the image, v to view or q to quit: "
                    )

                    if user_input == "s":
                        timestamp = time.strftime("%Y%m%d-%H%M%S")
                        filename = f"image_{timestamp}.png"
                        full_path = os.path.join("./User_images", filename)
                        cv2.imwrite(full_path, img)
                        print(f"Image saved as {full_path}")
                    elif user_input == "v":
                        cv2.imshow("Captured Image", img)
                        cv2.waitKey(0)
                        cv2.destroyAllWindows()
                    elif user_input == "q":
                        break
                    else:
                        print("Invalid input. Please try again.")
            else:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"image_{timestamp}.png"
                full_path = os.path.join("./Captured_images", filename)
                cv2.imwrite(full_path, img)

        grabResult.Release()

    def stream(self) -> None:
        with self.camera_mutex:
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

            # Converter til OpenCV format (fra Basler format til BGR/RGB)
            converter = pylon.ImageFormatConverter()
            converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

            print("Live view kører... Tryk på 'q' for at afslutte.")

            prev_time = time.time()

            while self.camera.IsGrabbing():
                grabResult = self.camera.RetrieveResult(
                    5000, pylon.TimeoutHandling_ThrowException
                )

                if grabResult.GrabSucceeded():
                    # Konverter billedet til et format OpenCV kan forstå (numpy array)
                    image = converter.Convert(grabResult)
                    frame = image.GetArray()

                    # Calculate FPS
                    current_time = time.time()
                    fps_actual = 1 / (current_time - prev_time)
                    prev_time = current_time

                    # Overlay FPS text on the image
                    cv2.putText(
                        frame,
                        f"FPS: {fps_actual:.1f}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2,
                    )

                    # Vis billedet i et vindue
                    cv2.imshow("Basler ace 2 Live View", frame)

                    # Stop hvis brugeren trykker på 'q'
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                grabResult.Release()

            # Ryd op
            self.camera.StopGrabbing()

        cv2.destroyAllWindows()

    def check_for_input(self) -> None:
        try:
            while True:
                user_input = input(
                    "Enter 'p' to take a picture, 's' to start live view, 'u' to update settings, or 'q' to quit: "
                )
                if user_input == "p":
                    self.snap_pic(user=True)
                elif user_input == "s":
                    self.stream()
                elif user_input == "u":
                    update_settings(self.camera)
                elif user_input == "q":
                    break
                else:
                    print("Invalid input. Please try again.")

        finally:
            print("Lukker kameraet")
            if hasattr(self, "camera") and self.camera.IsOpen():
                self.camera.Close()

    def auto_pic_snapper(self, interval: int) -> None:
        while True:
            self.snap_pic(user=False)
            time.sleep(interval)

    @staticmethod
    def run_in_thread(func, *args) -> threading.Thread:
        """General worker function to run a function in a thread"""
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()
        return thread


if __name__ == "__main__":
    camera_control()
