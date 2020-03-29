import json
import argparse
from datetime import datetime, timezone

import pytz
import requests

def utc_timestamp(dt):
    """
        Converts a datetime object into a timestamp
    """
    timezone = pytz.timezone("utc")
    dt = timezone.localize(dt)
    return int(dt.timestamp())

def datetime_from_utc(utc):
    """
        Converts a UTC timestamp into a datetime object in the UTC timezone
    """
    return datetime.fromtimestamp(utc, tz=pytz.utc)

def pushshift_api(query, after, before, sub):
    url = 'https://api.pushshift.io/reddit/search/submission/?&size=1000&after='+str(after)+'&before='+str(before)+'&subreddit='+str(sub)
    print(url)
    r = requests.get(url)
    data = json.loads(r.text)
    return data['data']

def pushshift_submission(subreddit, **kwargs):

    top_url = f"https://api.pushshift.io/reddit/search/submission/?subreddit={subreddit}"
    
    # filter out None terms first
    kwargs_cleaned = {}
    for k, v in kwargs.items():
        if v is not None:
            kwargs_cleaned[k] = v
    verbose = True
    if kwargs_cleaned.get("before") is not None and verbose:
        print(f"Getting threads before time {datetime_from_utc(kwargs_cleaned['before'])}")
    
    if kwargs_cleaned.get("after") is not None and verbose:
        print(f"Getting threads after time {datetime_from_utc(kwargs_cleaned['after'])}")
    
    
    payload_str = "&".join("%s=%s" % (k,v) for k,v in kwargs_cleaned.items())
    
    response = requests.get(top_url, params=payload_str)
    
    if verbose:
        print(response.url)
    
    return response.json()

def get_all_submissions(args):

    true_start_time = datetime.strptime(args.start_time, "%d-%m-%Y")
    true_end_time = datetime.strptime(args.end_time, "%d-%m-%Y")

    print(f"Start Time: {true_start_time}; End Time: {true_end_time}")

    assert true_end_time > true_start_time

    # we go backwards, so please forgive the name mixup
    start_time = utc_timestamp(true_end_time)
    last_time = utc_timestamp(true_start_time)

    # download 1000 submissions at a time
    limit=1000

    # initialize before and after
    before = start_time # start from this time and go backward until last_time is achieved
    after = None # this is ignored in the first call
    assert last_time < start_time, "last_time must occur before start_time"
    all_submissions = []

    while True:
        # get all submissions, with the created time
        submissions = pushshift_submission("tipofmytongue",
                                        before=before,
                                        limit=limit,
                                        fields=",".join(("created_utc", "id")))
        
        data = submissions["data"]
        
        for d in data:
            d["created_time"] = datetime_from_utc(d["created_utc"])
        
        all_submissions.extend(data)
        first_post = max(data, key=lambda _: _["created_utc"])
        last_post = min(data, key=lambda _: _["created_utc"])
        
        before = last_post["created_utc"]
        
        if before < last_time:
            print("Done!")
            break
        else:
            print(f"{len(all_submissions)} downloaded")

    # filter out all posts that occur before last_time
    all_submissions = [s for s in all_submissions if s["created_utc"] > last_time]
    # filter out all posts that occur after start_time 
    all_submissions = [s for s in all_submissions if s["created_utc"] < start_time]

    print(f"First Post has Time: {all_submissions[0]['created_time']}\nLast Post has Time: {all_submissions[-1]['created_time']}")

    print(f"A total of {len(all_submissions)} submissions downloaded")

    # remove datetime objects 
    for s in all_submissions:
        del s["created_time"]

    with open(args.output, "w") as writer:
        json.dump(all_submissions, writer, indent=2)





if __name__ == "__main__":
    parser = argparse.ArgumentParser("SubmissionIdDownloader", description="Downloads all submission ids from a given date range from the TOMT subreddit")
    parser.add_argument("--start-time", dest="start_time", help="start time in DD-MM-YYYY format", required=True)
    parser.add_argument("--end-time", dest="end_time", help="end time in DD-MM-YYYY format", required=True)
    parser.add_argument("--output", help="output location for the submissions dump", default="submissions.json")
    
    get_all_submissions(parser.parse_args())

    