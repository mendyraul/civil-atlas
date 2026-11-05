"""Local GeoJSON adapters with explicit, archived mapping sidecars."""
import json
import math
from hashlib import sha256

from app.ingestion.pleiades import NormalizedSnapshot
from app.schemas import AtlasRoute, PhysicalFeature, Source, SourceRecord


def validate_geometry(value):
    if not isinstance(value, dict) or value.get('type') not in {'LineString','MultiLineString','Polygon','MultiPolygon'}:
        raise ValueError('unsupported physical geometry')
    kind, coordinates = value['type'], value.get('coordinates')
    lines = coordinates if kind in {'MultiLineString','Polygon'} else ([coordinates] if kind=='LineString' else [ring for polygon in coordinates for ring in polygon])
    if not lines:
        raise ValueError('empty geometry')
    for line in lines:
        if len(line)<2 or (kind in {'Polygon','MultiPolygon'} and (len(line)<4 or line[0]!=line[-1])):
            raise ValueError('incomplete line or ring')
        for point in line:
            if len(point)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in point) or not (-180<=point[0]<=180 and -90<=point[1]<=90):
                raise ValueError('invalid longitude/latitude')
    return value


class GeographyAdapter:
    version = '1'
    source_type = 'historical_gis'

    def __init__(self, mapping):
        self.mapping = mapping
        if mapping.get('license') != self.license or not mapping.get('source_url') or not mapping.get('citation'):
            raise ValueError('mapping must declare the release license, source_url and citation')

    def entity_ids_for(self, external_id):
        return [(self.kind, f'{self.namespace}-{external_id}')]

    def normalize(self, raw, ids, dataset_version, retrieved_at):
        data = json.loads(raw)
        if data.get('type') != 'FeatureCollection' or not isinstance(data.get('features'),list):
            raise ValueError('expected saved GeoJSON FeatureCollection')
        if len(ids)!=len(set(ids)):
            raise ValueError('duplicate selected IDs')
        datasets = {'sources':[], 'source_records':[], self.kind:[]}
        source_id = f'{self.namespace}-source-{dataset_version}'
        notes = 'Source-reported data; editorial review required.'
        citation, url = self.mapping['citation'], self.mapping['source_url']
        # The mapping bytes are part of the normalized manifest hash and archived with it.
        source = Source(id=source_id,source_name=self.label,source_type=self.source_type,url=url,citation=citation,
            license=self.license,dataset_version=dataset_version,reliability_tier='unreviewed',retrieved_at=retrieved_at,
            created_at=retrieved_at,updated_at=retrieved_at).model_dump(mode='json')
        source.update(review_status='needs_review', mapping=self.mapping)
        datasets['sources'].append(source)
        seen, omissions = set(), []
        for feature in data['features']:
            props = feature.get('properties') or {}
            external = str(feature.get('id', props.get(self.mapping.get('id_field','id'),'')))
            if ids and external not in ids:
                continue
            if not external or external in seen:
                raise ValueError('missing or duplicate feature identifier')
            seen.add(external)
            key = f'{self.namespace}-{external}'
            mapping = self.mapping.get('features',{}).get(external,{})
            record_id = f'{key}-record'
            rec = SourceRecord(id=record_id,feature_id=key,feature_kind=self.kind,feature_label=str(props.get('name',external)),
                title=f'{self.label}: {external}',citation=citation,link=url,source_namespace=self.namespace,
                confidence='low',review_status='needs_review',notes=notes+' Original properties: '+json.dumps(props,sort_keys=True)).model_dump(mode='json')
            datasets['source_records'].append(rec)
            try:
                shape = validate_geometry(feature.get('geometry'))
                start,end = mapping.get('start_year'),mapping.get('end_year')
                if start is not None or end is not None:
                    if type(start) is not int or type(end) is not int or start>end or not mapping.get('date_citation'):
                        raise ValueError('dated features require ordered integer years and date_citation')
                common = dict(id=key,label=str(props.get('name',external)),confidence='low',review_status='needs_review',
                    source_record_ids=[record_id],source_notes=citation+' '+notes,source_properties=props,
                    source_id=source_id,date_citation=mapping.get('date_citation'))
                if self.kind=='routes':
                    if start is None:
                        raise ValueError('no source-supported route dates; retained as a source record')
                    if shape['type']!='LineString':
                        raise ValueError('routes require a single continuous LineString')
                    if not mapping.get('source_node_id') or not mapping.get('target_node_id'):
                        raise ValueError('route endpoints require an explicit existing-node crosswalk')
                    value = AtlasRoute(**{k:v for k,v in common.items() if k in AtlasRoute.model_fields},
                        slug=key,kind='route',route_kind='road',edge_type='road',source_node_id=mapping['source_node_id'],
                        target_node_id=mapping['target_node_id'],civilization_ids=mapping.get('civilization_ids',[]),
                        start_year=start,end_year=end,summary='Source-reported Roman road segment.',path=shape['coordinates'],
                        status_badges=['Needs review'],evidence=[]).model_dump(mode='json')
                    value.update({k:v for k,v in common.items() if k not in value})
                else:
                    value = PhysicalFeature(**common,geometry=shape,start_year=start,end_year=end,
                        feature_type=mapping.get('feature_type',self.mapping.get('feature_type','physical_geography'))).model_dump(mode='json')
                rec.update(valid_from_year=start,valid_to_year=end)
                datasets[self.kind].append(value)
            except (ValueError,TypeError,KeyError) as error:
                omissions.append({'id':external,'reason':str(error)})
        omissions.extend({'id':missing,'reason':'selected feature absent'} for missing in sorted(set(ids)-seen))
        return NormalizedSnapshot(datasets,omissions,selected_ids=sorted(seen|set(ids)))


class ItinereAdapter(GeographyAdapter):
    namespace = 'itinere'
    label = 'Itiner-e Roman roads'
    license = 'CC-BY-4.0'
    kind = 'routes'


class AWMCAdapter(GeographyAdapter):
    namespace = 'awmc'
    label = 'Ancient World Mapping Center physical geography'
    license = 'ODbL-1.0'
    kind = 'physical_features'
