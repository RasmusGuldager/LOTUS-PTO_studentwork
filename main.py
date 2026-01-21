from pypylon import pylon
import cv2

from config_loader import load_config


camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()    


def snap_pics(numberOfImagesToGrab):
    camera.StartGrabbingMax(numberOfImagesToGrab)

    while camera.IsGrabbing():
        grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        if grabResult.GrabSucceeded():
            # Access the image data.
            print("SizeX: ", grabResult.Width)
            print("SizeY: ", grabResult.Height)
            img = grabResult.Array
            print("Gray value of first pixel: ", img[0, 0])

        grabResult.Release()
    camera.Close()


def stream():
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly) 

    # Converter til OpenCV format (fra Basler format til BGR/RGB)
    converter = pylon.ImageFormatConverter()
    converter.OutputPixelFormat = pylon.PixelType_BGR8packed
    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    print("Live view kører... Tryk på 'q' for at afslutte.")

    while camera.IsGrabbing():
        grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

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
    camera.StopGrabbing()
    camera.Close()
    cv2.destroyAllWindows()



if __name__ == "__main__":
    load_config(camera)

    #snap_pics(1)

    stream()


