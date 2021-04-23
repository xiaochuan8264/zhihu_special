import argparse, threading, os, pickle, time
import requests as rq
import zhihu_spider as zhihu

parser = argparse.ArgumentParser()
parser.add_argument("file_object", help="the folder system is going into")
# parser.add_argument("title", help="the folder system is going into")
args = parser.parse_args()

def download(container, title):
    zhihu.dir_shift('pics')
    def single_pic_download(pic_link, pic_name, title):
        try:
            response = zhihu.s.get(url=pic_link, headers=zhihu.headers, timeout=20)
            with open(pic_name, 'wb') as f:
                f.write(response.content)
        except Exception as e:
            info = "%s 图片 [%s] 获取失败--%s"%(title,pic_link,e)
            zhihu.logs(info)
        time.sleep(1)
    threads = []
    for pic in container:
        temp = threading.Thread(target=single_pic_download, args=(pic[0], pic[1],title))
        threads.append(temp)
        temp.start()
    t = [_.join() for _ in threads]
    zhihu.dir_shift('..')

def main():
    with open(args.file_object, 'rb') as f:
        container = pickle.load(f)
    download(container[1:], container[0])
    os.remove(args.file_object)

if __name__ == "__main__":
    main()
