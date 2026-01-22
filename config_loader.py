import yaml


def load_config(camera):
    with open("config.yaml", 'r') as file:
        config = yaml.safe_load(file)

    image_settings = config['image_settings']
    video_settings = config['video_settings']
    lighting_settings = config['lighting_settings']
    auto_settings = config['auto_settings']


    # Image settings
    camera.Width.Value = image_settings['width']
    camera.Height.Value = image_settings['height']
    camera.OffsetX.Value = image_settings['offset_x']
    camera.OffsetY.Value = image_settings['offset_y']


    camera.ExposureTime.Value = lighting_settings['exposure_time']
    camera.Gain.Value = lighting_settings['gain']


    # Video settings
    if video_settings['enable_acquisition'] == "on":
        camera.AcquisitionFrameRateEnable.Value = True
        camera.AcquisitionFrameRate.Value = video_settings['acquisition_fps']
    elif video_settings['enable_acquisition'] == "off":
        camera.AcquisitionFrameRateEnable.Value = False
    else:
        raise ValueError("Invalid enable_acquisition value in config.yaml")


    # Auto settings
    camera.AutoTargetBrightness.Value = auto_settings['auto_brightness_target']


    if auto_settings['auto_exposure'] == "off":
        camera.ExposureAuto.Value = "Off"
    elif auto_settings['auto_exposure'] == "once":
        camera.ExposureAuto.Value = "Once"
    elif auto_settings['auto_exposure'] == "continuous":
        camera.ExposureAuto.Value = "Continuous"
    else:
        raise ValueError("Invalid auto_exposure value in config.yaml")

    camera.AutoExposureTimeLowerLimit.Value = auto_settings['auto_exposure_lower_limit']
    camera.AutoExposureTimeUpperLimit.Value = auto_settings['auto_exposure_upper_limit']
    

    if auto_settings['auto_function'] == "min_gain":
        camera.AutoFunctionProfile.value = "MinimizeGain"
    elif auto_settings['auto_function'] == "min_exposure":
        camera.AutoFunctionProfile.value = "MinimizeExposureTime"
    else:
        raise ValueError("Invalid auto_function value in config.yaml")


    if auto_settings['auto_gain'] == "off":
        camera.GainAuto.Value = "Off"
    elif auto_settings['auto_gain'] == "once":
        camera.GainAuto.Value = "Once"
    elif auto_settings['auto_gain'] == "continuous":
        camera.GainAuto.Value = "Continuous"
    else:
        raise ValueError("Invalid auto_gain value in config.yaml")

    camera.AutoGainLowerLimit.Value = auto_settings['auto_gain_lower_limit']
    camera.AutoGainUpperLimit.Value = auto_settings['auto_gain_upper_limit']


    # Pixel format
    if image_settings['pixel_format'] == "mono8":
        camera.PixelFormat.Value = "Mono8"
    elif image_settings['pixel_format'] == "mono10":
        camera.PixelFormat.Value = "Mono10"
    elif image_settings['pixel_format'] == "mono10p":
        camera.PixelFormat.Value = "Mono10p"
    elif image_settings['pixel_format'] == "mono12p":
        camera.PixelFormat.Value = "Mono12p"
    elif image_settings['pixel_format'] == "rgb8":
        camera.PixelFormat.Value = "RGB8"
    elif image_settings['pixel_format'] == "brg8":
        camera.PixelFormat.Value = "BGR8"
    elif image_settings['pixel_format'] == "ycbcr422":
        camera.PixelFormat.Value = "YCbCr422"
    elif image_settings['pixel_format'] == "bayer_gr8":
        camera.PixelFormat.Value = "BayerGR8"
    elif image_settings['pixel_format'] == "bayer_rg8":
        camera.PixelFormat.Value = "BayerRG8"
    elif image_settings['pixel_format'] == "bayer_gb8":
        camera.PixelFormat.Value = "BayerGB8"
    elif image_settings['pixel_format'] == "bayer_bg8":
        camera.PixelFormat.Value = "BayerBG8"
    elif image_settings['pixel_format'] == "bayer_gr10":
        camera.PixelFormat.Value = "BayerGR10"
    elif image_settings['pixel_format'] == "bayer_rg10":
        camera.PixelFormat.Value = "BayerRG10"
    elif image_settings['pixel_format'] == "bayer_gb10":
        camera.PixelFormat.Value = "BayerGB10"
    elif image_settings['pixel_format'] == "bayer_bg10":
        camera.PixelFormat.Value = "BayerBG10"
    elif image_settings['pixel_format'] == "bayer_gr10p":
        camera.PixelFormat.Value = "BayerGR10p"
    elif image_settings['pixel_format'] == "bayer_rg10p":
        camera.PixelFormat.Value = "BayerRG10p"
    elif image_settings['pixel_format'] == "bayer_gb10p":
        camera.PixelFormat.Value = "BayerGB10p"
    elif image_settings['pixel_format'] == "bayer_bg10p":
        camera.PixelFormat.Value = "BayerBG10p"
    elif image_settings['pixel_format'] == "bayer_gr12":
        camera.PixelFormat.Value = "BayerGR12"
    elif image_settings['pixel_format'] == "bayer_rg12":
        camera.PixelFormat.Value = "BayerRG12"
    elif image_settings['pixel_format'] == "bayer_gb12":
        camera.PixelFormat.Value = "BayerGB12"
    elif image_settings['pixel_format'] == "bayer_bg12":
        camera.PixelFormat.Value = "BayerBG12"
    elif image_settings['pixel_format'] == "bayer_gr12p":
        camera.PixelFormat.Value = "BayerGR12p"
    elif image_settings['pixel_format'] == "bayer_rg12p":
        camera.PixelFormat.Value = "BayerRG12p"
    elif image_settings['pixel_format'] == "bayer_gb12p":
        camera.PixelFormat.Value = "BayerGB12p"
    elif image_settings['pixel_format'] == "bayer_bg12p":
        camera.PixelFormat.Value = "BayerBG12p"
    else:
        raise ValueError("Invalid pixel_format value in config.yaml")
    
