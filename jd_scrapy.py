import requests
import requests.packages.urllib3
import time
import random
import json
from PIL import Image

class pyJD(object):

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
            'ContentType': 'text/html; charset=utf-8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
        }

        self.urls = {
            'login': 'https://passport.jd.com/new/login.aspx',
            'index': '',
            'QR_image': 'https://qr.m.jd.com/show',
            'QR_check': 'https://qr.m.jd.com/check',
            'QR_verify': 'https://passport.jd.com/uc/qrCodeTicketValidation'
        }

        self.sess = requests.Session()
        self.cookies = {}

    def login_by_QR(self):

        try:
            resp = self.sess.get(
                self.urls['login'],
                headers=self.headers
            )
            if resp.status_code != requests.codes.OK:
                print(u'获取登录页面失败: %u' % resp.status_code)
                return False

            ## save cookies
            for k, v in resp.cookies.items():
                self.cookies[k] = v

            # step 2: get QR image
            resp = self.sess.get(
                self.urls['QR_image'],
                headers=self.headers,
                cookies=self.cookies,
                params={
                    'appid': 133,
                    'size': 147,
                    't': int(time.time() * 1000)
                }
            )
            if resp.status_code != requests.codes.OK:
                print(u'获取二维码失败: %u' % resp.status_code)
                return False

            ## save cookies
            for k, v in resp.cookies.items():
                self.cookies[k] = v

            ## save QR code
            image_file = 'qr.png'
            with open(image_file, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=1024):
                    f.write(chunk)

            code = ''
            qr_image = Image.open(image_file)
            for x in range(0, 49):
                for y in range(0, 49):
                    pix = qr_image.getpixel((x*3, y*3))
                    if pix == 0:
                        code += '▇'
                    else:
                        code += '  '
                code += '\n'

            print(code)

            # step 3: check scan result
            ## mush have
            self.headers['Host'] = 'qr.m.jd.com'
            self.headers['Referer'] = 'https://passport.jd.com/new/login.aspx'

            # check if QR code scanned
            qr_ticket = None
            retry_times = 100
            while retry_times:
                retry_times -= 1
                resp = self.sess.get(
                    self.urls['QR_check'],
                    headers=self.headers,
                    cookies=self.cookies,
                    params={
                        'callback': 'jQuery%u' % random.randint(100000, 999999),
                        'appid': 133,
                        'token': self.cookies['wlfstk_smdl'],
                        '_': int(time.time() * 1000)
                    }
                )

                if resp.status_code != requests.codes.OK:
                    continue

                n1 = resp.text.find('(')
                n2 = resp.text.find(')')
                rs = json.loads(resp.text[n1 + 1:n2])

                if rs['code'] == 200:
                    print(u'{} : {}'.format(rs['code'], rs['ticket']))
                    qr_ticket = rs['ticket']
                    break
                else:
                    print(u'{} : {}'.format(rs['code'], rs['msg']))
                    time.sleep(3)

            if not qr_ticket:
                print(u'二维码登陆失败')
                return False

            # step 4: validate scan result
            ## must have
            self.headers['Host'] = 'passport.jd.com'
            self.headers['Referer'] = 'https://passport.jd.com/uc/login?ltype=logout'
            resp = self.sess.get(
                self.urls['QR_verify'],
                headers=self.headers,
                cookies=self.cookies,
                params={'t': qr_ticket},
            )
            if resp.status_code != requests.codes.OK:
                print(u'二维码登陆校验失败: %u' % resp.status_code)
                return False

            ## 京东有时候会认为当前登录有危险，需要手动验证
            ## url: https://safe.jd.com/dangerousVerify/index.action?username=...
            res = json.loads(resp.text)
            if not resp.headers.get('P3P'):
                if res.has_key('url'):
                    print(u'需要手动安全验证: {0}'.format(res['url']))
                    return False
                else:
                    self.print_json(res)
                    print(u'登陆失败!!')
                    return False

            ## login succeed
            self.headers['P3P'] = resp.headers.get('P3P')
            for k, v in resp.cookies.items():
                self.cookies[k] = v

            print(u'登陆成功')
            return True


        except Exception as e:
            print('Exp:', e)
            raise
            return False


if __name__ == '__main__':
    print('hello world')
    myJD = pyJD()
    myJD.login_by_QR()