import json
import re
import os
import time
import hashlib
import logging
import base64
import urllib.parse
import ast 
from typing import Any, Dict, Optional, List

# --- 导入外部配置文件 ---
import config as XiaoMi_config
# --- 导入外部配置文件 ---

# 使用 requests.Session 进行会话管理
import requests
from requests import Session, Response
from telebot import apihelper, TeleBot


# 将配置常量从 config.py 导入到本地变量 (保持原先的习惯，便于代码阅读)
USERS = XiaoMi_config.USERS
TELEGRAM_TOKEN = XiaoMi_config.TELEGRAM_TOKEN
TELEGRAM_CHAT_ID = XiaoMi_config.TELEGRAM_CHAT_ID
TELEGRAM_PROXY = XiaoMi_config.TELEGRAM_PROXY


# 配置日志格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)-8s - %(message)s')


def timestamp() -> int:
    """取13位时间戳"""
    return int(round(time.time() * 1000))

def md5_upper(s: str) -> str:
    """32位大写MD5加密"""
    return hashlib.md5(s.encode('utf-8')).hexdigest().upper()

def sha1_base64(nonce: str, ssecurity: str) -> str:
    """计算 clientSign"""
    input_str = f'nonce={nonce}&{ssecurity}'
    sha1_hash = hashlib.sha1(input_str.encode('utf-8')).digest()
    return base64.b64encode(sha1_hash).decode('utf-8')

def convert_to_hours(time_str: str) -> int:
    """
    将时间字符串转换为小时，支持 "X小时" 或 "X天"。
    已将 re.match 更改为 re.search，以应对 "音乐时长-1小时" 这种带前缀的字符串。
    """
    # 使用 re.search 允许在字符串中的任何位置找到匹配的数字和单位
    match = re.search(r"([\d.]+)(小时|天)", time_str)
    if match:
        value = float(match.group(1))
        unit = match.group(2)
        if unit == "小时":
            return int(value)
        elif unit == "天":
            return int(value * 24)
    raise ValueError(f"不支持的时间格式: {time_str}")

def safe_json_load(response: Response) -> Optional[Dict[str, Any]]:
    """健壮地解析 JSON 响应，处理小米API响应前的 START& 等前缀"""
    try:
        # 清除可能的非JSON前缀，例如 'START&'
        text = response.text.lstrip("&").lstrip("START").lstrip("&").strip()
        # 尝试查找第一个 { 和最后一个 }
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
             return json.loads(match.group(0))
        
        # 如果没有找到匹配，尝试直接加载
        return json.loads(text)
    except json.JSONDecodeError as e:
        logging.error(f"❌ JSON解析失败: {e}. 原始文本: {response.text[:100]}...")
        return None
    except Exception as e:
        logging.error(f"❌ 尝试解析JSON时发生意外错误: {e}")
        return None

def read_cookie_file(mobile: str, file_path: str = './cookies.txt') -> Dict[str, str]:
    """
    从文件读取指定用户的passToken和userId，使用 mobile={dict_str} 格式。
    注意：此函数已调整以匹配用户请求的非JSON格式。
    """
    default_value = {"passToken": "", "userId": ""}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.readlines()
            found = False
            value_str = ""
            
            for line in content:
                # 查找以 {mobile}= 开头的行
                if line.strip().startswith(f"{mobile}="):
                    # 提取 = 后的内容并去除换行符和空格
                    value_str = line.split('=', 1)[1].strip()
                    found = True
                    break
            
            if found:
                try:
                    # 使用 ast.literal_eval 转换字典字符串
                    value_dict = ast.literal_eval(value_str)
                    if isinstance(value_dict, dict):
                        return value_dict
                    else:
                        logging.error(f"❌ 读取Cookie文件失败: 找到的值不是字典: {value_str}")
                        return default_value
                except (ValueError, SyntaxError) as e:
                    logging.error(f"❌ 读取Cookie文件失败: 无法解析字典字符串 '{value_str}': {e}")
                    return default_value
            else:
                # 如果没找到，返回默认值
                logging.info(f"🔍 Cookie文件中未找到用户 {mobile} 的记录。")
                return default_value
    
    except FileNotFoundError:
        logging.info(f"✅ Cookie文件未找到，返回默认值。")
        return default_value
    
    except Exception as e:
        logging.error(f"❌ 读取Cookie文件时发生意外错误: {e}")
        return default_value

