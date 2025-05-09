import json
import re
import ast
import time
import hashlib
import logging
import base64
import urllib
import requests
from pprint import pformat
import config as XiaoMi_config
from typing import Any, Dict, Optional
 
# 配置日志格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)-8s - %(message)s')

# 取13位时间戳
def timestamp():
    return int(round(time.time() * 1000))
 
 
# 32位大写MD5加密
def md5(str):
    import hashlib
    m = hashlib.md5()
    m.update(str.encode('utf-8'))
    return m.hexdigest().upper()
 
 
# 正则取出{}中的内容
def get_json(text):
    start = text.find('{')
    end = text.rfind('}')
    return text[start:end + 1]

def sha1_base64(nonce, ssecurity):
    # 拼接字符串
    input_str = f'nonce={nonce}&{ssecurity}'
    
    # 计算 SHA-1 哈希
    sha1_hash = hashlib.sha1(input_str.encode('utf-8')).hexdigest()
    
    # 将十六进制哈希转换为字节
    hex_bytes = bytes.fromhex(sha1_hash)
    
    # 转换为 Base64
    clientSign = base64.b64encode(hex_bytes).decode('utf-8')
    
    return clientSign

def extract_hours(time_str):
    """从时间字符串中提取小时数"""
    # 使用正则表达式匹配格式为 "音乐时长-1小时" 的字符串
    match = re.search(r"(\d*\.?\d+)小时", time_str)
    if match:
        # 提取数字部分并转换为整数
        return int(float(match.group(1)))
    else:
        raise ValueError("不支持的时间格式")

def convert_to_hours(time_str):
    """将时间字符串转换为小时"""
    # 使用正则表达式提取数字部分
    match = re.match(r"([\d.]+)(小时|天)", time_str)
    if match:
        value = float(match.group(1))  # 提取数字部分（可能是浮点数）
        unit = match.group(2)           # 提取单位
        if unit == "小时":
            return int(value)           # 返回小时
        elif unit == "天":
            return int(value * 24)      # 1天 = 24小时
    else:
        raise ValueError("不支持的时间格式")

def get(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = 20,
    **kwargs,
):
    """
    说明：
        get请求封装
    参数：
        :param url: url
        :param headers: 请求头
        :param params: params
        :param data: data
        :param json: json
        :param timeout: 超时时间
    """
    return requests.get(url, headers=headers, params=params, timeout=timeout, **kwargs)

def text_cookies(user_id: str, pass_token: str):
    """使用passToken获取签到cookies"""
    try:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Redmi K80 Pro/cnm; MIUI/V14.0.5.0.SJKCNXM E/V140 B/S L/zh-CN LO/CN APP/xiaomi.account APPV/322103100 MK/UmVkbWkgSzMwIFBybw== SDKV/5.1.7.master",
            "Host": "account.xiaomi.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }
        cookies = {"userId": user_id, "passToken": pass_token, }
        response = get(
            "https://account.xiaomi.com/pass/serviceLogin?_json=true&appName=com.mipay.wallet&sid=jrairstar&_locale=zh_CN",
            cookies=cookies,
            headers=headers,
            allow_redirects=False
        )
        if "成功" in response.text:
            return True
        else: return False
    except Exception:
        return False

def get_cookies_by_passtk(user_id: str, pass_token: str, deviceId):
    """使用passToken获取签到cookies"""
    try:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Redmi K30 Pro/cnm; MIUI/V14.0.5.0.SJKCNXM E/V140 B/S L/zh-CN LO/CN APP/xiaomi.account APPV/322103100 MK/UmVkbWkgSzMwIFBybw== SDKV/5.1.7.master",
            "Host": "account.xiaomi.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }
        cookies = {"userId": user_id, "passToken": pass_token, }
        response = get(
            "https://account.xiaomi.com/pass/serviceLogin?_json=true&appName=com.mipay.wallet&sid=jrairstar&_locale=zh_CN",
            cookies=cookies,
            headers=headers,
            allow_redirects=False
        )

        result = response.text.lstrip("&").lstrip("START").lstrip("&")
        response_wallet = json.loads(result)
        url = response_wallet["location"]
        clientSign = sha1_base64(response_wallet["nonce"], response_wallet["ssecurity"])
        clientSign = urllib.parse.quote(clientSign)

        cookies_jrairstar = {
            "deviceId": deviceId
        }
        new_url = f"{url}&clientSign={clientSign}"
        headers['Host'] = 'api.jr.airstarfinance.net'
        response_jrairstar = requests.get(new_url, headers=headers, cookies=cookies_jrairstar, allow_redirects=False)
        Set_Cookie = response_jrairstar.headers["Set-Cookie"]

        pattern = r"(serviceToken|userId|jrairstar_slh|jrairstar_ph)=([^;]+)"
        matches = re.findall(pattern, Set_Cookie)

        # 将结果转换为字典
        cookie_dict = {key: value for key, value in matches}
        return cookie_dict
        
    except Exception:
        print("从passToken获取 Cookie 失败")
        return {}


