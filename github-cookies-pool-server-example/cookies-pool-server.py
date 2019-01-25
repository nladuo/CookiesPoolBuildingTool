from flask import Flask, request
import json
import requests
import datetime
import hashlib


def get_md5(_str):
    hl = hashlib.md5()
    _bytes = _str.encode("utf-8")
    hl.update(_bytes)
    return hl.hexdigest()


app = Flask(__name__)


All_Cookies = []
PASSWORD = "test"
cookie_id = 1


def github_validate(cookies):
    cookie_header = ""
    for c in cookies:
        cookie_header += c["name"] + "="
        cookie_header += c["value"] + "; "

    resp = requests.get("https://github.com", headers={
        "Cookie": cookie_header,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
    })
    if "Sign&nbsp;in" in resp.content.decode("utf-8"):
        return False
    else:
        return True


@app.route('/')
def ping():
    passwd = request.args.get('passwd')
    # check password valid
    if passwd != PASSWORD:
        return json.dumps({
            "code": 501,
            "msg": "password error"
        })
    return json.dumps({
        "code": 200,
        "msg": "pong"
    })


@app.route('/add_cookie')
def add_cookie():
    global cookie_id
    cookies_str = request.args.get('cookies')
    passwd = request.args.get('passwd')
    # check password valid
    if passwd != PASSWORD:
        return json.dumps({
            "code": 501,
            "msg": "password error"
        })
    cookies = json.loads(cookies_str)
    print(cookies)
    if github_validate(cookies):

        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        md5 = get_md5(cookies_str)

        exist = False
        for c in All_Cookies:
            if c["md5"] == md5:
                exist = True

        if not exist:
            All_Cookies.append({
                "id": cookie_id,
                "md5": md5,
                "update_time": now
            })
            cookie_id += 1
            return json.dumps({
                "code": 200,
                "msg": "success"
            })
        else:
            return json.dumps({
                "code": 503,
                "msg": "请勿添加重复的cookie"
            })
    else:
        return json.dumps({
            "code": 502,
            "msg": "cookie验证失败"
        })


@app.route('/get_cookies')
def get_cookies():
    passwd = request.args.get('passwd')
    if passwd != PASSWORD:
        return json.dumps({
            "code": 501,
            "msg": "password error"
        })

    return json.dumps({
        "code": 200,
        "data": All_Cookies
    })


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3839, debug=True)

