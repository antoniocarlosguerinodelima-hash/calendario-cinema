#!/usr/bin/env python3
"""Atualiza o calendário de estreias de cinema. Apenas previsões: NÃO confirma sessões locais."""
from __future__ import annotations
import datetime as dt
import hashlib
import html
import re
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup

START = dt.date(2026, 11, 5)
END = dt.date(2028, 12, 31)
FILE = Path("Cinema_Estreias_UCI_Cinemark_Identificados.ics")
UCI = "https://ucicinemas.com.br/Filmes/proximos_lancamentos"
CINEMARK = "https://www.cinemark.com.br/?menu=em_breve"
ALIAS = {
    "verao da lata": "o verao da lata",
    "o nascimento de cristo zero d c": "zero dc",
    "zero d c": "zero dc",
    "hexed": "enfeiticadas bem vindos a hexe",
    "dune part three": "duna parte tres",
    "avengers doomsday": "vingadores doutor destino",
    "avengers secret wars": "vingadores guerras secretas",
    "the cat in the hat": "o gatola da cartola",
    "focker in law": "entrando numa grande fria",
    "the hunger games sunrise on the reaping": "jogos vorazes amanhecer na colheita",
    "zero ad": "zero dc",
}
def normal(s):
    s = "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return ALIAS.get(s, s)

def unfold(s):
    return re.sub(r"\r?\n[ \t]", "", s.replace("\r\n", "\n"))

def unesc(s):
    return s.replace(r"\n", "\n").replace(r"\,", ",").replace(r"\;", ";").replace(r"\\", "\\")

def esc(s):
    return str(s).replace("\\", "\\\\").replace("\n", r"\n").replace(",", r"\,").replace(";", r"\;")

def fold(s):
    chunks, cur = [], ""
    for char in s:
        limit = 75 if not chunks else 74
        if len((cur + char).encode("utf-8")) > limit:
            chunks.append(cur)
            cur = ""
        cur += char
    chunks.append(cur)
    return "\r\n ".join(chunks)

def load():
    out = {}
    if not FILE.exists():
        return out
    source = unfold(FILE.read_text(encoding="utf-8-sig"))
    for block in re.findall(r"BEGIN:VEVENT\n(.*?)\nEND:VEVENT", source, re.S):
        d = re.search(r"^DTSTART;VALUE=DATE:(\d{8})$", block, re.M)
        n = re.search(r"^SUMMARY:(.+)$", block, re.M)
        uid = re.search(r"^UID:(.+)$", block, re.M)
        if not (d and n):
            continue
        try:
            day = dt.datetime.strptime(d.group(1), "%Y%m%d").date()
        except ValueError:
            continue
        if not START <= day <= END:
            continue
        full = unesc(n.group(1))
        title = full.split(" — ", 1)[0].strip()
        k = normal(title)
        if not k:
            continue
        networks = set()
        if re.search(r"\bUCI\b", full, re.I):
            networks.add("UCI")
        if re.search(r"\bCinemark\b", full, re.I):
            networks.add("Cinemark")
        if k not in out:
            out[k] = dict(title=title, date=day, uid=uid.group(1) if uid else None,
                          networks=networks, origin="Base inicial — previsão brasileira")
    return out

def get(url):
    r = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "pt-BR,pt;q=0.9"})
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def upsert(items, title, day, network, origin):
    if not title or not START <= day <= END:
        return
    title = html.unescape(title).strip()
    key = normal(title)
    if not (3 <= len(key) <= 130):
        return
    if key not in items:
        items[key] = dict(title=title, date=day, uid=None, networks=set(), origin=origin)
    rec = items[key]
    rec["networks"].add(network)
    # Uma data divulgada oficialmente pela UCI prevalece sobre a previsão antiga.
    if network == "UCI":
        rec["date"] = day
        rec["origin"] = origin

def uci_updates(items):
    soup = get(UCI)
    found = 0
    # Cada título aparece em um H1, seguido de "Lançamento previsto para: DD/MM/AAAA".
    for h in soup.select("h1"):
        title = h.get_text(" ", strip=True)
        if not title or len(title) > 130:
            continue
        parts = []
        for sibling in h.next_elements:
            if getattr(sibling, "name", None) in ("h1",):
                break
            if isinstance(sibling, str):
                parts.append(sibling.strip())
            if len(parts) >= 45:
                break
        match = re.search(r"Lançamento previsto para\s*:\s*(\d{2}/\d{2}/\d{4})", " ".join(parts), re.I)
        if not match:
            continue
        day = dt.datetime.strptime(match.group(1), "%d/%m/%Y").date()
        upsert(items, title.title() if title.isupper() else title, day, "UCI", "Site oficial UCI — em breve")
        found += 1
    return found

