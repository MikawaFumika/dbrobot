#!/usr/local/bin/python3
# -*- encoding:utf-8 -*-

import requests
from bs4 import BeautifulSoup
import time, re
import traceback
import random
import time
import os
from PIL import Image
import pytesseract
from urllib import request


session = requests.session()

headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 6.1)\
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36'}
session.headers.update(headers)

#yanzhengma

# 容错最大的有色判断
MAX_RGB_VALUE = 20
# 噪点大小
MAX_NOISY_COUNT = 25

# RGBA白色定义
WHITE_COLOR = (255, 255, 255, 255)
# RGBA黑色定义
BLACK_COLOR = (0, 0, 0, 255)


def print_char_pic(width, height, s_data):
    """
    画出字符图, 空格为白色, 点为黑色
    """
    _pic_str = ''
    for y in range(0, height):
        for x in range(0, width):
            _point = s_data[y * width + x]
            if _point == WHITE_COLOR:
                _pic_str += ' '
            else:
                _pic_str += '*'
        _pic_str += '\n'

    print(_pic_str)


def gen_white_black_points(image):
    """
    根据点阵颜色强制转换黑白点
    """
    data = image.getdata()
    new_data = []
    for item in data:
        if item[0] > MAX_RGB_VALUE and item[1] > MAX_RGB_VALUE and item[2] > MAX_RGB_VALUE:
            new_data.append(WHITE_COLOR)
        else:
            new_data.append(BLACK_COLOR)
    return new_data


def reduce_noisy(width, height, points):
    """
    横向扫描, 获取最大边界大小. 除去小于最大噪点大小的面积.
    """
    # 标记位置, 初始化都是0, 未遍历过
    flag_list = []
    for i in range(width * height):
        flag_list.append(0)

    # 遍历
    for index, value in enumerate(points):
        _y = index // width
        _x = index - _y * width
        # print _x, _y
        if flag_list[index] == 0 and value == BLACK_COLOR:
            flag_list[index] = 1
            _tmp_list = [index]
            recursion_scan_black_point(_x, _y, width, height, _tmp_list, flag_list, points)
            if len(_tmp_list) <= MAX_NOISY_COUNT:
                for x in _tmp_list:
                    points[x] = WHITE_COLOR

        else:
            flag_list[index] = 1


def recursion_scan_black_point(x, y, width, height, tmp_list, flag_list, points):
    # 左上
    if 0 <= (x - 1) < width and 0 <= (y - 1) < height:
        _x = x - 1
        _y = y - 1
        _inner_recursion(_x, _y, width, height, tmp_list, flag_list, points)

    # 上
    if 0 <= (y - 1) < height:
        _x = x
        _y = y - 1
        _inner_recursion(_x, _y, width, height, tmp_list, flag_list, points)

    # 右上
    if 0 <= (x + 1) < width and 0 <= (y - 1) < height:
        _x = x + 1
        _y = y - 1
        _inner_recursion(_x, _y, width, height, tmp_list, flag_list, points)

    # 左
    if 0 <= (x - 1) < width:
        _x = x - 1
        _y = y
        _inner_recursion(_x, _y, width, height, tmp_list, flag_list, points)

    # 右
    if 0 <= (x + 1) < width:
        _x = x + 1
        _y = y
        _inner_recursion(_x, _y, width, height, tmp_list, flag_list, points)

    # 左下
    if 0 <= (x - 1) < width and 0 <= (y + 1) < height:
        _x = x - 1
        _y = y + 1
        _inner_recursion(_x, _y, width, height, tmp_list, flag_list, points)

    # 下
    if 0 <= (y + 1) < height:
        _x = x
        _y = y + 1
        _inner_recursion(_x, _y, width, height, tmp_list, flag_list, points)

    # 右下
    if 0 <= (x + 1) < width and 0 <= (y + 1) < height:
        _x = x + 1
        _y = y + 1
        _inner_recursion(_x, _y, width, height, tmp_list, flag_list, points)


def _inner_recursion(new_x, new_y, width, height, tmp_list, flag_list, points):
    _index = new_x + width * new_y
    if flag_list[_index] == 0 and points[_index] == BLACK_COLOR:
        tmp_list.append(_index)
        flag_list[_index] = 1
        recursion_scan_black_point(new_x, new_y, width, height, tmp_list, flag_list, points)
    else:
        flag_list[_index] = 1


pixivdaily_url = 'https://www.pixiv.net/ranking.php?mode=daily&content=illust'
p_session = session.get(pixivdaily_url, headers=session.headers)
pixivpage = p_session.text
pwebpages = pixivpage.split('data-src')

randomv = random.sample(range(1, 50), 2)
j1 = 2 * (randomv[0]) - 1
j2 = 2 * (randomv[1]) - 1
pwebpage1 = pwebpages[j1].split('"')[1]
pid1 = pwebpage1[65:73]
pwebpage1url = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + pid1
pwebpage2 = pwebpages[j2].split('"')[1]
pid2 = pwebpage2[65:73]
pwebpage2url = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + pid2

comment = pwebpage1url + '; ' + pwebpage2url
image_url = pwebpage1 + '|' + pwebpage2

url = 'https://www.douban.com/accounts/login'
form_data = {
    "redir": "https://www.douban.com",
    "form_email": '',
    "form_password": '',
    "login": u'登录'
}

r = session.post(url, data=form_data, headers=session.headers)
page = r.text

try:
    '''获取验证码图片'''
    # 利用bs4获取captcha地址
    soup = BeautifulSoup(page, "html.parser")
    captchaAddr = soup.find('img', id='captcha_image')['src']
    # 利用正则表达式获取captcha的ID
    reCaptchaID = r'<input type="hidden" name="captcha-id" value="(.*?)"/'
    captchaID = re.findall(reCaptchaID, page)[0]



    request.urlretrieve('https://www.douban.com/misc/captcha?id=' + captchaID + '&size=s', '/Users/yeyusong/Downloads/captcha.jpg')

    img = Image.open('/Users/yeyusong/Downloads/captcha.jpg')
    img = img.convert('RGBA')
    w, h = img.size[0], img.size[1]
    print(w, h)
    point_list = gen_white_black_points(img)
    print_char_pic(w, h, point_list)
    reduce_noisy(w, h, point_list)
    print_char_pic(w, h, point_list)

    img.putdata(point_list)
    img.save("/Users/yeyusong/Downloads/captcha1.png")

    captcha=pytesseract.image_to_string(Image.open('/Users/yeyusong/Downloads/captcha1.png'))
    print('https://www.douban.com/misc/captcha?id=' + captchaID + '&size=s')
    print(captcha)

#    captcha = input('please input the captcha:')

    form_data['captcha-solution'] = captcha
    form_data['captcha-id'] = captchaID

    r = session.post(url, data=form_data, headers=session.headers)
    page = r.text
except TypeError as e:
    pass

soup = BeautifulSoup(page, "html.parser")
ck_num = soup.find('input', {'name': 'ck', 'type': 'hidden'})['value']

wait_seconds = 2
for i in range(wait_seconds):
    print(wait_seconds - i)
    time.sleep(1)
comment_data = {'ck': ck_num,
                'comment': comment,
                'uploaded': image_url
                }
additional_headers = {'Cache-Control': 'max-age=0',
                      'Content-Type': 'application/x-www-form-urlencoded'
                      }
session.headers.update(additional_headers)

douban_url = 'https://www.douban.com'
r2 = session.post(douban_url, data=comment_data, headers=session.headers)
print(r2.text)
time.sleep(5)






