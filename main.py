# -*- encoding: UTF-8 -*-
import qi
from take_pic import PhotoCapture
import atexit
import sys
import time
import os
import gender_predict
import dialog_answer

class SPR:
    is_Face_detected = False
    number = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
    num_man = 0
    num_woman = 0

    def __init__(self,params):
        atexit.register(self.__del__)

        self.ip = params["ip"]
        self.port = params["port"]

        self.session = qi.Session()
        self.switch = True
        try:
            self.session.connect("tcp://" + self.ip + ":" + str(self.port))
        except RuntimeError:
            print("connection Error!!")
            sys.exit(1)

        #需要用到的naoqi_service
        self.tts = self.session.service("ALTextToSpeech")
        self.tb = self.session.service("ALRobotPosture")
        self.motion = self.session.service("ALMotion")
        self.memory = self.session.service("ALMemory")
        self.FaceDet = self.session.service("ALFaceDetection")
        self.BasicAwareness = self.session.service("ALBasicAwareness")
        self.AutonomousLife = self.session.service("ALAutonomousLife")
        self.FaceCharcater = self.session.service("ALFaceCharacteristics")
        self.PeoPer = self.session.service("ALPeoplePerception")
        self.SoundDet = self.session.service("ALSoundDetection")
        self.SoundLoc = self.session.service("ALSoundLocalization")
        self.TabletSer = self.session.service("ALTabletService")

        #需要设置的参数
        self.tts.setParameter("speed", 75.0)
        self.tts.setLanguage("English")
        self.PeoPer.resetPopulation()
        self.motion.setStiffnesses("Head",1.0)
        self.conv_count = self.memory.subscriber("stop_loc")
        self.conv_count.signal.connect(self.callback_stop_loc)

        #运行部分
        #取消自动感知模式
        print "---Disabling the AutonomousLife Mode---"
        self.BasicAwareness.setEnabled(False)
        if self.AutonomousLife.getState() != "disabled":
            self.AutonomousLife.setState("disabled")
        print "---AutonomousLife Mode Disable!---"
        #说想要玩谜语游戏

        self.motion.wakeUp()
        self.tb.goToPosture("StandInit", 0.5)
        self.say("I want to play a riddle game,please stand behind me")
        self.tb.goToPosture("StandInit", 0.5)
        self.motion.moveInit()
        turn_count = 10
        while turn_count>=1:
            self.say(str(turn_count))
            time.sleep(0.75)
            turn_count -= 1
        #转身
        self.motion.setStiffnesses("Head", 1.0)
        self.motion.moveTo(0, 0, 3.14, _async=True)
        time.sleep(4)

        #开始检测性别,回答站在背后的人的问题
        self.take_pic = PhotoCapture(self.session)
        self.take_pic.takepic()
        self.count_num_of_human()
        self.dialog = dialog_answer.Dialog(self.session, '/home/nao/top/dialog.top')

        # 声源定位
        self.tts.say("We are going to play the Blind man’s bluff game, please stand around me")
        self.motion.setAngles("HeadPitch", -0.4,0.1)
        self.count = 5
        while self.count>= 1:
            time.sleep(0.75)
            self.tts.say(str(self.count))
            self.count -= 1
        self.sound_localization()
        self.blind_game = dialog_answer.Dialog(self.session,'/home/nao/top/dialog.top')

    def run(self):
        while True:
            time.sleep(1)

    def callback_stop_loc(self,msg):
        if self.count ==0:
           self.SoundLoc.unsubscribe("SoundLocated")

    def say(self,word):
        self.tts.say(word)

    def count_num_of_human(self):
        cmd = 'sshpass -p kurakura326 scp nao@' + str(self.ip) + ":/home/nao/picture/image_0.jpg ./person_image.jpg"
        os.system(cmd)
        self.num_man, self.num_woman,_ = gender_predict.gender("./person_image.jpg")
        self.show_person_image()
        if self.num_woman + self.num_man == 1:
            self.tts.say("I've seen one person")
        else:
            self.tts.say("There are " + str(self.num_woman + self.num_man) + "people")

        self.tts.say("the number of man is " + str(self.num_man))

        self.tts.say("the number of woman is " + str(self.num_woman))

    def sound_localization(self):
        self.SoundLoc.subscribe("SoundLocated")
        self.SoundLoc.setParameter("Sensitivity",0.7)
        self.sound_localization_sub = self.memory.subscriber("ALSoundLocalization/SoundLocated")
        self.sound_localization_sub.signal.connect(self.callback_sound_localization)

    def callback_sound_localization(self,msg):
        if self.switch == False:
            return
        self.switch = False
        sound_loc = self.memory.getData("ALSoundLocalization/SoundLocated")
        print("----Located!----", sound_loc[1][2])
        print("Energy:",sound_loc[1][3])
        # time.sleep(0.5)
        if sound_loc[1][2] > .5:
            self.motion.moveTo(0,0,sound_loc[1][0])
        self.switch = True

    def __del__(self):
        print ("exit")

    def show_person_image(self):
        cmd = "sshpass -p kurakura326 scp ./result.jpg nao@" + str(self.ip) + ":~/.local/share/PackageManager/apps/boot-config/html"
        os.system(cmd)
        self.TabletSer.hideImage()
        self.TabletSer.showImageNoCache("http://198.18.0.1/apps/boot-config/result.jpg")

def main():
    params = {
        'ip': "192.168.3.18",
        'port': 9559,
        'rgb_topic': 'pepper_robot/camera/front/image_raw'
    }
    pio = SPR(params)
    pio.run()

if __name__ == "__main__":
    main()