# 登陆
def login(mobile, deviceId, pwd, headers):
    cookies1 = {
        "userId": mobile,
        "deviceId": deviceId
    }
    url1 = "https://account.xiaomi.com/pass/serviceLogin"
    params1 = {
        "_json": "true",
        "sid": "miui_vip",
        "_locale": "zh_CN"
    }
    response1 = requests.get(url1, headers=headers, cookies=cookies1, params=params1)
 
    response1 = json.loads(get_json(response1.text))
    cookies2 = {
        "deviceId": deviceId
    }
    url2 = "https://account.xiaomi.com/pass/serviceLoginAuth2"
    data = {
        "qs": response1['qs'],
        # ?_json=true&sid=miui_vip&_locale=zh_CN
        "callback": "https://api.vip.miui.com/sts",
        "_json": "true",
        "_sign": response1['_sign'],
        "user": mobile,
        "hash": md5(pwd),  # 密码
        "sid": "miui_vip",
        "_locale": "zh_CN"
    }
    headers["Content-Length"] = "241"
    response2 = requests.post(url2, headers=headers, cookies=cookies2, data=data)
    print(response2.headers)
    Set_Cookie = response2.headers["Set-Cookie"]
    pattern = r"(userId|passToken)=([^;]+)"
    matches = re.findall(pattern, Set_Cookie)

    # 将结果转换为字典
    cookie_dict = {key: value for key, value in matches}
    return cookie_dict

def update_sessionid():
    url = "https://mt.y.qq.com/cgi-bin/musics.fcg"

    hex_str = "05 4B 63 2D 0D 78 9C 8D 54 DB 52 A3 40 10 FD 95 2D 9E 4D 9C 1B CC E0 5B D6 C4 0D D1 44 B3 B9 AC FA 42 C1 30 24 44 6E 81 81 88 56 FE 7D 67 46 AB 8C D6 56 AD 3C 4D 37 A7 CF 9C 3E DD F0 6A F1 22 CB AC 8B 57 EB B6 14 F9 6A E8 0D AD 0B 4B 10 66 33 8A 19 8E DC 88 10 C4 42 57 60 81 03 4C C3 38 46 D8 0D AD 33 AB 89 92 E8 7B 48 2E 15 0E 42 7D 6A D5 09 21 88 01 00 4C C5 5F 42 BE 35 94 10 98 47 17 14 B5 DF 8A 4A E7 90 8A CA 6D 91 0B D9 95 42 25 7E 8B 28 4B 7E 5C 63 F0 E3 AE 2A 34 95 A8 EA A4 C8 2F 8B 48 7C 26 9D 7B D3 91 87 1D 95 64 04 53 86 02 C8 39 70 03 48 21 83 AE 83 5C 37 D4 F7 41 82 21 B3 3F 0A BE 0F 2F 02 23 3A 0C 31 89 31 8C 62 C7 71 20 55 22 CE AC 48 B4 09 17 A9 68 45 AA 00 58 F7 53 15 CA 69 EB 3E 09 8A 69 72 3E F5 56 DE F9 1A 12 A0 5E C8 4C 0C CA D2 78 BF DF 67 4D 9D F0 34 91 9A 44 35 FC DE 31 04 58 23 CB A0 92 B9 A8 FC 3C C8 74 F6 59 71 65 C9 49 3E 28 4B 23 08 31 86 30 C0 D4 81 36 A4 88 28 F5 AE B6 38 4D 44 2E 47 B9 76 5E B3 1D 0C B6 A7 B5 B5 24 29 CD A0 68 1F 32 DC 87 84 F4 A1 86 34 06 62 53 62 BB 8E 0D 1D AC 52 F5 DB 0D 00 D9 C0 06 AE 12 86 00 FB 04 68 6A 51 FD 9B 4D 56 01 17 6F 63 86 3E F8 28 F2 21 25 0E B5 A9 8A 4E 9A 31 40 77 B1 DE 5E A7 97 3E 04 1B CF ED E6 87 43 8E EB C3 EC 85 EC C6 62 B6 98 B0 8C DD 46 E9 32 B7 E7 46 6B AE 85 D9 B6 43 18 A0 14 9D FA C2 B9 A8 6B 5F 16 4F 42 63 D6 D8 5F E6 0B FA D2 35 8F 52 DE C7 F6 68 75 F5 70 28 77 FE C2 1D DF 78 E5 EA 10 FF 7C 18 6F 96 DD 2F 70 E3 C7 A3 ED FC 2A DA 5D 0E AB 49 D1 93 7C 49 C7 BB 4E 74 8B 2E 45 C5 93 3B 68 D6 FB 59 D0 78 37 33 51 56 C1 80 8A 72 30 48 DC 69 58 26 57 0F 5E B1 9C 6D 86 0D 9A 65 5E BB 39 40 DE F6 FC AE DB 3F 5E F3 55 3E 9F 54 93 13 71 46 95 2F 9E CB A4 12 B5 52 47 94 A3 C0 3A 9E 59 66 15 FA 27 2B D1 BF 37 03 FF 13 A4 A9 90 8B B6 EA 2F 84 1C 44 77 69 D0 2D 64 20 9B 5A 7F C8 59 11 35 A9 5E 8E FF 56 2B 09 99 90 DB 42 DB FC 95 C8 A8 0B CC 9F A1 56 CE A9 8F EB 6D 1C 24 42 31 A1 44 F4 04 46 A4 47 22 CA 7B 01 E3 BC C7 38 E6 21 8B 29 8A B9 6D 86 A9 36 0F 39 8E 19 42 FD AE 0D 1E 8F C7 BF 62 B5 4D 39"
    hex_str = hex_str.replace(" ", "")
    byte_data = bytes.fromhex(hex_str)
    headers = {
    'User-Agent': "QQMusic 22130008(android 12)",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "",
    'Content-Type': "application/octet-stream",
    'sign': "R1lWVlhGUkRRRkFXf8F9RnrmmNvB04Ya8A6yi7m9QhU=",
    'M-Encoding': "m1",
    'x-sign-data-type': "json",
    'mask': "IOT4LbT8+vIkPO8D9JYvDJ8L0GTUNr38+WuG5XoCEoQNlW13hSCsfrxRDVA6G9GI7sit3fu8dGU8tv9pX0l+hISCbTpa1brafpM41nCXTGmGEF80dOVm5m5jkPiDSpQ1oA+ppbNuDrk=",
    'Content-Type': "application/x-www-form-urlencoded"
    }

    response = requests.post(url, data=byte_data, headers=headers)

    logging.info(f"update_sessionid: {response.text}")

