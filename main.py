import json
import re
import ast
import time
import hashlib
import base64
import urllib
import execjs
import requests
import config as XiaoMi_config
from typing import Any, Dict, Optional
 
 
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
    print(response2.text)
    Set_Cookie = response2.headers["Set-Cookie"]
    pattern = r"(userId|passToken)=([^;]+)"
    matches = re.findall(pattern, Set_Cookie)

    # 将结果转换为字典
    cookie_dict = {key: value for key, value in matches}
    return cookie_dict

def qqMusicVip(cookies_jrairstar, XiaoMi_config, session_id):
    finishMusicTask_body = {
	'musicVersion': '4.30.0.5',
	'session_id': session_id,
    }
    finishMusicTask_body["jrairstar_ph"] = cookies_jrairstar["jrairstar_ph"]
    XiaoMi_config.GoldRich_body["jrairstar_ph"] = cookies_jrairstar["jrairstar_ph"]
    
    # 视频
    for i in range(2):
        video_completeTask_response = requests.get(XiaoMi_config.video_completeTask_url, headers=XiaoMi_config.completeTask_headers, cookies=cookies_jrairstar)
        if "完成任务失败" in video_completeTask_response.text:
            print("video: ", video_completeTask_response.text)
            break
        video_response_value = json.loads(video_completeTask_response.text)
        # 检查响应是否成功
        if "value" in video_response_value:
            # 提取 value
            value = video_response_value['value']

            # 拼接新的 URL
            video_new_url = f"{XiaoMi_config.video_getaward_url}/{value}"  # 使用 / 拼接
            getaward_response = requests.get(video_new_url, headers=XiaoMi_config.completeTask_headers, cookies=cookies_jrairstar)
            print(getaward_response.text)

    # 音乐
    while True:
        finishMusicTask_response = requests.post(XiaoMi_config.finishMusicTask_url, headers=XiaoMi_config.finishMusicTask_headers, cookies=cookies_jrairstar, data=finishMusicTask_body)
        completeTask_response = requests.get(XiaoMi_config.completeTask_url, headers=XiaoMi_config.completeTask_headers, cookies=cookies_jrairstar)

        print("finishMusicTask: ", finishMusicTask_response.text)
        print("completeTask: ", completeTask_response.text)
        response_value = json.loads(completeTask_response.text)
        # 检查响应是否成功
        if "value" in response_value:
            # 提取 value
            value = response_value['value']

            # 拼接新的 URL
            new_url = f"{XiaoMi_config.getaward_url}/{value}"  # 使用 / 拼接
            getaward_response = requests.get(new_url, headers=XiaoMi_config.completeTask_headers, cookies=cookies_jrairstar)
            print(getaward_response.text)
        else:
            break
 
def read_cookie_file(startwith):
    file_path = '/home/mkr/Downloads/xiaomi/cookie.txt'  # 目标文件路径
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
        print(f"文件未找到: {file_path}")
    except Exception as e:
        print(f"发生错误: {e}")
    
    return None  # 如果没有找到，返回 None

def write_cookie_file(startwith, cookie_value):
    file_path = '/home/mkr/Downloads/xiaomi/cookie.txt'  # 目标文件路径
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
        print(f"文件未找到: {file_path}")
    except Exception as e:
        print(f"发生错误: {e}")

def xiaomi_main(session_id, XiaoMi_config):
    mobile =["", ""] # 手机号
    pwd = ["", ""] # 密码
    deviceId = ["3jnRcKFwE-aCC1aA", "aB3eFgHi-4jKlMnOp", "ZyXwVuTs-1QrStUvW", "5mNqRsTt-8HjKfGdE", "pL0oIuYt-2WqErTyZ"] #格式:AAaAa1-aCC1aAAA1
    phone_models = ["Redmi K20", "Redmi K30 Pro", "OnePlus 9", "Samsung Galaxy S21", "Mi 14 Pro", "OnePlus 12 Pro"]

    for i in range(len(mobile)):
        headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "{phone_models[i]}/cnm; MIUI/V14.0.5.0.SJKCNXM E/V140 B/S L/zh-CN LO/CN APP/xiaomi.account APPV/322103100 MK/UmVkbWkgSzMwIFBybw== SDKV/5.1.7.master CPN/com.mipay.wallet",
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
            print("更新cookies_login")

        cookies_jrairstar = get_cookies_by_passtk(cookies_login["userId"], cookies_login["passToken"], deviceId[i])
        qqMusicVip(cookies_jrairstar, XiaoMi_config, session_id)
    return 0
