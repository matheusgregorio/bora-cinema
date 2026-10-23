"""Busca no AdoroCinema os horários do dia dos filmes do convite e grava sessions.json."""
import datetime, html, json, re, sys, urllib.request, zoneinfo

CINEMAS = {"market": "F0196", "santacruz": "F0174"}
FILMS = {  # id do filme no AdoroCinema -> nome usado na página
    "1000016901": "Cara-de-Barro",
    "1000026649": "O Outro Lado das Redes",
    "1000015739": "Verity",
}
TZ = zoneinfo.ZoneInfo("America/Sao_Paulo")

def fetch(code, local=None):
    if local:
        return open(local, encoding="utf-8").read()
    req = urllib.request.Request(f"https://www.adorocinema.com/programacao/cinema-{code}/",
                                 headers={"User-Agent": "Mozilla/5.0 (bora-cinema; GitHub Actions)"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8")

SHOW = re.compile(r'data-experiences="([^"]*)"[^>]*?data-showtime-id="(\d+)"[^>]*?data-showtime-time="([^"]+)"')

def parse(page, day):
    # the page lists films one after another; cut it at each film title link
    starts = [(m.start(), m.group(1)) for m in re.finditer(r'href="/filmes/filme-(\d+)/"[^>]*>', page)]
    out = {name: [] for name in FILMS.values()}
    for k, (pos, fid) in enumerate(starts):
        if fid not in FILMS:
            continue
        end = starts[k + 1][0] if k + 1 < len(starts) else len(page)
        seen = set()
        for exp, sid, when in SHOW.findall(page[pos:end]):
            dt = datetime.datetime.fromisoformat(when)
            if dt.astimezone(TZ).date() != day:
                continue
            exp = html.unescape(exp)
            ver = "D" if "Dubbed" in exp else "L"
            key = (dt.strftime("%H:%M"), ver)
            if sid in seen or key in {(s["t"], s["v"]) for s in out[FILMS[fid]]}:
                continue
            seen.add(sid)
            out[FILMS[fid]].append({"t": key[0], "v": ver})
    for v in out.values():
        v.sort(key=lambda s: s["t"])
    return out

def main():
    day = datetime.datetime.now(TZ).date()
    if len(sys.argv) > 1:  # testes: data e arquivos locais
        day = datetime.date.fromisoformat(sys.argv[1])
    locals_ = dict(zip(CINEMAS, sys.argv[2:4])) if len(sys.argv) > 3 else {}
    data = {"date": day.isoformat(), "updated": datetime.datetime.now(TZ).isoformat(timespec="minutes"), "cinemas": {}}
    for key, code in CINEMAS.items():
        data["cinemas"][key] = parse(fetch(code, locals_.get(key)), day)
    total = sum(len(s) for c in data["cinemas"].values() for s in c.values())
    with open("sessions.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(json.dumps(data, ensure_ascii=False, indent=1))
    print(f"{total} sessões em {day}")

if __name__ == "__main__":
    main()
