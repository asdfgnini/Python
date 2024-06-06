import sys
from PySide6.QtCore import (Qt,QThread,QTimer,Signal,Slot)
from PySide6.QtWidgets import (QApplication,QWidget,QVBoxLayout,QPushButton,
QLabel)
from PySide6.QtGui import (QImage,QPixmap)
import cv2

# 子线程 
class VideoProcessorThread(QThread):
    # 定义一个信号，用于传递处理后的帧
    frame_processed = Signal(object)

    def __init__(self,rtsp_url,parent=None):
        super().__init__(parent)
        self.models = [torch.load("model1.pth"),torch.load("model2.pth")]
        self.current_model_index = 0
        # 打开rtsp视频流
        self.cap = cv2.VideoCapture(rtsp_url)
        # 设置cv缓冲区为0，以减少延时
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE,0)
        # 设定线程启停标志位
        self.running = True

    def run(self):
        while self.running:
            # 读取一帧数据
            ret,frame = self.cap.read()
            # 如果获取失败，则跳过
            if not ret:
                continue
            # 将获取的视频帧转换为RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)        
            # 将RGB帧转换为张量，并添加批次维度
            image = self.transform(frame_rgb).unsqueeze(0)
            # 关闭梯度计算
            with torch.no_grad():
                # 计算前向传播，进行预测
                output = self.models[self.current_model_index](image)
                # 获取预测结果
                _, predicted = torch.max(output, 1)

            # 创建结果文本
            result_text = f"Predicted class: {predicted.item()}"
            # 在帧上绘制结果文本
            cv2.putText(frame, result_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            # 发送处理后的帧信号
            self.frame_processed.emit(frame)


    def transform(self, frame):
        # 定义转换操作
        transform = transforms.Compose([
            # 转换为PIL图像
            transforms.ToPILImage(),
            # 调整大小
            transforms.Resize((224, 224)),
            # 转换为张量
            transforms.ToTensor(),
            # 归一化
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        # 返回转换后的帧
        return transform(frame)
    
    # 定义槽函数
    @Slot(int)
    def set_model(self,index):
        # 设置当前模型索引
        self.current_model_index = index 

    def stop(self):
        # 设置运行状态为False
        self.running = False
        # 等待线程结束
        self.wait()
        self.cap.release()


# 主线程，UI线程
class VideoProcessor(QWidget):
    def __init__(self,rtsp_url):
        super().__init__()
        # 初始化界面
        self.init_ui(rtsp_url)

    def init_ui(self,rtsp_url):
        self.setWindowTitle("video Provesser")
        self.setGeometry(100,100,600,480)
        
        layout = QVBoxLayout()

        self.label = QLabel()
        layout.addWidget(self.label)

        self.button_model1 = QPushButton("Model 1")
        # 连接槽函数
        self.button_model1.clicked.connect(lambda:self.thread.set_model(0))
        layout.addWidget(self.button_model1)

        self.button_model2 = QPushButton("Model 2")
        # 连接槽函数
        self.button_model2.clicked.connect(lambda:self.thread.set_model(1))
        layout.addWidget(self.button_model2)

        self.setLayout(layout)

        # 创建视频处理线程
        self.thread = VideoProcessorThread(rtsp_url)
        # 连接帧处理信号到槽函数
        self.thread.frame_processed.connect(self.update_frame)
        # 启动线程
        self.thread.start()

    def update_frame(self, frame):
        # 将 OpenCV 图像转换为 Qt 图像并显示
        qt_image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_BGR888)
        # 将QImage转换为QPixMap
        pixmap = QPixmap.fromImage(qt_image)
        # 在标签上显示QPixMap
        self.label.setPixmap(pixmap)

    def closeEvent(self,event):
        # 停止线程
        self.thread.stop()
        # 接受关闭事件
        event.accept()

if __name__ == "__main__":
    # 检查命令行参数个数
    if len(sys.argv) < 2:  
        print("请输入rtsp视频流地址。。。") 
        sys.exit(1)  

    # 获取RTSP URL
    rtsp_url = sys.argv[1]  # 获取RTSP URL
    # 创建应用程序
    app = QApplication(sys.argv)
    # 创建视频处理窗口
    window = VideoProcessor(rtsp_url)
    # 显示窗口
    window.show()
    # 进入主事件循环
    sys.exit(app.exec())