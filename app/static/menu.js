// Sol menü: süreçlere göre gruplar. '@plan' = Plan Panosu ekranı, diğerleri veritabanı tablo adlarıdır.
// Şemadaki her tablo tam olarak bir grupta yer almalıdır (tests/test_menu.py bunu denetler).
const MENU = [
 {id:'planlama', section:'Süreçler', title:'Planlama', items:['@plan','plan_scenario','plan_assignment']},
 {id:'siparis', section:'Süreçler', title:'Sipariş', items:['sales_order','order_line','order_line_qty']},
 {id:'depo', section:'Süreçler', title:'Depo ve Satın Alma', items:['material_requirement','purchase_order','purchase_order_line','material_lot','stock_movement']},
 {id:'kesim', section:'Süreçler', title:'Kesim', items:['marker','marker_size_ratio','cutting_order']},
 {id:'uretim', section:'Süreçler', title:'Üretim', items:['work_order','work_order_variant_qty','production_log','downtime_log','line_balance']},
 {id:'fason', section:'Süreçler', title:'Fason', items:['subcontract_order','subcontract_shipment','subcontract_shipment_line','subcontract_capacity']},
 {id:'kalite', section:'Süreçler', title:'Kalite', items:['defect_type','inspection','inspection_defect']},
 {id:'urun', section:'Tanımlar', title:'Ürün ve Model', items:['season','size_scale','size','color','style','style_variant']},
 {id:'malzeme', section:'Tanımlar', title:'Malzeme ve Ürün Ağacı', items:['material','fabric_spec','bom','bom_line']},
 {id:'rota', section:'Tanımlar', title:'Rota ve Operasyon', items:['department','routing','routing_step','operation']},
 {id:'hat', section:'Tanımlar', title:'Hat ve Kapasite', items:['production_line','machine','operator','operator_skill','changeover_time']},
 {id:'temel', section:'Tanımlar', title:'Temel Tanımlar', items:['tenant','app_user','business_partner','unit_of_measure','working_calendar','working_calendar_day']},
 {id:'analiz', section:'Analiz', title:'Yapay Zeka ve Analiz', items:['efficiency_history','actual_waste_history','delivery_prediction','assistant_audit_log']}
];
