from pypylon import pylon
import cv2, time, threading, os, logging

from Camera.config_loader import config_loader


class CameraControl:
    def __init__(self, auto_interval=None) -> None:
        self.camera = pylon.InstantCamera(
            pylon.TlFactory.GetInstance().CreateFirstDevice()
        )
        self.camera.Open()
        self.camera_mutex = threading.Lock()

        self.logger = logging.getLogger(__name__)
        self.update_settings()

        for folder in ["./User_images", "./Captured_images"]:
            os.makedirs(folder, exist_ok=True)

        if auto_interval is not None:
            self.run_in_thread(self.auto_pic_snapper, auto_interval)

    def snap_pic(self, user: bool = False) -> None:
        """
        Captures a single frame from the Basler camera and saves it to disk.
        If called by the user, prompts for saving or viewing the image.

        Args:
            user (bool): If True, saves to './User_images'. If False, saves to './Captured_images'.

        Raises:
            TimeoutException: If the camera fails to return a frame within 5000ms.
        """

        try:
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
                            self.logger.info(f"User saved image as {full_path}")

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
                    self.logger.info(f"Auto saved image as {full_path}")

            else:
                self.logger.error("Failed to grab image.")

            grabResult.Release()

        except Exception as e:
            self.logger.error(f"Error capturing image: {e}")
            self.try_reconnect()

    def stream(self) -> None:
        """
        Starts a live video stream from the Basler camera using OpenCV.

        Raises:
            TimeoutException: If the camera fails to return a frame within 5000ms.
        """

        try:
            with self.camera_mutex:
                self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

                # Converter til OpenCV format (fra Basler format til BGR/RGB)
                converter = pylon.ImageFormatConverter()
                converter.OutputPixelFormat = pylon.PixelType_BGR8packed
                converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

                print("Live view kører... Tryk på 'q' for at afslutte.")
                self.logger.info("Live view started.")

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
                            self.logger.info("Live view stopped by user.")
                            break
                    else:
                        self.logger.error("Failed to grab image (stream).")

                    grabResult.Release()

                # Ryd op
                self.camera.StopGrabbing()

            cv2.destroyAllWindows()
        
        except Exception as e:
            self.logger.error(f"Error during live stream: {e}")
            self.try_reconnect()

    def auto_pic_snapper(self, interval: int) -> None:
        """
        Automatically takes pictures at specified intervals.

        Args:
            interval (int): Time in seconds between each picture.

        Raises:
            TimeoutException: If the camera fails to return a frame within 5000ms.
        """

        self.logger.info(f"Auto picture snapper started with interval {interval} seconds.")
        
        while True:
            self.snap_pic(user=False)
            time.sleep(interval)

    def update_settings(self) -> None:
        """Loads camera settings from config file."""

        try:
            config_loader(self.camera)
            self.logger.info("Camera settings updated.")
        
        except Exception as e:
            self.try_reconnect()
    

    def try_reconnect(self):
        """Attempts to re-open the camera if lost."""

        try:
            self.camera = pylon.InstantCamera(
            pylon.TlFactory.GetInstance().CreateFirstDevice()
        )
            self.camera.Close()
            self.camera.Open()
            self.update_settings()
            self.logger.info("Camera reconnected successfully.")

        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}")


    @staticmethod
    def run_in_thread(func, *args) -> threading.Thread:
        """General worker function to run a function in a thread"""

        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()
        return thread


if __name__ == "__main__":
    camera_control = CameraControl()

    try:
        while True:
            user_input = input(
                "Enter 'p' to take a picture, 's' to start live view, 'u' to update settings, or 'q' to quit: "
            )
            if user_input == "p":
                camera_control.snap_pic(user=True)
            elif user_input == "s":
                camera_control.stream()
            elif user_input == "u":
                camera_control.update_settings()
            elif user_input == "q":
                break
            else:
                print("Invalid input. Please try again.")

    finally:
        print("Lukker kameraet")
        if hasattr(camera_control, "camera") and camera_control.camera.IsOpen():
            camera_control.camera.Close()
