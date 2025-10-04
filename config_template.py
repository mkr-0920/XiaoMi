from typing import List, Dict, Any

# --- 任务 API URL 配置 ---
# 这些 URL 包含 RegId 和 Oaid 等设备标识信息，如果您需要更换设备或更新参数，
# 请自行抓包替换对应的完整 URL。
finishMusicTask_url = "https://m.jr.airstarfinance.net/mp/api/qqMusicActivity/finishMusicTask"
completeTask_url = "https://m.jr.airstarfinance.net/mp/api/generalActivity/completeTask?activityCode=qq-music-201303&taskId=789&app=com.mipay.wallet&oaid=bb34f31df66617de&regId=FljLNOIxOyLAaa45iVbstKrQ5K1GZSQyfyWQFqh8zQvPgTRHGLzvlF1CRyckW4%2Bw&versionCode=20577576&versionName=6.86.0.5214.2284&isNfcPhone=true&channel=mipay_FLbanner_mymusic&deviceType=2&system=1&visitEnvironment=2&userExtra=%7B%22platformType%22:1,%22com.miui.player%22:%224.30.0.5%22,%22com.mipay.wallet%22:%226.86.0.5214.2284%22%7D"
getaward_url = "https://m.jr.airstarfinance.net/mp/api/generalActivity/luckDraw?imei=&device=lmi&appLimit=%7B%22com.qiyi.video%22:false,%22com.youku.phone%22:false,%22com.tencent.qqlive%22:false,%22com.hunantv.imgo.activity%22:false,%22com.cmcc.cmvideo%22:false,%22com.sankuai.meituan%22:false,%22com.anjuke.android.app%22:false,%22com.tal.abctimelibrary%22:false,%22com.lianjia.beike%22:false,%22com.kmxs.reader%22:false,%22com.jd.jrapp%22:false,%22com.smile.gifmaker%22:false,%22com.kuaishou.nebula%22:false%7D&activityCode=qq-music-201303&NFCQueryInfo=%7B%22deviceModel%22:%22lmi%22,%22cplc%22:%22479007644701F356060000150645284004544810000000510000041E2C9D3A1E80020000000000354552%22,%2C%22tsmclientVersionName%22:%2222.11.14.1.o%22,%22miuiSystemVersion%22:%22V140%22,%22appPackageName%22:%22com.mipay.wallet%22,%22appVersionName%22:%226.86.0.5214.2284%22,%22appVersionCode%22:20577576,%22miuiRomType%22:%22ANDROID%22%7D&app=com.mipay.wallet&oaid=bb34f31df66617de&regId=FljLNOIxOyLAaa45iVbstKrQ5K1GZSQyfyWQFqh8zQvPgTRHGLzvlF1CRyckW4%2Bw&versionCode=20577576&versionName=6.86.0.5214.2284&isNfcPhone=true&channel=mipay_FLbanner_mymusic&deviceType=2&system=1&visitEnvironment=2&userExtra=%7B%22platformType%22:1,%22com.miui.player%22:%224.30.0.5%22,%22com.mipay.wallet%22:%226.86.0.5214.2284%22%7D&userTaskId="
richsum_url = "https://m.jr.airstarfinance.net/mp/api/generalActivity/queryUserGoldRichSum?app=com.mipay.wallet&oaid=bb34f31df66617de&regId=SRmQk6gpPSF%2BIziLOYZ%2BFCa47cBirVAnewDTcbDkXuWOpugfC9rVLuimxdzl2Z6a&versionCode=20577595&versionName=6.89.1.5275.2323&isNfcPhone=true&channel=mipay_unloadoff_mymusic&deviceType=2&system=1&visitEnvironment=2&userExtra=%7B%22platformType%22:1,%22com.miui.player%22:%224.30.0.5%22,%22com.miui.video%22:%22v2025021290(MiVideo-UN)%22,%22com.mipay.wallet%22:%226.89.1.5275.2323%22%7D&activityCode=qq-music-201303"

