import os
import re
import time
import twitter
import tempfile

import numpy as np
import scipy.misc as misc

from urllib import request


def twitter_credentials():
    return dict(consumer_key=os.getenv('CONSUMER_KEY'),
                consumer_secret=os.getenv('CONSUMER_SECRET'),
                token=os.getenv('ACCESS_TOKEN_KEY'),
                token_secret=os.getenv('ACCESS_TOKEN_SECRET'))


def loop(api, media_api):
    last_id = 0
    while True:
        last_posted = api.statuses.user_timeline(screen_name='Sentinel2Bot')[0]
        _id = last_posted['id_str']

        # only react on a new post
        if _id == last_id:
            time.sleep(600)
            continue
        else:
            last_id = _id

        # import pprint
        # pprint.pprint(last_posted)

        img_url = last_posted['entities']['media'][0]['media_url']
        orig_text = last_posted['text'].strip()

        status = '{}, via @sentinel2bot'.format(
            re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', orig_text).strip())

        temp_dir = tempfile.gettempdir()
        app_dir = os.path.join(temp_dir, 'sentibrobot')
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        in_file = os.path.join(app_dir, '{}.jpg'.format(_id))
        out_file = os.path.join(app_dir, '{}_spo.jpg'.format(_id))

        request.urlretrieve(img_url, in_file)

        img = misc.imread(in_file)
        img = np.sort(img, axis=0)
        misc.imsave(out_file, img)

        with open(in_file, 'rb') as imagefile:
            imagedata = imagefile.read()
        img_id_orig = media_api.media.upload(media=imagedata)['media_id_string']

        with open(out_file, 'rb') as imagefile:
            imagedata = imagefile.read()
        img_id_sorted = media_api.media.upload(media=imagedata)['media_id_string']

        api.statuses.update(status=status,
                            media_ids=','.join([img_id_sorted, img_id_orig]),
                            lat=last_posted['geo']['coordinates'][0],
                            long=last_posted['geo']['coordinates'][1],
                            in_reply_to_status_id=_id)


if __name__ == '__main__':
    api = twitter.Twitter(auth=twitter.OAuth(**twitter_credentials()))
    media_api = twitter.Twitter(domain='upload.twitter.com',
                                auth=twitter.OAuth(**twitter_credentials()))
    loop(api, media_api)
