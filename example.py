from hik_camera import *

mch = MultipleCameraHelper(config_path='example_config.json')
mch.open_devices()

mch.save_image("topCamera", "./top.jpg", nJpgQuality=90)
mch.save_image("leftCamera", "./left.jpg", nJpgQuality=90)
mch.save_image("rightCamera", "./right.jpg", nJpgQuality=90)

mch.stop_and_close()