def qqMusicVip(cookies_jrairstar, XiaoMi_config):
    finishMusicTask_body = {
	'musicVersion': '4.30.0.5',
	'session_id': '4d2f474e-e324-4d7c-a8cc-8c3cb8f72fc51746761526672',
    }
    finishMusicTask_body["jrairstar_ph"] = cookies_jrairstar["jrairstar_ph"]
    XiaoMi_config.GoldRich_body["jrairstar_ph"] = cookies_jrairstar["jrairstar_ph"]
    
    video_sum = 0
    music_sum = 0
    # 视频
    for i in range(2):
        video_completeTask_response = requests.get(XiaoMi_config.video_completeTask_url, headers=XiaoMi_config.completeTask_headers, cookies=cookies_jrairstar)
        if "失败" in video_completeTask_response.text:
            logging.info(f"❌ video: {video_completeTask_response.text}")
            break
        video_response_value = json.loads(video_completeTask_response.text)
        # 检查响应是否成功
        if "value" in video_response_value:
            # 提取 value
            value = video_response_value['value']

            # 拼接新的 URL
            video_new_url = f"{XiaoMi_config.video_getaward_url}/{value}"  # 使用 / 拼接
            getaward_response = requests.get(video_new_url, headers=XiaoMi_config.completeTask_headers, cookies=cookies_jrairstar)
            getaward_response = json.loads(getaward_response.text)
            if "value" in getaward_response:
                video_hours = getaward_response["value"]["prizeInfo"]["prizeName"]
                video_hours = convert_to_hours(video_hours)
                video_sum = video_sum + video_hours



    # 音乐
    while True:
        finishMusicTask_response = requests.post(XiaoMi_config.finishMusicTask_url, headers=XiaoMi_config.finishMusicTask_headers, cookies=cookies_jrairstar, data=finishMusicTask_body)
        completeTask_response = requests.get(XiaoMi_config.completeTask_url, headers=XiaoMi_config.completeTask_headers, cookies=cookies_jrairstar)

        logging.info(f"finishMusicTask: {finishMusicTask_response.text}")
        logging.info(f"completeTask: {completeTask_response.text}")
        response_value = json.loads(completeTask_response.text)
        # 检查响应是否成功
        if "value" in response_value:
            # 提取 value
            value = response_value['value']

            # 拼接新的 URL
            new_url = f"{XiaoMi_config.getaward_url}/{value}"  # 使用 / 拼接
            getaward_response = requests.get(new_url, headers=XiaoMi_config.completeTask_headers, cookies=cookies_jrairstar)
            getaward_response = json.loads(getaward_response.text)
            if "value" in getaward_response:
                music_hours = getaward_response["value"]["prizeInfo"]["prizeName"]
                music_hours = extract_hours(music_hours)
                music_sum = music_sum + music_hours
        else:
            break
    video_richsum = 0
    music_richsum = 0
    video_richsum_response = requests.get(XiaoMi_config.video_richsum_url, headers=XiaoMi_config.completeTask_headers, cookies=cookies_jrairstar)
    if "value" in video_richsum_response.text:
        video_richsum_response = json.loads(video_richsum_response.text)
        video_richsum = round(video_richsum_response["value"]/100, 2)

    music_richsum_response = requests.get(XiaoMi_config.richsum_url, headers=XiaoMi_config.completeTask_headers, cookies=cookies_jrairstar)
    if "value" in music_richsum_response.text:
        music_richsum_response = json.loads(music_richsum_response.text)
        music_richsum = round(music_richsum_response["value"]/1440, 2)

    return video_sum, music_sum, video_richsum, music_richsum
 
