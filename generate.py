"""Generate OpenAPI and diagrams for the mathematics course platform design."""
from pathlib import Path
from xml.etree import ElementTree as ET
import yaml
from PIL import Image, ImageDraw, ImageFont

base=Path(__file__).parent; api=base/'api'; docs=base/'docs'
api.mkdir(exist_ok=True); docs.mkdir(exist_ok=True)
def st(value): return {'type':'string','example':value}
def num(value): return {'type':'integer','example':value}
def obj(fields): return {'type':'object','additionalProperties':False,'required':list(fields),'properties':fields}
def ref(name): return {'$ref':'#/components/schemas/'+name}
problem=obj({'type':st('https://mathcourses.example/problems/conflict'),'title':st('Конфликт'),'status':num(409),'detail':st('Запись уже существует'),'traceId':st('trace-42')})
services={
 'catalog-service':{'entity':'Course','fields':{'id':st('course-101'),'title':st('Алгебра для ЕГЭ'),'priceRub':num(2490),'status':st('PUBLISHED'),'teacherId':st('teacher-7')},'requests':{'CreateCourse':{'title':st('Алгебра для ЕГЭ'),'priceRub':num(2490)}},'ops':[('post','/api/v1/courses','CreateCourse','Course'),('get','/api/v1/courses',None,'CourseList'),('get','/api/v1/courses/{courseId}',None,'Course'),('get','/internal/v1/courses/{courseId}',None,'Course')]},
 'enrollment-service':{'entity':'Enrollment','fields':{'id':st('enr-42'),'courseId':st('course-101'),'studentId':st('student-7'),'priceRub':num(2490),'status':st('PENDING_PAYMENT')},'requests':{'CreateEnrollment':{'courseId':st('course-101')},'ActivateEnrollment':{'paymentId':st('pay-42'),'correlationId':st('corr-42')}},'ops':[('post','/api/v1/enrollments','CreateEnrollment','Enrollment'),('get','/api/v1/enrollments',None,'EnrollmentList'),('get','/api/v1/enrollments/{enrollmentId}',None,'Enrollment'),('get','/internal/v1/enrollments/{enrollmentId}',None,'Enrollment'),('post','/internal/v1/enrollments/{enrollmentId}/activate','ActivateEnrollment','Enrollment'),('post','/internal/v1/enrollments/{enrollmentId}/cancel',None,'Enrollment')]},
 'payment-service':{'entity':'Payment','fields':{'id':st('pay-42'),'enrollmentId':st('enr-42'),'amountRub':num(2490),'status':st('SUCCEEDED')},'requests':{'Charge':{'enrollmentId':st('enr-42'),'amountRub':num(2490),'correlationId':st('corr-42')},'Refund':{'reason':st('Не удалось открыть доступ'),'correlationId':st('corr-42')}},'ops':[('get','/api/v1/payments/{paymentId}',None,'Payment'),('get','/internal/v1/payments/{paymentId}',None,'Payment'),('post','/internal/v1/payments','Charge','Payment'),('post','/internal/v1/payments/{paymentId}/refund','Refund','Payment')]},
 'notification-service':{'entity':'Notification','fields':{'id':st('ntf-42'),'enrollmentId':st('enr-42'),'recipientId':st('student-7'),'kind':st('enrollment.activated'),'status':st('SENT')},'ops':[('get','/api/v1/notifications',None,'NotificationList'),('get','/api/v1/notifications/{notificationId}',None,'Notification'),('get','/internal/v1/notifications/{notificationId}',None,'Notification')]}}