def cinemark_updates(items):
    soup = get(CINEMARK)
    found = 0
    # A página nacional de "em breve" não informa todas as datas;
    # só associa rede ao título quando uma data BR já está no calendário.
    for a in soup.select("a"):
        txt = a.get_text(" ", strip=True)
        match = re.match(r"^(?:PRÉ[- ]VENDA|PRE[- ]VENDA|EM BREVE)\s+(.+)$", txt, re.I)
        if not match:
            continue
        title = re.split(r"\s+(?:Ação|Acao|Aventura|Comedia|Comédia|Terror|Drama|Ficção|Ficcao|Animação|Animacao|Documentário|Documentario|Eventos Especiais|Romance)\b", match.group(1), maxsplit=1, flags=re.I)[0].strip()
        key = normal(title)
        if key in items:
            items[key]["networks"].add("Cinemark")
            found += 1
    return found

def build(items):
    result = ["BEGIN:VCALENDAR", "VERSION:2.0",
              "PRODID:-//Cinema SP//Estreias Brasil 2026-2028//PT-BR",
              "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
              "X-WR-CALNAME:Cinema - UCI Anália Franco + Cinemark Mooca",
              "X-WR-CALDESC:Estreias previstas. Sessões locais precisam ser confirmadas.",
              "REFRESH-INTERVAL;VALUE=DURATION:P1D", "X-PUBLISHED-TTL:PT24H"]
    for key, rec in sorted(items.items(), key=lambda p: (p[1]["date"], p[1]["title"].casefold())):
        day = rec["date"]
        names = [name for name in ("UCI", "Cinemark") if name in rec["networks"]]
        label = " + ".join(names) if names else "BR (previsto)"
        uid = rec["uid"] or hashlib.sha1(key.encode()).hexdigest()[:24] + "@estreias-cinema.local"
        desc = ("Estreia prevista para o Brasil.\n"
                + ("Anunciado nas redes: " + ", ".join(names) if names else "Sem confirmação nas redes UCI e Cinemark")
                + "\nSessões no UCI Anália Franco e Cinemark Mooca Plaza ainda não confirmadas."
                + "\nOrigem: " + rec["origin"]
                + "\nUCI: " + UCI + "\nCinemark: " + CINEMARK)
        result += ["BEGIN:VEVENT", "UID:" + uid, "DTSTAMP:20261105T120000Z",
                   "DTSTART;VALUE=DATE:" + day.strftime("%Y%m%d"),
                   "DTEND;VALUE=DATE:" + (day + dt.timedelta(days=1)).strftime("%Y%m%d"),
                   "SUMMARY:" + esc(rec["title"] + " — " + label),
                   "DESCRIPTION:" + esc(desc), "TRANSP:TRANSPARENT",
                   "BEGIN:VALARM", "ACTION:DISPLAY", "TRIGGER:-P7D",
                   "DESCRIPTION:" + esc("Estreia em 7 dias: " + rec["title"]),
                   "END:VALARM", "END:VEVENT"]
    result.append("END:VCALENDAR")
    return "\r\n".join(fold(line) for line in result) + "\r\n"

def main():
    items = load()
    if not items:
        raise RuntimeError("Arquivo inicial .ics ausente: não sobrescrever calendário.")
    successes = 0
    for label, fn in [("UCI", uci_updates), ("Cinemark", cinemark_updates)]:
        try:
            count = fn(items)
            print(f"{label}: {count} títulos encontrados")
            if count > 0:
                successes += 1
        except Exception as err:
            print(f"AVISO: fonte {label} indisponível: {err}")
    if successes == 0:
        raise RuntimeError("Fontes sem dados: mantida a versão anterior.")
    contents = build(items)
    FILE.write_text(contents, encoding="utf-8", newline="")
    print(f"Calendário atualizado: {len(items)} filmes; até 31/12/2028.")

if __name__ == "__main__":
    main()
