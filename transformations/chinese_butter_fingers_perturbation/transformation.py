import itertools
import random
import unidecode as u
import json
import os

from interfaces.SentenceOperation import SentenceOperation
from tasks.TaskTypes import TaskType
import shutil
import jieba
import pypinyin


def chinese_butter_finger(text,
                          chinese_character_database,
                          common_chinese_character_database,
                          chinese_words_database,
                          prob,
                          rare_word_prob,
                          seed,
                          max_outputs,
                          consider_tone,
                          word_level_perturb):
    random.seed(seed)

    perturbed_texts = []
    for _ in itertools.repeat(None, max_outputs):
        butter_text = ""
        output = jieba.lcut(text)
        if(word_level_perturb):
            words_and_similar_word_dict_list = get_words_with_similar_pinyin(output,
                                                                            rare_word_prob,
                                                                            chinese_character_database,
                                                                            common_chinese_character_database,
                                                                            chinese_words_database,
                                                                            consider_tone)
            for dict in words_and_similar_word_dict_list:
                perturb_word = dict['perturb_word']
                similar_pinyins_words = dict['similar_pinyin_words']
                if random.random() <= prob and len(similar_pinyins_words) != 0:

                    new_chinese_character = random.choice(similar_pinyins_words)
                else:
                    new_chinese_character = perturb_word
                butter_text += new_chinese_character
        else:
            for chinese_character in text:
                similar_pinyins = get_characters_with_similar_pinyin(chinese_character,
                                                                     rare_word_prob,
                                                                     chinese_character_database,
                                                                     common_chinese_character_database,
                                                                     consider_tone)
                if random.random() <= prob and similar_pinyins != "":

                    new_chinese_character = random.choice(similar_pinyins)
                else:
                    new_chinese_character = chinese_character

                butter_text += new_chinese_character
        perturbed_texts.append(butter_text)
    return perturbed_texts

def get_characters_with_similar_pinyin(chinese_character,
                                       rare_word_prob,
                                       chinese_character_database,
                                       common_chinese_character_database,
                                       consider_tone):

    pinyin_for_char_to_be_perturbed = ""
    for char_dict in chinese_character_database:
        if(chinese_character == char_dict['word']):
            pinyin_for_char_to_be_perturbed = char_dict['pinyin']

    chars_with_similar_pinyin = ""
    if random.random() <= rare_word_prob:
        chars_with_similar_pinyin = retrieve_from_database(chinese_character,
                                                           chars_with_similar_pinyin,
                                                           chinese_character_database,
                                                           consider_tone,
                                                           pinyin_for_char_to_be_perturbed)
    else:
        chars_with_similar_pinyin = retrieve_from_database(chinese_character,
                                                           chars_with_similar_pinyin,
                                                           common_chinese_character_database,
                                                           consider_tone,
                                                           pinyin_for_char_to_be_perturbed)

    return chars_with_similar_pinyin

def get_words_with_similar_pinyin(text,
                                rare_word_prob,
                                chinese_character_database,
                                common_chinese_character_database,
                                chinese_words_database,
                                consider_tone):
    words_and_similar_word_dict_list = []
    for perturb_word in text:
        words_and_similar_word_dict = {}
        perturb_word_len = len(perturb_word)
        words_and_similar_word_dict['perturb_word'] = perturb_word
        similar_word_pinyin_list = []
        if (perturb_word_len == 1):
            similar_pinyins = get_characters_with_similar_pinyin(perturb_word,
                                                                 rare_word_prob,
                                                                 chinese_character_database,
                                                                 common_chinese_character_database,
                                                                 consider_tone)
            similar_word_pinyin_list = [char for char in similar_pinyins]

        if(perturb_word_len > 1):
            for i in range(len(chinese_words_database)):
                word_dict = chinese_words_database[i]
                word = word_dict['word']

                if (len(word) == perturb_word_len):
                    perturb_word_pinyins = pypinyin.pinyin(perturb_word)
                    perturb_word_pinyins_flatten = [item for pinyin in perturb_word_pinyins for item in pinyin]
                    perturb_word_pinyins_string = ''.join(perturb_word_pinyins_flatten)
                    word_pinyins = pypinyin.pinyin(word)
                    word_pinyins_flatten = [item for pinyin in word_pinyins for item in pinyin]
                    word_pinyins_string = ''.join(word_pinyins_flatten)

                    if(consider_tone == False):
                        perturb_word_pinyins_string = u.unidecode(perturb_word_pinyins_string)
                        word_pinyins_string = u.unidecode(word_pinyins_string)


                    if ((perturb_word_pinyins_string == word_pinyins_string) and (perturb_word != word)):
                        similar_word_pinyin_list.append(word)

        words_and_similar_word_dict['similar_pinyin_words'] = similar_word_pinyin_list
        words_and_similar_word_dict_list.append(words_and_similar_word_dict)
    return words_and_similar_word_dict_list


