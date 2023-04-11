import requests
import charset_normalizer as chartset
from bs4 import BeautifulSoup
# 请求地址
url = 'https://mp.weixin.qq.com/mp/appmsgalbum?__biz=Mzg2MjEwNjU3Ng==&action=getalbum&album_id=2709914702935769088&scene=173&from_msgid=2247484634&from_itemidx=1&count=3&nolastread=1#wechat_redirect'
# 添加请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
}
# 请求参数
# params={
#     "__biz": "Mzg2MjEwNjU3Ng==",
#     "mid": "2247484715",
#     "idx": "1",
#     "sn": "45c6e563e098bcda08c875071c56532b",
#     "chksm": "ce0da394f97a2a82e39917bd09dad0370089456c0e5cfb05d10abe0ad4551c4180438ae638fc#rd"
# }
# 获取请求的json格式
r = requests.get(url, headers=headers, verify=False)
r.encoding = chartset.detect(r.content)['encoding']
html = r.content.decode('utf-8')

bs = BeautifulSoup(html, "html.parser")

# print(bs.find('html').getText())
for li in bs.findAll('li'):
    print(li["data-link"])
