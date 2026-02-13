#!/usr/bin/env python3
import argparse,base64,csv,sys,time
from datetime import datetime,timezone
import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

T0="0x0e540ff014403c501655ba5fcd7f36ec5f6df99f851e513e7d6c4c93da112174"
API="https://api.etherscan.io/v2/api"
DLY=0.25

def decode_abi_strings(h):
    d=h[2:]if h.startswith("0x")else h
    rw=lambda o:int(d[o*2:o*2+64],16)
    def rs(bo):
        l=rw(bo);s=(bo+32)*2;return bytes.fromhex(d[s:s+l*2]).decode("utf-8",errors="replace")
    return rs(rw(0)),rs(rw(32))

def try_hex(s):
    try:
        r=bytes.fromhex(s).decode("utf-8")
        return r if r.isprintable()and len(r)>2 else None
    except:return None

def try_b64(s):
    try:
        r=base64.b64decode(s).decode("utf-8",errors="replace")
        return r if r.isprintable()and len(r)>2 else None
    except:return None

def aes_key(addr):
    a=addr.lower().encode()
    return PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=a,iterations=100_000).derive(a)

def try_aes(t,k):
    if":"not in t:return None
    try:
        i,c=t.split(":",1);iv=base64.b64decode(i);ct=base64.b64decode(c)
        return AESGCM(k).decrypt(iv,ct,None).decode("utf-8")if len(iv)==12 and len(ct)>=17 else None
    except:return None

def try_dhex(s):
    try:
        r=bytes.fromhex(bytes.fromhex(s).decode("utf-8")).decode("utf-8")
        return r if r.isprintable()and len(r)>2 else None
    except:return None

def decode(s,k):
    if not s or not s.strip():return"empty","",s
    s2=s.strip().rstrip("\x00")
    if s2.startswith(("http://","https://","all:","hwid:","ping:")):return"plaintext",s2,s
    r=try_hex(s2)
    if r:
        a=try_aes(r,k)
        if a:return"hex+aes-gcm",a,s
        b=try_b64(r)
        if b:return"hex+base64",b,s
        return"hex",r,s
    r=try_dhex(s2)
    if r:return"double_hex",r,s
    r=try_b64(s2)
    if r:return"base64",r,s
    r=try_aes(s2,k)
    if r:return"aes-gcm",r,s
    return"unknown",s2,s

def fetch_logs(addr,key,fb=0,tb=99999999,ps=1000,cid=137):
    out=[];pg=1
    while True:
        try:
            r=requests.get(API,params={"chainid":cid,"module":"logs","action":"getLogs","address":addr,"topic0":T0,"fromBlock":fb,"toBlock":tb,"page":pg,"offset":ps,"apikey":key},timeout=30).json()
        except:break
        if r.get("status")!="1"or not r.get("result"):break
        out.extend(r["result"]);print(f"  pg{pg}: {len(r['result'])} logs")
        if len(r["result"])<ps:break
        pg+=1;time.sleep(DLY)
    return out

def fetch_creator(addr,key,cid=137):
    try:
        r=requests.get(API,params={"chainid":cid,"module":"contract","action":"getcontractcreation","contractaddresses":addr,"apikey":key},timeout=30).json()
        time.sleep(DLY);return r["result"][0].get("contractCreator","unknown")
    except:time.sleep(DLY);return"unknown"

def process(logs,addr,k,creator):
    recs=[]
    for l in logs:
        tx=l.get("transactionHash","")
        bn=int(l.get("blockNumber","0x0"),16)
        ts=int(l.get("timeStamp","0x0"),16)
        dt=datetime.fromtimestamp(ts,tz=timezone.utc)
        try:old,new=decode_abi_strings(l.get("data","0x"))
        except Exception as e:
            recs.append({"contract":addr,"contract_creator":creator,"block":bn,"timestamp":dt.isoformat(),"tx_hash":tx,"field":"PARSE_ERROR","method":"error","decoded":str(e),"raw":l.get("data","")[:200]});continue
        for f,v in[("old_domain",old),("new_domain",new)]:
            m,d,r=decode(v,k)
            recs.append({"contract":addr,"contract_creator":creator,"block":bn,"timestamp":dt.isoformat(),"tx_hash":tx,"field":f,"method":m,"decoded":d,"raw":r[:300]})
    return recs

COLS=["contract","contract_creator","block","timestamp","tx_hash","field","method","decoded","raw"]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--api-key",required=True)
    p.add_argument("--contracts",default="")
    p.add_argument("--contracts-file",default="")
    p.add_argument("--from-block",type=int,default=0)
    p.add_argument("--to-block",type=int,default=99999999)
    p.add_argument("--output",default="")
    p.add_argument("--chain-id",type=int,default=137)
    a=p.parse_args()
    cc=[]
    if a.contracts:cc+=[c.strip()for c in a.contracts.split(",")if c.strip()]
    if a.contracts_file:
        try:cc+=[l.strip()for l in open(a.contracts_file)if l.strip()and not l.startswith("#")]
        except:print("[!] file not found",file=sys.stderr);sys.exit(1)
    if not cc:print("[!] no contracts",file=sys.stderr);sys.exit(1)
    seen=set();cc=[c for c in cc if not(c.lower()in seen or seen.add(c.lower()))]
    out=a.output or f"c2_domains_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    print(f"[*] {len(cc)} contracts, blocks {a.from_block}-{a.to_block}, output: {out}")
    all_r=[]
    for i,c in enumerate(cc,1):
        print(f"[{i}/{len(cc)}] {c}")
        cr=fetch_creator(c,a.api_key,a.chain_id);print(f"  creator: {cr}")
        k=aes_key(c)
        logs=fetch_logs(c,a.api_key,a.from_block,a.to_block,cid=a.chain_id)
        print(f"  {len(logs)} logs")
        if not logs:continue
        recs=process(logs,c,k,cr);all_r+=recs
        print(f"  decoded {sum(1 for r in recs if r['method']not in('empty','error','unknown'))}/{len(recs)}")
        if i<len(cc):time.sleep(DLY)
    with open(out,"w",newline="",encoding="utf-8")as f:
        w=csv.DictWriter(f,fieldnames=COLS);w.writeheader();w.writerows(all_r)
    print(f"\n[*] {len(all_r)} records -> {out}")
    for r in all_r:
        if r["method"]in("empty","error"):continue
        p2="OLD"if r["field"]=="old_domain"else"NEW"
        print(f"[{r['timestamp']}] {r['contract']} | {r['contract_creator']} | {p2} ({r['method']}): {r['decoded']}")
    return 0

if __name__=="__main__":sys.exit(main())
