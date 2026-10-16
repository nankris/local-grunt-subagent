#!/usr/bin/env python3
"""Tiny local HTTP server for Qwen3-0.6B (CPU, greedy, thinking off). POST /gen {"prompt":..., "max_new_tokens":N}.
Logs every call (prompt chars, tokens in/out, seconds) to results/qwen_calls.jsonl."""
import json, os, sys, time, threading, torch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from transformers import AutoTokenizer, AutoModelForCausalLM
MODEL = "/workspace/projects/4e0e7b68-80db-40d3-a6d5-b21cf99d82b6/work/Qwen3-0.6B"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(HERE, "results", "qwen_calls.jsonl")
torch.set_num_threads(2)
tok = AutoTokenizer.from_pretrained(MODEL)
m = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float32).eval()
lock = threading.Lock()
class Hd(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        msgs = [{"role": "user", "content": req["prompt"]}]
        text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        ids = tok(text, return_tensors="pt")
        t0 = time.time()
        with lock, torch.no_grad():
            out = m.generate(**ids, max_new_tokens=min(int(req.get("max_new_tokens", 256)), 512), do_sample=False)
        new = out[0][ids["input_ids"].shape[1]:]
        ans = tok.decode(new, skip_special_tokens=True).strip()
        rec = dict(t=int(t0), tag=req.get("tag", ""), prompt_chars=len(req["prompt"]), in_tokens=int(ids["input_ids"].shape[1]),
                   out_tokens=int(len(new)), seconds=round(time.time() - t0, 2))
        open(LOG, "a").write(json.dumps(rec) + "\n")
        b = json.dumps({"text": ans, **rec}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b)
print("ready", flush=True)
ThreadingHTTPServer(("127.0.0.1", 8765), Hd).serve_forever()