def write_cookie_file(mobile: str, cookie_dict: Dict[str, str], file_path: str = './cookies.txt'):
    """
    写入指定用户的passToken和userId到文件，使用 mobile={dict_str} 格式。
    注意：此函数已调整以匹配用户请求的非JSON格式。
    """
    # 转换为用户要求的格式字符串
    new_line = f"{mobile}={str(cookie_dict)}\n"
    found = False
    content = []
    
    try:
        # 尝试读取现有内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.readlines()
    except FileNotFoundError:
        # 文件不存在， content 保持为空列表
        pass 
    except Exception as e:
        logging.error(f"❌ 尝试读取旧Cookie文件时发生错误: {e}")
        return

    # 查找并替换或准备添加新行
    new_content = []
    for line in content:
        if line.strip().startswith(f"{mobile}="):
            new_content.append(new_line)
            found = True
        else:
            new_content.append(line) 
            
    if not found:
        # 如果没有找到，将新行添加到末尾
        new_content.append(new_line)
        
    # 写入新内容
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_content)
        logging.info(f"✅ 用户 {mobile[-4:]} 的 Cookies 已更新并写入文件。")
    except Exception as e:
        logging.error(f"❌ 写入Cookie文件失败: {e}")

# --- 业务逻辑类 ---

class XiaomiClient:
    """封装小米账户的登录、任务和奖励领取逻辑"""
    
    # 任务重试次数，尝试 3 次（1次初始尝试 + 2次重试）
    MAX_TASK_RETRIES = 3 

    def __init__(self, user_config: Dict[str, str], session: Session):
        self.mobile = user_config['mobile']
        self.pwd = user_config['pwd']
        self.device_id = user_config['deviceId']
        self.phone_model = user_config['phone_model']
        self.prize_code = user_config['prizeCode']
        self.music_rewards_number = user_config['music_rewards_number']
        self.video_rewards_number = user_config['video_rewards_number']
        self.session = session
        self.user_suffix = self.mobile[-4:]

        mihome_agent = "okhttp/3.12.1 APP/com.xiaomi.mihome APPV/6.0.101"
        self.account_headers = {
            "User-Agent": mihome_agent,
            "Accept-Encoding": "identity", # 使用 identity 避免压缩问题
            "Connection": "Keep-Alive",
        }
        self.session.headers.update(self.account_headers)
        
        # 构造 User-Agent 和 headers for account.xiaomi.com (登录)
        # self.account_headers = {
        #     "Content-Type": "application/x-www-form-urlencoded",
        #     "User-Agent": f"{self.phone_model}/cnm; MIUI/V14.0.5.0.SJKCNXM E/V140 B/S L/zh-CN LO/CN APP/xiaomi.account APPV/322103100 MK/UmVkbWkgSzMwIFBybw== SDKV/5.1.7.master CPN/com.mipay.wallet",
        #     "Host": "account.xiaomi.com",
        #     "Connection": "Keep-Alive",
        #     "Accept-Encoding": "gzip"
        # }
        # self.session.headers.update(self.account_headers)

    def _pre_login(self, sid: str) -> Optional[Dict[str, Any]]:
        """
        执行预登录操作，获取 _sign, qs 等后续步骤所需参数。
        这是一个被密码登录和二维码登录共用的辅助方法。
        """
        logging.info("➡️ 执行步骤 1 (预登录)...")
        try:
            url = f"https://account.xiaomi.com/pass/serviceLogin?_json=true&sid={sid}"
            self.session.headers.update({"Host": "account.xiaomi.com"})
            self.session.cookies.update({"deviceId": self.device_id, "sdkVersion": "3.4.1"})
            
            response = self.session.get(url)
            response.raise_for_status()

            if not response.text.startswith('&&&START&&&'):
                 raise ValueError("预登录响应格式不正确")

            data = json.loads(response.text.replace('&&&START&&&', ''))
            
            if not data or '_sign' not in data:
                logging.error(f"❌ 预登录失败. 未能获取 _sign. 响应: {response.text}")
                return None
            
            logging.info("✅ 登录步骤 1 (预登录) 成功, 已获取 _sign。")
            return data
        except Exception as e:
            logging.error(f"❌ 预登录过程中发生错误: {e}")
            return None

    @staticmethod
    def _print_qr(login_url: str):
        """在控制台打印二维码并保存为 qr.png 文件"""
        try:
            from qrcode import QRCode
            logging.info('📱 请在60秒内使用米家APP扫描下方二维码完成登录')
            qr = QRCode(border=1, box_size=10)
            qr.add_data(login_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save('qr.png')
            # 尝试在控制台打印
            qr.print_tty()
            logging.info('ℹ️  如果二维码显示不全, 请直接打开脚本目录下的 qr.png 文件进行扫描。')
        except ImportError:
            logging.error("❌ 未找到 qrcode 库, 无法生成二维码。请运行: pip install \"qrcode[pil]\"")
        except Exception as e:
            logging.warning(f"⚠️ 打印二维码到控制台失败: {e}. 请直接扫描 qr.png 文件。")


    def qr_login(self) -> Optional[Dict[str, str]]:
        """
        使用二维码扫码登录，此版本基于 token_extractor.py 的有效逻辑实现。
        """
        logging.info(f"🚀 开始为用户 {self.user_suffix} 进行二维码登录...")
        
        try:
            # 步骤 1: 直接请求二维码和长轮询地址 (基于 token_extractor.py)
            # 这个接口不需要复杂的 _sign，只需要提供正确的 sid 和 callback
            logging.info("➡️ 正在向新接口 /longPolling/loginUrl 请求二维码...")
            
            # 为 miui_vip 服务构造正确的 qs 和 callback
            sid = "miui_vip"
            callback_url = "https://api.vip.miui.com/sts"
            qs_miui_vip = f"?sid={sid}&_json=true"
            # 需要对 qs 参数进行 URL 编码
            qs_encoded = urllib.parse.quote(qs_miui_vip)

            params = {
                "_qrsize": "480",
                "qs": qs_encoded,
                "callback": callback_url,
                "_hasLogo": "false",
                "sid": sid,
                "_locale": "zh_CN", # 使用中文
                "_dc": str(int(time.time() * 1000))
            }

            url = "https://account.xiaomi.com/longPolling/loginUrl"
            response_qr = self.session.get(url, params=params)
            response_qr.raise_for_status()
            
            # 这个接口的响应带有 &&&START&&& 前缀
            qr_data = json.loads(response_qr.text.replace('&&&START&&&', ''))

            login_url = qr_data.get("loginUrl")
            lp_url = qr_data.get("lp")

            if not login_url or not lp_url:
                raise ValueError(f"未能从响应中获取二维码信息。响应: {qr_data}")

            self._print_qr(login_url)
            logging.info("✅ 二维码获取成功。")

            # 步骤 2: 长轮询等待扫码确认
            logging.info("⏳ 等待手机App扫码确认...")
            # token_extractor.py 中 lp 地址不带 https, 需要手动添加
            if not lp_url.startswith('https:'):
                lp_url = 'https:' + lp_url
            
            response_lp = self.session.get(lp_url, timeout=120) # 延长超时时间到2分钟
            response_lp.raise_for_status()

            lp_data = json.loads(response_lp.text.replace('&&&START&&&', ''))

            # 步骤 3: 提取最终凭证
            if lp_data.get("code") != 0:
                 raise ValueError(f"扫码登录失败: {lp_data.get('desc', '未知错误')}")

            user_id = lp_data.get("userId")
            pass_token = lp_data.get("passToken")

            if not user_id or not pass_token:
                logging.error(f"❌ 二维码登录成功，但未能提取有效凭证。响应: {lp_data}")
                return None

            logging.info(f"✅ 用户 {self.user_suffix} 二维码登录成功.")
            return {"userId": str(user_id), "passToken": pass_token}

        except requests.exceptions.Timeout:
            logging.error("❌ 登录超时，请重新运行脚本。")
            return None
        except Exception as e:
            logging.error(f"❌ 二维码登录过程中发生错误: {e}")
            return None
        finally:
            # 确保脚本退出时清理二维码图片
            if os.path.exists('qr.png'):
                os.remove('qr.png')


    def check_pass_token(self, user_id: str, pass_token: str) -> bool:
        """检查 passToken 是否有效"""
        logging.info(f"🔑 检查用户 {self.user_suffix} passToken 有效性...")
        try:
            self.session.cookies.update({"userId": user_id, "passToken": pass_token})
            
            response = self.session.get(
                "https://account.xiaomi.com/pass/serviceLogin?_json=true&appName=com.mipay.wallet&sid=jrairstar&_locale=zh_CN",
                allow_redirects=False,
                headers={"Host": "account.xiaomi.com"} # 明确Host
            )
            
            # 响应头中通常会包含 'Set-Cookie'，如果成功，会尝试重定向到 location (302)
            if response.status_code == 302:
                 logging.info(f"✅ 用户 {self.user_suffix} passToken 有效 (302 Redirect).")
                 return True
            
            # 尝试解析 JSON 响应
            result = safe_json_load(response)
            if result and result.get('code', 1) == 0: # 假设 code 0 为成功
                logging.info(f"✅ 用户 {self.user_suffix} passToken 有效 (JSON Code 0).")
                return True
            
            logging.warning(f"❌ 用户 {self.user_suffix} passToken 无效. 状态码: {response.status_code}, 响应: {response.text[:50]}...")
            return False
            
        except Exception as e:
            logging.error(f"❌ 检查 passToken 时发生网络错误: {e}")
            return False


    def login(self) -> Optional[Dict[str, str]]:
        """
        执行小米账户登录流程，获取新的 passToken 和 userId。
        此版本集成了从GitHub找到的、更新的预登录逻辑来解决70016错误。
        """
        logging.info(f"🚀 开始登录用户 {self.user_suffix}...")
        
        # 步骤 1: 预登录，获取 _sign 和 qs (采用新脚本的有效逻辑)
        # 我们将sid替换为我们需要的 "miui_vip"
        try:
            url1 = "https://account.xiaomi.com/pass/serviceLogin?_json=true&sid=miui_vip"
            
            # 确保使用 account host headers
            self.session.headers.update({"Host": "account.xiaomi.com"})
            # 新脚本的 Cookie 格式可能更有效
            self.session.cookies.update({"deviceId": self.device_id, "sdkVersion": "3.4.1"})

            response1 = self.session.get(url1)
            response1.raise_for_status() # 如果请求失败 (非200状态码), 抛出异常

            # 小米API的响应前缀是"&&&START&&&"，需要移除
            if not response1.text.startswith('&&&START&&&'):
                 raise ValueError("预登录响应格式不正确，缺少&&&START&&&前缀")

            pre_login_data = json.loads(response1.text.replace('&&&START&&&', ''))
            
            if not pre_login_data or '_sign' not in pre_login_data:
                logging.error(f"❌ 登录步骤 1 (预登录) 失败. 未能获取 _sign. 响应: {response1.text}")
                return None
            
            _sign = pre_login_data['_sign']
            qs = pre_login_data['qs']
            callback = pre_login_data['callback']
            
            logging.info("✅ 登录步骤 1 (预登录) 成功, 已获取 _sign。")

        except Exception as e:
            logging.error(f"❌ 登录步骤 1 (预登录) 过程中发生错误: {e}")
            return None

        # 步骤 2: 提交登录凭证 (沿用你之前的逻辑, 但使用上一步获取到的新凭证)
        try:
            url2 = "https://account.xiaomi.com/pass/serviceLoginAuth2"
            data2 = {
                "user": self.mobile,
                "hash": md5_upper(self.pwd),
                "_sign": _sign,
                "qs": qs,
                "callback": callback,
                "sid": "miui_vip",
                "_json": "true",
            }
            
            # 确保使用正确的 Host 和 Content-Type
            self.session.headers.update({"Host": "account.xiaomi.com", "Content-Type": "application/x-www-form-urlencoded"})
            response2 = self.session.post(url2, data=data2)
            response2.raise_for_status()
            
            if not response2.text.startswith('&&&START&&&'):
                 raise ValueError("认证响应格式不正确，缺少&&&START&&&前缀")

            auth_data = json.loads(response2.text.replace('&&&START&&&', ''))

            if auth_data.get('code') != 0:
                desc = auth_data.get('desc', '未知错误')
                # 检查是否需要验证码
                if 'notificationUrl' in auth_data or 'captchaUrl' in auth_data:
                    logging.error(f"❌ 登录失败: 需要安全验证 (验证码), 无法自动处理。描述: {desc}")
                else:
                    logging.error(f"❌ 登录失败. Code: {auth_data.get('code')}, 描述: {desc}")
                return None

            # 从响应中获取 userId，并从会话的Cookie中获取 passToken
            user_id = auth_data.get("userId")
            pass_token = self.session.cookies.get("passToken")

            if not user_id or not pass_token:
                logging.error(f"❌ 登录成功，但未能从响应中提取有效凭证. 响应: {response2.text}")
                return None
            
            logging.info(f"✅ 用户 {self.user_suffix} 登录成功.")
            return {"userId": str(user_id), "passToken": pass_token}

        except Exception as e:
            logging.error(f"❌ 登录步骤 2 (认证) 过程中发生错误: {e}")
            return None


    def get_jrairstar_cookies(self, user_id: str, pass_token: str) -> Optional[Dict[str, str]]:
        """使用 passToken 转换为 jr.airstarfinance.net 所需的 Cookies"""
        logging.info(f"🔗 转换 {self.user_suffix} 的 jrairstar cookies...")
        try:
            # 步骤 1: 访问 serviceLogin 获取 location, nonce, ssecurity
            self.session.cookies.update({"userId": user_id, "passToken": pass_token})
            
            # 确保使用 account host headers
            self.session.headers.update({"Host": "account.xiaomi.com"})
            response_wallet = self.session.get(
                "https://account.xiaomi.com/pass/serviceLogin?_json=true&appName=com.mipay.wallet&sid=jrairstar&_locale=zh_CN",
                allow_redirects=False,
            )
            
            response_wallet_data = safe_json_load(response_wallet)
            if not response_wallet_data or response_wallet_data.get('code') != 0:
                 logging.error(f"❌ 获取重定向参数失败. 响应: {response_wallet.text}")
                 return None

            url = response_wallet_data["location"]
            client_sign = sha1_base64(response_wallet_data["nonce"], response_wallet_data["ssecurity"])
            client_sign_quoted = urllib.parse.quote(client_sign)
            
            # 步骤 2: 访问重定向 URL 获取最终的 jrairstar cookies
            new_url = f"{url}&clientSign={client_sign_quoted}"
            
            # 更新 session cookies
            self.session.cookies.update({"deviceId": self.device_id})
            # 确保使用 jrairstar host headers
            self.session.headers.update({"Host": "api.jr.airstarfinance.net"})

            response_jrairstar = self.session.get(new_url, allow_redirects=False)
            set_cookie = response_jrairstar.headers.get("Set-Cookie", "")
            
            pattern = r"(serviceToken|userId|jrairstar_slh|jrairstar_ph)=([^;]+)"
            matches = re.findall(pattern, set_cookie)
            
            cookie_dict = {key: value for key, value in matches}
            
            if not cookie_dict:
                 logging.error(f"❌ 未能从 jrairstar 重定向响应中获取 cookies. 响应: {response_jrairstar.text[:100]}...")
                 return None

            logging.info(f"✅ 成功获取用户 {self.user_suffix} 的 jrairstar cookies.")
            return cookie_dict
            
        except Exception as e:
            logging.error(f"❌ 转换 jrairstar cookies 失败: {e}")
            return None

    def update_qq_music_session(self):
        """更新 QQ 音乐的 Session ID (原 update_sessionid)"""
        logging.info("🎶 尝试更新 QQ 音乐 Session ID...")
        url = "https://mt.y.qq.com/cgi-bin/musics.fcg"
        
        # Opaque payload, kept as is
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
        }

        try:
            # 使用 requests 库的原始调用方式，不使用 Session 的默认头
            response = requests.post(url, data=byte_data, headers=headers)
            logging.info(f"🎶 update_sessionid 响应: {response.text[:50]}...")
        except Exception as e:
            logging.error(f"❌ 更新 QQ 音乐 Session ID 失败: {e}")

    def run_vip_tasks(self, cookies_jrairstar: Dict[str, str]) -> Dict[str, Any]:
        """执行视频和音乐任务，并领取奖励 (已添加重试机制)"""
        
        # 任务结果
        result = {
            "video_sum_hours": 0,
            "music_sum_hours": 0,
            "video_richsum_days": 0.0,
            "music_richsum_days": 0.0,
            "music_exchange_result": "未兑换",
            "video_exchange_result": "未兑换"
        }
        
        # 将 jrairstar cookies 应用到 session
        self.session.cookies.update(cookies_jrairstar)
        
        # 将用户提供的 Mi_headers 应用到 session，覆盖 account_headers 中的 Host, User-Agent 等
        self.session.headers.update(XiaoMi_config.Mi_headers)
        
        # 确保 jrairstar_ph 在 music task body 中
        finish_music_task_body = {
            'musicVersion': '4.30.0.5',
            # 这里的 session_id 最好是通过 update_qq_music_session 获取，但目前是硬编码
            'session_id': '4d2f474e-e324-4d7c-a8cc-8c3cb8f72fc51746761526672', 
            'jrairstar_ph': cookies_jrairstar.get("jrairstar_ph", "")
        }
        
        MAX_RETRIES = self.MAX_TASK_RETRIES # 任务重试次数

        # --- 视频任务循环 (执行 2 次，带重试) ---
        for i in range(2):
            logging.info(f"🎬 开始第 {i+1} 次视频任务...")
            
            # 尝试 MAX_RETRIES 次完成并领取奖励
            for attempt in range(MAX_RETRIES):
                try:
                    # 1. 完成任务 (GET)
                    video_complete_url = XiaoMi_config.video_completeTask_url
                    video_task_resp = self.session.get(video_complete_url)
                    video_task_data = safe_json_load(video_task_resp)
                    
                    if not video_task_data:
                        # 如果无法解析数据，视为网络/服务错误，尝试重试
                        raise Exception("Failed to get video task response data (JSON/Network error).")

                    if video_task_data.get('code') != 0:
                        logging.info(f"❌ 视频任务完成失败或结束: {video_task_resp.text}. 尝试下一个任务。")
                        # 任务可能已完成，跳出重试循环，进入下一个外层任务（i+1）
                        break 

                    task_value = video_task_data.get('value')
                    if not task_value:
                        # 没有 value，说明无可领取的任务，跳出重试循环，进入下一个外层任务（i+1）
                        break

                    # 2. 领取奖励 (GET)
                    video_award_url = f"{XiaoMi_config.video_getaward_url}{task_value}"
                    award_resp = self.session.get(video_award_url)
                    award_data = safe_json_load(award_resp)
                    
                    if award_data and award_data.get('code') == 0 and award_data.get('value'):
                        prize_name = award_data["value"]["prizeInfo"]["prizeName"]
                        hours = convert_to_hours(prize_name)
                        result["video_sum_hours"] += hours
                        logging.info(f"✅ 视频任务领奖成功，获得 {hours} 小时.")
                        break # 成功，跳出重试循环
                    else:
                        logging.warning(f"❌ 视频任务领奖失败. 尝试重试 ({attempt + 1}/{MAX_RETRIES}). 响应: {award_resp.text}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(2 ** attempt) # 指数退避等待
                            continue
                        else:
                            logging.error(f"❌ 视频任务领奖失败，达到最大重试次数。")
                            break # 达到最大重试次数，跳出重试循环
                            
                except Exception as e:
                    logging.error(f"❌ 视频任务过程中发生网络/解析错误: {e}. 尝试重试 ({attempt + 1}/{MAX_RETRIES}).")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(2 ** attempt) # 指数退避等待
                        continue
                    else:
                        logging.error(f"❌ 视频任务失败，达到最大重试次数。")
                        break
            
            # 在每个外层任务（i）之间休息 1 秒
            time.sleep(1)


        # --- 音乐任务循环 (直到任务结束，带重试) ---
        while True:
            task_successful = False
            
            # 尝试 MAX_RETRIES 次完成并领取奖励
            for attempt in range(MAX_RETRIES):
                try:
                    logging.info(f"🎧 尝试完成和领取音乐任务 (重试 {attempt + 1}/{MAX_RETRIES})...")

                    # 1. 完成任务 (POST)
                    self.session.post(XiaoMi_config.finishMusicTask_url, data=finish_music_task_body) 
                    
                    # 2. 领取任务 (GET)
                    music_task_resp = self.session.get(XiaoMi_config.completeTask_url)
                    music_task_data = safe_json_load(music_task_resp)

                    if not music_task_data:
                        raise Exception("Failed to get completeTask response data (JSON/Network error).")

                    if music_task_data.get('code') != 0:
                        logging.info(f"❌ 音乐任务完成失败或结束: {music_task_resp.text}")
                        # 任务已结束，跳出重试循环
                        break 
                    
                    task_value = music_task_data.get('value')
                    if not task_value:
                        # 无可领取的任务，跳出重试循环
                        break
                    
                    # 3. 领取奖励 (GET)
                    music_award_url = f"{XiaoMi_config.getaward_url}{task_value}"
                    award_resp = self.session.get(music_award_url)
                    award_data = safe_json_load(award_resp)

                    if award_data and award_data.get('code') == 0 and award_data.get('value'):
                        prize_name = award_data["value"]["prizeInfo"]["prizeName"]
                        hours = convert_to_hours(prize_name)
                        result["music_sum_hours"] += hours
                        logging.info(f"✅ 音乐任务领奖成功，获得 {hours} 小时.")
                        task_successful = True
                        break # 成功，跳出重试循环
                    else:
                        logging.warning(f"❌ 音乐任务领奖失败. 尝试重试 ({attempt + 1}/{MAX_RETRIES}). 响应: {award_resp.text}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(2 ** attempt) # 指数退避等待
                            continue
                        else:
                            logging.error(f"❌ 音乐任务失败，达到最大重试次数。")
                            break
                            
                except Exception as e:
                    logging.error(f"❌ 音乐任务过程中发生网络/解析错误: {e}. 尝试重试 ({attempt + 1}/{MAX_RETRIES}).")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(2 ** attempt) # 指数退避等待
                        continue
                    else:
                        logging.error(f"❌ 音乐任务失败，达到最大重试次数。")
                        break
            
            # 如果重试后仍然失败（或任务已结束），则跳出外层 while True 循环
            if not task_successful:
                break
                
            time.sleep(1) # 在任务循环之间休息 1 秒

        # --- 统计累计时长 ---
        try:
            # 视频累计
            video_richsum_resp = self.session.get(XiaoMi_config.video_richsum_url)
            video_richsum_data = safe_json_load(video_richsum_resp)
            if video_richsum_data and "value" in video_richsum_data:
                result["video_richsum_days"] = round(video_richsum_data["value"] / 100, 2)

            # 音乐累计
            music_richsum_resp = self.session.get(XiaoMi_config.richsum_url)
            music_richsum_data = safe_json_load(music_richsum_resp)
            if music_richsum_data and "value" in music_richsum_data:
                # 假设 1440 是兑换所需的小时数或积分 (根据旧脚本保留)
                result["music_richsum_days"] = round(music_richsum_data["value"] / 1440, 2) 

        except Exception as e:
            logging.error(f"❌ 统计累计时长失败: {e}")

        # --- 兑换 VIP 奖励 ---
        
        # 音乐兑换
        if result["music_richsum_days"] >= 31:
            logging.info(f"🎵 尝试兑换用户 {self.user_suffix} 的音乐 VIP...")
            # 兑换 URL 保持原脚本结构
            exchange_url = f"https://m.jr.airstarfinance.net/mp/api/generalActivity/convertGoldRich?prizeCode=tencent-31&activityCode=qq-music-201303&phone={self.music_rewards_number}&app=com.mipay.wallet"
            exchange_resp = self.session.get(exchange_url)
            exchange_data = safe_json_load(exchange_resp)
            if exchange_data and exchange_data.get("value"):
                result["music_exchange_result"] = exchange_data["value"]["prizeInfo"]["prizeGiveDesc2"]
            else:
                result["music_exchange_result"] = f"兑换失败: {exchange_resp.text[:50]}..."
        
        # 视频兑换
        if result["video_richsum_days"] >= 31 and self.prize_code and self.video_rewards_number:
            logging.info(f"🎬 尝试兑换用户 {self.user_suffix} 的视频 VIP...")
            # 兑换 URL 保持原脚本结构
            video_exchange_url = f"https://m.jr.airstarfinance.net/mp/api/generalActivity/convertGoldRich?prizeCode={self.prize_code}&activityCode=2211-videoWelfare&phone={self.video_rewards_number}&app=com.mipay.wallet"
            exchange_resp = self.session.get(video_exchange_url)
            exchange_data = safe_json_load(exchange_resp)
            if exchange_data and exchange_data.get("value"):
                result["video_exchange_result"] = exchange_data["value"]["prizeInfo"]["prizeGiveDesc2"]
            else:
                result["video_exchange_result"] = f"兑换失败: {exchange_resp.text[:50]}..."
        
        return result

# --- 主执行逻辑 ---
def xiaomi_main_optimized(users: List[Dict[str, str]]):
    """主执行函数，迭代所有用户"""
    
    # 尝试执行 QQ Music Session 更新
    # 注意: 这里使用第一个用户的配置来构造临时 client
    if not users:
        logging.error("用户列表为空，无法执行任务。")
        return {}

    temp_client = XiaomiClient(users[0], requests.Session())
    temp_client.update_qq_music_session()
    
    prize_all: Dict[str, str] = {}
    
    for user in users:
        mobile = user['mobile']
        user_suffix = mobile[-4:]
        
        # 使用独立的 Session 处理每个用户，避免 Cookies 混淆
        with requests.Session() as session:
            client = XiaomiClient(user, session)
            
            # 1. 检查和更新 passToken
            cookie_data = read_cookie_file(mobile)
            user_id = cookie_data.get("userId", "")
            pass_token = cookie_data.get("passToken", "")

            # 检查 passToken 是否有效
            if not client.check_pass_token(user_id, pass_token):
                # 无效则重新登录, 优先使用二维码登录
                logging.info("🔑 passToken 无效或已过期，将启动二维码登录流程。")
                new_cookies = client.qr_login() # <--- 新的调用
                if new_cookies:
                    write_cookie_file(mobile, new_cookies)
                    user_id = new_cookies["userId"]
                    pass_token = new_cookies["passToken"]
                else:
                    prize_all[user_suffix] = "❌ 登录失败，跳过任务。"
                    continue
            
            # 2. 获取 jrairstar 任务 Cookies
            cookies_jrairstar = client.get_jrairstar_cookies(user_id, pass_token)
            if not cookies_jrairstar:
                prize_all[user_suffix] = "❌ 获取 jrairstar 任务 Cookies 失败，跳过任务。"
                continue
                
            # 3. 执行任务和兑换
            results = client.run_vip_tasks(cookies_jrairstar)

            prize_all[user_suffix] = (
                f"视频任务获得 {results['video_sum_hours']} 小时，累计 {results['video_richsum_days']} 天；"
                f"音乐任务获得 {results['music_sum_hours']} 小时，累计 {results['music_richsum_days']} 天；\n"
                f"音乐兑换结果: {results['music_exchange_result']}\n"
                f"视频兑换结果: {results['video_exchange_result']}"
            )
            
    return prize_all

# --- 程序入口 ---
if __name__ == '__main__':
    # 从配置文件导入 USERS
    formatted_prize_all_dict = xiaomi_main_optimized(USERS)
    formatted_prize_all_str = json.dumps(formatted_prize_all_dict, indent=2, ensure_ascii=False)
    
    logging.info(f"--- 最终任务报告 ---\n{formatted_prize_all_str}")

    # Telegram 通知
    apihelper.proxy = TELEGRAM_PROXY
    BOT = TeleBot(TELEGRAM_TOKEN)
    
    report_message = f"小米 VIP 任务报告:\n{formatted_prize_all_str}"
    
    try:
        BOT.send_message(chat_id=TELEGRAM_CHAT_ID, text=report_message)
    except Exception as e:
        logging.error(f"❌ Telegram 消息发送失败: {e}")
