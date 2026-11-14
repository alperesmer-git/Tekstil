-- Örnek veri (boş veritabanında ilk kurulumda çalışır)
INSERT INTO tenant(name) VALUES ('Demo Tekstil');
INSERT INTO unit_of_measure VALUES ('ADET','Adet'),('MT','Metre'),('KG','Kilogram');
INSERT INTO business_partner(tenant_id,code,name,is_customer) VALUES (1,'MUS-001','Örnek Müşteri A.Ş.',true);
INSERT INTO department(tenant_id,code,name) VALUES (1,'KESIM','Kesim'),(1,'DIKIM','Dikim'),(1,'UTU_PAKET','Ütü-Paket');
INSERT INTO production_line(tenant_id,department_id,code,name,operator_count)
  VALUES (1,2,'BANT-1','Bant 1',24),(1,2,'BANT-2','Bant 2',20),(1,1,'KESIM-1','Kesim Masası 1',6);
INSERT INTO size_scale(tenant_id,name) VALUES (1,'S-M-L-XL');
INSERT INTO size(size_scale_id,code,sort_order) VALUES (1,'S',1),(1,'M',2),(1,'L',3),(1,'XL',4);
INSERT INTO color(tenant_id,code,name) VALUES (1,'BYZ','Beyaz'),(1,'LCV','Lacivert');
INSERT INTO style(tenant_id,customer_id,style_code,description,product_group,size_scale_id)
  VALUES (1,1,'TSH-100','Basic tişört','tişört',1),(1,1,'PNT-200','Chino pantolon','pantolon',1);
INSERT INTO routing(style_id) VALUES (1),(2);
INSERT INTO routing_step(routing_id,seq,department_id,total_smv) VALUES (1,1,1,2.5),(1,2,2,9.8),(2,1,1,4),(2,2,2,22);
INSERT INTO sales_order(tenant_id,order_no,customer_id) VALUES (1,'SIP-0001',1);
INSERT INTO order_line(sales_order_id,style_id,ship_date,routing_id) VALUES (1,1,CURRENT_DATE+30,1),(1,2,CURRENT_DATE+40,2);
INSERT INTO work_order(order_line_id,routing_step_id,line_id,planned_qty,planned_start,planned_end) VALUES
  (1,2,1,4000,date_trunc('day',now())+interval '8 hours',date_trunc('day',now())+interval '4 days 17 hours'),
  (2,4,NULL,2500,NULL,NULL),
  (1,1,NULL,4000,NULL,NULL);
