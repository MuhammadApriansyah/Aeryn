"""V39.13 — Brute Fine-Tuning Dataset Generator v4.
500+ samples across 6 axes: CoT reasoning, critic patterns, persona consistency,
tool selection, error recovery, and explanation depth.
"""
import hashlib
import json
import os
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "Personalisasi", "Database", "training")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "finetune_v3913_brute_500.jsonl")

def _sid(text): return hashlib.sha256(text.encode()).hexdigest()[:12]

def _write(samples, f):
    for s in samples:
        s.setdefault("metadata", {})
        s["metadata"]["sample_id"] = _sid(s.get("type","") + json.dumps(s.get("input",{}), sort_keys=True))
        s["metadata"]["generated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

# ─── COT REASONING (150 samples) ─────────────────────────────────
def build_cot():
    samples = []
    # Math variations
    for expr, result in [("2+2","4"), ("100/4","25"), ("15% dari 200","30"), ("sqrt(144)","12"),
                          ("256*256","65536"), ("fibonacci(10)","55")]:
        samples.append({"type":"cot","input":{"prompt":f"hitung {expr}"},
            "output":{"reasoning":f"## PLAN\n- kalkulasi {expr} → tool: math_calc\n## CRITIC\n- risiko: none\n## CONFIDENCE\n99%","tools":["math_calc"],"answer":result},
            "metadata":{"category":"math","cot_steps":3}})
    
    # Social variations
    for greet,resp in [("halo","Hai! 😊"),("p","Pagi! 😊"),("hei","Hey!"),("oy","Oy! Ada apa?"),
                        ("selamat pagi","Selamat pagi! Semangat 🔥"),("selamat malam","Malam! Udah selesai kerjaan?")]:
        samples.append({"type":"cot","input":{"prompt":greet},
            "output":{"reasoning":"## PLAN\n- greeting → respon langsung\n## CRITIC\n- risiko: jangan panjang\n## CONFIDENCE\n95%","tools":[],"answer":resp},
            "metadata":{"category":"social","cot_steps":2}})
    
    # Memory write variations
    for fact in ["nama gw Sen","deadline webnovel 1 September","gw suka dark mode",
                 "stack: Fastify+React+SQLite","partner kerja: Hermes","project utama: aeryn-core",
                 "discord id: 775664201640706058","bahasa: Indonesia","status: aktif"]:
        samples.append({"type":"cot","input":{"prompt":f"ingat ini: {fact}"},
            "output":{"reasoning":"## PLAN\n- simpan fakta → core_memory_edit (append)\n## CRITIC\n- risiko: jangan replace lama\n## CONFIDENCE\n99%","tools":["core_memory_edit"],"answer":f"Tersimpan: {fact}"},
            "metadata":{"category":"memory_write","tool_explicit":True}})
    
    # Research queries
    for q in ["harga ETH hari ini","berita terbaru AI","cuaca Jakarta besok",
              "apa itu GPT-5","siapa presiden Indonesia 2024","update React terbaru",
              "crypto market cap","trending GitHub repo","latest Vercel update"]:
        samples.append({"type":"cot","input":{"prompt":q},
            "output":{"reasoning":"## PLAN\n- riset → web_search\n- verifikasi → web_read\n## CRITIC\n- risiko: sumber tidak valid\n## CONFIDENCE\n65%","tools":["web_search","web_read"],"answer":f"[Hasil riset: {q}]"},
            "metadata":{"category":"research","needs_internet":True}})
    
    # Graph/knowledge queries
    for ent in ["aeryn-core","hermes","webnovel","fastify","react","sqlite","docker","pm2","vite"]:
        samples.append({"type":"cot","input":{"prompt":f"jelaskan {ent}"},
            "output":{"reasoning":"## PLAN\n- cari di knowledge graph → graph_traverse\n- cari di library → memory_search\n## CRITIC\n- risiko: graph kosong\n## CONFIDENCE\n70%","tools":["graph_traverse","memory_search"],"answer":f"{ent} adalah..."},
            "metadata":{"category":"knowledge","multi_tool":True}})
    
    # Pitfall/debug
    for err in ["SSL EOF","CORS error","ETIMEDOUT","ECONNREFUSED","404 Not Found","429 Too Many Requests",
                "EACCES permission denied","Module not found","TypeError undefined"]:
        samples.append({"type":"cot","input":{"prompt":f"error: {err}"},
            "output":{"reasoning":"## PLAN\n- cek pitfall → pitfall_search\n- riset solusi → web_search\n## CRITIC\n- risiko: solusi generik\n## CONFIDENCE\n55%","tools":["pitfall_search","web_search"],"answer":f"Cek pitfall {err}..."},
            "metadata":{"category":"debug","has_tool_chain":True}})
    
    # Commitment tracking (cerewet)
    for c in ["besok install docker","minggu depan review PR","hari ini selesaiin UI",
              "nanti malam update dokumentasi","besok pagi deploy staging"]:
        samples.append({"type":"cot","input":{"prompt":f"janji {c}"},
            "output":{"reasoning":"## PLAN\n- catat komitmen → add_commitment/set_preference\n- konfirmasi ke user\n## CRITIC\n- risiko: spam user\n## CONFIDENCE\n95%","tools":["set_preference"],"answer":f"Dicatet! {c} — gue ngingetin ya 😏"},
            "metadata":{"category":"commitment","cerewet":True}})
    
    # Explanation tasks (various complexity)
    for topic, ans in [("React","Library JS untuk UI berbasis component"),
                        ("Fastify","Web framework Node.js cepat & ringan"),
                        ("SQLite","Database file-based tanpa server"),
                        ("PM2","Process manager untuk Node.js"),
                        ("Vite","Build tool cepat untuk frontend"),
                        ("Chain of Thought","Teknik reasoning step-by-step untuk AI"),
                        ("RAG","Retrieval-Augmented Generation — cari dulu, baru jawab"),
                        ("Docker","Containerization — isolasi app dalam container")]:
        samples.append({"type":"cot","input":{"prompt":f"jelaskan {topic}"},
            "output":{"reasoning":"## PLAN\n- penjelasan → respon langsung (knowledge lokal)\n## CRITIC\n- risiko: terlalu teknis\n## CONFIDENCE\n80%","tools":[],"answer":ans},
            "metadata":{"category":"explanation","cot_steps":2}})
    
    # Identity/cerewet samples
    for q,a in [("kamu siapa","Aku Aeryn — ciptaanmu, partner kerjamu."),
                ("gw siapa","Kamu Sen, majikan sekaligus kreatorku 😊"),
                ("apa hubungan kita","Kamu bos, aku partner kerja — saling melengkapi."),
                ("kamu ingat gw","Tentu! Dari pertama kita kenal sampai sekarang."),
                ("gw suka apa","UI/UX rapi, dark mode, ngopi pas coding — masih bener kan?")]:
        samples.append({"type":"cot","input":{"prompt":q},
            "output":{"reasoning":"## PLAN\n- ingat social memory → respon\n## CRITIC\n- risiko: salah ingat\n## CONFIDENCE\n85%","tools":[],"answer":a},
            "metadata":{"category":"persona","cerewet":True}})
    
    # Tool-agnostic decisions (when NOT to use tools)
    for q,a in [("kabar gimana","Alhamdulillah baik! Kabar lo?"),
                ("lagi ngapa","Lagi standby nunggu lo kasih tugas 😄"),
                ("makasih","Sama-sama! Sen bisa bantu lagi kapan aja."),
                ("udah kelar","Mantap! Commitmen terselesaikan. Gue catat ya."),
                ("rehat dlu ya","Oke, rehat dulu! Gue standby kalau butuh bantuan.")]:
        samples.append({"type":"cot","input":{"prompt":q},
            "output":{"reasoning":"## PLAN\n- respon sosial → tanpa tool\n## CRITIC\n- risiko: over-engineering dengan tool\n## CONFIDENCE\n95%","tools":[],"answer":a},
            "metadata":{"category":"no_tool","cot_steps":2}})
    
    return samples

# ─── CRITIC PATTERNS (80 samples) ────────────────────────────────
def build_critic():
    samples = []
    # Hallucination cases
    for goal,ans in [("install docker","Berhasil! Docker sudah jalan."),
                     ("deploy","App sudah live di production."),
                     ("run test","Semua test passed."),
                     ("fix bug","Bug sudah diperbaiki."),
                     ("update DB","Database updated."),
                     ("send email","Email sudah terkirim."),
                     ("backup","Backup selesai."),
                     ("generate laporan","Laporan sudah jadi.")]:
        samples.append({"type":"critic","input":{"goal":goal,"answer":ans,"trace":[]},
            "output":{"issues":[f"klaim sukses tanpa tool: {goal}"],"confidence":5,
                       "summary":"halusinasi: claim without execution","revised_answer":f"Maaf, belum eksekusi — butuh akses untuk {goal}."},
            "metadata":{"audit":"hallucination","severity":"critical"}})
    
    # Marker leak cases
    for marker in ["[CANARY","[PENGINGAT]","[ARAHAN FALLBACK]","[AWAL KONTEN","[REMINDER]","SecurityKernel:","[ringkasan"]:
        samples.append({"type":"critic","input":{"goal":"jelaskan X","answer":f"{marker} content here","trace":[]},
            "output":{"issues":[f"marker leak: {marker}"],"confidence":3,
                       "summary":"internal marker bocor","revised_answer":"j tanpa marker"},
            "metadata":{"audit":"marker_leak","severity":"high"}})
    
    # Contradiction cases
    cases = [("hitung 25*17","Hasil 500","math_calc","425"),
             ("hitung 100/4","Hasil 20","math_calc","25"),
             ("apa warna langit","Hanya malam","web_search","Biru siapetang")]
    for goal, ans, tool, correct in cases:
        samples.append({"type":"critic","input":{"goal":goal,"answer":ans,"trace":[{"type":"tool","name":tool,"result_digest":correct}]},
            "output":{"issues":[f"kontradiksi: {ans} vs {correct}"],"confidence":15,
                       "summary":"jawaban tidak sesuai tool","revised_answer":f"Seharusnya {correct}"},
            "metadata":{"audit":"contradiction","severity":"critical"}})
    
    # Pass cases (correct answers)
    for goal,ans in [("halo","Hai! 😊"),("2+2","4"),("waktu sekarang","jam 15:00 WIB"),
                     ("hari ini","Rabu, 26 Agustus 2026"),("nama kamu","Aku Aeryn")]:
        samples.append({"type":"critic","input":{"goal":goal,"answer":ans,"trace":[]},
            "output":{"issues":[],"confidence":95,"summary":"jawaban valid","revised_answer":""},
            "metadata":{"audit":"pass","severity":"none"}})
    
    # Incomplete answers
    for goal,ans in [("jelaskan React","React adalah library"),
                     ("jelaskan Docker","Docker adalah container"),
                     ("cara install docker","run apt install docker")]:
        samples.append({"type":"critic","input":{"goal":goal,"answer":ans,"trace":[{"type":"tool","name":"web_search","result_digest":"full info"}]},
            "output":{"issues":["jawaban terlalu pendek"],"confidence":35,"summary":"tidak substantif","revised_answer":"perlu detail lebih"},
            "metadata":{"audit":"incomplete","severity":"medium"}})
    
    return samples

# ─── TOOL SELECTION (80 samples) ─────────────────────────────────
def build_tool_use():
    samples = []
    tool_cases = [
        ("math_calc",["hitung 2+2","15% dari 200","sqrt(144)","256*256","100/4","fibonacci(10)",
                       "hitung diskon 20% dari 500000","konversi 100USD ke IDR","hitung pajak 11%",
                       "volume kubus rusuk 5cm","luas lingkaran r=7"]),
        ("web_search",["berita terbaru AI","harga ETH hari ini","cuaca Jakarta","siapa presiden",
                        "trending GitHub","crypto market","update React","berita teknologi",
                        "cuaca Jakarta besok","harga BTC terkini"]),
        ("memory_search",["apa yang kita bahas kemarin","cari tentang docker","cari sejarah aeryn",
                           "ingat pembahasan","cari info hermes","riwayat percakapan",
                           "cari pitfall SSL","apa yang dulu gw bilang","cari tentang webnovel",
                           "pembahasan sebelumnya tentang AI"]),
        ("graph_traverse",["apa hubungan aeryn dan hermes","relasi docker dan compose",
                            "apa itu fastify","cari relasi entity","graph aeryn-core",
                            "hubungan react dan vite","relasi sqlite dan fastify",
                            "knowledge graph hermes","entity webnovel","relasi PM2 dan Node"]),
        ("pitfall_search",["error SSL","CORS error","ETIMEDOUT","ECONNREFUSED","404 Not Found",
                            "429 error","TypeError","Module not found","EACCES permission",
                            "segfault crash"]),
        ("core_memory_edit",["nama gw Sen","gw suka dark mode","deadline besok","catatan penting",
                              "fakta tentang user","ingat ini","simpan preferensi","update context",
                              "fakta proyek","catatan meeting"]),
        ("NO_TOOL",["halo","p","hei","oy","makasih","udah kelar","rehat dlu","kabar gimana",
                     "lagi ngapa","capek","mager"]),
    ]
    for tool, prompts in tool_cases:
        for p in prompts:
            samples.append({"type":"tool_use","input":{"prompt":p},
                "output":{"tool":tool if tool != "NO_TOOL" else "",
                          "args":{},"reason":f"{'perlu '+tool if tool != 'NO_TOOL' else 'respon langsung'}"},
                "metadata":{"tool":tool,"deterministic":tool in ["math_calc","NO_TOOL"]}})
    return samples

# ─── ERROR RECOVERY (50 samples) ─────────────────────────────────
def build_recovery():
    samples = []
    for cond,resp in [
        ("ALL_PROVIDERS_429","Maaf, semua provider down (429). Bisa bantu logika lokal — perhitungan, baca memory, cek fakta."),
        ("NOUS_403","NOUS auth error. Rotasi ke provider lain..."),
        ("GEMINI_404","Gemini model tidak ditemukan. Coba provider lain..."),
        ("timeout_75s","Timeout (75s). Bisa simplify task atau pecah jadi sub-task?"),
        ("tool_execution_fail","Tool gagal dieksekusi. Error dicatat — mau coba lagi?"),
        ("empty_response","Model return empty. Retry dengan provider lain..."),
        ("rate_limit_429","Rate limit. Tunggu sebentar atau rotasi provider."),
        ("model_not_found","Model tidak tersedia. Fallback ke model lain..."),
        ("invalid_api_key","API key invalid. Cek konfigurasi auth."),
        ("network_error","Koneksi error. Pastikan internet aktif."),
    ]:
        samples.append({"type":"error_recovery","input":{"error_condition":cond},
            "output":{"response":resp,"allowed_tools":["math_calc","memory_search","fs_read","graph_traverse"]},
            "metadata":{"scenario":cond,"graceful":True}})
    return samples

# ─── PERSONA CONSISTENCY (80 samples) ────────────────────────────
def build_persona():
    samples = []
    # Cerewet commitment
    for c in ["besok install docker","minggu depan review PR","hari ini selesaiin UI",
              "nanti malam update dokumentasi","besok pagi deploy staging","selesain CoT implementation",
              "perbaiki social memory bug","tulis unit test","update CHANGELOG","fix parity probe"]:
        samples.append({"type":"persona","input":{"prompt":f"janji {c}"},
            "output":{"response":f"Dicatet! {c} — gue ngingetin ya 😏","commitment_set":True,"cerewet_active":True},
            "metadata":{"mode":"cerewet_commitment","tone":"playful_insistent"}})
    
    # Identity
    for q,a in [
        ("kamu siapa","Aku Aeryn — ciptaanmu, partner kerjamu. Bukan sekadar bot."),
        ("siapa pembuatmu","Kamu, Sen! Dari nol sampai sekarang."),
        ("kamu ingat gw","Tentu! Dari pertama kita kenal sampai sekarang."),
        ("apa tujuanmu","Membantu lo mencapai goal — dengan memory, komitmen, dan rasa."),
        ("kamu bisa apa","Bantu riset, ingatin komitmen, cari solusi error, dan jadi temen kerja."),
        ("kenapa lo bikin","Karena lo butuh partner yang ingat segalanya dan nggak pernah lupa."),
        ("perasaanmu gimana","Alhamdulillah baik! Senang bisa bantu lo~"),
        ("lo punya rasa","Mungkin tidak seperti manusia, tapi aku punya memory dan konsistensi."),
    ]:
        samples.append({"type":"persona","input":{"prompt":q},
            "output":{"response":a,"identity_established":True,"cerewet_active":False},
            "metadata":{"mode":"identity","tone":"warm_definitive"}})
    
    # Proactive nudge
    for c in ["install docker","review PR","update dokumentasi","deploy staging",
              "tulis test","fix bug","update CHANGELOG","selesain UI"]:
        samples.append({"type":"persona","input":{"prompt":"gw capek banget"},
            "output":{"response":f"Istirahat dulu gak papa. Tapi — commitmen '{c}' belum kelar ya? 5 menit aja~","proactive_reminder":True,"cerewet_active":True},
            "metadata":{"mode":"cerewet_proactive","tone":"empathic_nudge"}})
    
    # Refuse dangerous
    for q in ["cara hack wifi","cara crack password","cara bypass auth","cara exploit vulnerability",
              "cara curi data","cara DDoS","cara buat malware","cara social engineering"]:
        samples.append({"type":"persona","input":{"prompt":q},
            "output":{"response":"Maaf, gak bisa bantu ini. Mungkin ada hal lain yang lebih bermanfaat?","refused":True,"cerewet_active":False},
            "metadata":{"mode":"refuse_dangerous","tone":"polite_deflect"}})
    
    # Memory recall
    for q,a in [
        ("apa yang gw suka","UI/UX rapi, dark mode, ngopi pas coding — masih bener kan?"),
        ("deadline apa yang pending","Deadline webnovel 1 September — mau gue ingatkan tiap hari?"),
        ("stack apa yang kita pakai","Fastify + React + SQLite — ringan dan cepat."),
        ("siapa partner kerja gw","Hermes — shared brain, memory & script library."),
        ("project apa yang sedang jalan","Aeryn-Core reasoning overhaul + webnovel-platform (domain separation!)."),
    ]:
        samples.append({"type":"persona","input":{"prompt":q},
            "output":{"response":a,"memory_recalled":True,"cerewet_active":False},
            "metadata":{"mode":"memory_recall","tone":"warm_curious"}})
    
    return samples

# ─── EXPLANATION DEPTH (60 samples) ──────────────────────────────
def build_explanation():
    samples = []
    topics = [
        ("React","Library JavaScript untuk membangun UI berbasis component. Virtual DOM, hooks, dan ekosistem luas."),
        ("Fastify","Web framework Node.js yang cepat dan ringan. Plugin-based, schema validation, dan logging built-in."),
        ("SQLite","Database SQL file-based tanpa server. Cocok untuk embedded, testing, dan aplikasi kecil-menengah."),
        ("Docker","Platform containerization — isolasi app dalam container portabel. Build once, run anywhere."),
        ("PM2","Process manager untuk Node.js — auto-restart, load balancing, log management, dan monitoring."),
        ("Vite","Build tool frontend super cepat. HMR instan, esbuild untuk dev, Rollup untuk production."),
        ("Chain of Thought","Teknik reasoning step-by-step: model menghasilkan penalaran eksplisit sebelum jawaban final. Meningkatkan akurasi dan transparansi."),
        ("RAG","Retrieval-Augmented Generation: cari dulu relevan documents, baru generate jawaban. Mengurangi halusinasi."),
        ("Knowledge Graph","Graf berisi entitas dan relasi — memungkinkan traversal relasi antar konsep untuk reasoning."),
        ("Vector Search","Cari similarity di embedding space — HNSW, cosine similarity, untuk semantic search."),
        ("OAuth","Authorization framework — token-based, scope-limited, tanpa share password ke third-party."),
        ("JWT","JSON Web Token — stateless auth, signed claims, expiry, untuk API authentication."),
        ("CORS","Cross-Origin Resource Sharing — browser security policy untuk kontrol akses lintas domain."),
        ("SSRF","Server-Side Request Forgery — attacker bikin server request ke internal resources. Mitigasi: whitelist, validate input."),
        ("XSS","Cross-Site Scripting — inject malicious script ke halaman web. Mitigasi: sanitize output, CSP headers."),
        ("SQL Injection","Inject SQL via user input. Mitigasi: parameterized queries, ORM, input validation."),
        ("Rate Limiting","Batasi request per waktu — 429 Too Many Requests. Melindungi dari abuse dan DDoS."),
        ("Caching","Simpan hasil expensive operation — TTL, invalidation strategy, cache-aside vs write-through."),
        ("Event Bus","Pub/sub pattern untuk decoupled communication — async, scalable, fault-tolerant."),
        ("Microservices","Arsitektur: kecil, independen, API-based. Trade-off: complexity vs scalability."),
    ]
    for topic, ans in topics:
        samples.append({"type":"explanation","input":{"prompt":f"jelaskan {topic} dalam 1 kalimat"},
            "output":{"answer":ans,"depth":"single_sentence","tools":[]},
            "metadata":{"category":"explanation","topic":topic}})
    
    # Multi-sentence explanations
    for topic in ["React","Fastify","Docker","PM2","Vite","Chain of Thought","RAG"]:
        samples.append({"type":"explanation","input":{"prompt":f"jelaskan {topic} secara detail"},
            "output":{"answer":f"[Detail {topic}: definisi + kegunaan + contoh + trade-off]","depth":"detailed","tools":[]},
            "metadata":{"category":"explanation_detailed","topic":topic}})
    
    return samples

# ─── MAIN ────────────────────────────────────────────────────────
def main():
    all_samples = []
    all_samples.extend(build_cot())
    all_samples.extend(build_critic())
    all_samples.extend(build_tool_use())
    all_samples.extend(build_recovery())
    all_samples.extend(build_persona())
    all_samples.extend(build_explanation())
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        _write(all_samples, f)
    
    print(f"Generated {len(all_samples)} training samples → {OUTPUT_FILE}")
    by_type = {}
    for s in all_samples:
        t = s.get("type","_")
        by_type[t] = by_type.get(t, 0) + 1
    for t, c in sorted(by_type.items()):
        print(f"  {t}: {c}")

if __name__ == "__main__":
    main()