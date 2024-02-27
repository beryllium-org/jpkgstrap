#!/usr/bin/python3
from sys import argv, exit
from sys import path as spath
from random import randint
from os import mkdir, path, popen, environ, makedirs, listdir, getcwd, chdir
import shutil
from json import load, dump

spath.append("submodules/jz/")
from jz import decompress


def _serror() -> None:
    print("Invalid syntax! Use --help for info.")
    exit(1)


def _get_random_name(pkgname: str) -> str:
    res = "jpkg"
    for _ in range(12):
        res += str(randint(0, 9))
    if "/" in pkgname:
        pkgname = pkgname[pkgname.rfind("/") + 1 :]
    pkgname = pkgname[: pkgname.rfind(".")]
    res = path.join("/tmp", res + "_" + pkgname)
    return res


if __name__ == "__main__":
    args = argv[1:]
    if "-h" in args or "--help" in args:
        print("Help menu here")
        exit(0)

    print("Initializing jpkgstrap")
    packages = []
    tmpdirs = []
    root = None
    inU = False
    Denabled = False
    ok = True

    for i in args:
        if i[0] == "-":
            if len(i) == 2:
                if i[1] == "U":
                    if inU:
                        _serror()
                    inU = True
                elif i[1] == "D":
                    if Denabled:
                        _serror()
                    Denabled = True
                else:
                    _serror()
            else:
                _serror()
        elif inU:
            packages.append(i)
        elif root is None:
            root = i
        else:
            _serror()
    if root is None:
        print("No root specified! Must be an absolute path. Use --help for info.")
        exit(1)
    if not packages:
        print("No packages specified! Cannot deploy. Use --help for info.")

    print("\nTarget root:", root)
    print("Packages:")
    for i in packages:
        print(" -", i)

    for i in packages:
        rngpath = _get_random_name(i)
        tmpdirs.append(rngpath)
        print()
        makedirs(rngpath)
        decompress(i, rngpath)

    installed = set()
    dependencies = set()
    conflicts = set()

    print("\nConstructing database..")
    config = path.join(root, "etc/jpkg")
    for i in listdir(path.join(config, "installed")):
        with open(path.join(config, "installed", i)) as f:
            data = load(f)
            installed.add(data["package_name"])
            for j in data["dependencies"]:
                dependencies.add(j)
            for j in data["conflicts"]:
                conflicts.add(j)

    for i in tmpdirs:
        with open(path.join(i, "Manifest.json")) as f:
            data = load(f)
            installed.add(data["package_name"])
            for j in data["dependencies"]:
                dependencies.add(j)
            for j in data["conflicts"]:
                conflicts.add(j)

    print("Running dependency checks..")
    for i in dependencies:
        if i not in installed:
            ok = False
            print("Dependency", i, "not satisfied")
    for i in conflicts:
        if i in installed:
            ok = False
            print("Conflicting package", i)

    if not ok:
        print("Deployment aborted!")
    else:
        print("Database valid.\n")

    olddir = getcwd()
    if ok:
        for ii in tmpdirs:
            with open(path.join(ii, "Manifest.json")) as fi:
                datai = load(fi)
                print("Setting up", datai["package_name"], "..")
                try:
                    with open(path.join(ii, datai["strap"])) as si:
                        script = si.read()
                        chdir(ii)
                        exec(script)
                        chdir(olddir)
                    shutil.copy(
                        path.join(ii, "Manifest.json"),
                        path.join(
                            root, "etc/jpkg/installed", datai["package_name"] + ".json"
                        ),
                    )
                    shutil.copy(
                        path.join(ii, datai["remove"]),
                        path.join(
                            root, "etc/jpkg/uninstallers", datai["package_name"] + ".py"
                        ),
                    )
                except KeyError:
                    print(
                        "Error: Package",
                        datai["package_name"],
                        "does not support strapping!",
                    )
                    break
    if ok:
        print("\nInstallation Finished!")

    print()
    for i in tmpdirs:
        print("Removing", i)
        if i not in ["/tmp", "/tmp/"]:
            shutil.rmtree(i)
        else:
            print("SAFETY TRIGGERED!")
            exit(1)
