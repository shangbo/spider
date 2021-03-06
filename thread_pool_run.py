#!/usr/bin/env python
# -*- coding:utf-8 -*-

#stardard module
import threading
import Queue
import sys
import urllib2

#custom module
from html_parse import MMHtmlParse
from thread_run import do_page_parse

#set coding
reload(sys)
sys.setdefaultencoding('utf8')

MUTEX = threading.Lock()                        #全局变量锁,实现子线程互斥访问 



class ThreadPool(object):
    """
        handout and recyle the threads
    """
    def __init__(self, root_url, threads_num, image_group_num):
        self.root_url = root_url
        self.threads = []
        self.events = []
        self.queue = Queue.Queue()
        self.max_threads_num = threads_num
        self.image_group_num = image_group_num
        self.visited_url = []
        self.count = [0, ]              #add

        self._init_queue()
        self._create_event()
        self._create_threads()

    def _init_queue(self):
        """initialize url queue, put the root url into queue"""
        self.queue.put((do_page_parse, self.root_url))
       
    def _create_event(self):
        """set a event mechanism for every child thread for blocking and awaking child thread"""
        for i in range(self.max_threads_num):
            event = threading.Event()
            self.events.append(event)

    def _create_threads(self):
        """initialize 5 threads"""
        for i in range(self.max_threads_num):
            event = self.events[i]
            thread = PageParseThread(self.queue, i+1, event, self.visited_url, self.count)          # modified
            self.threads.append(thread)
            thread.start()


    def get_thread(self):
        """awake a thread for dealing the url in head of queue """
        for i, event in enumerate(self.events):
            if not event.isSet():
                event.set()
                return i
        return False

    
    def check_queue(self):
        """check queue for not dealing url"""
        un_deal = 0
        for event in self.events:
            if event.isSet():
                un_deal = 1
                break
        if self.queue.empty() and un_deal == 0:
            return False
        else:
            return True

    
    def check_image_finished(self):
        """check image totality"""
        if self.image_group_num == -2:
            return True
        else:
            if self.count[0] < self.image_group_num - 1:
                return True
            else:
                return False


class PageParseThread(threading.Thread):
    """
        define a thread for parse the <a> and <img> tag
    """
    def __init__(self, queue, thread_number=0, event=None, visited_url=None, count=[0,]):      # modified for robustness
        threading.Thread.__init__(self,name='page_parser_thread_%d' % thread_number)
        if isinstance(queue, Queue.Queue):
            self.queue = queue      
        else:
            self.queue = Queue.Queue()
        
        if isinstance(event, threading.Event):
            self.event = event
        else:
            self.event = threading.Event()

        if isinstance(visited_url, list)
            self.visited_url = visited_url
        else:
            self.visited_url = []

        self.parser = MMHtmlParse(self.queue, self.visited_url)  #为每一个线程匹配一个html解析器
        self.image_count = count                                 #图片计数

    def run(self):
        while True:
            self.event.wait()                                    #使用event将线程阻塞在此处
            if not self.queue.empty():
                func, url = self.queue.get()
                if self.visited_url.count(url) == 0 and isinstance(url, str): #modified for robustness
                    self.visited_url.append(url)      
                if self.queue.empty():                           #当取出最后一个url的时候做解析，可能会导入新的url
                    MUTEX.acquire()          
                    if url.startswith("http:"):
                        func(url)
                        self.image_count[0] += 1                                     # modified
                    else:
                        func(url, self.parser)
                    if not self.queue.empty(): 
                        MUTEX.release()
                else:                                  
                    if url.startswith("http:"):
                        func(url)
                        self.image_count[0] += 1                                     # modified
                        print "test: %d " % self.image_count[0]
                    else:
                        func(url, self.parser)
                self.queue.task_done()
                self.event.clear() 


def run_main():
    root_url = "/"
    image_group_num = deal_argv()
    if not image_group_num == -1:
        pool = ThreadPool(5,root_url, image_group_num)
        while pool.check_queue():
            pool.get_thread()
            if not pool.check_image_finished():
                print "finished"
                break

def deal_argv():
    """
    return -2:  run all time
    return -1:  arguments error!
    """
    if len(sys.argv) <= 2 :
        try:
            image_group_num = int(sys.argv[1])
            if image_group_num > 0:
                return image_group_num
            else:
                print "arguments error, %d less than 0,your argument must be greater than 0" % image_group_num
                return -1
        except IndexError:
            image_group_num = -2
            print "you don't give me a image totality argument,I will work all the time! You can use (ctrl + c) to stop me!"
            return image_group_num
        except ValueError:
            print "arguments error,you need to input a integer argument(>0)"
        
    else:
        print "arguments error,your arguments is too much! I need it only one!"
        return -1

if __name__ == '__main__':
     run_main()

    

