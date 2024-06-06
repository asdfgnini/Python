import sys
from PySide6.QtCore import (Qt,QThread,QTimer,Signal,Slot)
import cv2


class VideoProcessorThread(QThread):

    def __init__(self,rtsp_url,parent=None):
        super().__init__(parent)
        # 打开rtsp视频流
        self.cap = cv2.VideoCapture(rtsp_url)
        # 设置cv缓冲区为0，以减少延时
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE,0)
        # 提前读取一帧
        self.ret,self.frame = self.cap.read()
        # 设定线程启停标志位
        self.running = True

    def run(self):
        while self.running:
            if not self.ret:
                continue            
            self.ret,self.frame = self.cap.read()

    def read(self):
        return self.frame

    def stop(self):
        # 设置运行状态为False
        self.running = False
        # 等待线程结束
        self.wait()
        self.cap.release()


if __name__ == "__main__":
    stream = VideoProcessorThread("rtsp://admin:112750zjt@192.168.1.64/h264/ch1/main/av_stream")
    stream.start()
    while True:
        frame = stream.read()  
        frame = cv2.resize(frame,(1000,720))
        cv2.imshow('Threaded RTSP Stream', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    stream.stop()
    cv2.destroyAllWindows()


