# -*- encoding: UTF-8 -*-
import qi
import atexit
import time
class Dialog:
    answer_num = 0
    def __init__(self,session,topic_path):
        print  topic_path
        self.end = False
        self.conv = session.service("ALDialog")
        self.memo = session.service("ALMemory")
        self.conv.setLanguage("English")
        self.SoundDet = session.service("ALSoundDetection")
        topf_path = topic_path.decode('utf-8')
        if self.conv.getLoadedTopics('enu')== []:
            topic_name = self.conv.loadTopic(topf_path.encode('utf-8'))
            self.conv.activateTopic(topic_name)
        else:
            print self.conv.getLoadedTopics('enu')
        self.memo= session.service("ALMemory")
        print "initialize succeed"
        self.tts = session.service("ALTextToSpeech")
        self.tts.say("I'm ready to answer question. Please say that's all to stop. If I've answered 5 questions, I would stop too")
        time.sleep(0.5)
        self.conv.subscribe("Talking")
        self.end_of_conv = self.memo.subscriber("stop_talking")
        self.end_of_conv.signal.connect(self.callback_stoptalking)
        self.conv_count = self.memo.subscriber("answered")
        self.conv_count.signal.connect(self.callback_answered)
        # now that the dialog engine is stopped and there are no more activated topics,
        # we can unload our topic and free the associated memory
        while True:
            time.sleep(1)
            if self.end == True:
                break
            elif self.answer_num >= 5:
                self.tts.say(" Thanks for your cooperation")
                self.conv.unsubscribe('Talking')
                self.conv.deactivateTopic('Talking')
                self.reset_count()
                #通过 回答5次结束
                break

    def callback_stoptalking(self,msg):
        print msg
        self.conv.unsubscribe('Talking')
        self.conv.deactivateTopic('Talking')
        self.tts.say("Thanks for your cooperation")
        self.reset_count()
        self.end = True
        #通过that's all结束

    def callback_answered(self,msg):
        self.answer_num += 1

    def reset_count(self):
        self.answer_num = 0