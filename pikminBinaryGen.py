import struct
import json
import binascii
import os
import argparse
from collections import OrderedDict

DEFAULT_FILE_VERSION = "v0.1"
APPEARED_TYPES = {}

def read_bytes_as_hex(f, length):
    return str(binascii.hexlify(f.read(length)), encoding="ascii")

def write_hex_as_bytes(f, hex):
    f.write(binascii.unhexlify(hex))

def write_ascii_string(f, string):
    f.write(bytes(string, encoding="ascii"))

def read_multiparameters(f):
    return [str(binascii.hexlify(f.read(0x14)), encoding="ascii"), str(binascii.hexlify(f.read(0x14)), encoding="ascii")]

def write_multiparameters(f, multiparameters):
    multiparam1 = binascii.unhexlify(multiparameters[0])
    multiparam2 = binascii.unhexlify(multiparameters[1])

    assert len(multiparam1) == 0x14 and len(multiparam2) == 0x14
    f.write(multiparam1)
    f.write(multiparam2)

def read_id(f, reverse=True):
    if reverse:
        return str(f.read(4)[::-1], encoding="ascii")
    else:
        str(f.read(4), encoding="ascii")

def write_id(f, id, reverse=True):
    if reverse:
        f.write(bytes(id[::-1], encoding="ascii"))
    else:
        f.write(bytes(id), encoding="ascii")


def read_float_tripple(f):
    floats = struct.unpack(">fff", f.read(3*4))

    return " ".join(str(num) for num in floats)

def parse_float_tripple(tripple_string):
    floats = tripple_string.split(" ")
    return map(float, floats)

def read_parameters(f, asfloat=False):
    paramname = f.read(4)
    params = OrderedDict()
    while paramname != b"\xFF\xFF\xFF\xFF":
        if paramname[3] != 4:
            print(hex(f.tell()), paramname, paramname[3])
        assert paramname[3] == 4
        sane_param = str(paramname[0:3], encoding="ascii")

        if not asfloat:
            value = struct.unpack(">I", f.read(4))[0]
            params[sane_param] = hex(value)
        else:
            value = struct.unpack(">f", f.read(4))[0]
            params[sane_param] = value

        paramname = f.read(4)

    return params

def write_parameters(f, params, asFloat=False):
    for param, value in params.items():
        assert len(param) == 3
        f.write(bytes(param, encoding="ascii"))
        f.write(b"\x04")  # size of following value, always 4 bytes

        if asFloat:
            f.write(struct.pack(">f", float(value)))
        else:
            f.write(struct.pack(">I", convert_hex(value)))

    f.write(b"\xFF\xFF\xFF\xFF")

def convert_hex(hex):
    if hex.startswith("0x"):
        return int(hex, 16)
    else:
        return int(hex)

def write_int(f, val):
    f.write(struct.pack(">I", val))

