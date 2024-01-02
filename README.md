# Description

This repository contains an example of utilizing multiple HIK robotics cameras using Python and Linux to save images as .jpg files. The code was tested with several MV-CS060-10UC-PRO, MV-CE050-30UC and MV-CE050-30UM cameras.

# Dependencies
1. The Machine Vision Software (MVS) should be installed first. It can be found at the official HIK robotics website: https://www.hikrobotics.com/en/machinevision/service/download
2. Check the folder `MvImport` after MVS installation - by default, it is located at `/opt/MVS/Samples/64/Python/MvImport`. If it's not, you will need to change the Line 4 of `hik_camera.py` with the correct path such as
   ```Python3
   sys.path.append("path/to/MvImport")
   ``` 
3. To set the camera parameters and make a naming for them the json file is using, the example can be found at `example_config.json`:

    ```Python3
    {
      "topCamera":  # the name that will be using to call this camera
      {
        "serial": "DA1444043",  # serial number of camera
        "exposure": 9500,  # exposure time in ms
        "gain": 10  # gain value in dB
      }, ...  # other cameras using same scheme
    ```

# Usage
You can find the full code of the example at `example.py`
1. Create an instance of `MultipleCameraHelper` and pass the path to config file as argument. Then open cameras.
    ``` Python3
    mch = MultipleCameraHelper(config_path='example_config.json')
    mch.open_devices()
    ```
2. Call `save_image` in your code at the moment you want to capture a frame. First argument is the name of camera according to config file. Second one is the path to save .jpg file. The third is quality of JPG file (from 50 to 99)
    ``` Python3
    mch.save_image("topCamera", "./top.jpg", nJpgQuality=90)
    ```
3. After you are done with cameras call `stop_and_close` to properly handle cameras instances.
    ``` Python3
    mch.stop_and_close()
    ```
