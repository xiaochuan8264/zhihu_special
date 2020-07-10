import requests as rq
from bs4 import BeautifulSoup as bf
import os, time, pickle, threading, random, sys
from stopit import threading_timeoutable as Timeout
"""1、知乎访问单页具体内容不需要使用cookies，只需要构造user-agent即可"""
base_path = os.getcwd()
left_over = base_path + "\\剩余文件.pl"
headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}
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
        content = time.ctime() + ':\n' + errorinfo +'\n'+'*'*30 + '\n'
        f.write(content)

def generate_md(index, link, multiple_or_not=False):

    def process_icon_link(icon_link):
        if "?" in icon_link:
            icon_link = icon_link.split('?')[0]
            return icon_link
        else:
            return icon_link

    def get_title(header):
        dir_shift('pics')
        title = header.h1.get_text()
        icon = header.find('img')
        icon_link = process_icon_link(icon['src'])
        pic_suffix = os.path.splitext(icon_link)[1]
        icon_name = icon['alt']
        pic_name = icon_name + pic_suffix
        try:
            pic = s.get(url=icon_link, headers=headers, timeout=20)
            with open(pic_name, 'wb') as f:
                f.write(pic.content)
        except Exception as e:
            info = '图标 [%s] 获取失败--%s '%(icon_link, e)
            logs(info)
        finally:
            os.chdir('..')
            title_p = "# " + title + "\n"
            author = "__![%s](pics/%s)%s__\n"%(icon_name, pic_name, icon_name)
            with open(title + '.md', 'a', encoding='utf-8') as f:
                f.write(title_p)
                f.write(author)
            return title

    def get_pic(figure_tag, container):
        if figure_tag.name == 'img':
            link = figure_tag['src']
        else:
            link = figure_tag.find('img')['src']
        pic_name = link.split('/')[-1]
        container.append((link, pic_name))
        pic_path = 'pics/' + pic_name
        return [pic_path, container]

    @Timeout()
    def download_pics(container, title):
        dir_shift('pics')
        def single_pic_download(pic_link, pic_name, title):
            try:
                response = s.get(url=pic_link, headers=headers, timeout=20)
                with open(pic_name, 'wb') as f:
                    f.write(response.content)
            except Exception as e:
                info = "%s 图片 [%s] 获取失败--%s"%(title,pic_link,e)
                logs(info)
            time.sleep(1)

        threads = []
        for pic in container:
            temp = threading.Thread(target=single_pic_download, args=(pic[0], pic[1],title))
            threads.append(temp)
            temp.start()
        t = [_.join() for _ in threads]

    def handle_link(line):
        if line.name == 'a':
            link = line.get('href')
        else:
            link = line.find('a').get('href')
        text = line.get_text()
        return "<p><a href='%s'>%s</a></p>\n"%(link, text)

    def handle_p(p_tag):
        if not p_tag.get_text():
            return '\n'
        else:
            return "<p>%s</p>\n"%p_tag.get_text()

    def handle_others(line):
        attrs = line.attars
        tag = line.name
        try:
            if not attrs:
                for key in attrs.copy().keys():
                    del line[key]
        except AttributeError as e:
            pass
        text = "<%s>%s</%s>\n"%(tag,line.get_text(), tag)
        return text

    def get_paragraph(body, title):
        pic_container = []
        paragraphs = body.children
        with open(title + '.md', 'a', encoding='utf-8') as f:
            for line in paragraphs:
                # deal with images
                if (line.find('figure')!=-1 and line.find('figure')!=None ) or line.name == 'figure':
                    pic_info = get_pic(line, pic_container)
                    pic_path = pic_info[0]
                    pic_container = pic_info[1]
                    pic = "![界面截图](%s)"%pic_path + "\n"
                    f.write(pic)
                    time.sleep(1)
                elif line.name == 'a' or line.find('a'):
                    text = handle_link(line)
                    f.write(text)
                elif line.name == 'p':
                    text = handle_p(line)
                    f.write(text)
                elif "h" in line.name:
                    f.write(str(line)+'\n')
                else:
                    text = handle_others(line)
                    f.write(text)
        return pic_container

    def get_ending(article_tag, title):
        publish_date ="__%s__\n\n" % article_tag.find(class_="ContentItem-time").get_text()
        tags = [_.get_text() for _ in article_tag.find_all(class_="Tag Topic")]
        tag_note = ''
        for i in tags:
            tag_note += r"\#" + i + ' '
        tag_note = '__%s__\n' % tag_note
        view = article_tag.find(class_="ContentItem-actions").get_text()
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

    if not multiple_or_not:
        dir_shift(index)
    try:
        print('获取文章: %s'% index)
        new_base = os.getcwd()
        response = s.get(url=link, headers=headers, timeout=(30,30))
        soup = bf(response.content, 'lxml')
        article = soup.find('article')
        title = get_title(article.header)
        body = article.find(class_="RichText ztext Post-RichText")
        pics_collected = get_paragraph(body, title)
        get_ending(article, title)
        print('︹'*10)
        print('插入文章图片，共%d张' % len(pics_collected))
        download_pics(pics_collected, title, timeout=90)
        os.chdir(new_base)
        print('完成！')
        print('︺'*10)
        processed.remove([index, link])
    except Exception as e:
        error = '获取文章 [%s] 出错--%s'%(index, e)
        logs(error)
        raise
    os.chdir(base_path)

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
        except Exception as e:
            logs('文件未知错误--%s'%e)
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
            with open(left_over, 'rb') as f:
                data = pickle.load(f)
    else:
        print('输入错误，程序终止')
        sys.exit()
    processed = data.copy()
    single_line_task()