events={
 'course.updated':('catalog-service',['enrollment-service'],{'courseId':st('course-101'),'status':st('PUBLISHED')}),
 'enrollment.created':('enrollment-service',['payment-service'],{'enrollmentId':st('enr-42'),'courseId':st('course-101'),'studentId':st('student-7'),'amountRub':num(2490)}),
 'payment.succeeded':('payment-service',['enrollment-service'],{'enrollmentId':st('enr-42'),'paymentId':st('pay-42')}),
 'payment.failed':('payment-service',['enrollment-service'],{'enrollmentId':st('enr-42'),'reason':st('declined')}),
 'enrollment.activated':('enrollment-service',['notification-service'],{'enrollmentId':st('enr-42'),'studentId':st('student-7')}),
 'enrollment.cancelled':('enrollment-service',['notification-service'],{'enrollmentId':st('enr-42'),'studentId':st('student-7')}),
 'payment.refunded':('payment-service',['enrollment-service','notification-service'],{'enrollmentId':st('enr-42'),'paymentId':st('pay-42')})}
for name,data in services.items():
 entity=data['entity']; schemas={'Problem':problem,entity:obj(data['fields'])}
 schemas[entity+'List']=obj({'items':{'type':'array','items':ref(entity)},'page':num(1),'size':num(20),'total':num(1)})
 for req,fields in data.get('requests',{}).items(): schemas[req+'Request']=obj(fields)
 for event,(publisher,subscribers,payload) in events.items():
  if name in [publisher,*subscribers]:
   schemas['Event_'+event.replace('.','_')]=obj({'eventId':{'type':'string','format':'uuid','example':'e97f4c5a-794e-4dbd-94b1-67e5771076c7'},'eventType':st(event),'occurredAt':{'type':'string','format':'date-time','example':'2026-11-06T10:00:00Z'},'schemaVersion':num(1),'correlationId':st('corr-42'),'payload':obj(payload)})
 paths={}
 for method,path,request,response in data['ops']:
  params=[{'name':part[1:-1],'in':'path','required':True,'schema':{'type':'string','example':'example-42'}} for part in path.split('/') if part.startswith('{')]
  if method=='post': params.append({'name':'Idempotency-Key','in':'header','required':True,'schema':{'type':'string','format':'uuid','example':'e97f4c5a-794e-4dbd-94b1-67e5771076c7'}})
  if response.endswith('List'): params += [{'name':field,'in':'query','schema':{'type':'integer','minimum':1,'default':default}} for field,default in [('page',1),('size',20)]]
  sample={'items':[],'page':1,'size':20,'total':0} if response.endswith('List') else {k:v['example'] for k,v in data['fields'].items()}
  op={'tags':['internal' if path.startswith('/internal/') else 'public'],'summary':method.upper()+' '+path,'operationId':method+''.join(p.strip('{}').title() for p in path.split('/') if p),'parameters':params,'responses':{'201' if method=='post' and path=='/api/v1/enrollments' else '200':{'description':'Успех','content':{'application/json':{'schema':ref(response),'example':sample}}}}}
  if request: op['requestBody']={'required':True,'content':{'application/json':{'schema':ref(request+'Request'),'example':{k:v['example'] for k,v in data['requests'][request].items()}}}}
  for code,title in [('400','Некорректный запрос'),('401','Не авторизован'),('404','Не найдено'),('409','Конфликт'),('503','Сервис недоступен')]: op['responses'][code]={'description':title,'content':{'application/problem+json':{'schema':ref('Problem'),'example':{'type':'https://mathcourses.example/problems/http-'+code,'title':title,'status':int(code),'detail':'Описание ошибки','traceId':'trace-42'}}}}
  paths.setdefault(path,{})[method]=op
 spec={'openapi':'3.1.0','info':{'title':name,'version':'1.0.0','description':'Платформа онлайн курсов по математике','license':{'name':'MIT','identifier':'MIT'}},'servers':[{'url':'https://api.mathcourses.example'}],'security':[{'bearerAuth':[]}],'tags':[{'name':'public','description':'Через API Gateway'},{'name':'internal','description':'Только для сервисов'}],'paths':paths,'components':{'securitySchemes':{'bearerAuth':{'type':'http','scheme':'bearer','bearerFormat':'JWT'}},'schemas':schemas}}
 (api/(name+'.yaml')).write_text(yaml.safe_dump(spec,allow_unicode=True,sort_keys=False,width=100),encoding='utf-8')

