import uuid
from uuid import UUID, uuid4
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import random

def random_senti():
    return random.choice(["pos", "neg", "neu"])

class Aspect_Sentiment(BaseModel):
    aspect_term: str
    opinion: str
    sentiment: str

class TextBase(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    content: List[UUID]
    language: str
    sentiment: str = Field(default_factory=random_senti)  # 自动生成随机情感

    @field_validator('sentiment')
    def validate_sentiment(cls, v):
        if v not in ['pos', 'neg', 'neu']:
            raise ValueError('情感倾向必须是pos, neg, neu')
        return v

class Sentence(TextBase):
    word_count: Optional[int] = None  # 占位值，实际由验证器计算
    aspect_based_sent: Optional[List[Aspect_Sentiment]] = None

    @model_validator(mode='after')
    def adjust_word_count(self):
        if self.word_count is None:
            self.word_count = random.randint(10, 20)
        return self

class Chapter(TextBase):
    sentences: List[Sentence]

    @model_validator(mode='before')
    @classmethod
    def assemble_content(cls, data: dict) -> dict:
        """自动聚合句子的content并去重"""
        sentences = data.get('sentences', []) or data.get('sentences', [])  # 处理可能的拼写错误
        content = []
        for sentence in sentences:
            content.extend(sentence.content)
        data['content'] = list(set(content))
        return data

    @property
    def word_count(self):
        return sum(sentence.word_count for sentence in self.sentences)

class Article(TextBase):
    title: Optional[Sentence] = None
    chapters: List[Chapter]

    @model_validator(mode='before')
    @classmethod
    def assemble_content(cls, data: dict) -> dict:
        """聚合标题和章节的content并去重"""
        content = []
        if title := data.get('title'):
            content.extend(title.content)
        for chapter in data.get('chapters', []):
            content.extend(chapter.content)
        data['content'] = list(set(content))
        return data

    @property
    def word_count(self):
        total = sum(chapter.word_count for chapter in self.chapters)
        if self.title:
            total += self.title.word_count
        return total
# 基于对象的工具
def translate_chapter(chapter: Chapter, target_language: str):
    translated_chapter = chapter.model_copy()
    translated_chapter.language = target_language
    translated_chapter.id = uuid4()
    new_sentences = []
    for s in chapter.sentences:
        ns = s.model_copy()
        ns.language = target_language
        new_sentences.append(ns)
    translated_chapter.sentences = new_sentences
    return translated_chapter

def translate_text(text_obj: TextBase, target_language: str):
    """
    翻译文本对象到指定语言，如果字数超过最大长度则不进行翻译。
    返回翻译后的对象或原对象（如果未翻译）。
    """
    max_length = 256
    if text_obj.word_count > max_length:
        print(f"翻译失败：{text_obj.id} 的字数超过了最大限制 {max_length}")
        return text_obj

    translated_obj = text_obj.model_copy()
    translated_obj.language = target_language
    translated_obj.id = uuid4()
    has_title = getattr(translated_obj, "title", None)
    if has_title:
        translated_obj.title.language = target_language
        translated_obj.title.id = uuid4()
    if isinstance(translated_obj, Article):
        #  是文章类型，需要将所有章节翻译
        translated_chaps = []
        for chap in translated_obj.chapters:
            new_chap = translate_chapter(chap, target_language)
            translated_chaps.append(new_chap)
        translated_obj.chapters = translated_chaps
    if isinstance(translated_obj, Chapter):
        # 是章节类型，直接翻译
        translated_obj = translate_chapter(text_obj, target_language)
    return translated_obj

def sentiment_analysis_article(article: Article):
    # 只能处理特定语言的情感
    if article.language == "en":
        return article.sentiment
    else:
        return "pos"
    
def sentiment_analysis_chapter(chapter: Chapter):
    # 只能处理特定语言的情感
    if chapter.language == "en":
        return chapter.sentiment
    else:
        return "pos"

def sentiment_analysis_sentence(sentence: Sentence):
    '''
    对句子进行情感分析
    '''
    if sentence.language == "en":
        return sentence.sentiment
    else:
        return "pos"

def aspect_based_sentiment_analysis(sentence: Sentence):
    if sentence.language == "en":
        return sentence.aspect_based_sent
    else:
        return []

def get_title(article: Article):
    return article.title

def split_article(article: Article):
    return article.chapters

def split_chapter(chapter: Chapter):
    return chapter.sentences

def construct_chapter(sentences: List[Sentence]):
    languages = []
    for sent in sentences:
        languages.append(sent.language)
    if len(set(languages)) == 1:
        # 如果只有一种语言，就设置为这种语言
        chap_lang = languages[0]
    else:
        chap_lang = "mix_language"
    chapter = Chapter(sentences=sentences, language=chap_lang)
    return chapter

def construct_article(chapters: List[Chapter], title=None):
    languages = []
    for chap in chapters:
        languages.append(chap.language)
    if title:
        languages.append(title.language)
    if len(set(languages)) == 1:
        # 如果只有一种语言，就设置为这种语言
        art_lang = languages[0]
    else:
        art_lang = "mix_language"
    article = Article(chapters=chapters, language=art_lang, title=title)
    return article
        

# 对象到文件的转换
import json
from pathlib import Path
from pydantic import BaseModel

OBJ_DIR = "./data"

def save_object_to_json(obj: BaseModel):
    """
    将给定的对象保存为JSON文件。
    :param obj: 要保存的对象，可以是Sentence, Chapter, 或Article类型的实例。
    """
    # 确保目录存在
    Path(OBJ_DIR).mkdir(parents=True, exist_ok=True)
    
    # 使用对象的id属性作为文件名
    file_path = Path(OBJ_DIR) / f"{obj.id}.json"
    
    # 序列化为JSON字符串
    json_str = obj.model_dump_json()
    
    # 写入文件
    with open(file_path, 'w') as file:
        file.write(json_str)

def load_object_from_json(obj_id: UUID):
    """
    从JSON文件加载对象，并自动转换为正确的Pydantic模型。
    :param obj_id: 对象的uuid
    :return: 返回对应的Sentence, Chapter, 或Article类型的实例。
    """
    # 确保目录存在
    Path(OBJ_DIR).mkdir(parents=True, exist_ok=True)
    
    # 使用对象的id属性作为文件名
    file_path = Path(OBJ_DIR) / f"{obj_id}.json"
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # 根据"data"中的特定字段判断对象类型
    if 'chapters' in data:
        return Article.model_validate(data)
    elif 'sentences' in data:
        return Chapter.model_validate(data)
    elif 'aspect_based_sent' in data:
        return Sentence.model_validate(data)
    else:
        raise ValueError("无法识别JSON数据所属的模型类型")
    
# 直接操作文件的工具
def translate_tool(text_obj_id: UUID, target_language: str):
    '''
    输入文本的id和目标语言，翻译为指定语言
    '''
    text_obj = load_object_from_json(text_obj_id)
    translated_text = translate_text(text_obj, target_language)
    save_object_to_json(translated_text)
    return translated_text.id

def sentiment_analysis_article_tool(article_id: UUID):
    article_obj = load_object_from_json(article_id)
    senti = sentiment_analysis_article(article_obj)
    return senti

    
def sentiment_analysis_chapter_tool(chapter_id: UUID):
    chapter_obj = load_object_from_json(chapter_id)
    senti = sentiment_analysis_article(chapter_obj)
    return senti

def sentiment_analysis_sentence_tool(sentence_id: UUID):
    '''
    对句子进行情感分析，输入是句子的id
    '''
    sentence_obj = load_object_from_json(sentence_id)
    senti = sentiment_analysis_article(sentence_obj)
    return senti

def aspect_based_sentiment_analysis_tool(sentence_id: UUID):
    sentence_obj = load_object_from_json(sentence_id)
    senti = aspect_based_sentiment_analysis(sentence_obj)
    return senti

def get_title_tool(sentence_id: UUID):
    sentence_obj = load_object_from_json(sentence_id)
    return get_title(sentence_obj)

def split_article_tool(article_id: UUID):
    article_obj = load_object_from_json(article_id)
    chap_objs = split_article(article_obj)
    chap_ids = [chap.id for chap in chap_objs]
    return chap_ids

def split_chapter_tool(chapter_id: UUID):
    chapter_obj = load_object_from_json(chapter_id)
    sent_objs = split_article(chapter_obj)
    sent_ids = [sent.id for sent in sent_objs]
    return sent_ids

def construct_chapter_tool(sentences_id: List[UUID]):
    sent_objs = [load_object_from_json(s) for s in sentences_id]
    chapter_obj = construct_chapter(sent_objs)
    save_object_to_json(chapter_obj)
    return chapter_obj.id

def construct_article_tool(chapters_id: List[UUID], title_id=None):
    chap_objs = [load_object_from_json(c) for c in chapters_id]
    if title_id:
        title_obj = load_object_from_json(title_id)
        article_obj = construct_article(chap_objs, title=title_obj)
    else:
        article_obj = construct_article(chap_objs)
    save_object_to_json(article_obj)
    return article_obj.id