import os
import json
import argparse
import pickle as pkl

import praw
from prawcore import exceptions
from tqdm import tqdm


def safe_vars(obj):
    return None


def download_submission(args):

    with open(args.conf) as reader:
        config = json.load(reader)

    # create reddit instance
    # we want only read only, so no need to provide username / password
    reddit = praw.Reddit(client_id=config["client_id"],
                         client_secret=config["client_secret"],
                         user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1")

    assert reddit.read_only

    # create directory
    os.makedirs(args.output, exist_ok=True)

    with open(args.input) as reader:
        submissions = json.load(reader)

    n_submissions = len(submissions)
    not_found = []
    for idx in tqdm(range(n_submissions)):
        submission_id = submissions[idx]["id"]

        pkl_path = os.path.join(args.output, f"{submission_id}.pkl")

        # if path exists, skip
        if os.path.exists(pkl_path):
            continue
        

        try:
            submission = reddit.submission(submission_id)
            # extract all comments
            submission.comments.replace_more(limit=None)
        except exceptions.NotFound:
            not_found.append(submission_id)
            continue
    

        # dump the object
        with open(pkl_path, "wb") as writer:
            pkl.dump(submission, writer)

    print(f"{len(not_found)}  documents not found")


def pprint_tree(node, _prefix="", _last=True):
    # Source: https://vallentin.io/2016/11/29/pretty-print-tree
    print(_prefix, "`- " if _last else "|- ", repr(node.body), sep="")
    _prefix += "   " if _last else "|  "
    child_count = len(node.replies)
    for i, child in enumerate(node.replies):
        _last = i == (child_count - 1)
        pprint_tree(child, _prefix, _last)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "SubmissionIdDownloader", description="Downloads all submission ids from a given date range from the TOMT subreddit")
    parser.add_argument(
        "--conf", help="location of the JSON config", required=True)
    parser.add_argument("--input", help="submissions JSON file", required=True)
    parser.add_argument("--output", help="output folder", required=True)
    # parser.add_argument("--threads", help="number of threads to use", default=1)

    download_submission(parser.parse_args())
