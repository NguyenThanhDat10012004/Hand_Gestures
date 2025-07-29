## requirements.txt : bao gồm các thư viện cần thiết để chạy project
## hand_gesture.yaml: bao gồm các nhãn đã được đánh số 
## generate_landmark_data.py: dùng để thu thập dữ liệu tran/val/test đầu ra của nó sẽ là 1 file excel với 63 feature và các nhãn.
## hand_gesture_recgonition.py: dùng để train model MLP với bộ data được tạo ra mạng sẽ có 4 lớp , sử dụng optimize: adam, kĩ thuật drop, batchnorm1D.
## controller.py: giao tiếp với phần cứng Modbus RTU qua cổng nối tiếp (Serial Port)
## detect_simulation.py: sẽ tạo ra 1 window sau đó có chức năng nhận diện bàn tay, đi qua mediapine trả ra 63 feature rồi đi qua best model để phân loại nhãn.
