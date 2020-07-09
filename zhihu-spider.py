import requests as rq
from bs4 import BeautifulSoup as bf
import os
import time
import pickle
import threading
import random
import sys

"""1、知乎访问单页具体内容不需要使用cookies，只需要构造user-agent即可"""
base_path = os.getcwd()
headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}

cookies = {'_zap': '9690c57e-831d-48d4-9a04-50a8b725585f',
           ' d_c0': '"AJDZkfNoOBGPTiKZDn541aykDmbw4NBcaW8',
           ' _ga': 'GA1.2.807665962.1588623392',
           ' _gid': 'GA1.2.1777345792.1593351090',
           ' capsion_ticket':
           '"2|1:0|10:1593619136|14:capsion_ticket|44:YjU3YmUwMWFiZGQwNDEyYzliNTJiN2RhNGNlYzg4NjM',
           ' z_c0': '"2|1:0|10:1593619138|4:z_c0|92:Mi4xQ1ltYkF3QUFBQUFBa05tUjgyZzRFU1lBQUFCZ0FsVk53Z0RxWHdCM2FxZ1U1RTJNWWs1S0ZFczB4OGdEbWJCX0VR|627cd8f3188f88da0463e23324bcdf97a8ee35797f0da91072bed1261e1d23bc"',
           ' q_c1': '9f3550edaf5349c6acf591ae65aa6437|1593684133000|1593684133000',
           ' tst': 'r', ' _xsrf': 'ad077e8c-92d1-480b-8ba9-cff354c3261e',
           ' Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49': '1594059153,1594110705,1594213050,1594227325',
           ' SESSIONID': 'pDqfUDqjlbu3d5L2reuRI97SNQjDP0PkmXRtqsmMeWY',
           ' JOID': 'VlgVAknDADWM7dthOcbyrbxWNegst0RF6b6bEFKpZkC-iugpCzL6Mtbv32A7rGr0oSe8zVzV-J-m4HkIwfQ8eMw',
           ' osd': 'W1sRB0jOAzGJ7NZiPcPzoL9SMOkhtEBA6LOYFFeoa0O6j-kkCDb_M9vs22U6oWnwpCaxzljQ-ZKl5HwJzPc4fc0',
           ' Hm_lpvt_98beee57fd2ef70ccdd5ca52b9740c49': '1594228513',
           ' KLBRSID': 'd017ffedd50a8c265f0e648afe355952|1594228515|1594227329'
           }
# s.cookies = rq.utils.cookiejar_from_dict(cookies, cookiejar=None, overwrite=True)
s = rq.session()

def transcookies(rawcookies):
    a = rawcookies.split(';')
    a = [_.split('=') for _ in a]
    cookies = {}
    for i in a:
        cookies[i[0]] = i[1]
    return cookies

def analyze_raw_page():
    def extract(target):
        a = target.find('h2')
        title = a.a.get_text()
        link = a.a['href']
        return (title, link)

    def parseUrls(savedpage):
        with open(savedpage,'r',encoding='utf-8') as f:
            contents = f.read()
        soup = bf(contents, 'lxml')
        targets = soup.find_all(class_="css-8txec3")
        container = []
        for target in targets:
            container.append(extract(target))
        container = [["%03d_%s"%(each+1,container[each][0]), container[each][1]] for each in range(len(container))]
        with open('文章及链接.pl', 'wb') as f:
            pickle.dump(container, f)
        return container

    file_location = r"%s" % input('请复制粘贴要提取的文件地址：')
    data = parseUrls(file_location)
    return data

def dir_shift(folder):
    if not os.path.exists(folder):
        os.mkdir(folder)
        os.chdir(folder)
    else:
        os.chdir(folder)

def logs(errorinfo):
    file = base_path + '\\logs.txt'
    with open(file,'a', encoding='utf-8') as f:
        content = time.ctime() + ':\n' + errorinfo +'\n'+'*'*30
        f.write(content)