video_completeTask_url = "https://m.jr.airstarfinance.net/mp/api/generalActivity/completeTask?activityCode=2211-videoWelfare&app=com.mipay.wallet&oaid=bb34f31df66617de&regId=WzUCJo8FdVHB1JTFPj1ZQ2HqcTSa9XeH21nvgBtCZ8Ubpe2bMqWxXLnhN5ZPuNPE&versionCode=20577576&versionName=6.86.0.5214.2284&isNfcPhone=true&channel=mipay_indexicon_TVcard&deviceType=2&system=1&visitEnvironment=2&userExtra=%7B%22platformType%22:1,%22com.miui.player%22:%224.30.0.5%22,%22com.mipay.wallet%22:%226.86.0.5214.2284%22%7D&taskId=813&browsTaskId=17&browsClickUrlId=815260365&clickEntryType=undefined"
video_getaward_url = "https://m.jr.airstarfinance.net/mp/api/generalActivity/luckDraw?imei=&device=lmi&appLimit=%7B%22com.qiyi.video%22:false,%22com.youku.phone%22:false,%22com.tencent.qqlive%22:false,%22com.hunantv.imgo.activity%22:false,%22com.cmcc.cmvideo%22:false,%22com.sankuai.meituan%22:false,%22com.anjuke.android.app%22:false,%22com.tal.abctimelibrary%22:false,%22com.lianjia.beike%22:false,%22com.kmxs.reader%22:false,%22com.jd.jrapp%22:false,%22com.smile.gifmaker%22:false,%22com.kuaishou.nebula%22:false%7D&activityCode=2211-videoWelfare&app=com.mipay.wallet&oaid=bb34f31df66617de&regId=WzUCJo8FdVHB1JTFPj1ZQ2HqcTSa9XeH21nvgBtCZ8Ubpe2bMqWxXLnhN5ZPuNPE&versionCode=20577576&versionName=6.86.0.5214.2284&isNfcPhone=true&channel=mipay_indexicon_TVcard&deviceType=2&system=1&visitEnvironment=2&userExtra=%7B%22platformType%22:1,%22com.miui.player%22:%224.30.0.5%22,%22com.mipay.wallet%22:%226.86.0.5214.2284%22%7D&userTaskId="
video_richsum_url = "https://m.jr.airstarfinance.net/mp/api/generalActivity/queryUserGoldRichSum?app=com.mipay.wallet&oaid=bb34f31df66617de&regId=SRmQk6gpPSF%2BIziLOYZ%2BFCa47cBirVAnewDTcbDkXuWOpugfC9rVLuimxdzl2Z6a&versionCode=20577595&versionName=6.89.1.5275.2323&isNfcPhone=true&channel=mipay_unloadoff_TVcard&deviceType=2&system=1&visitEnvironment=2&userExtra=%7B%22platformType%22:1,%22com.miui.player%22:%224.30.0.5%22,%22com.miui.video%22:%22v2025021290(MiVideo-UN)%22,%22com.mipay.wallet%22:%226.89.1.5275.2323%22%7D&activityCode=2211-videoWelfare"

# --- 任务请求通用 Headers ---
Mi_headers = {
    "Host": "m.jr.airstarfinance.net",
    "Connection": "keep-alive",
    # X-Request-ID 是随机/会话标识，通常不需要更改
    "X-Request-ID": "8e68b02b-ca6a-41a0-b655-35caafffd9d5", 
    "sec-ch-ua-platform": "Android",
    "Cache-Control": "no-cache",
    "sec-ch-ua": '"Android WebView";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?1",
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 12; zh-CN; Redmi K30 Pro Build/SKQ1.211006.001; AppBundle/com.mipay.wallet; AppVersionName/6.86.0.5214.2284; AppVersionCode/20577576; MiuiVersion/stable-V14.0.5.0.SJKCNXM; DeviceId/lmi; NetworkType/WIFI; mix_version) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Mobile Safari/537.36 XiaoMi/MiuiBrowser/4.3",
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "com.mipay.wallet",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}

# --- 敏感信息配置区域 (请勿提交到 GitHub!) ---

# 请替换 USER 列表中的空字符串为您的真实小米账号信息和配置。
USERS: List[Dict[str, str]] = [
    {
        "mobile": "", # 替换为您的手机号
        "pwd": "", # 替换为您的密码
        "deviceId": "", # 替换为您的设备ID (例如: 8qTnY4vBz-7fpxk2)
        "phone_model": "", # 替换为您的手机型号 (例如: Mi 14)
        "prizeCode": "", # 兑换奖励代码 (例如: LSXD_PRIZE1263)
        "music_rewards_number": "", # 音乐 VIP 奖励接收手机号
        "video_rewards_number": "", # 视频 VIP 奖励接收手机号
    },
    {
        "mobile": "", 
        "pwd": "",
        "deviceId": "",
        "phone_model": "",
        "prizeCode": "",
        "music_rewards_number": "",
        "video_rewards_number": "",
    },
    {
        "mobile": "", 
        "pwd": "",
        "deviceId": "",
        "phone_model": "",
        "prizeCode": "",
        "music_rewards_number": "",
        "video_rewards_number": "",
    },
    {
        "mobile": "", 
        "pwd": "",
        "deviceId": "",
        "phone_model": "",
        "prizeCode": "",
        "music_rewards_number": "",
        "video_rewards_number": "",
    },
    {
        "mobile": "", 
        "pwd": "",
        "deviceId": "",
        "phone_model": "",
        "prizeCode": "",
        "music_rewards_number": "",
        "video_rewards_number": "",
    },
    {
        "mobile": "", 
        "pwd": "",
        "deviceId": "",
        "phone_model": "",
        "prizeCode": "",
        "music_rewards_number": "",
        "video_rewards_number": "",
    },
    {
        "mobile": "", 
        "pwd": "",
        "deviceId": "",
        "phone_model": "",
        "prizeCode": "",
        "music_rewards_number": "",
        "video_rewards_number": "",
    },
    {
        "mobile": "", 
        "pwd": "",
        "deviceId": "",
        "phone_model": "",
        "prizeCode": "",
        "music_rewards_number": "",
        "video_rewards_number": "",
    },
    {
        "mobile": "", 
        "pwd": "",
        "deviceId": "",
        "phone_model": "",
        "prizeCode": "",
        "music_rewards_number": "",
        "video_rewards_number": "",
    },
    {
        "mobile": "", 
        "pwd": "",
        "deviceId": "",
        "phone_model": "",
        "prizeCode": "",
        "music_rewards_number": "",
        "video_rewards_number": "",
    },
]

# --- Telegram 配置 ---
# 请替换为您自己 Telegram Bot 的 Token 和 Chat ID
TELEGRAM_TOKEN = "" # 替换为您的 Telegram Bot Token
TELEGRAM_CHAT_ID = "" # 替换为您的 Chat ID
TELEGRAM_PROXY = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
