import os
import numpy
from os import listdir
from os.path import isfile, join, isdir


parent_path = os.path.abspath('.')
path = "{}/images".format(parent_path)


def get_model_images_count(path):
    image_count = 0
    for name in os.listdir(path):
        sub_path = join(path, name)
        if os.path.isfile(sub_path):
            image_count += 1
            print(sub_path)     # TODO print dataset
    exit(0)
    return image_count


def get_make_count(path):
    model_count = 0
    table = {}
    for name in os.listdir(path):
        sub_path = join(path, name)
        if os.path.isdir(sub_path):
            model_count += 1
            table[name] = get_model_images_count(sub_path)

    return model_count, table


if __name__ == "__main__":
    print("Car Make, Count of models, Count of images, Mean images per model")
    for f in sorted(listdir(path)):
        sub_path = join(path, f)
        # print(sub_path)
        if isdir(sub_path):
            model_count, make = get_make_count(sub_path)
            s = sum([v for k, v in make.items()])
            m = round(numpy.mean([v for k, v in make.items()]))

            print("{},{},{},{}".format(f, model_count, s, int(m)))