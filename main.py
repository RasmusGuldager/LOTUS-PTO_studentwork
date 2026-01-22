from pypylon import pylon
import cv2, time

from config_loader import load_config


class camera_control:
    def __init__(self):
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.camera.Open()
        self.check_for_input()


    def snap_pic(self):
        self.camera.StartGrabbingMax(1)

        while self.camera.IsGrabbing():
            grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            if grabResult.GrabSucceeded():
                img = grabResult.Array
                
                while True:
                    user_input = input("Press s to save the image, v to view or q to quit: ")

                    if user_input == 's':
                        timestamp = time.strftime("%Y%m%d-%H%M%S")
                        filename = f"image_{timestamp}.png"
                        cv2.imwrite(f'{filename}', img)
                        print(f"Image saved as {filename}")
                    elif user_input == 'v':
                        cv2.imshow('Captured Image', img)
                        cv2.waitKey(0)
                        cv2.destroyAllWindows()
                    elif user_input == 'q':
                        break
                    else:
                        print("Invalid input. Please try again.")

            grabResult.Release()
        self.camera.Close()


    def stream(self):
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly) 

        # Converter til OpenCV format (fra Basler format til BGR/RGB)
        converter = pylon.ImageFormatConverter()
        converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        print("Live view kører... Tryk på 'q' for at afslutte.")

        while self.camera.IsGrabbing():
            grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            if grabResult.GrabSucceeded():
                # Konverter billedet til et format OpenCV kan forstå (numpy array)
                image = converter.Convert(grabResult)
                frame = image.GetArray()

                # Vis billedet i et vindue
                cv2.imshow('Basler ace 2 Live View', frame)

                # Stop hvis brugeren trykker på 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            grabResult.Release()

        # Ryd op
        self.camera.StopGrabbing()

        cv2.destroyAllWindows()


    def update_settings(self):
        load_config(self.camera)

    
    def check_for_input(self):
        try:
            while True:
                user_input = input("Enter 'p' to take a picture, 's' to start live view, or 'q' to quit: ")
                if user_input == 'p':
                    self.snap_pic()
                elif user_input == 's':
                    self.stream()
                elif user_input == 'q':
                    break
                else:
                    print("Invalid input. Please try again.")

        finally:
            print("Lukker kameraet")
            if hasattr(self, 'camera') and self.camera.IsOpen():
                self.camera.Close()



if __name__ == "__main__":
    camera_control()


