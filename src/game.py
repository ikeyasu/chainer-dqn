import os
import random
import time
import numpy as np
import pyocr
from PIL import Image, ImageOps
import pyautogui as ag

class Game(object):
    def __init__(self, width, height):
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def region(self):
        return (self.x, self.y, self.width, self.height)

    def load_images(self, image_dir):
        raise NotImplementedError

    def detect_position(self):
        raise NotImplementedError

    def process(self, screen):
        raise NotImplementedError

    def action_size(self):
        raise NotImplementedError

    def play(self, action):
        raise NotImplementedError

    def randomize_action(self, action, random_probability):
        if random.random() < random_probability:
            return random.randint(0, self.action_size() - 1)
        return action

    def find_image(self, screen, image, x=0, y=0, w=None, h=None, center=False, blackwhite=-1):
        if w is None:
            right = screen.width
        else:
            right = x + w
        if h is None:
            bottom = screen.height
        else:
            bottom = y + h
        cropped = screen.crop((x, y, right, bottom))
        if blackwhite >= 0:
            cropped = ImageOps.grayscale(cropped).point(lambda x: 0 if x < blackwhite else 255)
            image = ImageOps.grayscale(image).point(lambda x: 0 if x < blackwhite else 255)
            #cropped.save('cropped.png', 'PNG')
            #image.save('image.png', 'PNG')
        position = ag.locate(image, cropped)
        if position != None:
            if center:
                return (x + position[0] + position[2] / 2, y + position[1] + position[3] / 2)
            else:
                return (x + position[0], y + position[1])
        return None

    def find_image_center(self, screen, image, x=0, y=0, w=None, h=None, blackwhite=-1):
        return self.find_image(screen, image, x, y, w, h, center=True, blackwhite=blackwhite)

    def move_to(self, x, y):
        ag.moveTo(x + self.x, y + self.y)

    def click(self):
        ag.click()

    def mousedown(self):
        ag.mouseDown()

    def mouseup(self):
        ag.mouseUp()

class PoohHomerun(Game):
    STATE_TITLE  = 0
    STATE_SELECT = 1
    STATE_PLAY   = 2
    STATE_RESULT = 3
    WIDTH        = 600
    HEIGHT       = 450
    ACTIONS      = np.array([[np.float32(i + 260) / WIDTH * 2 - 1, 0, j, 1 - j] for i in range(0, 100, 3) for j in range(2)], dtype=np.float32)

    def __init__(self):
        super(PoohHomerun, self).__init__(self.WIDTH, self.HEIGHT)
        self.state = self.STATE_TITLE
        self.pausing_play = False
        self.images = {}
        self.random_prev_pos = 0
        self.random_count = 0
        self.adjust_state_count = 0

    def load_images(self, image_dir):
        for name in ['start', 'stage', 'select_title', 'select', 'end', 'homerun', 'hit', 'foul', 'strike']:
            self.images[name] = Image.open(os.path.join(image_dir, '{}.png'.format(name)))

    def detect_position(self):
        screen = ag.screenshot()
        for name, offset_x, offset_y in [('start', 288, 252), ('select_title', 28, 24)]:
            position = self.find_image(screen, self.images[name])
            if position != None:
                x, y = position
                x -= offset_x
                y -= offset_y
                self.set_position(x, y)
                return (x, y)
        return None

    def adjust_state(self, screen):
        position = self.find_image(screen, self.images['start'], 270, 240, 60, 40)
        if position != None:
            self.state = self.STATE_TITLE
            return
        position = self.find_image(screen, self.images['select_title'], 10, 16, 60, 40)
        if position != None:
            self.state = self.STATE_SELECT
            return
        position = self.find_image(screen, self.images['select'], 460, 406, 60, 40)
        if position != None:
            self.state = self.STATE_RESULT
            return

    def process(self, screen):
        self.adjust_state_count -= 1
        if self.adjust_state_count <= 0:
            self.adjust_state(screen)
            self.adjust_state_count = 200

        if self.state == self.STATE_TITLE:
            return self._process_title(screen)
        elif self.state == self.STATE_SELECT:
            return self._process_select(screen)
        elif self.state == self.STATE_RESULT:
            return self._process_result(screen)
        else:
            return self._process_play(screen)

    def action_size(self):
        return len(self.ACTIONS)

    def play(self, action):
        x, y, up, down = self.ACTIONS[action]
        self.move_to((x + 1) * self.WIDTH / 2, 300)
        if up > 0:
            self.mouseup()
        else:
            self.mousedown()

    def randomize_action(self, action, random_probability):
        prev_pos = self.random_prev_pos
        pos_size = self.action_size() // 2
        if random.random() * 15 < random_probability:
            self.random_count += random.randint(1, 29)
            prev_pos = random.randint(0, pos_size - 1)
        if self.random_count > 0:
            self.random_count -= 1
            pos = prev_pos
            button = random.randint(0, 1)
            if pos < 0:
                pos = 0
            elif pos >= pos_size - 1:
                pos = pos_size - 1
            action = pos * 2 + button
            prev_pos += random.randint(-5, 5)
        self.random_prev_pos = prev_pos
        return action

    def _process_title(self, screen):
        self.move_to(0, 0)
        time.sleep(0.1)
        position = self.find_image_center(screen, self.images['start'], 270, 240, 60, 40)
        if position != None:
            x, y = position
            self.move_to(x, y)
            time.sleep(0.1)
            self.click()
            time.sleep(3)
        position = self.find_image_center(screen, self.images['select_title'], 10, 16, 60, 40)
        if position != None:
            self.state = self.STATE_SELECT
        return (None, False)

    def _process_select(self, screen):
        self.move_to(0, 0)
        time.sleep(0.1)
        for i in reversed(range(8)):
            position = self.find_image_center(screen, self.images['stage'], 70 + i % 4 * 130, 180 + i / 4 * 170, 80, 20)
            if position != None and (i == 0 or random.randint(0, 1) == 0):
                x, y = position
                self.move_to(x, y + 10)
                time.sleep(0.1)
                self.click()
                time.sleep(2)
                break
        position = self.find_image_center(screen, self.images['select_title'], 10, 16, 60, 40)
        if position == None:
            self.state = self.STATE_PLAY
            return (None, False)
        return (None, False)

    def _process_play(self, screen):
        position = self.find_image_center(screen, self.images['end'], 278, 208, 28, 20)
        if position != None:
            self.mouseup()
            self.pausing_play = False
            self.state = self.STATE_RESULT
            return 0, True
        position = self.find_image_center(screen, self.images['homerun'], 284, 187, 28, 20)
        if position != None:
            if self.pausing_play:
                return None, False
            self.pausing_play = True
            return 100, True
        position = self.find_image_center(screen, self.images['hit'], 284, 201, 28, 20)
        if position != None:
            if self.pausing_play:
                return None, False
            self.pausing_play = True
            return -80, True
        position = self.find_image_center(screen, self.images['foul'], 284, 207, 28, 20)
        if position != None:
            if self.pausing_play:
                return None, False
            self.pausing_play = True
            return -90, True
        position = self.find_image_center(screen, self.images['strike'], 284, 187, 28, 20)
        if position != None:
            if self.pausing_play:
                return None, False
            self.pausing_play = True
            return -100, True
        if self.pausing_play:
            self.pausing_play = False
        return 0, False

    def _process_result(self, screen):
        self.move_to(0, 0)
        time.sleep(0.1)
        position = self.find_image_center(screen, self.images['select'], 460, 406, 60, 40)
        if position != None:
            x, y = position
            self.move_to(x, y)
            time.sleep(0.1)
            self.click()
            time.sleep(3)
        else:
            x, y = 410, 425
            self.move_to(x, y)
            time.sleep(0.1)
            self.click()
            time.sleep(3)
        position = self.find_image_center(screen, self.images['select_title'], 10, 16, 60, 40)
        if position != None:
            self.state = self.STATE_SELECT
        return (None, False)