def write_generator(f, gen):
    write_id(f, gen["name"])
    write_id(f, "v0.0")
    f.write(struct.pack(">II", convert_hex(gen["unk1"]), convert_hex(gen["unk2"])))
    write_hex_as_bytes(f, gen["metadata"])
    f.write(struct.pack(">fff", *parse_float_tripple(gen["position"])))
    f.write(struct.pack(">fff", *parse_float_tripple(gen["position offset"])))

    if gen["object type"] == "NULL":
        f.write(b"\x00\x00\x00\x00")  # If object is null we will skip all object data and go to area/spawn data
    else:
        write_id(f, gen["object type"])

        # Write the object version or in the case of boss and teki an integer
        if gen["object type"] in ("boss", "teki"):
            f.write(struct.pack("I", gen["object version"]))
        else:
            write_id(f, gen["object version"])


        objectdata = gen["object data"]

        if gen["object type"] in ("piki", "debg", "navi"):
            pass

        elif gen["object type"] in ("actr", "mobj", "plnt", "pelt"):
            f.write(struct.pack(">I", objectdata["unk int"]))

        elif gen["object type"] == "item":
            write_int(f, len(objectdata["item name"]))
            write_ascii_string(f, objectdata["item name"])

            write_hex_as_bytes(f, objectdata["item data 1"])
            write_hex_as_bytes(f, objectdata["item data 2"])

        elif gen["object type"] == "work":
            write_int(f, len(objectdata["string1"]))
            write_ascii_string(f, objectdata["string1"])

            write_int(f, len(objectdata["string2"]))
            write_ascii_string(f, objectdata["string2"])

            if objectdata["string1"].strip("\x00") == "move stone":
                #f.write(struct.pack(">fff", *parse_float_tripple(objectdata["work XYZ?"])))
                f.write(struct.pack(">fff", *objectdata["work XYZ?"]))

        elif gen["object type"] == "mpar":
            f.write(struct.pack(">III",
                                objectdata["unk int"],
                                objectdata["unk int 2"],
                                objectdata["more data"]))

            if objectdata["more data"] == 1:
                f.write(struct.pack(">ffffff", *objectdata["additional data"]))

        elif gen["object type"] == "teki":
            if gen["object version"] < 7:
                f.write(struct.pack(">III", objectdata["unk int"], objectdata["unk int1"], objectdata["unk int2"]))
                write_multiparameters(f, objectdata["multi parameters"])

            elif gen["object version"] == 8:
                f.write(struct.pack(">III", objectdata["unk int"], objectdata["unk int1"], objectdata["unk int2"]))
                write_id(f, objectdata["identification"])
                f.write(struct.pack(">IIIffff", *objectdata["personality data"]))


            elif gen["object version"] == 9:
                f.write(struct.pack(">BBB", objectdata["unk byte"], objectdata["unk byte1"], objectdata["unk byte2"]))
                write_id(f, objectdata["identification"])
                f.write(struct.pack(">IIIffff", *objectdata["personality data"]))

            elif gen["object version"] >= 10:
                f.write(struct.pack(">BBB", objectdata["unk byte"], objectdata["unk byte1"], objectdata["unk byte2"]))
                write_id(f, objectdata["identification"])
                write_multiparameters(f, objectdata["multi parameters"])

        elif gen["object type"] == "boss":
            if gen["object version"] >= 2:
                write_int(f, objectdata["boss type?"])
            elif gen["object version"] < 2:
                write_int(f, objectdata["boss type?"])
                write_id(f, objectdata["boss name"])

        else:
            raise RuntimeError("Unknown object type:", gen["object type"])

        write_parameters(f, objectdata["obj parameters"])

    # Write area data
    write_id(f, gen["area data"][0])  # Area type: Can be pint or circ
    write_id(f, "v0.0")
    f.write(struct.pack(">fff", *parse_float_tripple(gen["area data"][1])))  # Area position info?

    asFloat = gen["area data"][0] == "circ"  #if circle area then we parse the parameter as a float
    write_parameters(f, gen["area data"][2], asFloat=asFloat)  # Area parameters

    # Write spawn type data
    write_id(f, gen["spawn type data"][0])  # Spawn type: Can be 1one, aton or irnd
    write_id(f, "v0.0")
    write_parameters(f, gen["spawn type data"][1]) # Spawn type parameters

