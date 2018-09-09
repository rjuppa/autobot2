import codecs
import json
import os
from os import listdir
from os.path import isfile, join, isdir


import numpy as np
import chainer

from shutil import copyfile
from chainer.links import ResNet50Layers

import cv2


def is_positive(est, word, limit):
    label, percent = est
    return word in label and percent >= limit


def is_there(est, word):
    label, percent = est
    return word in label


def clasify_car(est1, est2):
    label1, percent1 = est1
    label2, percent2 = est2
    if is_positive(est1, "pickup", 10) or is_positive(est2, "pickup", 10):
        return True

    if is_positive(est1, "race", 10) or is_positive(est2, "race", 10):
        return True

    # remove
    removed = ["limousine", "seat", "meter", "lock", "back", "spot", "player",
               "switch", "tub", "radio", "microwave", "speaker", "dial", "phone",
               "monitor", "camera", "lens", "machine", "toaster", "buckle", "purse",
               "car wheel", "joystick", "soap", "belt", "disc", "cart", "pencil",
               "breastplate", "stove", "plane", "Samoyed", "Pot", "remote", "chair",
               "cradle", "steam", "carton", "projector", "mask", "modem", "shop",
               "tank", "sandal", "screen", "stove", "passenger", "bubble", "computer",
               "mirror", "wireless", "laptop", "cup", "safe", "glasses", "disk", "brake",
               "oil", "filter", "Loafer", "carriage", "boat", "binder", "menu", "trimaran",
               "printer", "soccer", "can", "bassinet", "tow", "dam", "dike", "banister",
               "handrail", "amphibian", "handrail", "watch", "rotisserie", "vacuum"]
    for word in removed:
        if is_there(est1, word) or is_there(est2, word):
            return False

    # test
    if is_positive(est1, "wagon", 70) or is_positive(est2, "wagon", 70):
        return True

    if is_positive(est1, "04285008", 40) or is_positive(est2, "04285008", 40):
        # sport car
        return True

    if is_there(est1, "minivan") or is_there(est2, "minivan"):
        if is_there(est1, "convertible") or is_there(est2, "convertible"):
            return False

    if (percent1 + percent2) >= 50:
        cars = ["minivan", "minibus", "wagon", "04285008", "03977966", "taxi", "03796401",
                "convertible", "van", "ambulance", "car", "jeep", "RV", "truck", "police",
                "race"]
        for word in cars:
            if is_there(est1, word) or is_there(est2, word):
                return True

    if (percent1 + percent2) >= 40:
        cars = ["minivan", "minibus", "wagon", "04285008", "03977966"]
        for word in cars:
            if is_there(est1, word) or is_there(est2, word):
                return True

    return False


def get_html(b):
    if b:
        return "<h2 style='color:green'>CAR</h2>"
    else:
        return "<h2 style='color:red'>--</h2>"


def copy_file(src, is_car):
    fn = src.split("/")[-1]
    dir = os.path.dirname(src)
    if is_car:
        path = dir + "/car"
    else:
        path = dir + "/interier"

    if not os.path.exists(path):
        os.makedirs(path)

    copyfile(src, path + "/" + fn)


def get_vehicle(path):
    parts = path.split("/")
    make = parts[-3]
    dirname = parts[-2]
    names = dirname.split("_")
    y = names[-1]
    try:
        year = int(y)
    except ValueError:
        year = 0

    if year > 0:
        model = " ".join(names[1:-1])
    else:
        model = " ".join(names[1:])

    if make == "Land":
        make = "Land Rover"
        model = " ".join(names[2:-1])

    if make == "Alfa":
        make = "Alfa Romeo"
        model = " ".join(names[2:-1])

    return make, model, year


def process_folder(path, model, synset):
    image_files = [join(path, name) for name in sorted(os.listdir(path))]
    line = "<html><table border=1>"
    line += "<tr><td width=120></td><td width=100></td><td width=400></td><td width=100></td></tr>"
    template = "\n<tr><td><img src='file://{}' width='100' /></td> <td>{}</td> <td>{}</td> <td>{}</td></tr>"
    footer = "\n</table></html>"
    image_path = ""
    for image_path in image_files:
        print("---> {}".format(image_path))
        if not os.path.isfile(image_path):
            continue

        if image_path[-4:] != ".jpg":
            continue

        # retrieve info
        make, version, year = get_vehicle(image_path)
        img = cv2.imread(image_path)
        h, w, ch = img.shape
        img = cv2.resize(img, (224, 224))

        # classify an image
        pred = model.predict([img])
        pred = chainer.cuda.to_cpu(pred.data)
        estim = np.argsort(pred)[0][-1::-1]
        idx1 = estim[0]
        idx2 = estim[1]
        percent1 = round(pred[0][idx1] * 100)
        percent2 = round(pred[0][idx2] * 100)
        label1 = synset[idx1]
        label2 = synset[idx2]

        is_car = clasify_car((label1, percent1), (label2, percent2))

        # render html
        labels = "{}<br>{}".format(label1, label2)
        ps = "{}<br>{}".format(percent1, percent2)
        if is_car:
            line += template.format(image_path, ps, labels, get_html(is_car))

        # copy an image
        copy_file(image_path, is_car)

        # create a mata-file json
        data = {"file": image_path.split("/")[-1],
                "label1": label1, "pc1": percent1,
                "label2": label1, "pc2": percent1,
                "is_car": is_car, "make": make,
                "model": version, "year": year,
                "width": w, "height": h, "channels": ch}
        with codecs.open(image_path.replace(".jpg", ".json"), "w", "utf-8") as outfile:
            json.dump(data, outfile)

    # write html overview table
    line += footer
    dir = os.path.dirname(image_path)
    txt_file = "{}/results.html".format(dir)
    f = codecs.open(txt_file, "w", "utf-8")
    f.write(line)
    f.close()


if __name__ == '__main__':

    # load neural network model
    parent_path = os.path.abspath('..')
    path = "{}/datasets".format(parent_path)
    file_name = "ResNet-50-model"
    npz_path = "{}/{}.npz".format(path, file_name)
    synset_path = "{}/synset_words.txt".format(path)
    model = ResNet50Layers(npz_path)

    with open(synset_path) as f:
        synset = f.read().split("\n")[:-1]

    image_root = path = "{}/images".format(parent_path)
    for make_dir in sorted(listdir(image_root)):
        make_path = join(image_root, make_dir)
        make_name = make_path.split("/")[-1]
        if isdir(make_path):
            for model_dir in sorted(listdir(make_path)):
                model_path = join(make_path, model_dir)
                model_name = model_path.split("/")[-1]
                if isdir(model_path) and model_name.startswith(make_name):
                    print("======================")
                    print("MODEL: {}".format(model_name))
                    process_folder(model_path, model, synset)

    # sub_path = "{}/images/Alfa/Alfa_Romeo_159_2005".format(parent_path)


