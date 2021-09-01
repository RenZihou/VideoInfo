import os
from crawler.database import BiliDB

if __name__ == '__main__':
    with BiliDB() as db:
        for each in os.listdir('./cover'):
            if each[0] != 'B':
                continue
            bvid = each.replace('.jpg', '')
            try:
                aid = list(db.execute('SELECT avid FROM videos WHERE bvid = ?', (bvid,)))[0][0]
                os.rename('./cover/%s' % each, './cover/%d.jpg' % aid)
            except Exception:
                continue