def read_generator(f):
    gen = OrderedDict()
    #print(hex(f.tell()))
    gen["name"] = read_id(f)
    assert read_id(f) == "v0.0"

    gen["unk1"], gen["unk2"] = (hex(x) for x in struct.unpack(">II", f.read(2*4)))

    gen["metadata"] = read_bytes_as_hex(f, 32)
    gen["position"] = read_float_tripple(f)
    gen["position offset"] = read_float_tripple(f)
    gen["object type"] = read_id(f)  # reverse string

    objtype = gen["object type"]

    if objtype == "\x00\x00\x00\x00":
        gen["object type"] = objtype = "NULL"
    APPEARED_TYPES[objtype] = True
    if objtype in ("boss, teki"):
        gen["object version"] = struct.unpack("I", f.read(4))[0]
    elif objtype == "NULL":
        pass
    else:
        gen["object version"] = str(f.read(4)[::-1], encoding="ascii")


    objectdata = {}
    #print("doing object of type", gen["object type"])
    if objtype in ("piki", "debg", "navi"):
        pass

    elif objtype in ("actr", "mobj", "plnt", "pelt"):
        objectdata["unk int"] = struct.unpack(">I", f.read(4))[0]

    elif objtype == "item":
        stringlength = struct.unpack(">I", f.read(4))[0]
        objectdata["item name"] = str(f.read(stringlength), encoding="ascii")

        objectdata["item data 1"] = str(binascii.hexlify(f.read(32)), encoding="ascii")
        objectdata["item data 2"] = str(binascii.hexlify(f.read(32)), encoding="ascii")

    elif objtype == "work":
        stringlength = struct.unpack(">I", f.read(4))[0]
        objectdata["string1"] = str(f.read(stringlength), encoding="ascii")
        stringlength = struct.unpack(">I", f.read(4))[0]
        objectdata["string2"] = str(f.read(stringlength), encoding="ascii")
        #print(objectdata["string1"], objectdata["string2"] )
        #print(objectdata["string1"], type(objectdata["string1"]), len(objectdata["string1"].strip("\x00")))
        #print(objectdata["string1"].strip() == "move stone")

        if objectdata["string1"].strip("\x00") == "move stone":
            objectdata["work XYZ?"] = struct.unpack(">fff", f.read(3*4))

    elif objtype == "mpar":
        objectdata["unk int"], objectdata["unk int 2"], objectdata["more data"] = struct.unpack(">III", f.read(3*4))
        if objectdata["more data"] == 1:
            objectdata["additional data"] = [x for x in struct.unpack(">ffffff", f.read(6*4))]
        else:
            objectdata["additional data"] = []

    elif objtype == "teki":
        if gen["object version"] < 7:
            objectdata["unk int"], objectdata["unk int1"], objectdata["unk int2"] = struct.unpack(">III", f.read(3*4))
            objectdata["multi parameters"] = read_multiparameters(f)
        elif gen["object version"] == 8:
            objectdata["unk int"], objectdata["unk int1"], objectdata["unk int2"] = struct.unpack(">III", f.read(3*4))
            objectdata["identification"] = read_id(f)
            objectdata["personality data"] = struct.unpack(">IIIffff", f.read(7*4))

        elif gen["object version"] == 9:
            objectdata["unk byte"], objectdata["unk byte1"], objectdata["unk byte2"] = struct.unpack(">BBB", f.read(3*1))
            objectdata["identification"] = read_id(f)
            objectdata["personality data"] = struct.unpack(">IIIffff", f.read(7*4))

        elif gen["object version"] >= 10:
            objectdata["unk byte"], objectdata["unk byte1"], objectdata["unk byte2"] = struct.unpack(">BBB", f.read(3*1))
            objectdata["identification"] = read_id(f)
            objectdata["multi parameters"] = read_multiparameters(f)

    elif objtype == "boss":
        if gen["object version"] >= 2:
            objectdata["boss type?"] = struct.unpack(">I", f.read(4))[0]
        elif gen["object version"] < 2:
            objectdata["boss type?"] = struct.unpack(">I", f.read(4))[0]
            objectdata["boss name"] = str(f.read(4), encoding="ascii")
    elif objtype == "NULL":
        pass
    else:
        raise RuntimeError("unknown type: {}".format(objtype))
    gen["object data"] = objectdata

    if objtype != "NULL":
        objectdata["obj parameters"] = read_parameters(f)

    areatype = read_id(f)
    assert read_id(f) == "v0.0"
    areaxyz = read_float_tripple(f)
    areaparams = read_parameters(f, asfloat=True)

    gen["area data"] = [areatype, areaxyz, areaparams]

    spawntype = read_id(f)
    assert read_id(f) == "v0.0"

    spawnparams = read_parameters(f)

    gen["spawn type data"] = [spawntype, spawnparams]

    return gen

def read_gen_file(f):
    assert read_id(f) == "v0.1" # file version
    position = read_float_tripple(f)
    rotation, generator_count = struct.unpack(">fI", f.read(2*4))
    header = {"position": position, "rotation": rotation}
    generators = ["Header", header]

    for i in range(generator_count):
        generator = read_generator(f)
        generators.append("Object type: {0}".format(generator["object type"]))
        generators.append(generator)

    more = f.read(1)
    if len(more) > 0:
        print("Warning: There is still data after the generators. File offset:", hex(f.tell()-1))


    return generators

