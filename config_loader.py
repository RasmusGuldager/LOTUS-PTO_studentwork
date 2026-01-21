import yaml

def load_config(camera):
    with open("config.yaml", 'r') as file:
        config = yaml.safe_load(file)

    image_settings = config['image_settings']
    lighting_settings = config['lighting_settings']
    auto_settings = config['auto_settings']


    camera.Width.Value = image_settings['width']
    camera.Height.Value = image_settings['height']
    camera.OffsetX.Value = image_settings['offset_x']
    camera.OffsetY.Value = image_settings['offset_y']


    camera.ExposureTime.Value = lighting_settings['exposure_time']
    camera.Gain.Value = lighting_settings['gain']


    camera.AutoTargetBrightness.Value = auto_settings['auto_brightness_target']


    if auto_settings['auto_exposure'] == "off":
        camera.ExposureAuto.Value = "Off"
    elif auto_settings['auto_exposure'] == "once":
        camera.ExposureAuto.Value = "Once"
    elif auto_settings['auto_exposure'] == "continuous":
        camera.ExposureAuto.Value = "Continuous"

    camera.AutoExposureTimeLowerLimit.Value = auto_settings['auto_exposure_lower_limit']
    camera.AutoExposureTimeUpperLimit.Value = auto_settings['auto_exposure_upper_limit']
    

    if auto_settings['auto_function'] == "min_gain":
        camera.AutoFunctionProfile.value = "MinimizeGain"
    elif auto_settings['auto_function'] == "min_exposure":
        camera.AutoFunctionProfile.value = "MinimizeExposureTime"


    if auto_settings['auto_gain'] == "off":
        camera.GainAuto.Value = "Off"
    elif auto_settings['auto_gain'] == "once":
        camera.GainAuto.Value = "Once"
    elif auto_settings['auto_gain'] == "continuous":
        camera.GainAuto.Value = "Continuous"

    camera.AutoGainLowerLimit.Value = auto_settings['auto_gain_lower_limit']
    camera.AutoGainUpperLimit.Value = auto_settings['auto_gain_upper_limit']