nodes=[('client','Веб клиент',30,350),('gateway','API Gateway',250,350),('keycloak','JWT mock',250,520),('catalog','catalog-service',510,80),('enrollment','enrollment-service',510,260),('payment','payment-service',510,440),('notification','notification-service',510,620),('cdb','catalog_data',800,80),('edb','enrollment_data',800,260),('pdb','payment_data',800,440),('ndb','notification_data',800,620),('broker','RabbitMQ',1090,350),('provider','Платёжный mock',1370,440),('email','Email mock',1370,620)]
edges=[('client','gateway','HTTPS /api/v1/*',False),('gateway','keycloak','JWT mock',False),('gateway','catalog','GET /courses',False),('gateway','enrollment','POST /enrollments',False),('gateway','payment','GET /payments/{id}',False),('gateway','notification','GET /notifications',False),('enrollment','catalog','GET /internal/v1/courses/{id}',False),('enrollment','payment','GET /internal/v1/payments/{id}',False),('payment','enrollment','GET /internal/v1/enrollments/{id}',False),('catalog','cdb','JSON volume',False),('enrollment','edb','JSON volume',False),('payment','pdb','JSON volume',False),('notification','ndb','JSON volume',False),('payment','provider','локальный режим',False),('notification','email','локальный режим',False),('catalog','broker','course.updated',True),('enrollment','broker','enrollment.created/activated/cancelled',True),('payment','broker','payment.succeeded/failed/refunded',True),('broker','enrollment','payment.* / course.updated',True),('broker','payment','enrollment.created',True),('broker','notification','enrollment.* / payment.refunded',True)]
mx=ET.Element('mxfile',host='app.diagrams.net'); dia=ET.SubElement(mx,'diagram',name='Architecture'); graph=ET.SubElement(dia,'mxGraphModel',page='1',pageWidth='1700',pageHeight='900'); root=ET.SubElement(graph,'root');ET.SubElement(root,'mxCell',id='0');ET.SubElement(root,'mxCell',id='1',parent='0')
for ident,label,x,y in nodes:
 c=ET.SubElement(root,'mxCell',id=ident,value=label,style='rounded=1;whiteSpace=wrap;html=1;fillColor=#EAF2F8;strokeColor=#476782;',vertex='1',parent='1');ET.SubElement(c,'mxGeometry',x=str(x),y=str(y),width='200',height='64',attrib={'as':'geometry'})
for idx,(source,target,label,async_) in enumerate(edges):
 c=ET.SubElement(root,'mxCell',id='edge'+str(idx),value=label,style='endArrow=block;html=1;'+('dashed=1;' if async_ else ''),edge='1',source=source,target=target,parent='1');ET.SubElement(c,'mxGeometry',relative='1',attrib={'as':'geometry'})
ET.ElementTree(mx).write(docs/'architecture.drawio',encoding='utf-8',xml_declaration=True)
try: big=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
except:big=ImageFont.load_default();small=big
im=Image.new('RGB',(1700,1120),'white');d=ImageDraw.Draw(im);d.text((40,25),'Онлайн курсы по математике — архитектура',font=big,fill='#152B42')
coordinates={ident:(x,y+70) for ident,_label,x,y in nodes}
for source,target,_label,asynchronous in edges:
 sx,sy=coordinates[source]; tx,ty=coordinates[target]
 start=(sx+200 if tx>sx else sx, sy+30); end=(tx if tx>sx else tx+200, ty+30)
 color='#A66A25' if asynchronous else '#365F85'
 if asynchronous:
  segments=12
  for step in range(segments):
   if step % 2 == 0:
    a=step/segments; b=min((step+0.55)/segments,1)
    d.line((start[0]+(end[0]-start[0])*a,start[1]+(end[1]-start[1])*a,start[0]+(end[0]-start[0])*b,start[1]+(end[1]-start[1])*b),fill=color,width=2)
 else: d.line((start,end),fill=color,width=2)
 d.polygon([(end[0],end[1]),(end[0]-8 if tx>sx else end[0]+8,end[1]-4),(end[0]-8 if tx>sx else end[0]+8,end[1]+4)],fill=color)
