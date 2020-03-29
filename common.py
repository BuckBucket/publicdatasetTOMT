import os
import re
import json
import random
import traceback
import pickle as pkl
from datetime import datetime
from urllib.parse import urlparse

import pytz
import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
from urlextract import URLExtract

from download_submissions import pprint_tree


user_blacklist = {
    "AutoModerator",
    "WhatIsThisBot",
    "notifier-bot",
    'surfwax95',
    'RoboBama',
    'I_Me_Mine',
    'sjhill',
    'roastedbagel',
    'SamCarterX206',
    'Jordan117',
    'teraflop',
    'Leinbow'
}

_extractor = URLExtract()


def load_submission(folder, submission_id):
    with open(os.path.join(folder, f"{submission_id}.pkl"), "rb") as reader:
        return pkl.load(reader)


def load_submissions(folder):
    submissions = []
    for submission_id in os.listdir(folder):
        submission_id = submission_id.split(".")[0]
        try:
            submissions.append(load_submission(folder, submission_id))
        except:
            print(f"Submission with ID: {submission_id} has an error!")
    return submissions


def load_rows(folder, delete_invalid=False):
    files = os.listdir(folder)
    rows = [None] * len(files)
    for idx in tqdm(range(len(files))):
        submission_id = files[idx]
        submission_id = submission_id.split(".")[0]
        try:
            submission = load_submission(folder, submission_id)
            rows[idx] = Row(submission)
        except Exception as e:
            traceback.print_exc()
            print(f"Submission with ID: {submission_id} has an error!")
    return rows


class Row:
    def __init__(self,
                 submission):
        # status
        if submission.selftext == "[removed]":
            self.status = "removed"
        elif submission.link_flair_text is None:
            self.status = "unknown"
        else:
            self.status = submission.link_flair_text

        # category
        category = re.search(r'\[TOMT\](\s*)\[([^]]*)\]',
                             submission.title, re.IGNORECASE)

        if category:
            category = category.group(2)
        else:
            if re.search(r"^\s*\[TOMP].*", submission.title, re.IGNORECASE) is not None:
                category = "nsfw"
            else:
                category = "uncategorized"

        self.category = category
        date = datetime.fromtimestamp(submission.created_utc, tz=pytz.utc)
        self.date = date.strftime("%d-%m-%Y")
        self.hour = date.hour


class CleanRow:
    def __init__(self,
                 submission,
                 status_dict,
                 category_dict):
        # status
        if submission.selftext == "[removed]":
            self.status = "removed"
        elif submission.link_flair_text is None:
            self.status = "unknown"
        else:
            self.status = status_dict[submission.link_flair_text]

        # category
        category = re.search(r'\[TOMT\](\s*)\[([^]]*)\]',
                             submission.title, re.IGNORECASE)

        if category:
            category = category.group(2)
            # if it's not in the diction
            category = category_dict.get(category.lower(), "not_annotated")
            original_category = category.lower()
        else:
            if re.search(r"^\s*\[TOMP].*", submission.title, re.IGNORECASE) is not None:
                category = "nsfw"
                original_category = category
            else:
                category = "uncategorized"
                original_category = category
        self.submission_id = submission.id
        self.category = category
        self.original_category = original_category
        date = datetime.fromtimestamp(submission.created_utc, tz=pytz.utc)
        self.date = date.strftime("%d-%m-%Y")
        self.hour = date.hour

        self.n_top_replies = len(submission.comments)

        # count number of replies
        self.n_total_replies = len(submission.comments.list())

        self.url = submission.url

        self.imdb_links = []
        self.other_links = []
        # collect links
        for comment in submission.comments.list():
            i, o = find_links(comment.body)
            self.imdb_links.extend(i)
            self.other_links.extend(o)


def find_links(text):
    # from: http://www.noah.org/wiki/RegEx_Python#URL_regex_pattern
    other_links = set()
    imdb_links = set()

    for url in _extractor.find_urls(text):
        if "imdb" in urlparse(url).netloc:
            imdb_links.add(url)
        else:
            other_links.add(url)

    return imdb_links, other_links


def load_clean_rows(folder, status_dict, category_dict):
    files = os.listdir(folder)
    rows = [None] * len(files)
    for idx in tqdm(range(len(files))):
        submission_id = files[idx]
        submission_id = submission_id.split(".")[0]
        try:
            submission = load_submission(folder, submission_id)
            rows[idx] = CleanRow(submission, status_dict, category_dict)
        except Exception as e:
            traceback.print_exc()
            print(f"Submission with ID: {submission_id} has an error!")
    return rows


def load_meta(meta, root_path="./"):
    with open(os.path.join(root_path, "meta_data", meta + ".json")) as reader:
        return json.load(reader)
