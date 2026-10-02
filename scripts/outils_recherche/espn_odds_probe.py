import requests, json, sys
UA={"User-Agent":"Mozilla/5.0"}
def first_event(sport, league, date):
    r=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard",params={"dates":date},headers=UA,timeout=30).json()
    ev=r.get("events",[])
    return ev[0]["id"] if ev else None, len(ev)
def odds(sport, league, eid):
    u=f"https://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/events/{eid}/competitions/{eid}/odds"
    d=requests.get(u,headers=UA,timeout=30).json()
    out=[]
    for it in d.get("items",[]):
        h=it.get("homeTeamOdds",{}); 
        op=it.get("open") or {}; cl=it.get("close") or {}
        out.append((it.get("provider",{}).get("name"), it.get("details"), it.get("overUnder"), h.get("moneyLine"),
                    "open" if it.get("open") else "", "close" if it.get("close") else "",
                    (h.get("open") or {}).get("moneyLine",{}).get("american") if isinstance(h.get("open"),dict) else None,
                    (h.get("close") or {}).get("moneyLine",{}).get("american") if isinstance(h.get("close"),dict) else None))
    return out
tests=[("basketball","nba",d) for d in ["20080115","20120115","20150115","20190115","20230115","20260115"]]+\
      [("hockey","nhl",d) for d in ["20100115","20150115","20200115","20240115"]]+\
      [("football","nfl",d) for d in ["20101010","20151011","20201011"]]+\
      [("baseball","mlb",d) for d in ["20100715","20150715","20220715"]]+\
      [("soccer","eng.1",d) for d in ["20150321","20200307","20250315"]]+\
      [("soccer","fra.1",d) for d in ["20250315"]]+[("mma","ufc","20250412"),("tennis","atp","20250701"),("rugby","164205","20250315")]
for s,l,d in tests:
    try:
        eid,n=first_event(s,l,d)
        print(s,l,d,"events",n,"id",eid, odds(s,l,eid) if eid else "")
    except Exception as e: print(s,l,d,"ERR",e)
