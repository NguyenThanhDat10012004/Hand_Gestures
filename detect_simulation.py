import os
import cv2
import time
import yaml
import torch
import numpy as np
from torch import nn
import mediapipe as mp
from controller import ModbusMaster

class HandLandmarksDetector():
    def __init__(self) -> None:
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.mp_hands = mp.solutions.hands
        self.detector = self.mp_hands.Hands(False,max_num_hands=1,min_detection_confidence=0.5)

    def detectHand(self,frame):
        hands = []
        frame = cv2.flip(frame, 1)
        annotated_image = frame.copy()
        results = self.detector.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if results.multi_hand_landmarks is not None:
            for hand_landmarks in results.multi_hand_landmarks:
                hand = []
                self.mp_drawing.draw_landmarks(
                    annotated_image,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style())
                for landmark in hand_landmarks.landmark:
                    x,y,z = landmark.x,landmark.y,landmark.z
                    hand.extend([x,y,z])
            hands.append(hand)
        return hands,annotated_image


class NeuralNetwork(nn.Module):
    def __init__(self):
        super(NeuralNetwork, self).__init__()
        self.flatten = nn.Flatten()
        list_label = label_dict_from_config_file("hand_gesture.yaml")
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(63, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Dropout(p=0.4),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Dropout(p=0.4),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Dropout(p=0.6),
            nn.Linear(128, len(list_label)),
        )
        
    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits
    def predict(self,x,threshold=0.9):
        logits = self(x)
        softmax_prob = nn.Softmax(dim=1)(logits)
        chosen_ind = torch.argmax(softmax_prob,dim=1)
        return torch.where(softmax_prob[0,chosen_ind]>threshold,chosen_ind,-1)
    def predict_with_known_class(self,x):
        logits = self(x)
        softmax_prob = nn.Softmax(dim=1)(logits)
        return torch.argmax(softmax_prob,dim=1)
    def score(self,logits):
        return -torch.amax(logits,dim=1)

def label_dict_from_config_file(relative_path):
    with open(relative_path,"r") as f:
       label_tag = yaml.full_load(f)["gestures"]
    return label_tag


class LightGesture:
    def __init__(self, model_path, device=False):
        self.device = device
        self.height = 720
        self.width = 1280

        self.detector = HandLandmarksDetector()
        self.status_text = None
        self.signs = label_dict_from_config_file("hand_gesture.yaml")
        self.classifier = NeuralNetwork()
        self.classifier.load_state_dict(torch.load(model_path))
        self.classifier.eval()

        if self.device:
            self.controller = ModbusMaster()
        self.light1 = False
        self.light2 = False
        self.light3 = False
    

    def light_device(self, img, lights):
        # Append a white rectangle at the bottom of the image
        height, width, _ = img.shape
        rect_height = int(0.15 * height)
        rect_width = width
        white_rect = np.ones((rect_height, rect_width, 3), dtype=np.uint8) * 255

        # Draw a red border around the rectangle
        cv2.rectangle(white_rect, (0, 0), (rect_width, rect_height), (0, 0, 255), 2)

        # Calculate circle positions
        circle_radius = int(0.45*rect_height)
        circle1_center = (int(rect_width * 0.25), int(rect_height / 2))
        circle2_center = (int(rect_width * 0.5), int(rect_height / 2))
        circle3_center = (int(rect_width * 0.75), int(rect_height / 2))

        # Draw the circles
        on_color = (0, 255, 255)
        off_color = (0, 0, 0)
        colors = [off_color, on_color]
        circle_centers = [circle1_center, circle2_center, circle3_center]
        for cc, light in zip(circle_centers, lights):
            color = colors[int(light)]
            cv2.circle(white_rect, cc, circle_radius, color, -1)

        # Append the white rectangle to the bottom of the image
        img = np.vstack((img, white_rect))
        return img

    def run(self):
        cam =  cv2.VideoCapture(0)
        cam.set(3,1280)
        cam.set(4,720)
        while cam.isOpened():
            _,frame = cam.read()

            hand,img = self.detector.detectHand(frame)
            if len(hand) != 0:
                with torch.no_grad():
                    hand_landmark = torch.from_numpy(np.array(hand[0],dtype=np.float32).flatten()).unsqueeze(0)
                    class_number = self.classifier.predict(hand_landmark).item()
                    if class_number != -1:
                        self.status_text = self.signs[class_number]

                        if self.status_text == "light1":
                            if self.light1 == False:
                                print("lights on")
                                self.light1=True
                                if self.device:
                                    self.controller.switch_actuator_1(True)
                        elif self.status_text == "light2":
                            if self.light2 == False:
                                self.light2=True
                                if self.device:
                                    self.controller.switch_actuator_2(True)
                        elif self.status_text == "light3":
                            if self.light3 == False:
                                self.light3=True
                                if self.device:
                                    self.controller.switch_actuator_3(True)          
                        elif self.status_text == "turn_on":
                            self.light1 = self.light2 = self.light3 = True    
                            if  self.light1 and  self.light2 and  self.light3:
                                pass
                            else:
                                self.light1 = self.light2 = self.light3 = True
                                if self.device:
                                    self.controller.switch_actuator_1(self.light1)
                                    time.sleep(0.03)
                                    self.controller.switch_actuator_2(self.light2)
                                    time.sleep(0.03)
                                    self.controller.switch_actuator_3(self.light3)                                       
                        elif self.status_text == "turn_off":
                            if not self.light1 and not self.light2 and not self.light3:
                                pass
                            else:
                                self.light1 = self.light2 = self.light3 = False
                                if self.device:
                                    self.controller.switch_actuator_1(self.light1)
                                    time.sleep(0.03)
                                    self.controller.switch_actuator_2(self.light2)
                                    time.sleep(0.03)
                                    self.controller.switch_actuator_3(self.light3)
                                
                    else:
                        self.status_text = "undefined command"
                        
            else:
                self.status_text = None

            img = self.light_simulation(img, [self.light1, self.light2, self.light3])

            cv2.putText(img, self.status_text, (5,20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.namedWindow('window', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('window', 1920, 1080)
            cv2.imshow("window",img)
            key = cv2.waitKey(1)
            if key == ord("q"):
                break
        cv2.destroyAllWindows()        



if __name__ == "__main__":

    model_path = "./models/model_02-11 15_19_NeuralNetwork_best"
    light = LightGesture(model_path, device=True)
    light.run()