for ident,label,x,y in nodes:
 d.rounded_rectangle((x,y+70,x+200,y+130),radius=8,fill='#EAF2F8',outline='#476782',width=2);d.text((x+10,y+88),label,font=small,fill='#152B42')
d.text((40,820),'Синхронные вызовы',font=big,fill='#152B42')
for j,line in enumerate(['enrollment → catalog: GET /internal/v1/courses/{courseId}','enrollment → payment: GET /internal/v1/payments/{paymentId}','payment → enrollment: GET /internal/v1/enrollments/{enrollmentId}']):d.text((50,855+j*32),line,font=small,fill='#365F85')
d.text((40,970),'События RabbitMQ',font=big,fill='#152B42')
for j,line in enumerate(['enrollment.created → payment','payment.succeeded / failed → enrollment','enrollment.activated / cancelled → notification']):d.text((50,1005+j*32),line,font=small,fill='#754E25')
im.save(docs/'architecture.png')
def sequence(filename,title,steps):
 actors=['Студент','Gateway','Catalog','Enrollment','RabbitMQ','Payment','Шлюз оплаты','Notification']; xs=[100+210*j for j in range(len(actors))];im=Image.new('RGB',(1700,170+len(steps)*58),'white');d=ImageDraw.Draw(im);d.text((40,20),title,font=big,fill='#152B42')
 for j,a in enumerate(actors):d.rounded_rectangle((xs[j]-85,65,xs[j]+85,105),radius=5,fill='#EAF2F8',outline='#476782');d.text((xs[j]-76,77),a,font=small,fill='#152B42');d.line((xs[j],105,xs[j],im.height-30),fill='#B9C6D1',width=2)
 for j,(a,b,label) in enumerate(steps):
  y=140+j*58;x1=xs[actors.index(a)];x2=xs[actors.index(b)];d.line((x1,y,x2,y),fill='#365F85',width=2);d.polygon([(x2,y),(x2-8 if x2>x1 else x2+8,y-4),(x2-8 if x2>x1 else x2+8,y+4)],fill='#365F85');d.text((min(x1,x2)+8,y-24),label,font=small,fill='#1E344A')
 im.save(docs/filename)
sequence('sequence-success.png','Запись на курс — успешный путь',[('Студент','Gateway','POST /enrollments'),('Gateway','Enrollment','создать PENDING_PAYMENT'),('Enrollment','Catalog','GET /internal/v1/courses/{id}'),('Catalog','Enrollment','цена и доступность'),('Enrollment','RabbitMQ','enrollment.created'),('RabbitMQ','Payment','создать списание'),('Payment','Шлюз оплаты','charge'),('Шлюз оплаты','Payment','успех'),('Payment','RabbitMQ','payment.succeeded'),('RabbitMQ','Enrollment','открыть доступ'),('Enrollment','RabbitMQ','enrollment.activated'),('RabbitMQ','Notification','отправить письмо'),('Студент','Gateway','GET /enrollments/{id}: ACTIVE')])
sequence('sequence-failure.png','Запись на курс — отказ оплаты',[('Студент','Gateway','POST /enrollments'),('Gateway','Enrollment','создать PENDING_PAYMENT'),('Enrollment','Catalog','проверить курс и цену'),('Enrollment','RabbitMQ','enrollment.created'),('RabbitMQ','Payment','создать списание'),('Payment','Шлюз оплаты','charge'),('Шлюз оплаты','Payment','отказ'),('Payment','RabbitMQ','payment.failed'),('RabbitMQ','Enrollment','отменить запись'),('Enrollment','RabbitMQ','enrollment.cancelled'),('RabbitMQ','Notification','уведомить студента'),('Студент','Gateway','GET /enrollments/{id}: CANCELLED')])
print('Generated four API contracts and three diagrams')
