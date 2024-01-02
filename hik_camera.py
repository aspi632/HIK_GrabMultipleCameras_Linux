import sys
import json
import os

sys.path.append(os.getenv('MVCAM_SDK_PATH') + "/Samples/64/Python/MvImport")
from MvCameraControl_class import *
import MvErrorDefine_const as Errors


class MultipleCameraHelper:
    def __init__(self, config_path='config.json'):
        assert os.path.isfile(config_path), "Wrong config path " + config_path
        with open(config_path) as f:
            self.config = json.load(f)

        self.deviceList = MV_CC_DEVICE_INFO_LIST()
        memset(byref(self.deviceList), 0, sizeof(self.deviceList))
        MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, self.deviceList)
        assert self.deviceList.nDeviceNum == len(self.config), \
            f"Find {self.deviceList.nDeviceNum} / {len(self.config)} devices!"

        self.errors = {eval(item): item for item in dir(Errors) if not item.startswith("__")}

    def open_devices(self, verbose=True):
        for i in range(self.deviceList.nDeviceNum):
            camObj = MvCamera()
            devInfo = cast(self.deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            strSerialNumber = "".join([chr(p) for p in devInfo.SpecialInfo.stUsb3VInfo.chSerialNumber if p != 0])

            serialNumbersFromConfig = [self.config[key]["serial"] for key in self.config.keys()]
            assert strSerialNumber in serialNumbersFromConfig, "No such serial number in config " + strSerialNumber
            key = list(self.config.keys())[serialNumbersFromConfig.index(strSerialNumber)]
            if verbose:
                print('Opening', strSerialNumber, 'as a', key)

            ret = camObj.MV_CC_CreateHandle(devInfo)
            if ret != MV_OK:
                camObj.MV_CC_DestroyHandle()
                self.show_error(ret, "CreateHandle")

            ret = camObj.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
            if ret != MV_OK:
                self.show_error(ret, "OpenDevice")

            ret = camObj.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
            if ret != MV_OK:
                self.show_error(ret, "SetEnumValue")

            # Get/set exposure time
            stParamExposure = MVCC_FLOATVALUE()
            memset(byref(stParamExposure), 0, sizeof(MVCC_FLOATVALUE))
            ret = camObj.MV_CC_GetFloatValue("ExposureTime", stParamExposure)
            if ret != MV_OK:
                self.show_error(ret, "GetFloatValue (ExposureTime)")
            if stParamExposure.fCurValue != float(self.config[key]["exposure"]):
                ret = camObj.MV_CC_SetFloatValue("ExposureTime", float(self.config[key]["exposure"]))
                if ret != MV_OK:
                    self.show_error(ret, "SetFloatValue (ExposureTime)")

            # Get/set gain value
            stParamGain = MVCC_FLOATVALUE()
            memset(byref(stParamGain), 0, sizeof(MVCC_FLOATVALUE))
            ret = camObj.MV_CC_GetFloatValue("Gain", stParamGain)
            if ret != MV_OK:
                self.show_error(ret, "GetFloatValue (Gain)")
            if stParamGain.fCurValue != float(self.config[key]["gain"]):
                ret = camObj.MV_CC_SetFloatValue("Gain", float(self.config[key]["gain"]))
                if ret != MV_OK:
                    self.show_error(ret, "SetFloatValue (Gain)")

            # Get payload size
            stParam = MVCC_INTVALUE()
            memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))
            ret = camObj.MV_CC_GetIntValue("PayloadSize", stParam)
            if ret != MV_OK:
                self.show_error(ret, "Get Payload")
            nPayloadSize = stParam.nCurValue

            # Save the camera instance and payload value to corresponding key in config dict
            self.config[key]["cameraObject"] = camObj
            self.config[key]["nPayloadSize"] = nPayloadSize

    def save_image(self, key, filename, nJpgQuality=90, verbose=True):
        assert key in self.config.keys(), "Wrong camera key " + key
        assert os.path.isdir(os.path.dirname(filename)), "Wrong path " + filename
        if verbose and os.path.isfile(filename):
            print(filename, "will be overwritten")

        camera = self.config[key]["cameraObject"]
        nPayloadSize = self.config[key]["nPayloadSize"]

        ret = camera.MV_CC_StartGrabbing()
        if ret != MV_OK:
            self.show_error(ret, "StartGrabbing")

        stImageInfo = MV_FRAME_OUT_INFO_EX()
        memset(byref(stImageInfo), 0, sizeof(stImageInfo))
        pData = (c_ubyte * nPayloadSize)()
        ret = camera.MV_CC_GetOneFrameTimeout(pData, nPayloadSize, stImageInfo, 1000)

        if ret != MV_OK:
            self.show_error(ret, "GetOneFrameTimeout")

        imageLen = stImageInfo.nFrameLen
        imageBuffer = (c_ubyte * imageLen)()

        stSaveParam = MV_SAVE_IMAGE_PARAM_EX()
        stSaveParam.nWidth = c_ushort(stImageInfo.nWidth)
        stSaveParam.nHeight = c_ushort(stImageInfo.nHeight)
        stSaveParam.pData = pData
        stSaveParam.nDataLen = c_uint(imageLen)
        stSaveParam.enPixelType = stImageInfo.enPixelType
        stSaveParam.pImageBuffer = imageBuffer
        stSaveParam.nImageLen = c_uint(imageLen)
        stSaveParam.nBufferSize = c_uint(sizeof(imageBuffer))
        stSaveParam.iMethodValue = c_uint(0)
        stSaveParam.nJpgQuality = c_uint(nJpgQuality)
        stSaveParam.enImageType = c_int(2)

        nRet = camera.MV_CC_SaveImageEx2(stSaveParam)
        if nRet != MV_OK:
            self.show_error(ret, "SaveImage")

        with open(filename, 'wb') as file:
            file.write(bytearray(imageBuffer))

        if verbose:
            print(f"Saved photo of {key} to '{filename}' successfully.")

        del pData
        del imageBuffer

    def stop_and_close(self, verbose=True):
        if verbose:
            print("Closing all cameras...")
        for key in self.config.keys():
            camera = self.config[key]["cameraObject"]

            # Stop grab image
            ret = camera.MV_CC_StopGrabbing()
            if ret != MV_OK:
                self.show_error(ret, "StopGrabbing", raiseError=False)
                sys.exit()

            # Close device
            ret = camera.MV_CC_CloseDevice()
            if ret != MV_OK:
                self.show_error(ret, "CloseDevice", raiseError=False)
                sys.exit()

            # Destroy handle
            ret = camera.MV_CC_DestroyHandle()
            if ret != MV_OK:
                self.show_error(ret, "DestroyHandle", raiseError=False)
                sys.exit()

    def show_error(self, ret, op_name, raiseError=True):
        error_string = "%s failed with error [0x%x] " % (op_name, ret) + self.errors[ret]
        if raiseError:
            raise ValueError(error_string)
        else:
            print(error_string)
