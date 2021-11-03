import glob
import pprint
import urllib
import urllib.parse
import os
import sys


def save_tag_text(tag_list, args):
    with open('./z_list\\end.txt', mode='a', encoding='utf-8') as f:
        t = tag_list[0] + '\n'
        f.write(t)

    tag_list.pop(0)

    with open(args, mode='w', encoding='utf-8') as f:
        for i in tag_list:
            t = i + '\n'
            f.write(t)


def glob_form_txt(path, extension, save_txt_path):
    # print('get from ./do2/*.txt files')
    files = glob.glob(path + '*' + extension)
    files = [f.replace(path, '').replace(extension, '').split("+")[0] for f in files]

    files = [urllib.parse.unquote(f) for f in files]
    pprint.pprint(files)

    with open(save_txt_path, mode='w', encoding='utf-8') as f:
        for i in files:
            t = i + '\n'
            f.write(t)


def glob_dirs(path, save_txt_path):
    files = os.listdir(path)
    files = [f for f in files if os.path.isdir(os.path.join(path, f))]

    files = [f.replace(path, '').split("+")[0] for f in files]
    files = [urllib.parse.unquote(f) for f in files]
    pprint.pprint(files)

    with open(save_txt_path, mode='w', encoding='utf-8') as f:
        for i in files:
            t = i + '\n'
            f.write(t)


def remove_Duplicate(txt_path):
    with open(txt_path, mode='r', encoding='utf-8') as file:
        f = file.readlines()
        f = [li.rstrip() for li in f]

        tag_list_src = sorted(f)
        tag_list_sorted = sorted(list(set(f)))

    with open(txt_path, mode='w', encoding='utf-8') as f:
        for i in tag_list_sorted:
            t = i + '\n'
            f.write(t)

    with open(txt_path.replace('.txt', '') + '_back.txt', mode='w', encoding='utf-8') as f:
        for i in tag_list_src:
            t = i + '\n'
            f.write(t)


def check_all_Duplicate(txt_path):
    with open(txt_path, mode='r', encoding='utf-8') as file:
        f = file.readlines()
        f = [li.rstrip() for li in f]

        tag_list_sorted = sorted(list(set(f)))

    with open('./z_list\\end.txt', mode='r', encoding='utf-8') as file:
        f_all = file.readlines()
        f_all = [li.rstrip() for li in f_all]

        all_list_sorted = sorted(list(set(f_all)))

    for item in all_list_sorted:
        for tag in tag_list_sorted:
            if item == tag:
                print('item: {}'.format(item))
                tag_list_sorted.remove(item)

    # print(tag_list_sorted)

    with open(txt_path, mode='w', encoding='utf-8') as f:
        for i in tag_list_sorted:
            t = i + '\n'
            f.write(t)

    # with open(txt_path.replace('.txt', '') + '_back.txt', mode='w', encoding='utf-8') as f:
    #     for i in tag_list_src:
    #         t = i + '\n'
    #        f.write(t)


if __name__ == '__main__':
    args = sys.argv

    # check_all_Duplicate(args[1])
    remove_Duplicate(args[1])
    
    
    # glob_form_txt('.\\end_commit\\', '.txt')
    # glob_dirs('H:\いろいろ\sankaku_complex\___old', './z_list\\new_end_commit.txt')