def generate_md(index, link, multiple_or_not=False):

    def get_title(header):
        dir_shift('pics')
        title = header.h1.get_text()
        icon = header.find('img')
        icon_link = icon['src']
        pic_suffix = os.path.splitext(icon_link)[1]
        icon_name = icon['alt']
        pic_name = icon_name + pic_suffix
        try:
            pic = s.get(url=icon_link, headers=headers, timeout=(30,30))
            with open(pic_name, 'wb') as f:
                f.write(pic.content)
        except:
            info = '图标 [%s] 获取失败 '%icon_link
            logs(info)
        finally:
            os.chdir('..')
            title_p = "# " + title + "\n"
            author = "__![%s](pics/%s)%s__\n"%(icon_name, pic_name, icon_name)
            with open(title + '.md', 'a', encoding='utf-8') as f:
                f.write(title_p)
                f.write(author)
            return title

    def get_pic(figure_tag):
        dir_shift('pics')
        link = figure_tag.find('img')['src']
        pic_name = link.split('/')[-1]
        print('插入图片%s'%pic_name)
        try:
            response = s.get(url=link, headers=headers, timeout=(20,30))
            with open(pic_name, 'wb') as f:
                f.write(response.content)
        except:
            info = "%s 图片 [%s] 获取失败"%(title,link)
            logs(info)
        finally:
            os.chdir('..')
            pic_adress = 'pics/' + pic_name
            return pic_adress

    def _further_deal_with_links(p_tag):
        if p_tag.a:
            link = p_tag.a.get_text()
            return "<p><a>%s</a></p>\n"%link
        else:
            return str(p_tag) + '\n'

    def get_paragraph(body):
        paragrahs = body.children
        with open(title + '.md', 'a', encoding='utf-8') as f:
            for line in paragrahs:
                if line.find('figure'):
                    pic_adress = get_pic(line)
                    pic = "![界面截图](%s)"%pic_adress + "\n"
                    f.write(pic)
                    time.sleep(1)
                else:
                    line = _further_deal_with_links(line)
                    f.write(line)

    def get_ending(article_tag):
        publish_date ="__%s__\n\n" % article.find(class_="ContentItem-time").get_text()
        tags = [_.get_text() for _ in article.find_all(class_="Tag Topic")]
        tag_note = ''
        for i in tags:
            tag_note += r"\#" + i + ' '
        tag_note = '__%s__\n' % tag_note
        view = article.find(class_="ContentItem-actions").get_text()
        view = view.replace('\u200b','-')
        view = view.split('--')
        likes ="***%s***\n" % view[0].replace('-','')
        comments ="***%s***\n" % view[1].split('-')[0]
        with open(title +'.md', 'a', encoding='utf-8') as f:
            f.write('\n\n')
            f.write(publish_date)
            f.write(tag_note)
            f.write(likes)
            f.write(comments)

    def sub_main(index, link):
        try:
            print('获取文章: %s'% index)
            response = s.get(url=link, headers=headers, timeout=(30,30))
            soup = bf(response.content, 'lxml')
            article = soup.find('article')
            title = get_title(article.header)
            body = article.find(class_="RichText ztext Post-RichText")
            get_paragraph(body)
            get_ending(article)
            processed.remove([index, link])
            # time.sleep(30)
        except:
            error = '获取文章 [%s] 出错'%index
            logs(error)

    if not multiple_or_not:
        dir_shift(index)
        sub_main(index, link)
        os.chdir('..')
    else:
        sub_main(index, link)

def mutipletask():
    distributed_tasks = [data[i*10: (i+1)*10] for i in range(len(data)//10 +1)]
    for tasks in distributed_tasks:
        threads = []
        for task in tasks:
            title = task[0]
            link = task[1]
            temp = threading.Thread(target=generate_md, args=(title, link, True))
            threads.append(temp)
            temp.start()
        end = [_.join() for _ in threads]
    print('\n获取成功，暂停程序1分钟，免得被封....\n')
    time.sleep(60)

def single_line_task():
    for each in data:
        title = each[0]
        link = each[1]
        try:
            generate_md(title, link)
            seconds = random.randint(1,60)
            print('\n获取成功，暂停程序%d秒，免得被封....\n'% seconds)
            time.sleep(seconds)
        except:
            logs('获取文件未知错误')
            input('暂时暂停程序.....')
        finally:
            if len(processed):
                with open(left_over,'wb') as f:
                    pickle.dump(processed, f)

if __name__=="__main__":
    choice = input('是否首先解析文件？yes/no: ')
    if choice == 'yes':
        data = analyze_raw_page()
    elif choice == 'no':
        if not os.path.exists('剩余文件.pl'):
            with open('文章及链接.pl', 'rb') as f:
                data = pickle.load(f)
        else:
            left_over = base_path + "\\剩余文件.pl"
            with open(left_over, 'rb') as f:
                data = pickle.load(f)
    else:
        print('输入错误，程序终止')
        sys.exit()
    processed = data.copy()
    single_line_task()