def write_gen_file(inputjson, output):
    # Filter everything that is not a dict. This gets rid of the
    # description strings added by read_gen_file
    filtered = [obj for obj in inputjson if isinstance(obj, dict)]

    # First item is header, all other items are generators
    header = filtered[0]

    x,y,z = parse_float_tripple(header["position"])
    generator_count = len(filtered) - 1
    write_id(output, DEFAULT_FILE_VERSION)
    output.write(struct.pack(">ffffI", x, y, z, float(header["rotation"]), generator_count))

    if len(filtered) > 1:
        for generator in filtered[1:]:
            write_generator(output, generator)


if __name__ == "__main__":
    GEN2TXT = 1
    TXT2GEN = 2

    parser = argparse.ArgumentParser()
    parser.add_argument("input",
                        help="Filepath to the file that should be converted")
    parser.add_argument("--gen2txt", action="store_true", default=False,
                        help="If set, converts a .gen file to a json text file.")
    parser.add_argument("--txt2gen", action="store_true", default=False,
                        help="If set, converts a json text file to .gen")
    parser.add_argument("output", default=None, nargs = '?',
                        help="Filepath to which the result of the conversion will be written")
    args = parser.parse_args()

    mode = 0

    if not args.gen2txt and not args.txt2gen:
        print("Conversion mode not set. Trying to detect by file ending...")

        if args.input.endswith(".gen"):
            print("Detected gen2txt")
            mode = GEN2TXT
        elif args.output.endswith(".gen"):
            print("Detected txt2gen")
            mode = TXT2GEN
        else:
            raise RuntimeError("Couldn't detect conversion mode. You need to set either --gen2txt or --txt2gen!")

    if args.gen2txt and args.txt2gen:
        raise RuntimeError("You cannot use both conversion modes at the same time!")

    if args.gen2txt:
        mode = GEN2TXT
    elif args.txt2gen:
        mode = TXT2GEN

    if mode == 0:
        raise RuntimeError("Conversion mode undefined. Did you set a conversion mode? (--gen2txt or --txt2gen)")

    if mode == GEN2TXT:
        print("Converting gen file to text...")
        print("Reading", args.input)
        with open(args.input, "rb") as f:
            data = read_gen_file(f)
        print("Gen file read, now writing to", args.output)
        with open(args.output, "w") as f:
            json.dump(data, f, indent=" "*4)
        print("Done")
    elif mode == TXT2GEN:
        print("Converting text file to gen...")
        print("Reading", args.input)
        with open(args.input, "r") as f:
            data = json.load(f, object_pairs_hook=OrderedDict)
        print("Text file loaded, now converting and writing to", args.output)
        with open(args.output, "wb") as f:
            write_gen_file(data, f)
        print("Done")



    # Regression test assuming a folder "stages" in the same path as the tool itself
    """if True:
        for dirpath, drinames, filenames in os.walk("stages"):
            for filename in filenames:
                if ".gen" in filename: #filename.endswith(".gen"):
                    path = os.path.join(dirpath, filename)
                    print("reading", path)
                    with open(path, "rb") as f:
                        control_data = f.read()
                        f.seek(0)
                        data = read_gen_file(f)

                    with open("testgen.json", "w") as f:
                        json.dump(data, f, indent=" "*4)

                    with open("testgen.json", "r") as f:
                        newdata = json.load(f, object_pairs_hook=OrderedDict)

                    with open("testgen.gen", "wb") as f:
                        write_gen_file(newdata, f)

                    with open("testgen.gen", "rb") as f:
                        checkagainst = f.read()

                    assert control_data == checkagainst"""

    #print(APPEARED_TYPES)
    """genfile = os.path.join(gendir, "stage3", "default.gen")
    with open(genfile, "rb") as f:
        data = read_gen_file(f)

    with open("testgen.json", "w") as f:
        json.dump(data, f, indent=" "*4)

    with open("testgen.json", "r") as f:
        data = json.load(f, object_pairs_hook=OrderedDict)

    with open("newbingen.gen", "wb") as f:
        write_gen_file(data, f)"""