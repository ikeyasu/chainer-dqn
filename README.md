# Deep Q-Network Implementation using chainer

# Requirement

* [Chainer](http://chainer.org/)
* [PyAutoGUI](https://pyautogui.readthedocs.org/en/latest/)
* [PyQt4](https://riverbankcomputing.com/software/pyqt/intro)
* [tesseract](https://github.com/tesseract-ocr/tesseract)

$ brew install tesseract --all-languages
$ pip install pyocr
$ sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Supported Game

* [Winnie the Pooh's Home Run Derby](http://games.kids.yahoo.co.jp/sports/013.html)
* [Coin Getter](http://games.kids.yahoo.co.jp/action/016.html)

# Usage

Run the game and:

```
python src/train.py -g 0 -o model/dqn --random 0.4 --random_reduction 0.00002 --min_random 0.1
```

Options:
* -g, --gpu: (optional) GPU device index (default: -1).
* -i, --input: (optional) input model file path without extension.
* -o, --output: (required) output model file path without extension.
* -r, --random: (optional) randomness of playing (default: 0.2).
* --pool_size: (optional) number of frames of memory pool (default: 50000).
* --random_reduction: (optional) randomness reduction rate per iteration (default: 0.00002).
* --min_random: (optional) minimum randomness of playing (default: 0.1).
* --double_dqn: (optional) use Double DQN algorithm
* --update_target_interval: (optional) interval to update target Q function of Double DQN (default: 2000)

# License

MIT License
