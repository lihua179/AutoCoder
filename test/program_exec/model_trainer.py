# -*- coding: utf-8 -*-










import time

if __name__ == '__main__':
    count = 0
    while True:
        count += 1
        print(f'模型训练-{count}')
        if count > 40:
            print(f'退出程序')
            raise ValueError('error???')
            # break
        time.sleep(0.1)
# import time
#
# if __name__ == '__main__':
#     count = 0
#     while True:
#         count += 1
#         print(f'数据采集2-{count}')
#         time.sleep(0.5)
#         if count > 30:
#             print(f'退出程序')
#             break
