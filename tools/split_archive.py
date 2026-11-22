#!/usr/bin/env python3
"""Split/reassemble an existing ZIP without changing its bytes. Python 3.10+."""
import argparse, hashlib, json, pathlib, re, zipfile
CHUNK=20*1024*1024
def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def split(src,out):
    src=pathlib.Path(src); out=pathlib.Path(out); out.mkdir(parents=True,exist_ok=True)
    if not zipfile.is_zipfile(src): raise ValueError("Input must be a valid ZIP")
    if not re.fullmatch(r"[A-Za-z0-9._-]+",src.name): raise ValueError("Use a simple ASCII filename")
    parts=[]
    with src.open("rb") as f:
        for i in range(100000):
            b=f.read(CHUNK)
            if not b: break
            name=f"{src.name}.part{i:04d}"
            p=out/name
            if p.exists(): raise FileExistsError(p)
            p.write_bytes(b)
            parts.append({"file":name,"size":len(b),"sha256":hashlib.sha256(b).hexdigest()})
    manifest={"format":1,"archive":src.name,"sha256":digest(src),"size":src.stat().st_size,"parts":parts}
    m=out/(src.name+".manifest.json")
    if m.exists(): raise FileExistsError(m)
    m.write_text(json.dumps(manifest,indent=2)+"\n")
    print(m)
def restore(manifest,out,extract):
    m=pathlib.Path(manifest); d=json.loads(m.read_text()); out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
    name=d["archive"]
    if pathlib.PurePath(name).name!=name: raise ValueError("Unsafe archive filename")
    target=out/name
    if target.exists(): raise FileExistsError(target)
    tmp=out/(name+".assembling")
    if tmp.exists(): raise FileExistsError(tmp)
    try:
        with tmp.open("wb") as dest:
            for part in d["parts"]:
                n=part["file"]
                if pathlib.PurePath(n).name!=n: raise ValueError("Unsafe part name")
                p=m.parent/n
                if p.stat().st_size!=part["size"] or digest(p)!=part["sha256"]: raise ValueError("Part checksum mismatch: "+n)
                with p.open("rb") as f:
                    for b in iter(lambda:f.read(1024*1024),b""):dest.write(b)
        if tmp.stat().st_size!=d["size"] or digest(tmp)!=d["sha256"]:raise ValueError("Archive checksum mismatch")
        if not zipfile.is_zipfile(tmp):raise ValueError("Reassembled file is not ZIP")
        tmp.rename(target)
    finally:
        if tmp.exists():tmp.unlink()
    if extract:
        root=(out/"extracted"/name.removesuffix(".zip"));root.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(target) as z:
            total=0
            for item in z.infolist():
                dest=(root/item.filename).resolve()
                if not dest.is_relative_to(root.resolve()):raise ValueError("Unsafe archive entry")
                if (item.external_attr>>16)&0o170000==0o120000:raise ValueError("Symlink entry")
                total+=item.file_size
                if total>2*1024**3:raise ValueError("Uncompressed archive exceeds 2 GiB safety cap")
            z.extractall(root)
        print("Extracted:",root)
    print("Restored:",target)
def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest="cmd",required=True)
    a=s.add_parser("split");a.add_argument("zip");a.add_argument("--out",required=True)
    b=s.add_parser("restore");b.add_argument("manifest");b.add_argument("--out",required=True);b.add_argument("--extract",action="store_true")
    a=p.parse_args()
    if a.cmd=="split":split(a.zip,a.out)
    else:restore(a.manifest,a.out,a.extract)
if __name__=="__main__":main()
