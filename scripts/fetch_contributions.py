"""Fetch the public contribution calendar and write data/contributions.json.

No token: GitHub serves the calendar as public HTML at /users/<name>/contributions (the fragment the profile page
itself loads). Standard library only, so the daily workflow needs nothing installed.
"""
import json
import re
import urllib.request
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path

USER = 'shanttoosh'
ROOT = Path(__file__).resolve().parent.parent


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}  # cell id -> {date, level, week, weekday}
        self.tips = {}  # cell id -> tooltip text
        self._tip_for = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'td' and a.get('data-date') and a.get('id', '').startswith('contribution-day-component-'):
            weekday, week = (int(x) for x in a['id'].rsplit('-', 2)[-2:])
            self.days[a['id']] = {'date': a['data-date'], 'level': int(a.get('data-level', 0)), 'week': week, 'weekday': weekday}
        elif tag == 'tool-tip' and a.get('for', '').startswith('contribution-day-component-'):
            self._tip_for = a['for']

    def handle_data(self, data):
        if self._tip_for:
            self.tips[self._tip_for] = self.tips.get(self._tip_for, '') + data

    def handle_endtag(self, tag):
        if tag == 'tool-tip':
            self._tip_for = None


def streaks(days):
    """Longest run of days with contributions, and the current one (today may still be empty)."""
    longest = run = 0
    for d in days:
        run = run + 1 if d['count'] else 0
        longest = max(longest, run)
    current = 0
    for i, d in enumerate(reversed(days)):
        if d['count']:
            current += 1
        elif i > 0:
            break
    return longest, current


def main():
    req = urllib.request.Request(f'https://github.com/users/{USER}/contributions', headers={'User-Agent': 'profile-readme'})
    html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8')
    cal = Calendar()
    cal.feed(html)
    if len(cal.days) < 300:
        raise SystemExit(f'only {len(cal.days)} days parsed; the page layout may have changed')
    days = []
    for cid, d in cal.days.items():
        m = re.match(r'\s*(\d[\d,]*) contributions?', cal.tips.get(cid, ''))
        days.append({**d, 'count': int(m.group(1).replace(',', '')) if m else 0})
    days.sort(key=lambda d: d['date'])
    longest, current = streaks(days)
    best = max(days, key=lambda d: d['count'])
    out = {
        'user': USER,
        'from': days[0]['date'],
        'to': days[-1]['date'],
        'total': sum(d['count'] for d in days),
        'activeDays': sum(1 for d in days if d['count']),
        'longestStreak': longest,
        'currentStreak': current,
        'bestDay': {'date': best['date'], 'count': best['count']},
        'days': days,
    }
    path = ROOT / 'data' / 'contributions.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
    print(f"{out['total']} contributions on {out['activeDays']} days ({out['from']} to {out['to']}); "
          f"longest streak {longest}, current {current}")


if __name__ == '__main__':
    main()