def read_cookie_file(startwith):
    file_path = '/home/ubuntu/tgbot/xiaomi/cookie.txt'  # 目标文件路径
    try:
        # 读取文件内容
        with open(file_path, 'r') as f:
            content = f.readlines()
            for line in content:
                # 查找以 startwith 开头的行
                if line.startswith(f"{startwith}="):
                    # 提取 = 后的内容并去除换行符
                    value = line.split('=', 1)[1].strip()
                    return value  # 返回提取的值
    except FileNotFoundError:
        logging.info(f"❌ 文件未找到: {file_path}")
    except Exception as e:
        logging.info(f"❌ 发生错误: {e}")
    
    return None  # 如果没有找到，返回 None

def write_cookie_file(startwith, cookie_value):
    file_path = '/home/ubuntu/tgbot/xiaomi/cookie.txt'  # 目标文件路径
    try:
        with open(file_path, 'r') as f:
            content = f.readlines()

        with open(file_path, 'w') as f:
            for line in content:
                # 查找以 startwith 开头的行
                if line.startswith(f"{startwith}="):
                    f.write(f"{startwith}={cookie_value}\n")
                else:
                    f.write(line)  # 保留其他行
    except FileNotFoundError:
        logging.info(f"❌ 文件未找到: {file_path}")
    except Exception as e:
        logging.info(f"❌ 发生错误: {e}")

def xiaomi_main(XiaoMi_config):
    update_sessionid()
    mobile =["", ""] # 手机号
    pwd = ["", ""] # 密码
    deviceId = ["3jnRcKFwE-g3Pxun", "3jnRcKFwE-aCC1aA", "aB3eFgHi-4jKlMnOp", "ZyXwVuTs-1QrStUvW", "5mNqRsTt-8HjKfGdE", "pL0oIuYt-2WqErTyZ"] #格式:AAaAa1-aCC1aAAA1
    phone_models = ["Redmi K20", "Redmi K30 Pro", "OnePlus 9", "Samsung Galaxy S21", "Mi 14 Pro", "OnePlus 12 Pro"]
    prize_all={}
    for i in range(len(mobile)):
        headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": f"{phone_models[i]}/cnm; MIUI/V14.0.5.0.SJKCNXM E/V140 B/S L/zh-CN LO/CN APP/xiaomi.account APPV/322103100 MK/UmVkbWkgSzMwIFBybw== SDKV/5.1.7.master CPN/com.mipay.wallet",
        "Host": "account.xiaomi.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
        }
        cookies_read = read_cookie_file(mobile[i])
        # 将结果转换为字典
        cookies_login = ast.literal_eval(cookies_read)

        if not text_cookies(cookies_login["userId"], cookies_login["passToken"]):
            cookies_login = login(mobile[i], deviceId[i], pwd[i], headers)
            write_cookie_file(mobile[i], cookies_login)
            logging.info("🍪 更新cookies_login")

        cookies_jrairstar = get_cookies_by_passtk(cookies_login["userId"], cookies_login["passToken"], deviceId[i])
        video_sum, music_sum, video_richsum, music_richsum = qqMusicVip(cookies_jrairstar, XiaoMi_config)
        prize_all[mobile[i][-4:]] = f"视频{video_sum}小时，累计{video_richsum}天；音乐{music_sum}小时，累计{music_richsum}天；"
    formatted_prize_all = pformat(prize_all, indent=2)
    logging.info(f"{formatted_prize_all}")
    # return formatted_prize_all