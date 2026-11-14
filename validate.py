from pathlib import Path
import yaml

root=Path(__file__).parent
files=list((root/'api').glob('*-service.yaml'))
assert len(files)==4, f'Expected four service contracts, got {len(files)}'
assert {p.stem for p in files}=={'catalog-service','enrollment-service','payment-service','notification-service'}
for file in files:
    doc=yaml.safe_load(file.read_text(encoding='utf-8'))
    assert doc['openapi'].startswith('3.1.')
    assert doc['paths']
    schemas=doc['components']['schemas']
    assert 'Problem' in schemas
    for path, methods in doc['paths'].items():
        for method, op in methods.items():
            assert op['tags']==(['internal'] if path.startswith('/internal/') else ['public'])
            assert 'responses' in op
            assert all(code in op['responses'] for code in ('400','401','404','409','503'))
            if method=='post':
                assert any(p['name']=='Idempotency-Key' for p in op.get('parameters',[]))
            if op['summary'].startswith('Список'):
                assert {'page','size'} <= {p['name'] for p in op.get('parameters',[])}
            for response in op['responses'].values():
                for media in response.get('content',{}).values():
                    reference=media['schema'].get('$ref')
                    if reference: assert reference.split('/')[-1] in schemas
    print(file.name,'OK:',sum(len(v) for v in doc['paths'].values()),'operations,',len(schemas),'schemas')
assert (root/'docs'/'architecture.drawio').exists()
assert len(list((root/'docs').glob('*.png')))==3
print('Diagrams OK')
