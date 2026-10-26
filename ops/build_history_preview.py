"""Build lazy century snapshots from an unchanged local Cliopatria release.

Only exact name AND Wikidata pairs are selected: upstream reuses some QIDs for
unrelated polities. No geometry simplification, interpolation or DB publication.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

POLITIES = [
    ('Roman Republic', 'roman-republic', 'Q175881'),
    ('Roman Empire', 'roman-empire', 'Q12544'),
    ('Western Roman Empire', 'western-roman-empire', 'Q42834'),
    ('Eastern Roman Empire', 'eastern-roman-empire', 'Q12544'),
    ('Byzantine Empire', 'byzantine-empire', 'Q112039853'),
    ('Achaemenid Empire', 'achaemenid-empire', 'Q389688'),
    ('Macedonian Empire', 'macedonian-empire', 'Q83958'),
    ('Seleucid Empire', 'seleucid-empire', 'Q705904'),
    ('Ptolemaic Kingdom', 'ptolemaic-kingdom', 'Q2320005'),
    ('Parthian Empire', 'parthian-empire', 'Q1986139'),
    ('Sasanian Empire', 'sasanian-empire', 'Q1661685'),
    ('Han Dynasty', 'han-dynasty', 'Q1068371'),
    ('Tang Dynasty', 'tang-dynasty', 'Q9683'),
    ('Yuan Dynasty', 'yuan-dynasty', 'Q7313'),
    ('Ming Dynasty', 'ming-dynasty', 'Q9903'),
    ('Qing Dynasty', 'qing-dynasty', 'Q8733'),
    ('Mongol Empire', 'mongol-empire', 'Q12557'),
    ('Ottoman Empire', 'ottoman-empire', 'Q12560'),
    ('Maurya Empire', 'maurya-empire', 'Q62943'),
    ('Gupta Empire', 'gupta-empire', 'Q11774'),
    ('Kushan Empire', 'kushan-empire', 'Q25979'),
    ('Satavahana Dynasty', 'satavahana-dynasty', 'Q5257'),
    ('Mughal Empire', 'mughal-empire', 'Q33296'),
    ('Rashidun Caliphate', 'rashidun-caliphate', 'Q12490507'),
    ('Umayyad Caliphate', 'umayyad-caliphate', 'Q8575586'),
    ('Abbasid Caliphate', 'abbasid-caliphate', 'Q12536'),
    ('Kingdom of Kush', 'kingdom-of-kush', 'Q241790'),
    ('Kingdom of Axum', 'aksumite-kingdom', 'Q139377'),
    ('Ghana Empire', 'ghana-empire', 'Q206789'),
    ('Mali Empire', 'mali-empire', 'Q184536'),
    ('Songhai Empire', 'songhai-empire', 'Q202687'),
    ('Mayan City-States', 'maya-civilization', 'Q28567'),
    ('Inca Empire', 'inca-empire', 'Q28573'),
    ('Aztec Triple Alliance', 'aztec-triple-alliance', 'Q2608489'),
    ('Kingdom of the Franks', 'kingdom-of-the-franks', 'Q146246'),
    ('Spanish Empire', 'spanish-empire', 'Q80702'),
    ('British Colonial Empire', 'british-colonial-empire', 'Q8680'),
    ('Russian Empire', 'russian-empire', 'Q34266'),
]
MIN_YEAR, MAX_YEAR = -600, 1800


def year_slug(year):
    return f'{abs(year)}bce' if year < 0 else f'{year}ce'


def build(snapshot, output, reviewed=False):
    raw = snapshot.read_bytes()
    with zipfile.ZipFile(snapshot) as archive:
        source = json.loads(archive.read(next(n for n in archive.namelist() if n.endswith('.geojson'))))
    wanted = {name: (identifier, qid) for name, identifier, qid in POLITIES}
    rows, geometries, seen = [], {}, set()
    status = 'reviewed' if reviewed else 'needs_review'
    for feature in source['features']:
        p = feature['properties']
        if p.get('Type') != 'POLITY' or p.get('Name') not in wanted:
            continue
        start, end = p['FromYear'], p['ToYear']
        if start > MAX_YEAR or end < MIN_YEAR:
            continue
        identifier, qid = wanted[p['Name']]
        if p['Wikidata'] != qid or type(start) is not int or type(end) is not int or start > end:
            raise ValueError(f'Unexpected identity or dates: {p}')
        key = f'{identifier}-{year_slug(start)}-{year_slug(end)}'
        layer_id = f'cliopatria-{key}'
        if layer_id in geometries:
            raise ValueError(f'Duplicate interval: {layer_id}')
        geometries[layer_id] = feature['geometry']
        rows.append(dict(id=layer_id, civilizationId=identifier, name=p['Name'], wikidata=qid,
                         validFromYear=start, validToYear=end, areaKm2=p.get('Area'),
                         sourceRecordId=f'cliopatria-record-{key}'))
        seen.add(p['Name'])
    if seen != wanted.keys():
        raise ValueError(f'No rows for {wanted.keys() - seen}')
    rows.sort(key=lambda r: (r['civilizationId'], r['validFromYear']))
    for left, right in zip(rows, rows[1:]):
        if left['civilizationId'] == right['civilizationId'] and left['validToYear'] >= right['validFromYear']:
            raise ValueError(f'Overlapping source intervals: {left["id"]}, {right["id"]}')
    output.mkdir(parents=True, exist_ok=True)
    chunks = []
    for century in range(MIN_YEAR, MAX_YEAR + 1, 100):
        layers = []
        for row in rows:
            if row['validFromYear'] > century + 99 or row['validToYear'] < century:
                continue
            layers.append(dict(id=row['id'], civilizationId=row['civilizationId'], name=f'{row["name"]} (Cliopatria)',
                layerType='source_reported_extent', interpretationKind='boundary_variant',
                interpretationLabel=f'Cliopatria (Seshat) {source["name"]}',
                variantGroup=f'{row["civilizationId"]}-source-readings', isPrimary=False, displayOrder=10,
                validFromYear=row['validFromYear'], validToYear=row['validToYear'], geometryJson=geometries[row['id']],
                isPlaceholder=False, confidence='low', reviewStatus=status,
                sourceNote='Original dated source interpretation. Source checks do not establish exact historical frontiers.',
                sourceRecordIds=[row['sourceRecordId']], claimIds=[]))
        filename = f'century-{century}.json'
        content = json.dumps(dict(layers=layers), separators=(',', ':')) + '\n'
        (output / filename).write_text(content)
        chunks.append(dict(startYear=century, endYear=min(century+99, MAX_YEAR), filename=filename,
                           sha256=hashlib.sha256(content.encode()).hexdigest(), bytes=len(content.encode())))
    catalog = dict(release=source['name'], minYear=MIN_YEAR, maxYear=MAX_YEAR,
        upstreamUrl='https://github.com/Seshat-Global-History-Databank/cliopatria', upstreamLicense='CC-BY-4.0',
        upstreamArtifactSha256=hashlib.sha256(raw).hexdigest(), reviewStatus=status,
        reviewScope='Source identity, inclusive dates, unchanged coordinates and geometry checks. No independent expert historical verification; confidence remains low.',
        coverage='Curated polities only. Missing coverage does not imply empty land. Source intervals may be approximate.',
        rows=rows, chunks=chunks)
    (output / 'catalog.json').write_text(json.dumps(catalog, separators=(',', ':')) + '\n')
    imports = '\n'.join(f"  '{c['startYear']}': () => import('./{c['filename']}')," for c in chunks)
    (output / 'loaders.ts').write_text("// Generated by ops/build_history_preview.py. Geometry loads one century at a time.\n"
        "export const historyChunks = {\n" + imports + "\n};\n")
    print(json.dumps(dict(polities=len(seen), intervals=len(rows), chunks=len(chunks),
                         bytes=sum(c['bytes'] for c in chunks), reviewStatus=status)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('frontend/data/history'))
    parser.add_argument('--reviewed-source-checks', action='store_true',
                        help='Explicitly record completed source checks for the static preview; never publishes to the DB.')
    args = parser.parse_args()
    build(args.snapshot, args.output, args.reviewed_source_checks)