def retrieve_from_database(chinese_character,
                            chars_with_similar_pinyin,
                            chinese_character_database,
                            consider_tone,
                            pinyin_for_char_to_be_perturbed):
    for char_dict in chinese_character_database:
        if (consider_tone):
            if ((pinyin_for_char_to_be_perturbed == char_dict['pinyin']) and (chinese_character != char_dict['word'])):
                chars_with_similar_pinyin += char_dict['word']
        else:
            if (u.unidecode(pinyin_for_char_to_be_perturbed) == u.unidecode(char_dict['pinyin']) and (chinese_character != char_dict['word'])):
                chars_with_similar_pinyin += char_dict['word']
    return chars_with_similar_pinyin


def load_chinese_character_data_into_memory():
    dirname = os.path.dirname(__file__)
    filepath = os.path.join(dirname, "chinese_char.json")
    with open(filepath) as file:
        chinese_character_database = json.load(file)
    return chinese_character_database

def load_common_chinese_character_data_into_memory():
    dirname = os.path.dirname(__file__)
    filepath = os.path.join(dirname, "common_chinese_char.json")
    with open(filepath) as file:
        chinese_character_database = json.load(file)
    return chinese_character_database

def load_chinese_words_data():
    dirname = os.path.dirname(__file__)
    words_list = []
    with open(os.path.join(dirname, 'thuocl/thuocl_all.txt'), mode='r') as file:
        lines = file.readlines()
        for line in lines:
            if(line.rstrip() != ""):
                dict = {}
                word_freq = line.split()
                dict["word"] = word_freq[0]
                dict["freq"] = word_freq[1]
                words_list.append(dict)
    with open(os.path.join(dirname, '四十万汉语大词库.txt'), mode='r') as file:
        lines = file.readlines()
        for line in lines:
            if(line.rstrip() != ""):
                dict = {}
                word_freq = line.split()
                dict["word"] = word_freq[0]
                dict["freq"] = None
                words_list.append(dict)
    return words_list


"""
Chinese Words and Characters Butter Fingers Perturbation
"""

class ChineseButterFingersPerturbation(SentenceOperation):
    tasks = [
        TaskType.TEXT_CLASSIFICATION,
        TaskType.TEXT_TO_TEXT_GENERATION
    ]
    languages = ["zh"]

    def __init__(self, seed=0, max_outputs=1, prob=0.3, rare_word_prob = 0.1, consider_tone = False, word_level_perturb = True):
        super().__init__(seed, max_outputs=max_outputs)
        self.prob = prob
        self.rare_word_prob = rare_word_prob
        self.seed = seed
        self.max_outputs = max_outputs
        self.chinese_character_database = load_chinese_character_data_into_memory()
        self.common_chinese_character_database = load_common_chinese_character_data_into_memory()
        self.chinese_words_database = load_chinese_words_data()
        self.consider_tone = consider_tone
        self.word_level_perturb = word_level_perturb

    def generate(self, sentence: str):
        perturbed_texts = chinese_butter_finger(
            text=sentence,
            chinese_character_database=self.chinese_character_database,
            common_chinese_character_database=self.common_chinese_character_database,
            chinese_words_database = self.chinese_words_database,
            prob=self.prob,
            rare_word_prob = self.rare_word_prob,
            seed=self.seed,
            max_outputs=self.max_outputs,
            consider_tone = self.consider_tone,
            word_level_perturb = self.word_level_perturb
        )
        return perturbed_texts