# http://games.kids.yahoo.co.jp/action/016.html
class CoinGetter(Game):
    STATE_TITLE = 0
    STATE_PLAY = 1
    STATE_RESULT = 2
    WIDTH = 550
    HEIGHT = 447
    # key: 0=do nothing, 1=up, 2=right, 3=down, 4=left
    # updown: 0=down, 1=up
    ACTIONS = np.array([(key, pressed_duration) for key in [0, 1, 2, 3, 4] for pressed_duration in [0, 1]],
                       dtype=np.int)
    KEYS = [None, 'up', 'right', 'down', 'left']

    def __init__(self):
        super(CoinGetter, self).__init__(self.WIDTH, self.HEIGHT)
        self.state = self.STATE_TITLE
        self.images = {}
        self.random_count = 0
        self.adjust_state_count = 0
        self.prev_coin = None
        self.prev_key = None
        self.level = 1

        tools = pyocr.get_available_tools()
        if len(tools) == 0:
            print("No OCR tool found")
            return
        # The tools are returned in the recommended order of usage
        self.ocr_tool = tools[0]

    def load_images(self, image_dir):
        for name in ['start', 'restart', 'left_top', 'coin', 'title', 'game_over', 'levelup', 'level', 'to_title']:
            self.images[name] = Image.open(os.path.join(image_dir, '{}.png'.format(name)))

    def get_number(self, screen, image, offset, size):
        def filter(col):
            if col > 170:
                return 255
            else:
                return 0
        position = self.find_image(screen, self.images[image])
        if position is None:
            return None
        x, y = position
        cropped = screen.crop((x + offset[0], y + offset[1],
                               x + size[0], y + size[1]))
        cropped = ImageOps.grayscale(cropped).point(filter)
        txt = self.ocr_tool.image_to_string(
            cropped,
            lang="eng",
            builder=pyocr.builders.TextBuilder(tesseract_layout=6)
        )
        return int(txt)

    def get_coin_image(self, screen):
        position = self.find_image(screen, self.images['coin'], 144, 415, 152, 27)
        if position is None:
            return None
        x, y = position
        return screen.crop((x, y, x + 60, y + 20))

    def get_level(self, screen):
        return self.get_number(screen, 'level', (15, 0), (60, 20))

    def detect_position(self, screen = None):
        if screen is None:
            screen = ag.screenshot()
        for img, offset in [('left_top', (0, 0)), ('title', (153, 49))]:
            position = self.find_image(screen, self.images[img])
            if position is not None:
                x, y = position
                ox, oy = offset
                x -= ox
                y -= oy
                self.set_position(x, y)
                return x, y
        return None

    def adjust_state(self, screen):
        position = self.find_image(screen, self.images['start'], 213, 382, 138, 44, blackwhite=100)
        if position is not None:
            self.state = self.STATE_TITLE
            return self.state
        position = self.find_image_center(screen, self.images['restart'], 263, 255, 128, 44, blackwhite=100)
        if position is not None:
            self.state = self.STATE_RESULT
            return self.state
        position = self.find_image(screen, self.images['left_top'], 0, 0, 100, 100)
        if position is not None:
            self.state = self.STATE_PLAY
            return self.state
        return None

    def process(self, screen):
        self.adjust_state_count -= 1
        if self.adjust_state_count <= 0:
            self.adjust_state(screen)
            self.adjust_state_count = 100

        if self.state == self.STATE_TITLE:
            return self._process_title(screen)
        elif self.state == self.STATE_RESULT:
            return self._process_result(screen)
        else:
            return self._process_play(screen)


    def action_size(self):
        return len(self.ACTIONS)

    def keyup_all(self):
        for key in self.KEYS[1:]:
            ag.keyUp(key)

    def play(self, action):
        key, updown = self.ACTIONS[action]
        key = self.KEYS[key]
        if key is None:
            return
        print "ACTION: {}, {}".format(key, "DOWN" if updown == 0 else "UP")
        if self.prev_key != key and self.prev_key is not None:
            ag.keyUp(self.prev_key)
        self.prev_key = key
        ag.keyDown(key) if updown == 0 else ag.keyUp(key)

    def randomize_action(self, action, random_probability):
        if random.random() < random_probability:
            return random.randint(0, self.action_size() - 1)
        return action

    def _process_title(self, screen):
        print "process: TITLE"
        self.move_to(0, 0)
        self.click()
        time.sleep(0.1)
        position = self.find_image_center(screen, self.images['start'], 213, 382, 138, 44, blackwhite=100)
        if position is not None:
            x, y =  position
            self.move_to(x, y)
            time.sleep(0.1)
            self.click()
            self.move_to(0, 0)
            self.adjust_state_count -= 1
        return None, False

    def _process_play(self, screen):
        print "process: PLAY",
        #position = self.find_image_center(screen, self.images['game_over'])
        #if position is None:
        #screen.save('screen.png', 'PNG')
        position = self.find_image_center(screen, self.images['restart'], 263, 255, 128, 44)
        if position is not None:
            time.sleep(5)
            self.state = self.STATE_RESULT
            return -100, True
        #position = self.find_image_center(screen, self.images['levelup'])
        #if position is not None:
        #    time.sleep(3)
        #    self.state = self.STATE_RESULT
        #    return 1000, True
        #level = self.get_level(screen)
        #if level != self.level:
        #    self.level = level
        #    return 1000, True
        coin = self.get_coin_image(screen)
        termination = (self.prev_coin != coin)
        reward = 100 if termination else -1
        self.prev_coin = coin
        return reward, termination

    def _process_result(self, screen):
        print "process: RESULT"
        self.keyup_all()
        self.move_to(0, 0)
        time.sleep(0.1)
        position = self.find_image_center(screen, self.images['to_title'], 167, 255, 128, 44, blackwhite=100)
        #position = self.find_image_center(screen, self.images['restart'], 263, 255, 128, 44, blackwhite=100)
        if position != None:
            x, y = position
            self.move_to(x, y)
            time.sleep(0.5)
            self.click()
            time.sleep(0.1)
            self.move_to(0, 0)
            self.adjust_state_count -= 1
        return None, False


if __name__ == '__main__':
    #test
    from PyQt4.QtGui import QPixmap, QApplication
    import sys


    def main(img_dir):
        game = CoinGetter()
        game.load_images(img_dir)
        game.detect_position()

        app = QApplication(sys.argv)
        window_id = app.desktop().winId()
        left, top, w, h = game.region()
        pixmap = QPixmap.grabWindow(window_id, left, top, w, h)
        image = pixmap.toImage()
        bits = image.bits()
        bits.setsize(image.byteCount())
        screen = Image.fromarray(np.array(bits).reshape((h, w, 4))[:,:,2::-1])

        #print game._process_play(screen)
        #coin = game.get_coin_image(screen)
        #coin.save('coin.png', 'PNG')
        #print game._process_title(screen)
        #print game._process_result(screen)
        #print game.adjust_state(screen)

    main('../image_coingetter')
